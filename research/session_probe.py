#!/usr/bin/env python3
"""
SID 0x10 (StartDiagSession) sub-function 0x80-0x9F 探索。
PR を返す session ごとに、 NRC=0x10 クラスター LID を再点火し、
session 種類によって 拒否が解けるか検証。
"""
import serial, sys, time

sys.stdout.reconfigure(line_buffering=True)

PORT = "/dev/ttyUSB0"
BAUD = 10400

NRC10 = [0x06, 0x07, 0x10, 0x17, 0x23, 0x24, 0x27, 0x31, 0x32, 0x36, 0x37, 0x3C]


def cs(d):
    return sum(d) & 0xFF


def parse_resp(raw):
    """First response frame from ECM(0x10) → tester(0xF0)."""
    n = len(raw)
    for i in range(n):
        b = raw[i]
        if b == 0x80 and i + 5 < n and raw[i + 1] == 0xF0 and raw[i + 2] == 0x10:
            length = raw[i + 3]
            if i + 4 + length + 1 > n:
                continue
            sid = raw[i + 4]
            data = bytes(raw[i + 4:i + 4 + length])
            return (sid, data)
        if 0x81 <= b <= 0xBF and i + 4 < n and raw[i + 1] == 0xF0 and raw[i + 2] == 0x10:
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


print("=== Phase 1: SID 0x10 (StartDiagSession) sub-function 探索 ===")
session_results = {}
pr_sessions = []
for sub in range(0x80, 0xA0):
    raw = send_recv([0x80, 0x10, 0xF0, 0x02, 0x10, sub])
    sid, data = parse_resp(raw)
    if sid == 0x50:
        print(f"  ★ session 0x{sub:02X}: PR (0x50) data={data.hex()}")
        session_results[sub] = "PR"
        pr_sessions.append(sub)
    elif sid == 0x7F and len(data) >= 3 and data[1] == 0x10:
        nrc = data[2]
        print(f"    session 0x{sub:02X}: NR NRC=0x{nrc:02X}")
        session_results[sub] = ("NR", nrc)
    else:
        print(f"    session 0x{sub:02X}: silent (raw={raw.hex()})")
        session_results[sub] = "silent"
    time.sleep(0.15)

# Also test UDS-style 0x01-0x07 (some Honda ECUs use UDS subfn)
print("\n--- UDS-style sub-fn 0x01-0x07 も念のため ---")
for sub in range(0x01, 0x08):
    raw = send_recv([0x80, 0x10, 0xF0, 0x02, 0x10, sub])
    sid, data = parse_resp(raw)
    if sid == 0x50:
        print(f"  ★ session 0x{sub:02X}: PR (0x50) data={data.hex()}")
        session_results[sub] = "PR"
        pr_sessions.append(sub)
    elif sid == 0x7F and len(data) >= 3 and data[1] == 0x10:
        nrc = data[2]
        print(f"    session 0x{sub:02X}: NR NRC=0x{nrc:02X}")
    else:
        print(f"    session 0x{sub:02X}: silent")
    time.sleep(0.15)

if not pr_sessions:
    print("\n→ PR session なし。 ECM はデフォルト session のみ受付。")
    print("  StartDiagSession 経由で NRC=0x10 解除は不可、 別アプローチ必要。")
    s.close()
    exit(0)

# Phase 2: re-test NRC=0x10 cluster inside each PR session
STOP_P = [0x80, 0x10, 0xF0, 0x01, 0x20]
STOP = bytes(STOP_P) + bytes([cs(STOP_P)])

print(f"\n=== Phase 2: 各 PR session 内で NRC=0x10 cluster 再試行 ===")
for sub in pr_sessions:
    print(f"\n--- session 0x{sub:02X} 内 ---")
    # re-enter session right before each LID to avoid timeout
    for lid in NRC10:
        send_recv([0x80, 0x10, 0xF0, 0x02, 0x10, sub], wait=0.1)
        p = [0x80, 0x10, 0xF0, 0x08, 0x30, lid, 0x0F, 0, 0, 0, 0, 0]
        raw = send_recv(p, wait=0.15)
        sid, data = parse_resp(raw)
        if sid == 0x70:
            print(f"  ★ LID 0x{lid:02X}: PR ★ raw={raw.hex()}")
        elif sid == 0x7F and len(data) >= 3:
            print(f"    LID 0x{lid:02X}: NR NRC=0x{data[2]:02X}")
        else:
            print(f"    LID 0x{lid:02X}: silent")
        # always stop active test
        s.write(STOP)
        s.flush()
        time.sleep(0.05)
        s.read(128)
        time.sleep(0.4)

s.close()
print("\n=== 完了 ===")
