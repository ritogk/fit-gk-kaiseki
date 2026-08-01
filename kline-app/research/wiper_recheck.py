#!/usr/bin/env python3
"""
NRC=0x10 cluster (12個) を 現在の車両状態で 1発ずつ再投入。
IOCP=0x0F、 0.3秒envelope + StopDiagSession、 1.5秒gap で観察。
"""
import serial, sys, time

sys.stdout.reconfigure(line_buffering=True)

PORT = "/dev/ttyUSB0"
BAUD = 10400

NRC10 = [0x06, 0x07, 0x10, 0x17, 0x23, 0x24, 0x27, 0x31, 0x32, 0x36, 0x37, 0x3C]


def cs(d):
    return sum(d) & 0xFF


def parse(raw, lid):
    n = len(raw)
    for i in range(n):
        b = raw[i]
        if b == 0x80 and i + 5 < n and raw[i + 1] == 0xF0 and raw[i + 2] == 0x10:
            length = raw[i + 3]
            if i + 4 + length + 1 > n:
                continue
            sid = raw[i + 4]
            if sid == 0x70 and length >= 2 and raw[i + 5] == lid:
                return ("PR", None, raw[i:i + 5 + length].hex())
            if sid == 0x7F and length >= 3:
                return ("NR", raw[i + 6], raw[i:i + 5 + length].hex())
    return ("silent", None, raw.hex())


s = serial.Serial(PORT, BAUD, timeout=0.05)
s.dtr = False
s.rts = False
time.sleep(0.3)
s.reset_input_buffer()
s.break_condition = True
time.sleep(0.025)
s.break_condition = False
time.sleep(0.025)
sc_p = [0x81, 0x46, 0xF0, 0x81]
s.write(bytes(sc_p) + bytes([cs(sc_p)]))
s.flush()
time.sleep(0.2)
r = s.read(128)
if not (r and 0xC1 in r):
    print("StartComm失敗:", r.hex() if r else "(empty)")
    s.close()
    exit(1)
print("StartComm OK\n")
print("=== NRC=0x10 cluster 再投入 (IGN ON / Engine OFF 想定) ===\n")

STOP_P = [0x80, 0x10, 0xF0, 0x01, 0x20]
STOP = bytes(STOP_P) + bytes([cs(STOP_P)])

found_pr = []
for lid in NRC10:
    p = [0x80, 0x10, 0xF0, 0x08, 0x30, lid, 0x0F, 0, 0, 0, 0, 0]
    msg = bytes(p) + bytes([cs(p)])
    s.reset_input_buffer()
    s.write(msg)
    s.flush()
    time.sleep(0.15)
    raw = s.read(256)
    time.sleep(0.15)
    s.write(STOP)
    s.flush()
    time.sleep(0.05)
    s.read(128)
    kind, nrc, hexstr = parse(raw, lid)
    if kind == "PR":
        print(f"  ★★★ LID 0x{lid:02X}: PR ★★★ raw={hexstr}")
        found_pr.append(lid)
        time.sleep(2.5)
    elif kind == "NR":
        print(f"    LID 0x{lid:02X}: NR NRC=0x{nrc:02X}")
        time.sleep(1.5)
    else:
        print(f"    LID 0x{lid:02X}: silent")
        time.sleep(1.5)

s.close()
print(f"\n=== 結果: PR {len(found_pr)}個 ===")
if found_pr:
    print("PR LIDs:", [f"0x{lid:02X}" for lid in found_pr])
else:
    print("全て NRC=0x10、 IGN ON / Engine OFF でも条件未達のまま。")
