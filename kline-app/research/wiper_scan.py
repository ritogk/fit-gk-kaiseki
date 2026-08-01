#!/usr/bin/env python3
"""
ワイパー LID 探索: ECM(0x10) IO Control 全LID走査。

- Phase A: NRC=0x10 クラスター 再走査 (条件変化を期待)
- Phase B: 未走査 0x27-0xFF を IOCP=0x0F

各 LID: 0.4s envelope を StopDiagSession で短縮。
PR 検出時は 2.5s pause で観察、 silent/NR は 0.5s で次へ。
"""
import serial, sys, time

# Force unbuffered stdout for live progress
sys.stdout.reconfigure(line_buffering=True)

PORT = "/dev/ttyUSB0"
BAUD = 10400
LOG = "wiper_scan.log"

KNOWN_PR_0F = {0x08, 0x0A, 0x0B, 0x1C, 0x1D, 0x20, 0x25}
KNOWN_PR_01 = {0x04, 0x05, 0x09, 0x11, 0x26}
KNOWN = KNOWN_PR_0F | KNOWN_PR_01
NRC10 = [0x06, 0x07, 0x10, 0x17, 0x23, 0x24, 0x27, 0x31, 0x32, 0x36, 0x37, 0x3C]
UNSCANNED = [i for i in range(0x27, 0x100) if i not in KNOWN and i not in NRC10]

ENV_DUR = 0.4
GAP_FAST = 0.5
GAP_PR = 2.5
RESP_WIN = 0.15


def cs(d):
    return sum(d) & 0xFF


def parse(raw, lid):
    n = len(raw)
    for i in range(n):
        b = raw[i]
        # long format: 80 [tgt] [src] [len] ...
        if b == 0x80 and i + 5 < n and raw[i + 1] == 0xF0 and raw[i + 2] == 0x10:
            length = raw[i + 3]
            if i + 4 + length + 1 > n:
                continue
            sid = raw[i + 4]
            if sid == 0x70 and length >= 2 and raw[i + 5] == lid:
                return ("PR", None, raw[i:i + 5 + length].hex())
            if sid == 0x7F and length >= 3:
                return ("NR", raw[i + 6], raw[i:i + 5 + length].hex())
        # short format: 0x81-0xBF (length in fmt byte)
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
    print("StartComm失敗:", r.hex())
    s.close()
    exit(1)
print("StartComm OK")

STOP_P = [0x80, 0x10, 0xF0, 0x01, 0x20]
STOP = bytes(STOP_P) + bytes([cs(STOP_P)])

results = {}
log = open(LOG, "w")


def fire_and_parse(lid, iocp=0x0F):
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


def scan(lids, label, iocp=0x0F):
    hdr = f"\n=== {label} ({len(lids)}個 IOCP=0x{iocp:02X}) ==="
    print(hdr)
    log.write(hdr + "\n")
    for lid in lids:
        kind, nrc, hexstr = fire_and_parse(lid, iocp)
        results[(lid, iocp)] = (kind, nrc, hexstr)
        if kind == "PR":
            line = f"  ★ LID 0x{lid:02X}: PR  raw={hexstr}"
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


try:
    scan(NRC10, "Phase A: NRC=0x10 クラスター 再走査")
    scan(UNSCANNED, "Phase B: 未走査 0x27-0xFF")
finally:
    s.close()
    log.close()

print("\n=== サマリ ===")
print("PR responders:")
for (lid, iocp), (k, n, _) in sorted(results.items()):
    if k == "PR":
        marker = " (NEW!)" if lid not in KNOWN else ""
        print(f"  LID 0x{lid:02X} IOCP=0x{iocp:02X}: PR{marker}")
print("\nNRC=0x10 (条件未達) LIDs:")
for (lid, iocp), (k, n, _) in sorted(results.items()):
    if k == "NR" and n == 0x10:
        print(f"  LID 0x{lid:02X}")
nrc_other = [(lid, n) for (lid, iocp), (k, n, _) in results.items() if k == "NR" and n != 0x10]
if nrc_other:
    print("\nNRC=0x10 以外の NR (新NRC):")
    for lid, n in sorted(set(nrc_other)):
        print(f"  LID 0x{lid:02X}: NRC=0x{n:02X}")
print(f"\nログ: {LOG}")
