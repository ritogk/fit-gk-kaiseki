#!/usr/bin/env python3
"""
MICU(0x72) 高速スキャン — waitを限界まで切り詰め.

通常版: ~7分 → ターボ版: ~1.5分
"""
import serial, sys, time

sys.stdout.reconfigure(line_buffering=True)

PORT = "/dev/ttyUSB0"
BAUD = 10400
LOG = "micu72_turbo.log"

MICU = 0x72
ECM = 0x10
TESTER = 0xF0
GATEWAY = 0x46

WAIT = 0.04
GAP = 0.01


def cs(d):
    return sum(d) & 0xFF


def parse_resp(raw, expected_src):
    n = len(raw)
    for i in range(n):
        b = raw[i]
        if b == 0x80 and i + 5 < n and raw[i + 1] == TESTER and raw[i + 2] == expected_src:
            length = raw[i + 3]
            if i + 4 + length + 1 > n:
                continue
            return (raw[i + 4], bytes(raw[i + 4:i + 4 + length]))
        if 0x81 <= b <= 0xBF and i + 4 < n and raw[i + 1] == TESTER and raw[i + 2] == expected_src:
            length = b & 0x3F
            if length == 0 or i + 3 + length + 1 > n:
                continue
            return (raw[i + 3], bytes(raw[i + 3:i + 3 + length]))
    return (None, b"")


s = None
log = None
findings = []
pr_lids = []


def connect():
    global s
    s = serial.Serial(PORT, BAUD, timeout=0.03)
    s.dtr = False
    s.rts = False
    time.sleep(0.3)
    s.reset_input_buffer()
    s.break_condition = True
    time.sleep(0.025)
    s.break_condition = False
    time.sleep(0.025)
    sc_p = [0x81, GATEWAY, TESTER, 0x81]
    s.write(bytes(sc_p) + bytes([cs(sc_p)]))
    s.flush()
    time.sleep(0.15)
    r = s.read(128)
    if not (r and 0xC1 in r):
        raise RuntimeError(f"StartComm失敗: {r.hex() if r else '(empty)'}")
    print("StartComm OK")


def reconnect():
    global s
    try:
        s.close()
    except Exception:
        pass
    time.sleep(0.3)
    connect()


def tx(payload, wait=WAIT):
    msg = bytes(payload) + bytes([cs(payload)])
    s.reset_input_buffer()
    s.write(msg)
    s.flush()
    time.sleep(wait)
    return s.read(256)


def stop(addr=MICU):
    p = [0x80, addr, TESTER, 0x01, 0x20]
    s.write(bytes(p) + bytes([cs(p)]))
    s.flush()
    time.sleep(0.02)
    s.read(128)


def hit(line):
    full = f"  ★ {line}"
    print(full)
    log.write(full + "\n")
    log.flush()
    findings.append(line)


def miss(line):
    log.write(f"    {line}\n")


# Phase 1: LID 0x00-0xFF × IOCP=0x0F
def phase1():
    print("\n=== Phase 1: MICU(0x72) LID 0x00-0xFF × IOCP=0x0F ===")
    log.write("\n=== Phase 1: LID sweep IOCP=0x0F ===\n")
    for lid in range(0x100):
        raw = tx([0x80, MICU, TESTER, 0x08, 0x30, lid, 0x0F, 0, 0, 0, 0, 0])
        sid, data = parse_resp(raw, MICU)
        if sid == 0x70 and len(data) >= 2 and data[1] == lid:
            hit(f"LID 0x{lid:02X} IOCP=0x0F: PR")
            pr_lids.append(lid)
            stop()
            time.sleep(0.3)
        elif sid == 0x7F and len(data) >= 3 and data[2] not in (0x31, 0x11):
            miss(f"LID 0x{lid:02X}: NR NRC=0x{data[2]:02X}")
        time.sleep(GAP)
        if lid % 64 == 63:
            print(f"  {lid + 1}/256")


# Phase 1b: LID 0x00-0xFF × IOCP=0x01
def phase1b():
    print("\n=== Phase 1b: MICU(0x72) LID 0x00-0xFF × IOCP=0x01 ===")
    log.write("\n=== Phase 1b: LID sweep IOCP=0x01 ===\n")
    for lid in range(0x100):
        raw = tx([0x80, MICU, TESTER, 0x08, 0x30, lid, 0x01, 0, 0, 0, 0, 0])
        sid, data = parse_resp(raw, MICU)
        if sid == 0x70 and len(data) >= 2 and data[1] == lid:
            hit(f"LID 0x{lid:02X} IOCP=0x01: PR")
            if lid not in pr_lids:
                pr_lids.append(lid)
            stop()
            time.sleep(0.3)
        elif sid == 0x7F and len(data) >= 3 and data[2] not in (0x31, 0x11):
            miss(f"LID 0x{lid:02X}: NR NRC=0x{data[2]:02X}")
        time.sleep(GAP)
        if lid % 64 == 63:
            print(f"  {lid + 1}/256")


# Phase 2: PR LID × 全IOCP
def phase2():
    if not pr_lids:
        print("\n  → PR なし、Phase 2 skip")
        return
    print(f"\n=== Phase 2: PR LID {[f'0x{x:02X}' for x in pr_lids]} × IOCP 0x00-0xFF ===")
    log.write(f"\n=== Phase 2: IOCP expand ===\n")
    for lid in pr_lids:
        print(f"  --- LID 0x{lid:02X} ---")
        for iocp in range(0x100):
            raw = tx([0x80, MICU, TESTER, 0x08, 0x30, lid, iocp, 0, 0, 0, 0, 0])
            sid, data = parse_resp(raw, MICU)
            if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                hit(f"LID 0x{lid:02X} IOCP=0x{iocp:02X}: PR")
                stop()
                time.sleep(0.3)
            elif sid == 0x7F and len(data) >= 3 and data[2] not in (0x31,):
                miss(f"LID 0x{lid:02X} IOCP=0x{iocp:02X}: NR NRC=0x{data[2]:02X}")
            time.sleep(GAP)


# Phase 3: 全SID
def phase3():
    print("\n=== Phase 3: MICU(0x72) 全SID 0x00-0xFF ===")
    log.write("\n=== Phase 3: SID sweep ===\n")
    for sv in range(0x100):
        if sv == 0x30:
            continue
        raw = tx([0x80, MICU, TESTER, 0x02, sv, 0x00])
        sid, data = parse_resp(raw, MICU)
        if sid is not None:
            pr_sid = sv + 0x40
            if sid == pr_sid:
                hit(f"SID 0x{sv:02X}: PR data={data.hex()}")
                time.sleep(0.2)
            elif sid == 0x7F and len(data) >= 3 and data[2] not in (0x11,):
                miss(f"SID 0x{sv:02X}: NR NRC=0x{data[2]:02X}")
        time.sleep(GAP)
        if sv % 64 == 63:
            print(f"  {sv + 1}/256")


# Phase 4: stateバイト
def phase4():
    if not pr_lids:
        return
    print(f"\n=== Phase 4: state変動 ===")
    log.write("\n=== Phase 4: state sweep ===\n")
    states = [
        [0x01,0,0,0,0], [0x02,0,0,0,0], [0x04,0,0,0,0], [0x08,0,0,0,0],
        [0x10,0,0,0,0], [0x20,0,0,0,0], [0x40,0,0,0,0], [0x80,0,0,0,0],
        [0xFF,0,0,0,0], [0,0x01,0,0,0], [0,0x02,0,0,0], [0,0x04,0,0,0],
        [0,0xFF,0,0,0], [0,0,0x01,0,0], [0,0,0xFF,0,0], [0xFF,0xFF,0xFF,0xFF,0xFF],
    ]
    for lid in pr_lids:
        print(f"  --- LID 0x{lid:02X} ---")
        for iocp in [0x0F, 0x01]:
            for st in states:
                raw = tx([0x80, MICU, TESTER, 0x08, 0x30, lid, iocp] + st)
                sid, data = parse_resp(raw, MICU)
                if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                    label = ','.join(f'{x:02X}' for x in st)
                    hit(f"LID 0x{lid:02X} IOCP=0x{iocp:02X} state=[{label}]: PR")
                    stop()
                    time.sleep(0.3)
                time.sleep(GAP)


connect()
log = open(LOG, "w")
t0 = time.time()
try:
    phase1()
    reconnect()
    phase1b()
    reconnect()
    phase2()
    reconnect()
    phase3()
    reconnect()
    phase4()
finally:
    s.close()
    log.close()

elapsed = time.time() - t0
print(f"\n{'=' * 50}")
print(f"=== MICU(0x72) サマリ ({elapsed:.0f}秒) ===")
print(f"{'=' * 50}")
if findings:
    for f in findings:
        print(f"  ★ {f}")
else:
    print("  (発見なし)")
print(f"\nPR LIDs: {[f'0x{x:02X}' for x in pr_lids]}")
print(f"ログ: {LOG}")
