"""ISO 14230 (KWP2000) K-Line client for Honda Fit GK5 ECM(0x10).

Connects via OBD2 pin7 K-Line through gateway 0x46 to ECM(0x10) at 10400 bps.
Implements StartCommunication (Fast Init), IO Control by LocalId (SID 0x30),
and StopDiagSession (SID 0x20) for hard envelope cutoff.

Single-process serial access only — a process-local lock guards the port.
"""
import os
import time
import threading
import serial


PORT = os.environ.get("KLINE_PORT", "/dev/ttyUSB0")
BAUD = 10400
ECM = 0x10
TESTER = 0xF0
GATEWAY = 0x46

_serial_lock = threading.Lock()


def cs(d):
    return sum(d) & 0xFF


def parse_resp(raw, expected_src=ECM):
    """Find the first response frame from <expected_src> back to TESTER."""
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


class KLineBusyError(RuntimeError):
    pass


class KLineClient:
    """Context-managed K-Line session to ECM(0x10) via gateway 0x46."""

    def __init__(self, port=None, baud=BAUD):
        self.port = port or PORT
        self.baud = baud
        self.s = None
        self._locked = False

    def __enter__(self):
        if not _serial_lock.acquire(blocking=False):
            raise KLineBusyError("K-Line port is busy (another operation in progress)")
        self._locked = True
        try:
            self._connect()
        except Exception:
            self._release_lock()
            raise
        return self

    def __exit__(self, *exc):
        try:
            if self.s:
                try:
                    self.s.close()
                except Exception:
                    pass
                self.s = None
        finally:
            self._release_lock()

    def _release_lock(self):
        if self._locked:
            try:
                _serial_lock.release()
            finally:
                self._locked = False

    def _connect(self):
        s = serial.Serial(self.port, self.baud, timeout=0.05)
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
        time.sleep(0.2)
        r = s.read(128)
        if not (r and 0xC1 in r):
            try:
                s.close()
            except Exception:
                pass
            raise RuntimeError(f"StartCommunication failed: {r.hex() if r else '(empty)'}")
        self.s = s

    def send_raw(self, payload, wait=0.05):
        msg = bytes(payload) + bytes([cs(payload)])
        self.s.reset_input_buffer()
        self.s.write(msg)
        self.s.flush()
        time.sleep(wait)
        return self.s.read(256)

    def io_control(self, lid, iocp=0x0F, state=(0, 0, 0, 0, 0)):
        """SID 0x30 InputOutputControlByLocalIdentifier on ECM."""
        p = [0x80, ECM, TESTER, 0x08, 0x30, lid, iocp,
             state[0], state[1], state[2], state[3], state[4]]
        raw = self.send_raw(p, wait=0.1)
        sid, data = parse_resp(raw, ECM)
        if sid == 0x70 and len(data) >= 2 and data[1] == lid:
            return {"kind": "PR", "lid": lid, "iocp": iocp, "raw": raw.hex()}
        if sid == 0x7F and len(data) >= 3:
            return {"kind": "NR", "lid": lid, "iocp": iocp, "nrc": data[2], "raw": raw.hex()}
        return {"kind": "silent", "lid": lid, "iocp": iocp, "raw": raw.hex()}

    def stop_diag(self):
        """SID 0x20 StopDiagnosticSession — short-circuits any active test envelope."""
        return self.send_raw([0x80, ECM, TESTER, 0x01, 0x20], wait=0.05)

    def fire_envelope(self, lid, iocp, duration_s):
        """Trigger an active test, hold, then StopDiag for hard cutoff."""
        result = self.io_control(lid, iocp)
        if result["kind"] == "PR":
            time.sleep(max(0.0, duration_s - 0.1))
            self.stop_diag()
        return result
