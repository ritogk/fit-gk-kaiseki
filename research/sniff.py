"""K-Line passive sniffer — HDS等が流す信号をそのまま盗み見る.

自分からは何も送信しない。ポートを開いてひたすら受信バイトを表示する。
OBD2を分岐してHDSと並列接続した状態で使う。

Usage:
    .venv/bin/python research/sniff.py [port] [baud]
    例: .venv/bin/python research/sniff.py /dev/ttyUSB0 10400
    Ctrl+C で停止。
"""
import sys
import time
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
BAUD = int(sys.argv[2]) if len(sys.argv) > 2 else 10400

KNOWN_ADDRS = {
    0x10: "ECM", 0x11: "TCM", 0x12: "ABS", 0x13: "SRS",
    0x14: "EPS", 0x17: "TPMS", 0x1A: "A/C", 0x1E: "MICU",
    0x30: "METER", 0x40: "IMMO", 0x46: "GW",
    0xF0: "TESTER", 0xF1: "TESTER2",
}

SID_NAMES = {
    0x10: "StartDiag",
    0x11: "ECUReset",
    0x14: "ClearDTC",
    0x18: "ReadDTCbyStatus",
    0x1A: "ReadECUIdent",
    0x20: "StopDiag",
    0x21: "ReadDataByLocalId",
    0x22: "ReadDataByCommonId",
    0x27: "SecurityAccess",
    0x30: "IOControlByLocalId",
    0x31: "RoutineControl",
    0x34: "RequestDownload",
    0x36: "TransferData",
    0x3E: "TesterPresent",
    0x81: "StartComm",
    0xC1: "StartCommPR",
}


def addr_name(a):
    return KNOWN_ADDRS.get(a, f"0x{a:02X}")


def sid_name(s):
    if s >= 0x40 and (s - 0x40) in SID_NAMES:
        return SID_NAMES[s - 0x40] + "_PR"
    return SID_NAMES.get(s, f"0x{s:02X}")


def try_parse_frames(buf):
    """バッファからKWP2000フレームを可能な限りパースして表示する."""
    i = 0
    consumed = 0
    while i < len(buf):
        b = buf[i]

        # Format: 0x80 TGT SRC LEN [data...] CS
        if b == 0x80 and i + 4 < len(buf):
            tgt = buf[i + 1]
            src = buf[i + 2]
            length = buf[i + 3]
            end = i + 4 + length + 1  # +1 for checksum
            if end > len(buf):
                break  # incomplete
            frame = buf[i:end]
            expected_cs = sum(buf[i:end - 1]) & 0xFF
            actual_cs = buf[end - 1]
            cs_ok = "OK" if expected_cs == actual_cs else "BAD"

            data = buf[i + 4:i + 4 + length]
            sid = data[0] if data else 0
            ts = time.strftime("%H:%M:%S")

            print(f"[{ts}] {addr_name(src)} -> {addr_name(tgt)}  "
                  f"SID={sid_name(sid)}  "
                  f"data={data.hex(' ')}  "
                  f"raw={frame.hex(' ')}  CS={cs_ok}")

            consumed = end
            i = end
            continue

        # Format: 0x8X (length in upper byte, 1-byte header variant)
        if 0x81 <= b <= 0xBF and i + 3 < len(buf):
            length = b & 0x3F
            tgt = buf[i + 1]
            src = buf[i + 2]
            end = i + 3 + length + 1
            if end > len(buf):
                break
            frame = buf[i:end]
            expected_cs = sum(buf[i:end - 1]) & 0xFF
            actual_cs = buf[end - 1]
            cs_ok = "OK" if expected_cs == actual_cs else "BAD"

            data = buf[i + 3:i + 3 + length]
            sid = data[0] if data else 0
            ts = time.strftime("%H:%M:%S")

            print(f"[{ts}] {addr_name(src)} -> {addr_name(tgt)}  "
                  f"SID={sid_name(sid)}  "
                  f"data={data.hex(' ')}  "
                  f"raw={frame.hex(' ')}  CS={cs_ok}")

            consumed = end
            i = end
            continue

        i += 1
        consumed = i

    return consumed


def main():
    print(f"=== K-Line Sniffer ===")
    print(f"Port: {PORT}  Baud: {BAUD}")
    print(f"何も送信しません。HDS側の信号を受信待機中...")
    print(f"Ctrl+C で停止\n")

    s = serial.Serial(PORT, BAUD, timeout=0.1)
    s.dtr = False
    s.rts = False
    s.reset_input_buffer()

    buf = bytearray()
    raw_count = 0

    try:
        while True:
            chunk = s.read(256)
            if not chunk:
                continue

            # 生バイトも表示（パース失敗時の手がかり用）
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] RAW({len(chunk):3d}): {chunk.hex(' ')}")

            buf.extend(chunk)
            consumed = try_parse_frames(buf)
            if consumed > 0:
                buf = buf[consumed:]

    except KeyboardInterrupt:
        print("\n停止しました。")
    finally:
        s.close()


if __name__ == "__main__":
    main()
