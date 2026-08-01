"""実ハード無しで can-live を検証する（仮想バス）。

CAN アダプタや車が無い場所で、 受信→デコード→WebSocket 配信のパイプラインと、
送信→ISO-TP→UDS 往復が成立するかを確認する。 macOS でもそのまま動く。

    ../.venv/bin/python vbus_test.py          # 両方
    ../.venv/bin/python vbus_test.py pipeline # 受信パイプラインのみ
    ../.venv/bin/python vbus_test.py isotp    # 送信/ISO-TP/UDS のみ

依存: python-can, cantools（pipeline）/ can-isotp（isotp）
socketcan は使わない。 can.interface.Bus を virtual に差し替えて回すので、
server 側が interface="socketcan" 固定のままでも動く。

背景と macOS での動かし方は docs/macos-can.md を参照。
"""
import asyncio
import json
import struct
import sys
import threading
import time

import can

VCHAN = "canlive-vbus-test"
PORT = 8199

_real_bus = can.interface.Bus


def _virtual_bus(*_a, **_kw):
    return _real_bus(channel=VCHAN, interface="virtual", receive_own_messages=False)


# ---------------------------------------------------------------- pipeline


def _sample_frames():
    """実車相当の合成フレーム: RPM=3500 / ステア=-123.4deg / アクセル≈50% / 車速≈60km/h。"""
    thr = bytearray(8)
    thr[3] = 128  # THR_AccelPos = 128 * 0.392 = 50.176 %

    steer = bytearray(6)
    struct.pack_into(">h", steer, 0, -1234)  # STR_Angle = -123.4 deg

    rpm = bytearray(8)
    struct.pack_into(">H", rpm, 2, 3500)  # ENG_RPM = 3500

    ws = bytearray(8)
    struct.pack_into(">H", ws, 0, 6000)  # WS_FL = 60.00 km/h
    struct.pack_into(">H", ws, 2, 6010)  # WS_FR = 60.10 km/h
    struct.pack_into(">H", ws, 4, 5990)  # WS_RL = 59.90 km/h

    brake = bytearray(8)
    brake[0] = 1  # BRK_State = 1

    return [
        (0x130, bytes(thr)),
        (0x156, bytes(steer)),
        (0x17C, bytes(rpm)),
        (0x1D0, bytes(ws)),
        (0x1A4, bytes(brake)),
        (0x999, b"\xde\xad\xbe\xef"),  # DBC 未定義 ID（生バイト一覧にだけ出るはず）
    ]


def _feed(stop):
    """server がバスを開くのを待ってから合成フレームを流し続ける。"""
    time.sleep(2.0)
    bus = _virtual_bus()
    frames = _sample_frames()
    while not stop.is_set():
        for fid, data in frames:
            bus.send(can.Message(arbitration_id=fid, data=data, is_extended_id=False))
        time.sleep(0.02)
    bus.shutdown()


async def _check_ws():
    import websockets

    await asyncio.sleep(3.0)
    async with websockets.connect(f"ws://127.0.0.1:{PORT}/api/canlive/ws") as ws:
        got = []
        t0 = time.time()
        while time.time() - t0 < 3.0 and len(got) <= 60:
            got.append(json.loads(await ws.recv()))

    frame = [m for m in got if m.get("type") == "frame"][-1]
    s = frame["signals"]
    print("signals:", json.dumps(s, ensure_ascii=False))
    print("観測ID :", [f["hex"] for f in frame["frames"]])

    checks = {
        "rpm == 3500": s["rpm"] == 3500,
        "steeringAngle == -123.4": abs(s["steeringAngle"] + 123.4) < 0.05,
        "throttle ≈ 50.2": abs(s["throttle"] - 50.2) < 0.2,
        "speed ≈ 60.05": abs(s["speed"] - 60.05) < 0.1,
        "brakePressed": s["brakePressed"] is True,
        "alive": frame["alive"] is True,
        "未定義ID 0x999 も raw に出る": any(f["hex"] == "0x999" for f in frame["frames"]),
    }
    for k, v in checks.items():
        print(f"  {'OK ' if v else 'NG '} {k}")
    return all(checks.values())


def test_pipeline() -> bool:
    """can0 受信 → cantools デコード → WS 配信 を仮想バスで通す。"""
    print("=== pipeline: 受信→デコード→WS配信 ===")
    import uvicorn

    can.interface.Bus = _virtual_bus  # server 側の socketcan 固定を回避
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from server.main import app

    stop = threading.Event()
    cfg = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    threading.Thread(target=uvicorn.Server(cfg).run, daemon=True).start()
    threading.Thread(target=_feed, args=(stop,), daemon=True).start()
    try:
        return asyncio.run(_check_ws())
    finally:
        stop.set()


# ------------------------------------------------------------------- isotp


def test_isotp() -> bool:
    """送信 → ISO-TP マルチフレーム → UDS 往復。

    Linux の kernel モジュール(can-isotp.ko)は使わず純Python実装で行う。
    bus を gs_usb / slcan に差し替えれば実機でも同じコードが通る。
    """
    print("=== isotp: 送信→ISO-TP→UDS 往復 ===")
    import isotp

    def addr(tx, rx):
        return isotp.Address(isotp.AddressingMode.Normal_11bits, txid=tx, rxid=rx)

    stop, received = threading.Event(), []

    def ecu():
        """ECU 役: リクエストを受けたら UDS 肯定応答(0x62) を 40byte で返す。"""
        bus = _real_bus(channel="diag", interface="virtual", receive_own_messages=False)
        stack = isotp.CanStack(bus, address=addr(0x7E8, 0x7E0))
        while not stop.is_set():
            stack.process()
            if stack.available():
                received.append(bytes(stack.recv()))
                stack.send(bytes([0x62, 0xF1, 0x90]) + bytes(range(37)))
            time.sleep(0.001)
        bus.shutdown()

    threading.Thread(target=ecu, daemon=True).start()
    time.sleep(0.3)

    bus = _real_bus(channel="diag", interface="virtual", receive_own_messages=False)
    stack = isotp.CanStack(bus, address=addr(0x7E0, 0x7E8))

    # 単一フレームに収まらない 12byte → FirstFrame + FlowControl + ConsecutiveFrame
    req = bytes([0x22, 0xF1, 0x90]) + bytes(range(9))
    stack.send(req)

    resp, t0 = None, time.time()
    while time.time() - t0 < 3.0:
        stack.process()
        if stack.available():
            resp = bytes(stack.recv())
            break
        time.sleep(0.001)

    stop.set()
    time.sleep(0.2)
    bus.shutdown()

    print(f"  リクエスト   : {req.hex()} ({len(req)}byte)")
    print(f"  ECU が受信   : {received[0].hex() if received else '(なし)'}")
    print(f"  レスポンス   : {resp.hex() if resp else '(なし)'} ({len(resp) if resp else 0}byte)")

    checks = {
        "ECU がリクエストを完全受信": bool(received) and received[0] == req,
        "UDS 肯定応答 0x62": resp is not None and resp[0] == 0x62,
        "マルチフレーム 40byte 復元": resp is not None and len(resp) == 40,
    }
    for k, v in checks.items():
        print(f"  {'OK ' if v else 'NG '} {k}")
    return all(checks.values())


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    results = {}
    if which in ("all", "isotp"):
        results["isotp"] = test_isotp()
    if which in ("all", "pipeline"):
        results["pipeline"] = test_pipeline()
    if not results:
        print(f"usage: {sys.argv[0]} [all|pipeline|isotp]", file=sys.stderr)
        raise SystemExit(2)
    print("=== RESULT:", "PASS" if all(results.values()) else "FAIL", results)
    raise SystemExit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
