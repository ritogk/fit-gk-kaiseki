#!/usr/bin/env python3
"""
ライトでビートシーケンサ。
複数LIDを時間軸上に並べたパターンを再生する。

パターン例:
  4/4 120BPM, kick=HB(0x1D), snare=FOG(0x20)
  step:   0  1  2  3   ← 0.5sずつ = 1拍
  kick:   X  .  X  .
  snare:  .  X  .  X
"""
import serial, time, sys
from threading import Thread

PORT = "/dev/ttyUSB0"
BAUD = 10400

# ON時間 (各ヒット): 短くするとtight、 長くするとfat
HIT_DUR = 0.15

# (offset_sec, LID, IOCP, label)
def make_pattern(bpm=120, measures=4):
    beat_sec = 60.0 / bpm
    p = []
    for m in range(measures):
        base = m * 4 * beat_sec
        # kick on 1 and 3
        p.append((base + 0 * beat_sec, 0x1D, 0x0F, "KICK"))
        p.append((base + 2 * beat_sec, 0x1D, 0x0F, "KICK"))
        # snare on 2 and 4 (車幅灯 0x25 — フォグ非搭載車のため)
        p.append((base + 1 * beat_sec, 0x25, 0x0F, "SNARE"))
        p.append((base + 3 * beat_sec, 0x25, 0x0F, "SNARE"))
    return sorted(p)


def cs(d):
    return sum(d) & 0xFF


def send(s, payload, wait=0.04):
    msg = bytes(payload) + bytes([cs(payload)])
    s.reset_input_buffer()
    s.write(msg); s.flush()
    time.sleep(wait)
    s.read(128)


s = serial.Serial(PORT, BAUD, timeout=0.005)
s.dtr = False; s.rts = False
time.sleep(0.3); s.reset_input_buffer()
s.break_condition = True; time.sleep(0.025)
s.break_condition = False; time.sleep(0.025)

# StartComm
msg = bytes([0x81, 0x46, 0xF0, 0x81, cs([0x81, 0x46, 0xF0, 0x81])])
s.write(msg); s.flush()
time.sleep(0.2)
raw = s.read(128)
idx = raw.find(msg)
resp = raw[idx + len(msg):] if idx >= 0 else raw
if not (resp and len(resp) >= 8 and resp[4] == 0xC1):
    print("StartComm失敗"); s.close(); exit(1)
print("StartComm OK")

bpm = int(sys.argv[1]) if len(sys.argv) > 1 else 120
measures = int(sys.argv[2]) if len(sys.argv) > 2 else 4
pattern = make_pattern(bpm, measures)
print(f"--- {bpm} BPM × {measures}小節 ({len(pattern)}ヒット) ---\n")

STOP = [0x80, 0x10, 0xF0, 0x01, 0x20]

start = time.time()
for offset, lid, iocp, label in pattern:
    target = start + offset
    while time.time() < target:
        time.sleep(0.001)
    t = time.time() - start
    on_cmd = [0x80, 0x10, 0xF0, 0x08, 0x30, lid, iocp, 0, 0, 0, 0, 0]
    send(s, on_cmd, wait=0.04)
    # ON 持続 (HIT_DUR から transaction時間 引いた残り)
    remain = HIT_DUR - 0.04
    if remain > 0:
        time.sleep(remain)
    send(s, STOP, wait=0.03)
    print(f"  t={t:5.2f}s  {label:6s} (LID 0x{lid:02X})")

print(f"\n=== 終了 ({time.time()-start:.1f}s) ===")
s.close()
