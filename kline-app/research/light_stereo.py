#!/usr/bin/env python3
"""
左右ウィンカー stereo ビート + ハイビーム アクセント。
- kick = 左ウィンカー (LID 0x0A)
- snare = 右ウィンカー (LID 0x0B)
- HB アクセント = ハイビーム (LID 0x1D) 1拍目だけ
"""
import serial, time, sys

PORT = "/dev/ttyUSB0"
BAUD = 10400

BPM = int(sys.argv[1]) if len(sys.argv) > 1 else 120
MEASURES = int(sys.argv[2]) if len(sys.argv) > 2 else 30

L_DUR = 0.12
R_DUR = 0.12
HB_DUR = 0.10


def cs(d):
    return sum(d) & 0xFF


def send(s, payload, wait=0.04):
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
        # HB on beat 1 (downbeat accent)
        p.append((base + 0 * beat_sec, 0x1D, 0x0F, HB_DUR, "HB "))
        # 左 on beats 1, 3 (kick)
        p.append((base + 0 * beat_sec + 0.05, 0x0A, 0x0F, L_DUR, "L  "))
        p.append((base + 2 * beat_sec, 0x0A, 0x0F, L_DUR, "L  "))
        # 右 on beats 2, 4 (snare)
        p.append((base + 1 * beat_sec, 0x0B, 0x0F, R_DUR, "R  "))
        p.append((base + 3 * beat_sec, 0x0B, 0x0F, R_DUR, "R  "))
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
print(f"--- {BPM} BPM × {MEASURES}小節 stereo (L=左ウィンカー / R=右ウィンカー / HB=accent) ---\n")

start = time.time()
for offset, lid, iocp, dur, label in pattern:
    target = start + offset
    while time.time() < target:
        time.sleep(0.0005)
    send(s, [0x80, 0x10, 0xF0, 0x08, 0x30, lid, iocp, 0, 0, 0, 0, 0], wait=0.04)
    remain = dur - 0.04
    if remain > 0:
        time.sleep(remain)
    send(s, STOP, wait=0.03)

print(f"\n=== 終了 ({time.time()-start:.1f}s) ===")
s.close()
