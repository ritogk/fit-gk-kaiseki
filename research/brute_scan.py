#!/usr/bin/env python3
"""
ECM(0x10) 全方位ブルートフォーススキャナ.

Phase 1: 全SIDスイープ (0x00-0xFF) — ECMが応答するサービスを発見
Phase 2: SID 0x21 ReadDataByLocalId — LID 0x00-0xFF
Phase 3: SID 0x1A ReadECUIdentification — sub 0x00-0xFF
Phase 4: SID 0x31 StartRoutineByLocalId — routineId 0x00-0xFF
Phase 5: SID 0x30 IOControl 未テストIOCP探索 — 既知PR LIDで IOCP 0x00-0xFF
Phase 6: SID 0x30 IOCP=0x01 × LID 0x00-0x27 系統的スイープ

Usage:
    .venv/bin/python research/brute_scan.py [phase]
    phase省略時は全phase実行。 phase=1 など指定で単体実行可。
"""
import serial, sys, time

sys.stdout.reconfigure(line_buffering=True)

PORT = "/dev/ttyUSB0"
BAUD = 10400
LOG = "brute_scan.log"

ECM = 0x10
TESTER = 0xF0
GATEWAY = 0x46

RESP_WIN = 0.12
GAP = 0.3
GAP_PR = 1.5

KNOWN_PR_LIDS = {0x08, 0x0A, 0x0B, 0x1C, 0x1D, 0x20, 0x25,
                 0x04, 0x05, 0x09, 0x11, 0x26, 0x02, 0x12,
                 0x0D, 0x0E, 0x19, 0x1A, 0x1B}
TESTED_IOCPS = {0x0F, 0x01, 0x02, 0x03, 0x05, 0x1E}

STOP_P = [0x80, ECM, TESTER, 0x01, 0x20]


def cs(d):
    return sum(d) & 0xFF


STOP_MSG = bytes(STOP_P) + bytes([cs(STOP_P)])


def parse_resp(raw, expected_src=ECM):
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


class Scanner:
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
        print("StartComm OK")

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

    # ================================================================
    # Phase 1: 全SIDスイープ — ECMがどのSIDに応答するか
    # ================================================================
    def phase1_sid_sweep(self):
        hdr = "\n=== Phase 1: 全SID スイープ (0x00-0xFF → ECM) ==="
        print(hdr)
        self.log.write(hdr + "\n")
        responding = {}
        for sid_val in range(0x00, 0x100):
            if sid_val == 0x30:
                self.out(f"SID 0x{sid_val:02X}: skip (IOControl — 別phaseで走査)")
                continue
            # 1バイトペイロード (SIDのみ) で叩く
            p = [0x80, ECM, TESTER, 0x01, sid_val]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, ECM)
            if sid is not None:
                pr_sid = sid_val + 0x40
                if sid == pr_sid:
                    self.out(f"SID 0x{sid_val:02X}: PR (0x{sid:02X}) data={data.hex()}", highlight=True)
                    responding[sid_val] = ("PR", data)
                    time.sleep(GAP_PR)
                    continue
                elif sid == 0x7F and len(data) >= 3:
                    nrc = data[2]
                    nrc_name = {0x10: "generalReject", 0x11: "serviceNotSupported",
                                0x12: "subFnNotSupported", 0x13: "incorrectMsgLen",
                                0x14: "responseTooLong", 0x22: "conditionsNotCorrect",
                                0x31: "requestOutOfRange", 0x33: "securityAccessDenied",
                                0x35: "invalidKey", 0x36: "exceededAttempts",
                                0x78: "responsePending"}.get(nrc, "")
                    self.out(f"SID 0x{sid_val:02X}: NR NRC=0x{nrc:02X} ({nrc_name})")
                    if nrc not in (0x11,):
                        responding[sid_val] = ("NR", nrc)
                else:
                    self.out(f"SID 0x{sid_val:02X}: resp sid=0x{sid:02X} data={data.hex()}")
            else:
                self.out(f"SID 0x{sid_val:02X}: silent")
            time.sleep(GAP)
            if sid_val % 32 == 31:
                self.keepalive()
        return responding

    # ================================================================
    # Phase 1b: 応答したSIDのsub-function 2バイト目スイープ
    # ================================================================
    def phase1b_subfn_sweep(self, responding_sids):
        interesting = {}
        for sid_val, (kind, detail) in responding_sids.items():
            if sid_val in (0x10, 0x20, 0x27, 0x3E, 0x81):
                continue
            if kind == "NR" and detail == 0x13:
                interesting[sid_val] = detail
            elif kind == "NR" and detail == 0x12:
                interesting[sid_val] = detail
            elif kind == "PR":
                interesting[sid_val] = detail

        if not interesting:
            print("\n  → sub-fn展開対象のSIDなし")
            return

        hdr = f"\n=== Phase 1b: 応答SID sub-fn スイープ ({len(interesting)}個) ==="
        print(hdr)
        self.log.write(hdr + "\n")

        for sid_val in sorted(interesting.keys()):
            print(f"\n  --- SID 0x{sid_val:02X} sub-fn 0x00-0xFF ---")
            self.log.write(f"\n  --- SID 0x{sid_val:02X} sub-fn 0x00-0xFF ---\n")
            for sub in range(0x00, 0x100):
                p = [0x80, ECM, TESTER, 0x02, sid_val, sub]
                raw = self.send_recv(p)
                sid, data = parse_resp(raw, ECM)
                pr_sid = sid_val + 0x40
                if sid == pr_sid:
                    self.out(f"SID 0x{sid_val:02X} sub=0x{sub:02X}: PR data={data.hex()}", highlight=True)
                    time.sleep(GAP_PR)
                elif sid == 0x7F and len(data) >= 3:
                    nrc = data[2]
                    if nrc not in (0x11, 0x12, 0x31):
                        self.out(f"SID 0x{sid_val:02X} sub=0x{sub:02X}: NR NRC=0x{nrc:02X}")
                else:
                    pass
                time.sleep(0.15)
                if sub % 64 == 63:
                    self.keepalive()

    # ================================================================
    # Phase 2: SID 0x21 ReadDataByLocalIdentifier
    # ================================================================
    def phase2_read_local(self):
        hdr = "\n=== Phase 2: SID 0x21 ReadDataByLocalId (LID 0x00-0xFF) ==="
        print(hdr)
        self.log.write(hdr + "\n")
        for lid in range(0x00, 0x100):
            p = [0x80, ECM, TESTER, 0x02, 0x21, lid]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, ECM)
            if sid == 0x61:
                self.out(f"LID 0x{lid:02X}: PR data={data.hex()}", highlight=True)
                time.sleep(GAP_PR)
            elif sid == 0x7F and len(data) >= 3:
                nrc = data[2]
                if nrc not in (0x31,):
                    self.out(f"LID 0x{lid:02X}: NR NRC=0x{nrc:02X}")
            time.sleep(0.15)
            if lid % 64 == 63:
                self.keepalive()
                print(f"  ... {lid + 1}/256 完了")

    # ================================================================
    # Phase 3: SID 0x1A ReadECUIdentification
    # ================================================================
    def phase3_ecu_ident(self):
        hdr = "\n=== Phase 3: SID 0x1A ReadECUIdentification (sub 0x00-0xFF) ==="
        print(hdr)
        self.log.write(hdr + "\n")
        for sub in range(0x00, 0x100):
            p = [0x80, ECM, TESTER, 0x02, 0x1A, sub]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, ECM)
            if sid == 0x5A:
                ascii_part = ""
                try:
                    ascii_part = data[1:].decode("ascii", errors="replace")
                except Exception:
                    pass
                self.out(f"sub 0x{sub:02X}: PR data={data.hex()} ascii=\"{ascii_part}\"", highlight=True)
                time.sleep(GAP_PR)
            elif sid == 0x7F and len(data) >= 3:
                nrc = data[2]
                if nrc not in (0x31, 0x12):
                    self.out(f"sub 0x{sub:02X}: NR NRC=0x{nrc:02X}")
            time.sleep(0.15)
            if sub % 64 == 63:
                self.keepalive()
                print(f"  ... {sub + 1}/256 完了")

    # ================================================================
    # Phase 4: SID 0x31 StartRoutineByLocalIdentifier
    # ================================================================
    def phase4_routine_control(self):
        hdr = "\n=== Phase 4: SID 0x31 StartRoutineByLocalId (routine 0x00-0xFF) ==="
        print(hdr)
        self.log.write(hdr + "\n")
        for rid in range(0x00, 0x100):
            p = [0x80, ECM, TESTER, 0x02, 0x31, rid]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, ECM)
            if sid == 0x71:
                self.out(f"routine 0x{rid:02X}: PR data={data.hex()}", highlight=True)
                self.stop_diag()
                time.sleep(GAP_PR)
            elif sid == 0x7F and len(data) >= 3:
                nrc = data[2]
                if nrc not in (0x31, 0x12):
                    self.out(f"routine 0x{rid:02X}: NR NRC=0x{nrc:02X}")
            time.sleep(0.15)
            if rid % 64 == 63:
                self.keepalive()
                print(f"  ... {rid + 1}/256 完了")

    # ================================================================
    # Phase 5: IOControl 未テストIOCP — 既知PR LID (0x08=ハザード) で全IOCP走査
    # ================================================================
    def phase5_iocp_sweep(self):
        test_lid = 0x08
        hdr = f"\n=== Phase 5: IOControl IOCP全走査 (LID=0x{test_lid:02X} × IOCP 0x00-0xFF) ==="
        print(hdr)
        self.log.write(hdr + "\n")
        for iocp in range(0x00, 0x100):
            if iocp in TESTED_IOCPS:
                self.out(f"IOCP 0x{iocp:02X}: skip (既テスト済)")
                continue
            p = [0x80, ECM, TESTER, 0x08, 0x30, test_lid, iocp, 0, 0, 0, 0, 0]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, ECM)
            if sid == 0x70 and len(data) >= 2 and data[1] == test_lid:
                self.out(f"IOCP 0x{iocp:02X}: PR raw={raw.hex()}", highlight=True)
                self.stop_diag()
                time.sleep(GAP_PR)
            elif sid == 0x7F and len(data) >= 3:
                nrc = data[2]
                if nrc not in (0x31,):
                    self.out(f"IOCP 0x{iocp:02X}: NR NRC=0x{nrc:02X}")
            else:
                pass
            time.sleep(0.15)
            if iocp % 64 == 63:
                self.keepalive()
                print(f"  ... {iocp + 1}/256 完了")

    # ================================================================
    # Phase 6: IOCP=0x01 × LID 0x00-0x27 系統的スイープ
    # ================================================================
    def phase6_iocp01_sweep(self):
        hdr = "\n=== Phase 6: IOCP=0x01 × LID 0x00-0x27 ==="
        print(hdr)
        self.log.write(hdr + "\n")
        skip = {0x26}
        for lid in range(0x00, 0x28):
            if lid in skip:
                self.out(f"LID 0x{lid:02X}: skip (horn)")
                continue
            p = [0x80, ECM, TESTER, 0x08, 0x30, lid, 0x01, 0, 0, 0, 0, 0]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, ECM)
            if sid == 0x70 and len(data) >= 2 and data[1] == lid:
                known = "既知" if lid in KNOWN_PR_LIDS else "NEW"
                self.out(f"LID 0x{lid:02X} IOCP=0x01: PR ({known})", highlight=(known == "NEW"))
                self.stop_diag()
                time.sleep(GAP_PR)
            elif sid == 0x7F and len(data) >= 3:
                nrc = data[2]
                self.out(f"LID 0x{lid:02X}: NR NRC=0x{nrc:02X}")
            else:
                self.out(f"LID 0x{lid:02X}: silent")
            time.sleep(GAP)

    # ================================================================
    # Phase 7: SID 0x22 ReadDataByCommonId — DID サンプリング
    # Honda common DIDs + 0x0000-0x00FF + 0xF000-0xF0FF
    # ================================================================
    def phase7_read_common(self):
        hdr = "\n=== Phase 7: SID 0x22 ReadDataByCommonId (DIDサンプリング) ==="
        print(hdr)
        self.log.write(hdr + "\n")

        dids = []
        dids.extend(range(0x0000, 0x0100))
        dids.extend(range(0xF000, 0xF100))
        dids.extend(range(0xF400, 0xF420))
        dids.extend([0x0100, 0x0200, 0x0300, 0x0400, 0x0500,
                     0x1000, 0x2000, 0x3000, 0x4000, 0x5000,
                     0x6000, 0x7000, 0x8000, 0x9000, 0xA000,
                     0xB000, 0xC000, 0xD000, 0xE000])

        total = len(dids)
        for idx, did in enumerate(dids):
            hi = (did >> 8) & 0xFF
            lo = did & 0xFF
            p = [0x80, ECM, TESTER, 0x03, 0x22, hi, lo]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, ECM)
            if sid == 0x62:
                self.out(f"DID 0x{did:04X}: PR data={data.hex()}", highlight=True)
                time.sleep(GAP_PR)
            elif sid == 0x7F and len(data) >= 3:
                nrc = data[2]
                if nrc not in (0x31, 0x12, 0x11):
                    self.out(f"DID 0x{did:04X}: NR NRC=0x{nrc:02X}")
            time.sleep(0.12)
            if idx % 64 == 63:
                self.keepalive()
                print(f"  ... {idx + 1}/{total} 完了")

    # ================================================================
    # Phase 8: SID 0x18 ReadDTCByStatus
    # ================================================================
    def phase8_read_dtc(self):
        hdr = "\n=== Phase 8: SID 0x18 ReadDTCByStatus ==="
        print(hdr)
        self.log.write(hdr + "\n")
        status_masks = [0xFF, 0x01, 0x02, 0x04, 0x08, 0x09, 0x0A]
        for sm in status_masks:
            p = [0x80, ECM, TESTER, 0x03, 0x18, 0x02, sm]
            raw = self.send_recv(p)
            sid, data = parse_resp(raw, ECM)
            if sid == 0x58:
                self.out(f"statusMask=0x{sm:02X}: PR data={data.hex()}", highlight=True)
                time.sleep(GAP_PR)
            elif sid == 0x7F and len(data) >= 3:
                nrc = data[2]
                self.out(f"statusMask=0x{sm:02X}: NR NRC=0x{nrc:02X}")
            else:
                self.out(f"statusMask=0x{sm:02X}: silent")
            time.sleep(GAP)

    def run(self, phases=None):
        self.log = open(LOG, "w")
        self.connect()
        try:
            if phases is None or 1 in phases:
                responding = self.phase1_sid_sweep()
                if responding:
                    self.phase1b_subfn_sweep(responding)
                    self.reconnect()
            if phases is None or 2 in phases:
                self.phase2_read_local()
                self.reconnect()
            if phases is None or 3 in phases:
                self.phase3_ecu_ident()
                self.reconnect()
            if phases is None or 4 in phases:
                self.phase4_routine_control()
                self.reconnect()
            if phases is None or 5 in phases:
                self.phase5_iocp_sweep()
                self.reconnect()
            if phases is None or 6 in phases:
                self.phase6_iocp01_sweep()
            if phases is None or 7 in phases:
                self.reconnect()
                self.phase7_read_common()
            if phases is None or 8 in phases:
                self.reconnect()
                self.phase8_read_dtc()
        finally:
            self.s.close()
            self.log.close()

        print("\n" + "=" * 60)
        print("=== 全Findings サマリ ===")
        print("=" * 60)
        if self.findings:
            for f in self.findings:
                print(f"  ★ {f}")
        else:
            print("  (新規発見なし)")
        print(f"\nログ: {LOG}")


if __name__ == "__main__":
    phases = None
    if len(sys.argv) > 1:
        phases = set(int(x) for x in sys.argv[1:])

    scanner = Scanner()
    scanner.run(phases)
