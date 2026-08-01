#!/usr/bin/env python3
"""
IOCP=0x02, 0x03 × LID 0x00-0x27 走査 (これまで完全未走査の領域)。
LID 0x26 (ホーン) は安全のため除外。 各 LID 0.2秒 envelope を StopDiagSession で短縮。
"""
import serial, sys, time

sys.stdout.reconfigure(line_buffering=True)

PORT = "/dev/ttyUSB0"
BAUD = 10400
LOG = "iocp23_scan.log"

SKIP = {0x26}  # horn — 絶対発射しない
LIDS = [i for i in range(0x00, 0x28) if i not in SKIP]
IOCPS = [0x02, 0x03]

ENV_DUR = 0.2
GAP_FAST = 0.4
GAP_PR = 2.5
RESP_WIN = 0.15


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
        if 0x81 <= b <= 0xBF and i + 4 < n and raw[i + 1] == 0xF0 and raw[i + 2] == 0x10:
            length = b & 0x3F
            if length == 0 or i + 3 + length + 1 > n:
                continue
            sid = raw[i + 3]
            if sid == 0x70 and length >= 2 and raw[i + 4] == lid:
                return ("PR", None, raw[i:i + 4 + length].hex())
            if sid == 0x7F and length >= 3:
                return ("NR", raw[i + 5], raw[i:i + 4 + length].hex())
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

STOP_P = [0x80, 0x10, 0xF0, 0x01, 0x20]
STOP = bytes(STOP_P) + bytes([cs(STOP_P)])

results = {}
log = open(LOG, "w")


def fire_and_parse(lid, iocp):
    p = [0x80, 0x10, 0xF0, 0x08, 0x30, lid, iocp, 0, 0, 0, 0, 0]
    msg = bytes(p) + bytes([cs(p)])
    s.reset_input_buffer()
    s.write(msg)
    s.flush()
    time.sleep(RESP_WIN)
    raw1 = s.read(256)
    rem = ENV_DUR - RESP_WIN
    if rem > 0:
        time.sleep(rem)
    s.write(STOP)
    s.flush()
    time.sleep(0.05)
    s.read(128)
    return parse(raw1, lid)


for iocp in IOCPS:
    hdr = f"\n=== IOCP=0x{iocp:02X} × LID 0x00-0x27 (skip 0x26) ==="
    print(hdr)
    log.write(hdr + "\n")
    log.flush()
    for lid in LIDS:
        kind, nrc, hexstr = fire_and_parse(lid, iocp)
        results[(lid, iocp)] = (kind, nrc, hexstr)
        if kind == "PR":
            line = f"  ★ LID 0x{lid:02X} IOCP=0x{iocp:02X}: PR ★ raw={hexstr}"
            print(f"\n{line}\n")
            log.write(line + "\n")
            log.flush()
            time.sleep(GAP_PR)
        elif kind == "NR":
            line = f"    LID 0x{lid:02X}: NR NRC=0x{nrc:02X}"
            print(line)
            log.write(line + "\n")
            log.flush()
            time.sleep(GAP_FAST)
        else:
            line = f"    LID 0x{lid:02X}: silent"
            print(line)
            log.write(line + "\n")
            log.flush()
            time.sleep(GAP_FAST)

s.close()
log.close()

print("\n=== サマリ ===")
print("PR responders:")
for (lid, iocp), (k, n, _) in sorted(results.items()):
    if k == "PR":
        print(f"  LID 0x{lid:02X} IOCP=0x{iocp:02X}: PR")
print("\nNR breakdown:")
nrc_count = {}
for (lid, iocp), (k, n, _) in results.items():
    if k == "NR":
        nrc_count[n] = nrc_count.get(n, 0) + 1
for nrc, cnt in sorted(nrc_count.items()):
    print(f"  NRC=0x{nrc:02X}: {cnt}個")
print(f"\nログ: {LOG}")
