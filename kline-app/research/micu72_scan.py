#!/usr/bin/env python3
"""
MICU(0x72) 集中スキャン — 全LID × 主要IOCP.

Phase 1: LID 0x00-0xFF × IOCP=0x0F (標準ON)
Phase 2: PR検出LIDに対して全IOCP 0x00-0xFF 展開
Phase 3: 全SIDスイープ (0x72がどのサービスに応答するか)

GW(0x46)経由でStartComm後、MICU宛にIOControl送信。
"""
import serial, sys, time

sys.stdout.reconfigure(line_buffering=True)

PORT = "/dev/ttyUSB0"
BAUD = 10400
LOG = "micu72_scan.log"

MICU = 0x72
ECM = 0x10
TESTER = 0xF0
GATEWAY = 0x46

RESP_WIN = 0.12
GAP = 0.15


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
            sid = raw[i + 4]
            data = bytes(raw[i + 4:i + 4 + length])
            return (sid, data)
        if 0x81 <= b <= 0xBF and i + 4 < n and raw[i + 1] == TESTER and raw[i + 2] == expected_src:
            length = b & 0x3F
            if length == 0 or i + 3 + length + 1 > n:
                continue
            sid = raw[i + 3]
            data = bytes(raw[i + 3:i + 3 + length])
            return (sid, data)
    return (None, b"")


class MICU72Scanner:
    def __init__(self):
        self.s = None
        self.log = None
        self.findings = []
        self.pr_lids = []

    def connect(self):
        self.s = serial.Serial(PORT, BAUD, timeout=0.05)
        self.s.dtr = False
        self.s.rts = False
        time.sleep(0.3)
        self.s.reset_input_buffer()
        self.s.break_condition = True
        time.sleep(0.025)
        self.s.break_condition = False
        time.sleep(0.025)
        sc_p = [0x81, GATEWAY, TESTER, 0x81]
        self.s.write(bytes(sc_p) + bytes([cs(sc_p)]))
        self.s.flush()
        time.sleep(0.2)
        r = self.s.read(128)
        if not (r and 0xC1 in r):
            raise RuntimeError(f"StartComm失敗: {r.hex() if r else '(empty)'}")
        print("StartComm OK (via GW 0x46)")

    def reconnect(self):
        try:
            self.s.close()
        except Exception:
            pass
        time.sleep(0.5)
        self.connect()

    def send_recv(self, payload, wait=RESP_WIN):
        msg = bytes(payload) + bytes([cs(payload)])
        self.s.reset_input_buffer()
        self.s.write(msg)
        self.s.flush()
        time.sleep(wait)
        return self.s.read(256)

    def stop_diag(self, addr=MICU):
        stop_p = [0x80, addr, TESTER, 0x01, 0x20]
        self.s.write(bytes(stop_p) + bytes([cs(stop_p)]))
        self.s.flush()
        time.sleep(0.05)
        self.s.read(128)

    def keepalive(self):
        self.send_recv([0x80, ECM, TESTER, 0x02, 0x3E, 0x01], wait=0.05)

    def out(self, line, highlight=False):
        prefix = "  ★ " if highlight else "    "
        full = prefix + line
        print(full)
        if self.log:
            self.log.write(full + "\n")
            self.log.flush()
        if highlight:
            self.findings.append(line)

    # ================================================================
    # Phase 1: MICU(0x72) LID 0x00-0xFF × IOCP=0x0F
    # ================================================================
    def phase1_lid_sweep(self):
        hdr = "\n=== Phase 1: MICU(0x72) LID 0x00-0xFF × IOCP=0x0F ==="
        print(hdr)
        self.log.write(hdr + "\n")
        for lid in range(0x00, 0x100):
            p = [0x80, MICU, TESTER, 0x08, 0x30, lid, 0x0F, 0, 0, 0, 0, 0]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, MICU)
            if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                self.out(f"LID 0x{lid:02X} IOCP=0x0F: PR raw={raw.hex()}", highlight=True)
                self.pr_lids.append(lid)
                self.stop_diag()
                time.sleep(1.0)
            elif sid == 0x7F and len(data) >= 3:
                nrc = data[2]
                if nrc not in (0x31, 0x11):
                    self.out(f"LID 0x{lid:02X}: NR NRC=0x{nrc:02X}")
            time.sleep(GAP)
            if lid % 32 == 31:
                self.keepalive()
                print(f"  ... {lid + 1}/256 完了")

    # ================================================================
    # Phase 1b: IOCP=0x01 でも全LIDスイープ
    # ================================================================
    def phase1b_lid_sweep_01(self):
        hdr = "\n=== Phase 1b: MICU(0x72) LID 0x00-0xFF × IOCP=0x01 ==="
        print(hdr)
        self.log.write(hdr + "\n")
        for lid in range(0x00, 0x100):
            p = [0x80, MICU, TESTER, 0x08, 0x30, lid, 0x01, 0, 0, 0, 0, 0]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, MICU)
            if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                self.out(f"LID 0x{lid:02X} IOCP=0x01: PR raw={raw.hex()}", highlight=True)
                if lid not in self.pr_lids:
                    self.pr_lids.append(lid)
                self.stop_diag()
                time.sleep(1.0)
            elif sid == 0x7F and len(data) >= 3:
                nrc = data[2]
                if nrc not in (0x31, 0x11):
                    self.out(f"LID 0x{lid:02X}: NR NRC=0x{nrc:02X}")
            time.sleep(GAP)
            if lid % 32 == 31:
                self.keepalive()
                print(f"  ... {lid + 1}/256 完了")

    # ================================================================
    # Phase 2: PR検出LID × 全IOCP 0x00-0xFF
    # ================================================================
    def phase2_iocp_expand(self):
        if not self.pr_lids:
            print("\n  → Phase 1 で PR なし、Phase 2 スキップ")
            return
        hdr = f"\n=== Phase 2: PR検出LID {[f'0x{x:02X}' for x in self.pr_lids]} × 全IOCP ==="
        print(hdr)
        self.log.write(hdr + "\n")
        for lid in self.pr_lids:
            print(f"\n  --- LID 0x{lid:02X} × IOCP 0x00-0xFF ---")
            self.log.write(f"\n  --- LID 0x{lid:02X} × IOCP 0x00-0xFF ---\n")
            for iocp in range(0x00, 0x100):
                p = [0x80, MICU, TESTER, 0x08, 0x30, lid, iocp, 0, 0, 0, 0, 0]
                raw = self.send_recv(p)
                sid, data = parse_resp(raw, MICU)
                if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                    self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X}: PR", highlight=True)
                    self.stop_diag()
                    time.sleep(1.0)
                elif sid == 0x7F and len(data) >= 3:
                    nrc = data[2]
                    if nrc not in (0x31,):
                        self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X}: NR NRC=0x{nrc:02X}")
                time.sleep(0.1)
                if iocp % 64 == 63:
                    self.keepalive()
            print(f"  LID 0x{lid:02X} 完了")

    # ================================================================
    # Phase 3: MICU(0x72) 全SIDスイープ
    # ================================================================
    def phase3_sid_sweep(self):
        hdr = "\n=== Phase 3: MICU(0x72) 全SID 0x00-0xFF ==="
        print(hdr)
        self.log.write(hdr + "\n")
        for sid_val in range(0x00, 0x100):
            if sid_val == 0x30:
                continue
            p = [0x80, MICU, TESTER, 0x02, sid_val, 0x00]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, MICU)
            if sid is not None:
                pr_sid = sid_val + 0x40
                if sid == pr_sid:
                    ascii_part = ""
                    try:
                        ascii_part = data.decode("ascii", errors="replace")
                    except Exception:
                        pass
                    self.out(f"SID 0x{sid_val:02X}: PR data={data.hex()} \"{ascii_part}\"", highlight=True)
                    time.sleep(0.5)
                elif sid == 0x7F and len(data) >= 3:
                    nrc = data[2]
                    if nrc not in (0x11,):
                        self.out(f"SID 0x{sid_val:02X}: NR NRC=0x{nrc:02X}")
            time.sleep(GAP)
            if sid_val % 32 == 31:
                self.keepalive()
                print(f"  ... {sid_val + 1}/256 完了")

    # ================================================================
    # Phase 4: PR LID × stateバイト変動 (方向制御探索)
    # ================================================================
    def phase4_state_sweep(self):
        if not self.pr_lids:
            print("\n  → PR LID なし、Phase 4 スキップ")
            return
        hdr = f"\n=== Phase 4: PR LID × stateバイト変動 ==="
        print(hdr)
        self.log.write(hdr + "\n")

        states = [
            ([0x01, 0x00, 0x00, 0x00, 0x00], "s0=01"),
            ([0x02, 0x00, 0x00, 0x00, 0x00], "s0=02"),
            ([0x03, 0x00, 0x00, 0x00, 0x00], "s0=03"),
            ([0x04, 0x00, 0x00, 0x00, 0x00], "s0=04"),
            ([0x08, 0x00, 0x00, 0x00, 0x00], "s0=08"),
            ([0x10, 0x00, 0x00, 0x00, 0x00], "s0=10"),
            ([0x20, 0x00, 0x00, 0x00, 0x00], "s0=20"),
            ([0x40, 0x00, 0x00, 0x00, 0x00], "s0=40"),
            ([0x80, 0x00, 0x00, 0x00, 0x00], "s0=80"),
            ([0xFF, 0x00, 0x00, 0x00, 0x00], "s0=FF"),
            ([0x00, 0x01, 0x00, 0x00, 0x00], "s1=01"),
            ([0x00, 0x02, 0x00, 0x00, 0x00], "s1=02"),
            ([0x00, 0x04, 0x00, 0x00, 0x00], "s1=04"),
            ([0x00, 0x08, 0x00, 0x00, 0x00], "s1=08"),
            ([0x00, 0x10, 0x00, 0x00, 0x00], "s1=10"),
            ([0x00, 0xFF, 0x00, 0x00, 0x00], "s1=FF"),
            ([0x00, 0x00, 0x01, 0x00, 0x00], "s2=01"),
            ([0x00, 0x00, 0x02, 0x00, 0x00], "s2=02"),
            ([0x00, 0x00, 0xFF, 0x00, 0x00], "s2=FF"),
            ([0xFF, 0xFF, 0xFF, 0xFF, 0xFF], "all=FF"),
        ]
        for lid in self.pr_lids:
            print(f"\n  --- LID 0x{lid:02X} × state変動 ---")
            self.log.write(f"\n  --- LID 0x{lid:02X} × state変動 ---\n")
            for iocp in [0x0F, 0x01]:
                for state, label in states:
                    p = [0x80, MICU, TESTER, 0x08, 0x30, lid, iocp] + state
                    raw = self.send_recv(p)
                    sid, data = parse_resp(raw, MICU)
                    if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                        self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X} {label}: PR", highlight=True)
                        self.stop_diag()
                        time.sleep(1.0)
                    elif sid == 0x7F and len(data) >= 3:
                        nrc = data[2]
                        if nrc not in (0x31,):
                            self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X} {label}: NR NRC=0x{nrc:02X}")
                    time.sleep(0.1)

    def run(self):
        self.log = open(LOG, "w")
        self.connect()
        try:
            self.phase1_lid_sweep()
            self.reconnect()
            self.phase1b_lid_sweep_01()
            self.reconnect()
            self.phase2_iocp_expand()
            self.reconnect()
            self.phase3_sid_sweep()
            self.reconnect()
            self.phase4_state_sweep()
        finally:
            self.s.close()
            self.log.close()

        print("\n" + "=" * 60)
        print("=== MICU(0x72) Findings サマリ ===")
        print("=" * 60)
        if self.findings:
            for f in self.findings:
                print(f"  ★ {f}")
        else:
            print("  (新規発見なし)")
        print(f"\nPR LIDs: {[f'0x{x:02X}' for x in self.pr_lids]}")
        print(f"ログ: {LOG}")


if __name__ == "__main__":
    scanner = MICU72Scanner()
    scanner.run()
