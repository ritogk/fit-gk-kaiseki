#!/usr/bin/env python3
"""
ハザード 2秒ON + 3秒OFF を 5秒周期で繰り返す。
- ON 期間: IOControl LID 0x08 IOCP 0x0F を 1秒間隔でrefresh (MICU 自然リレー1.5Hz維持)
- OFF 期間: StopDiagSession で envelope 強制中断 + 静寂

usage: hazard_5s_cycle.py [cycles=5]
"""
import serial, time, sys

PORT = "/dev/ttyUSB0"
BAUD = 10400
CYCLES = int(sys.argv[1]) if len(sys.argv) > 1 else 5

ON_DURATION = 2.0      # ハザードON期間
OFF_DURATION = 3.0     # ハザードOFF期間


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
print("StartComm OK")
print(f"--- {CYCLES}サイクル ハザード {ON_DURATION}s ON / {OFF_DURATION}s OFF ---")

ON  = [0x80, 0x10, 0xF0, 0x08, 0x30, 0x08, 0x0F, 0, 0, 0, 0, 0]
STOP = [0x80, 0x10, 0xF0, 0x01, 0x20]

start = time.time()
for cyc in range(CYCLES):
    cycle_start = time.time()
    print(f"\n[Cycle {cyc+1}/{CYCLES}]")

    # ON期間: 1秒周期で IOControl refresh
    print(f"  t={time.time()-start:5.2f}s ハザード ON期間 ({ON_DURATION}s)")
    on_start = time.time()
    while time.time() - on_start < ON_DURATION:
        send(s, ON, wait=0.05)
        # 1秒間隔 (送信50ms含めて950ms休憩)
        sleep_left = 1.0 - 0.05
        if time.time() - on_start + sleep_left > ON_DURATION:
            break
        time.sleep(sleep_left)

    # OFF移行: StopDiagSession で envelope 強制中断
    print(f"  t={time.time()-start:5.2f}s StopDiagSession で OFF")
    send(s, STOP, wait=0.05)

    # OFF期間で次サイクルまで待機
    elapsed = time.time() - cycle_start
    remaining = (ON_DURATION + OFF_DURATION) - elapsed
    if remaining > 0:
        time.sleep(remaining)

print(f"\n=== 終了 ({CYCLES}サイクル, {time.time()-start:.1f}s) ===")
s.close()
