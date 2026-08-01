#!/usr/bin/env python3
"""
ハイビーム + ロービーム + ハザード の 3系統ビート。
- HB (LID 0x1D): 4分音符 (毎拍)
- LB (LID 0x1C): 8分裏 (offbeat)
- HZ (LID 0x08): 1拍目と3拍目 (downbeat accent)
"""
import serial, time, sys

PORT = "/dev/ttyUSB0"
BAUD = 10400

BPM = int(sys.argv[1]) if len(sys.argv) > 1 else 120
MEASURES = int(sys.argv[2]) if len(sys.argv) > 2 else 8

HB_DUR = 0.08
LB_DUR = 0.08
HZ_DUR = 0.18  # 少し長め (リレー engage 余裕)


def cs(d):
    return sum(d) & 0xFF


def send(s, payload, wait=0.03):
    msg = bytes(payload) + bytes([cs(payload)])
    s.reset_input_buffer()
    s.write(msg); s.flush()
    time.sleep(wait)
    s.read(128)


def make_pattern():
    beat_sec = 60.0 / BPM
    p = []
    for m in range(MEASURES):
        base = m * 4 * beat_sec
        # HZ: beats 1, 3 (downbeats、 一番先に置く)
        p.append((base + 0 * beat_sec - 0.001, 0x08, 0x0F, HZ_DUR, "HZ "))
        p.append((base + 2 * beat_sec - 0.001, 0x08, 0x0F, HZ_DUR, "HZ "))
        # HB: beats 1, 2, 3, 4
        for i in range(4):
            p.append((base + i * beat_sec + 0.20, 0x1D, 0x0F, HB_DUR, "HB "))
        # LB: offbeats (1.5, 2.5, 3.5, 4.5)
        for i in range(4):
            p.append((base + (i + 0.5) * beat_sec, 0x1C, 0x0F, LB_DUR, "LB "))
    return sorted(p)


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
    print("StartComm失敗"); s.close(); exit(1)
print("StartComm OK")

pattern = make_pattern()
STOP = [0x80, 0x10, 0xF0, 0x01, 0x20]
print(f"--- {BPM} BPM × {MEASURES}小節 ---")
print(f"--- HZ:downbeats / HB:4分音符 / LB:8分裏 ---\n")

start = time.time()
for offset, lid, iocp, dur, label in pattern:
    target = start + offset
    while time.time() < target:
        time.sleep(0.0005)
    send(s, [0x80, 0x10, 0xF0, 0x08, 0x30, lid, iocp, 0, 0, 0, 0, 0], wait=0.03)
    remain = dur - 0.03
    if remain > 0:
        time.sleep(remain)
    send(s, STOP, wait=0.03)

print(f"\n=== 終了 ({time.time()-start:.1f}s) ===")
s.close()
