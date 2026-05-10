#!/usr/bin/env python3
"""
任意 LID/IOCP の ON/OFF パターン制御。
StopDiagSession で envelope 中断、 任意のサイクル制御可能。

usage: light_pattern.py LID(hex) IOCP(hex) ON_SEC OFF_SEC CYCLES
例:    light_pattern.py 1D 0F 1.0 1.0 5     # ハイビーム 1s ON/1s OFF × 5
       light_pattern.py 08 0F 2.0 3.0 5     # ハザード 2s ON/3s OFF × 5
"""
import serial, time, sys

PORT = "/dev/ttyUSB0"
BAUD = 10400

LID = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x1D
IOCP = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x0F
ON_SEC = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
OFF_SEC = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
CYCLES = int(sys.argv[5]) if len(sys.argv) > 5 else 5


def cs(d):
    return sum(d) & 0xFF


def send(s, payload, wait=0.05):
    msg = bytes(payload) + bytes([cs(payload)])
    s.reset_input_buffer()
    s.write(msg); s.flush()
    time.sleep(wait)
    raw = s.read(128)
    idx = raw.find(msg)
    return raw[idx + len(msg):] if idx >= 0 else raw


s = serial.Serial(PORT, BAUD, timeout=0.005)
s.dtr = False; s.rts = False
time.sleep(0.3); s.reset_input_buffer()
s.break_condition = True; time.sleep(0.025)
s.break_condition = False; time.sleep(0.025)
sc = send(s, [0x81, 0x46, 0xF0, 0x81])
if not (sc and len(sc) >= 8 and sc[4] == 0xC1):
    print("StartComm失敗"); s.close(); exit(1)
print(f"StartComm OK")
print(f"--- LID 0x{LID:02X} IOCP 0x{IOCP:02X} : {ON_SEC}s ON / {OFF_SEC}s OFF × {CYCLES} ---")

ON  = [0x80, 0x10, 0xF0, 0x08, 0x30, LID, IOCP, 0, 0, 0, 0, 0]
STOP = [0x80, 0x10, 0xF0, 0x01, 0x20]

start = time.time()
for cyc in range(CYCLES):
    cycle_start = time.time()
    print(f"\n[Cycle {cyc+1}/{CYCLES}]")

    # ON期間: 必要なら 0.8s毎に refresh (1秒以下のONなら1発でOK)
    print(f"  t={time.time()-start:5.2f}s ON")
    on_start = time.time()
    while True:
        send(s, ON, wait=0.05)
        elapsed = time.time() - on_start
        if elapsed >= ON_SEC:
            break
        # 残り時間 vs refresh間隔の小さい方
        sleep_left = min(0.8 - 0.05, ON_SEC - elapsed)
        if sleep_left <= 0:
            break
        time.sleep(sleep_left)

    # StopDiagSession で OFF
    print(f"  t={time.time()-start:5.2f}s OFF (StopDiag)")
    send(s, STOP, wait=0.05)

    # 次サイクルまで待機
    elapsed = time.time() - cycle_start
    remaining = (ON_SEC + OFF_SEC) - elapsed
    if remaining > 0:
        time.sleep(remaining)

print(f"\n=== 終了 ({CYCLES}サイクル, {time.time()-start:.1f}s) ===")
s.close()
