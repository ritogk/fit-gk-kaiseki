#!/usr/bin/env python3
"""
ワイパー深掘り 3点同時 probe:
1. Security Access (SID 0x27) on ECM(0x10) — seed取得可能かチェック
2. NRC=0x10 cluster LID 0x06 で State バイト変動 (0x00, 0x01, 0x02, 0x03, 0x07, 0x0F, 0xFF)
3. 別ECUアドレス (0x18, 0x28, 0x38, ..., 0xF8) で LID 0x06 IO Control 試射
"""
import serial, sys, time

sys.stdout.reconfigure(line_buffering=True)

PORT = "/dev/ttyUSB0"
BAUD = 10400


def cs(d):
    return sum(d) & 0xFF


def parse_resp(raw, expected_src=0x10):
    """First response frame from <expected_src> → tester(0xF0)."""
    n = len(raw)
    for i in range(n):
        b = raw[i]
        if b == 0x80 and i + 5 < n and raw[i + 1] == 0xF0 and raw[i + 2] == expected_src:
            length = raw[i + 3]
            if i + 4 + length + 1 > n:
                continue
            sid = raw[i + 4]
            data = bytes(raw[i + 4:i + 4 + length])
            return (sid, data)
        if 0x81 <= b <= 0xBF and i + 4 < n and raw[i + 1] == 0xF0 and raw[i + 2] == expected_src:
            length = b & 0x3F
            if length == 0 or i + 3 + length + 1 > n:
                continue
            sid = raw[i + 3]
            data = bytes(raw[i + 3:i + 3 + length])
            return (sid, data)
    return (None, raw)


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


def send_recv(payload, wait=0.15):
    msg = bytes(payload) + bytes([cs(payload)])
    s.reset_input_buffer()
    s.write(msg)
    s.flush()
    time.sleep(wait)
    return s.read(256)


# ============================================================
# Phase 1: Security Access (SID 0x27) on ECM(0x10)
# ============================================================
print("=== Phase 1: Security Access on ECM(0x10) ===")
for sub in [0x01, 0x03, 0x05, 0x07, 0x09, 0x0B]:
    raw = send_recv([0x80, 0x10, 0xF0, 0x02, 0x27, sub])
    sid, data = parse_resp(raw, 0x10)
    if sid == 0x67:
        print(f"  ★ subLevel 0x{sub:02X}: PR (seed) data={data.hex()}")
    elif sid == 0x7F and len(data) >= 3:
        print(f"    subLevel 0x{sub:02X}: NR NRC=0x{data[2]:02X}")
    else:
        print(f"    subLevel 0x{sub:02X}: silent (raw={raw.hex()})")
    time.sleep(0.2)

# ============================================================
# Phase 2: State byte variation for cluster LID 0x06
# (8-byte payload: 30 06 0F [s0] [s1] [s2] [s3] [s4])
# ============================================================
print("\n=== Phase 2: LID 0x06 State byte 変動 ===")
state_patterns = [
    (0x00, 0x00, 0x00, 0x00, 0x00, "all zero (baseline)"),
    (0x01, 0x00, 0x00, 0x00, 0x00, "state0=1"),
    (0x02, 0x00, 0x00, 0x00, 0x00, "state0=2"),
    (0x03, 0x00, 0x00, 0x00, 0x00, "state0=3"),
    (0x07, 0x00, 0x00, 0x00, 0x00, "state0=7"),
    (0x0F, 0x00, 0x00, 0x00, 0x00, "state0=0F"),
    (0xFF, 0x00, 0x00, 0x00, 0x00, "state0=FF"),
    (0x00, 0xFF, 0x00, 0x00, 0x00, "state1=FF"),
    (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, "all FF"),
]
STOP_P = [0x80, 0x10, 0xF0, 0x01, 0x20]
STOP = bytes(STOP_P) + bytes([cs(STOP_P)])
for s0, s1, s2, s3, s4, label in state_patterns:
    p = [0x80, 0x10, 0xF0, 0x08, 0x30, 0x06, 0x0F, s0, s1, s2, s3, s4]
    raw = send_recv(p, wait=0.15)
    sid, data = parse_resp(raw, 0x10)
    if sid == 0x70:
        print(f"  ★ {label}: PR ★ raw={raw.hex()}")
    elif sid == 0x7F and len(data) >= 3:
        print(f"    {label}: NR NRC=0x{data[2]:02X}")
    else:
        print(f"    {label}: silent")
    s.write(STOP); s.flush(); time.sleep(0.05); s.read(128)
    time.sleep(0.3)

# ============================================================
# Phase 3: Alternate ECU addresses with LID 0x06 IO Control
# ============================================================
print("\n=== Phase 3: 別ECUアドレス で LID 0x06 試射 ===")
addrs_to_test = [0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
                 0x20, 0x28, 0x30, 0x38, 0x40, 0x48,
                 0x58, 0x60, 0x68, 0x88, 0x98,
                 0xA8, 0xB8, 0xC8, 0xD8, 0xE8, 0xF8]
for addr in addrs_to_test:
    p = [0x80, addr, 0xF0, 0x08, 0x30, 0x06, 0x0F, 0, 0, 0, 0, 0]
    raw = send_recv(p, wait=0.15)
    # Check who responded
    n = len(raw)
    found = None
    for i in range(n):
        b = raw[i]
        if b == 0x80 and i + 5 < n and raw[i + 1] == 0xF0:
            src = raw[i + 2]
            length = raw[i + 3]
            if i + 4 + length + 1 > n:
                continue
            sid = raw[i + 4]
            found = (src, sid, bytes(raw[i + 4:i + 4 + length]))
            break
        if 0x81 <= b <= 0xBF and i + 4 < n and raw[i + 1] == 0xF0:
            src = raw[i + 2]
            length = b & 0x3F
            if length == 0 or i + 3 + length + 1 > n:
                continue
            sid = raw[i + 3]
            found = (src, sid, bytes(raw[i + 3:i + 3 + length]))
            break
    if found:
        src, sid, data = found
        if sid == 0x70:
            print(f"  ★ addr 0x{addr:02X}: src=0x{src:02X} PR ★ raw={raw.hex()}")
        elif sid == 0x7F and len(data) >= 3:
            print(f"    addr 0x{addr:02X}: src=0x{src:02X} NR NRC=0x{data[2]:02X}")
        else:
            print(f"    addr 0x{addr:02X}: src=0x{src:02X} sid=0x{sid:02X} data={data.hex()}")
    else:
        print(f"    addr 0x{addr:02X}: silent")
    s.write(STOP); s.flush(); time.sleep(0.05); s.read(128)
    time.sleep(0.25)

s.close()
print("\n=== 完了 ===")
