#!/usr/bin/env python3
"""
ドアミラー開閉 & パワーウインドウ制御 特化スキャナ.

ミラー/ウインドウはMICU(ボディコントローラ)が直接制御する。
K-LineではECM(0x10)経由で届くかもしれないし、MICU(0x72)直接かもしれない。
両方を総当りで探る。

Strategy:
  Phase A: ECM(0x10) IOControl — 全IOCP × NRC=0x10 クラスター LID
           → NRC=0x10 はIOCPが違えば通る可能性
  Phase B: ECM(0x10) IOControl — 全IOCP × LID 0x00-0x27 (既知PR以外)
           → 未発見のミラー/ウインドウLIDがあるかもしれない
  Phase C: MICU(0x72) 直接通信 — StartComm → 各SID試行
  Phase D: MICU(0x1E) 直接通信 — ゲートウェイ経由
  Phase E: ECM ReadDataByLocalId — ミラー/ウインドウ状態読み取り

Usage:
    .venv/bin/python research/mirror_window_scan.py
"""
import serial, sys, time

sys.stdout.reconfigure(line_buffering=True)

PORT = "/dev/ttyUSB0"
BAUD = 10400
LOG = "mirror_window_scan.log"

ECM = 0x10
MICU = 0x72
MICU2 = 0x1E
TESTER = 0xF0
GATEWAY = 0x46

RESP_WIN = 0.12
GAP = 0.25

NRC10_LIDS = [0x06, 0x07, 0x10, 0x17, 0x23, 0x24, 0x27]
UNKNOWN_LIDS = [lid for lid in range(0x00, 0x28)
                if lid not in {0x02, 0x04, 0x05, 0x08, 0x09, 0x0A, 0x0B,
                               0x0D, 0x0E, 0x11, 0x12, 0x19, 0x1A, 0x1B,
                               0x1C, 0x1D, 0x20, 0x25, 0x26}
                and lid not in set(NRC10_LIDS)]

STOP_P = [0x80, ECM, TESTER, 0x01, 0x20]


def cs(d):
    return sum(d) & 0xFF


STOP_MSG = bytes(STOP_P) + bytes([cs(STOP_P)])


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


def parse_any_resp(raw):
    n = len(raw)
    for i in range(n):
        b = raw[i]
        if b == 0x80 and i + 5 < n and raw[i + 1] == TESTER:
            src = raw[i + 2]
            length = raw[i + 3]
            if i + 4 + length + 1 > n:
                continue
            sid = raw[i + 4]
            data = bytes(raw[i + 4:i + 4 + length])
            return (src, sid, data)
        if 0x81 <= b <= 0xBF and i + 4 < n and raw[i + 1] == TESTER:
            src = raw[i + 2]
            length = b & 0x3F
            if length == 0 or i + 3 + length + 1 > n:
                continue
            sid = raw[i + 3]
            data = bytes(raw[i + 3:i + 3 + length])
            return (src, sid, data)
    return (None, None, b"")


class MirrorWindowScanner:
    def __init__(self):
        self.s = None
        self.log = None
        self.findings = []

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

    def stop_diag(self):
        self.s.write(STOP_MSG)
        self.s.flush()
        time.sleep(0.05)
        self.s.read(128)

    def out(self, line, highlight=False):
        prefix = "  ★ " if highlight else "    "
        full = prefix + line
        print(full)
        if self.log:
            self.log.write(full + "\n")
            self.log.flush()
        if highlight:
            self.findings.append(line)

    def keepalive(self):
        self.send_recv([0x80, ECM, TESTER, 0x02, 0x3E, 0x01], wait=0.05)

    def start_comm_to(self, addr):
        """指定アドレスにStartCommunicationを送信."""
        sc_p = [0x81, addr, TESTER, 0x81]
        raw = self.send_recv(sc_p, wait=0.2)
        src, sid, data = parse_any_resp(raw)
        return src is not None and sid == 0xC1

    # ================================================================
    # Phase A: NRC=0x10 LIDs × 全IOCP (これらが条件次第でミラー/ウインドウの可能性)
    # ================================================================
    def phase_a_nrc10_iocp_sweep(self):
        hdr = "\n=== Phase A: NRC=0x10 LIDs × 全IOCP 0x00-0xFF ==="
        print(hdr)
        print("  NRC=0x10 LIDs はIOCPが違えば通る可能性がある")
        self.log.write(hdr + "\n")
        for lid in NRC10_LIDS:
            print(f"\n  --- LID 0x{lid:02X} ---")
            self.log.write(f"\n  --- LID 0x{lid:02X} ---\n")
            for iocp in range(0x00, 0x100):
                p = [0x80, ECM, TESTER, 0x08, 0x30, lid, iocp, 0, 0, 0, 0, 0]
                raw = self.send_recv(p)
                sid, data = parse_resp(raw, ECM)
                if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                    self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X}: PR ★ raw={raw.hex()}", highlight=True)
                    self.stop_diag()
                    time.sleep(1.0)
                elif sid == 0x7F and len(data) >= 3:
                    nrc = data[2]
                    if nrc not in (0x10, 0x31):
                        self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X}: NR NRC=0x{nrc:02X}")
                time.sleep(0.1)
                if iocp % 64 == 63:
                    self.keepalive()
            print(f"  LID 0x{lid:02X} 完了")

    # ================================================================
    # Phase B: 未確認LIDs (NRC=0x10でもPRでもない) × 主要IOCP
    # ================================================================
    def phase_b_unknown_lid_sweep(self):
        hdr = f"\n=== Phase B: 未確認LIDs {[f'0x{x:02X}' for x in UNKNOWN_LIDS]} × IOCP走査 ==="
        print(hdr)
        self.log.write(hdr + "\n")
        iocps_to_test = list(range(0x00, 0x20)) + [0xFF]
        for lid in UNKNOWN_LIDS:
            print(f"\n  --- LID 0x{lid:02X} ---")
            for iocp in iocps_to_test:
                p = [0x80, ECM, TESTER, 0x08, 0x30, lid, iocp, 0, 0, 0, 0, 0]
                raw = self.send_recv(p)
                sid, data = parse_resp(raw, ECM)
                if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                    self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X}: PR ★", highlight=True)
                    self.stop_diag()
                    time.sleep(1.0)
                elif sid == 0x7F and len(data) >= 3:
                    nrc = data[2]
                    if nrc not in (0x31,):
                        self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X}: NR NRC=0x{nrc:02X}")
                time.sleep(0.1)

    # ================================================================
    # Phase C: MICU(0x72) 直接通信
    # ================================================================
    def phase_c_micu_direct(self):
        hdr = "\n=== Phase C: MICU(0x72) 直接通信 ==="
        print(hdr)
        self.log.write(hdr + "\n")

        print("  StartComm → 0x72 ...")
        ok = self.start_comm_to(MICU)
        if ok:
            self.out("MICU(0x72) StartComm: PR ★", highlight=True)
        else:
            self.out("MICU(0x72) StartComm: 応答なし — GW経由で再試行")
            self.reconnect()
            ok = self.start_comm_to(MICU)
            if not ok:
                self.out("MICU(0x72): GW経由でも応答なし、ECM経由でMICU宛SID送信試行")

        sids_to_test = [
            (0x10, 0x83, "StartDiagSession 0x83"),
            (0x10, 0x81, "StartDiagSession 0x81"),
            (0x1A, 0x87, "ReadECUIdent ECU_part#"),
            (0x1A, 0x90, "ReadECUIdent VIN"),
            (0x1A, 0x91, "ReadECUIdent HW_ver"),
            (0x21, 0x00, "ReadDataByLocalId 0x00"),
            (0x21, 0x01, "ReadDataByLocalId 0x01"),
            (0x21, 0x10, "ReadDataByLocalId 0x10"),
        ]

        for target_addr in [MICU, MICU2]:
            addr_name = f"0x{target_addr:02X}"
            print(f"\n  --- {addr_name} 宛 SID 試行 ---")
            self.log.write(f"\n  --- {addr_name} 宛 SID 試行 ---\n")
            for sid_val, sub, desc in sids_to_test:
                p = [0x80, target_addr, TESTER, 0x02, sid_val, sub]
                raw = self.send_recv(p, wait=0.2)
                src, sid, data = parse_any_resp(raw)
                if src is not None:
                    pr_sid = sid_val + 0x40
                    if sid == pr_sid:
                        ascii_part = ""
                        try:
                            ascii_part = data[1:].decode("ascii", errors="replace")
                        except Exception:
                            pass
                        self.out(f"{addr_name} {desc}: PR src=0x{src:02X} data={data.hex()} \"{ascii_part}\"",
                                 highlight=True)
                    elif sid == 0x7F and len(data) >= 3:
                        self.out(f"{addr_name} {desc}: NR NRC=0x{data[2]:02X} src=0x{src:02X}")
                    else:
                        self.out(f"{addr_name} {desc}: sid=0x{sid:02X} src=0x{src:02X} data={data.hex()}")
                else:
                    self.out(f"{addr_name} {desc}: silent")
                time.sleep(GAP)

            print(f"\n  --- {addr_name} 宛 IOControl LID 0x00-0x27 IOCP=0x0F ---")
            self.log.write(f"\n  --- {addr_name} 宛 IOControl ---\n")
            for lid in range(0x00, 0x28):
                if lid == 0x26:
                    continue
                p = [0x80, target_addr, TESTER, 0x08, 0x30, lid, 0x0F, 0, 0, 0, 0, 0]
                raw = self.send_recv(p, wait=0.15)
                src, sid, data = parse_any_resp(raw)
                if src is not None:
                    if sid == 0x70:
                        self.out(f"{addr_name} LID 0x{lid:02X}: PR src=0x{src:02X} ★", highlight=True)
                        stop_p = [0x80, target_addr, TESTER, 0x01, 0x20]
                        self.s.write(bytes(stop_p) + bytes([cs(stop_p)]))
                        self.s.flush()
                        time.sleep(0.1)
                        self.s.read(128)
                        time.sleep(1.0)
                    elif sid == 0x7F and len(data) >= 3:
                        nrc = data[2]
                        if nrc not in (0x31, 0x11):
                            self.out(f"{addr_name} LID 0x{lid:02X}: NR NRC=0x{nrc:02X} src=0x{src:02X}")
                time.sleep(0.1)

    # ================================================================
    # Phase D: NRC=0x10 LIDs — stateバイトでミラー方向/ウインドウ方向指定
    # ================================================================
    def phase_d_state_byte_sweep(self):
        hdr = "\n=== Phase D: NRC=0x10 LIDs × state バイト変動 (方向指定探索) ==="
        print(hdr)
        self.log.write(hdr + "\n")

        state_patterns = [
            ([0x01, 0x00, 0x00, 0x00, 0x00], "s0=01 (UP/OPEN)"),
            ([0x02, 0x00, 0x00, 0x00, 0x00], "s0=02 (DOWN/CLOSE)"),
            ([0x03, 0x00, 0x00, 0x00, 0x00], "s0=03"),
            ([0x04, 0x00, 0x00, 0x00, 0x00], "s0=04"),
            ([0x10, 0x00, 0x00, 0x00, 0x00], "s0=10"),
            ([0x20, 0x00, 0x00, 0x00, 0x00], "s0=20"),
            ([0x40, 0x00, 0x00, 0x00, 0x00], "s0=40"),
            ([0x80, 0x00, 0x00, 0x00, 0x00], "s0=80"),
            ([0x00, 0x01, 0x00, 0x00, 0x00], "s1=01"),
            ([0x00, 0x02, 0x00, 0x00, 0x00], "s1=02"),
            ([0x01, 0x01, 0x00, 0x00, 0x00], "s0=01,s1=01"),
            ([0x01, 0x02, 0x00, 0x00, 0x00], "s0=01,s1=02"),
            ([0xFF, 0xFF, 0x00, 0x00, 0x00], "s0=FF,s1=FF"),
        ]

        for lid in NRC10_LIDS:
            print(f"\n  --- LID 0x{lid:02X} ---")
            self.log.write(f"\n  --- LID 0x{lid:02X} ---\n")
            for iocp in [0x0F, 0x01, 0x04, 0x05, 0x07, 0x08]:
                for state, label in state_patterns:
                    p = [0x80, ECM, TESTER, 0x08, 0x30, lid, iocp] + state
                    raw = self.send_recv(p)
                    sid, data = parse_resp(raw, ECM)
                    if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                        self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X} {label}: PR ★", highlight=True)
                        self.stop_diag()
                        time.sleep(1.0)
                    elif sid == 0x7F and len(data) >= 3:
                        nrc = data[2]
                        if nrc not in (0x10, 0x31):
                            self.out(f"LID 0x{lid:02X} IOCP=0x{iocp:02X} {label}: NR NRC=0x{nrc:02X}")
                    time.sleep(0.08)
            self.keepalive()

    # ================================================================
    # Phase E: 他ECUアドレス (ミラー/ウインドウ専用ECUがあるか)
    # ================================================================
    def phase_e_other_ecus(self):
        hdr = "\n=== Phase E: 全ECUアドレス StartComm → IOControl 探索 ==="
        print(hdr)
        self.log.write(hdr + "\n")

        addrs = list(range(0x01, 0x100))
        skip = {TESTER, 0xF1, ECM, GATEWAY}

        for addr in addrs:
            if addr in skip:
                continue
            sc_p = [0x81, addr, TESTER, 0x81]
            raw = self.send_recv(sc_p, wait=0.15)
            src, sid, data = parse_any_resp(raw)
            if src is not None and sid == 0xC1:
                self.out(f"addr 0x{addr:02X}: StartComm PR ★ src=0x{src:02X}", highlight=True)

                for test_lid in [0x06, 0x07, 0x10, 0x17]:
                    p = [0x80, addr, TESTER, 0x08, 0x30, test_lid, 0x0F, 0, 0, 0, 0, 0]
                    raw2 = self.send_recv(p, wait=0.15)
                    src2, sid2, data2 = parse_any_resp(raw2)
                    if src2 is not None:
                        if sid2 == 0x70:
                            self.out(f"  addr 0x{addr:02X} LID 0x{test_lid:02X}: PR ★★★", highlight=True)
                            stop_p2 = [0x80, addr, TESTER, 0x01, 0x20]
                            self.s.write(bytes(stop_p2) + bytes([cs(stop_p2)]))
                            self.s.flush()
                            time.sleep(0.1)
                            self.s.read(128)
                        elif sid2 == 0x7F and len(data2) >= 3:
                            self.out(f"  addr 0x{addr:02X} LID 0x{test_lid:02X}: NR NRC=0x{data2[2]:02X}")
                    time.sleep(0.1)

                self.reconnect()
            time.sleep(0.08)

    def run(self):
        self.log = open(LOG, "w")
        self.connect()
        try:
            self.phase_a_nrc10_iocp_sweep()
            self.reconnect()
            self.phase_b_unknown_lid_sweep()
            self.reconnect()
            self.phase_c_micu_direct()
            self.reconnect()
            self.phase_d_state_byte_sweep()
            self.reconnect()
            self.phase_e_other_ecus()
        finally:
            self.s.close()
            self.log.close()

        print("\n" + "=" * 60)
        print("=== ミラー/ウインドウ Findings サマリ ===")
        print("=" * 60)
        if self.findings:
            for f in self.findings:
                print(f"  ★ {f}")
        else:
            print("  (新規発見なし)")
        print(f"\nログ: {LOG}")


if __name__ == "__main__":
    scanner = MirrorWindowScanner()
    scanner.run()
