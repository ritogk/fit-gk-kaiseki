"""ライブ can0 受信スレッド。

設計（低遅延の肝）:
- socketcan の ``bus.recv()`` はブロッキングなので、必ず専用デーモンスレッドで回す。
  asyncio イベントループは絶対に塞がない（K-Line ワーカーと同じ教訓）。
- 受信→即デコード→最新値 dict を更新→ ``on_update`` で asyncio 側へ dirty 通知。
- マップ済み ID（DBC に定義のある約25種）以外はデコードせず捨てる＝CPU/遅延削減。
- can0 が down / 未 up の時は OSError を捕まえて 1秒ごとに再接続を試みる。
"""
import logging
import threading
import time

import can
import cantools

from .config import CAN_CHANNEL, DBC_PATH, STALE_SEC

log = logging.getLogger("can-live.reader")


class CanReader:
    def __init__(self, dbc_path=DBC_PATH, channel: str = CAN_CHANNEL):
        self.db = cantools.database.load_file(str(dbc_path))
        self._frame_by_id = {m.frame_id: m for m in self.db.messages}
        self._latest: dict[str, float] = {}
        # 生バイト保持（DBC 未定義 ID も含む全 ID）。実車校正の生バイト・ライブ表示用。
        self._raw_frames: dict[int, dict] = {}
        self._lock = threading.Lock()
        self._last_rx = 0.0
        self._on_update = None
        self._channel = channel
        self._stop = False

    def start(self, on_update=None) -> None:
        """受信スレッド起動。on_update は新フレーム反映後に毎回呼ばれる（引数なし）。"""
        self._on_update = on_update
        threading.Thread(target=self._run, name="can-reader", daemon=True).start()

    def stop(self) -> None:
        self._stop = True

    def _run(self) -> None:
        while not self._stop:
            bus = None
            try:
                bus = can.interface.Bus(
                    channel=self._channel,
                    interface="socketcan",
                    receive_own_messages=False,
                )
            except (OSError, can.CanError) as e:
                # can0 が未 up など。1秒後に再試行（再接続ハンドリング）。
                log.warning("can0 open failed (%s); retry in 1s", e)
                time.sleep(1.0)
                continue

            log.info("can0 opened on %s", self._channel)
            try:
                while not self._stop:
                    msg = bus.recv(timeout=1.0)
                    if msg is None:
                        continue  # 無音。staleness は is_alive() 側で判定。
                    now = time.time()
                    i = msg.arbitration_id
                    data = list(msg.data)

                    # まず生バイトを記録（全 ID。校正用ライブ表示の元データ）。
                    decoded = None
                    m = self._frame_by_id.get(i)
                    if m is not None:
                        try:
                            decoded = m.decode(
                                bytes(data), decode_choices=False, allow_truncated=True
                            )
                        except Exception:
                            decoded = None  # 長さ不整合など壊れフレームは飛ばす

                    with self._lock:
                        rf = self._raw_frames.get(i)
                        if rf is None:
                            self._raw_frames[i] = {
                                "dlc": msg.dlc,
                                "data": data,
                                "count": 1,
                            }
                        else:
                            rf["dlc"] = msg.dlc
                            rf["data"] = data
                            rf["count"] += 1
                        if decoded is not None:
                            self._latest.update(decoded)
                        self._last_rx = now

                    if self._on_update is not None:
                        self._on_update()
            except (OSError, can.CanError) as e:
                # can0 が down/消失（Network is down 等）。bus を畳んで 0.5s 後に再オープン。
                log.warning("can0 read error (%s); reopening", e)
            finally:
                if bus is not None:
                    try:
                        bus.shutdown()
                    except Exception:
                        pass
            time.sleep(0.5)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._latest)

    def raw_frames_snapshot(self) -> list:
        """全 ID の生バイトを id 昇順で返す（校正用ライブ表示）。"""
        with self._lock:
            items = sorted(self._raw_frames.items())
            return [
                {
                    "id": i,
                    "hex": f"0x{i:03X}",
                    "dlc": v["dlc"],
                    "data": list(v["data"]),
                    "count": v["count"],
                }
                for i, v in items
            ]

    def is_alive(self) -> bool:
        return (time.time() - self._last_rx) < STALE_SEC
