#!/usr/bin/env python3
"""
2系統ライトでポリリズムを刻む。
K-Line は半二重 → 時系列で interleave、 各 fire ~80ms。
衝突は時刻ソートで自動回避。

usage: light_polyrhythm.py [BPM=120] [measures=8]
"""
import serial, time, sys

PORT = "/dev/ttyUSB0"
BAUD = 10400

# 各ライトの hit duration (短すぎると見えない、 長すぎると遅延)
HB_DUR = 0.10  # ハイビーム — 短tap
HZ_DUR = 0.20  # ハザード — MICU リレー engage まで時間欲しい

BPM = int(sys.argv[1]) if len(sys.argv) > 1 else 120
MEASURES = int(sys.argv[2]) if len(sys.argv) > 2 else 8


def cs(d):
    return sum(d) & 0xFF


def send(s, payload, wait=0.04):
    msg = bytes(payload) + bytes([cs(payload)])
    s.reset_input_buffer()
    s.write(msg); s.flush()
    time.sleep(wait)
    s.read(128)


def make_pattern():
    """HB = 4拍 (4分音符), HZ = 3拍/小節 (3連符相当) → 4 against 3"""
    beat_sec = 60.0 / BPM
    measure_sec = 4 * beat_sec
    p = []
    for m in range(MEASURES):
        base = m * measure_sec
        # HB: 4 hits per measure (0, 1, 2, 3 ビート)
        for i in range(4):
            p.append((base + i * beat_sec, 0x1D, 0x0F, HB_DUR, "HB "))
        # HZ: 3 hits per measure (0, 4/3, 8/3 ビート)
        for i in range(3):
            p.append((base + i * (measure_sec / 3), 0x08, 0x0F, HZ_DUR, "HZ "))
    return sorted(p)


def main():
    s = serial.Serial(PORT, BAUD, timeout=0.005)
    s.dtr = False; s.rts = False
    time.sleep(0.3); s.reset_input_buffer()
    s.break_condition = True; time.sleep(0.025)
    s.break_condition = False; time.sleep(0.025)
    sc_msg = bytes([0x81, 0x46, 0xF0, 0x81, cs([0x81, 0x46, 0xF0, 0x81])])
    s.write(sc_msg); s.flush()
    time.sleep(0.2)
    raw = s.read(128)
    if not (raw and 0xC1 in raw):
        print("StartComm失敗"); s.close(); return 1
    print("StartComm OK")

    pattern = make_pattern()
    STOP = [0x80, 0x10, 0xF0, 0x01, 0x20]
    print(f"--- {BPM} BPM × {MEASURES}小節 ---")
    print(f"--- HB(ハイビーム): 4分音符 / HZ(ハザード): 3連符 (4-against-3) ---\n")

    start = time.time()
    for offset, lid, iocp, dur, label in pattern:
        target = start + offset
        while time.time() < target:
            time.sleep(0.0005)
        on_cmd = [0x80, 0x10, 0xF0, 0x08, 0x30, lid, iocp, 0, 0, 0, 0, 0]
        send(s, on_cmd, wait=0.04)
        remain = dur - 0.04
        if remain > 0:
            time.sleep(remain)
        send(s, STOP, wait=0.03)
        t = time.time() - start
        print(f"  t={t:6.2f}s {label}")

    print(f"\n=== 終了 ({time.time()-start:.1f}s) ===")
    s.close()


if __name__ == "__main__":
    raise SystemExit(main())
