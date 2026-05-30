"""Persistent K-Line session for real-time live performance.

Keeps the serial port open and processes note_on/note_off commands
via a dedicated worker thread for minimum latency (~20-40ms end-to-end).
"""
import os
import queue
import threading
import time

import serial

from .client import PORT, BAUD, ECM, TESTER, GATEWAY, _serial_lock
from .commands import LIDS


def _cs(d):
    return sum(d) & 0xFF


_IO_CONTROL_TEMPLATE = [0x80, ECM, TESTER, 0x08, 0x30, 0x00, 0x0F, 0, 0, 0, 0, 0]
_STOP_DIAG = [0x80, ECM, TESTER, 0x01, 0x20]
_TESTER_PRESENT = [0x80, ECM, TESTER, 0x01, 0x3E]
# Min gap between consecutive K-Line frames (half-duplex P2). Physical floor is
# ~20ms (13B cmd + 7B resp @10400bps); below that the bus collides and some
# io_control frames get dropped. Tune live via KLINE_TX_GAP to find the floor.
_TX_GAP = float(os.environ.get("KLINE_TX_GAP", "0.02"))
# horn_short(LID 0x26)の StopDiag 送信間隔。短いほど鳴動が短いが、詰めすぎると
# StopDiag が半二重バス衝突で取りこぼされ、ECUエンベロープで鳴りっぱなしになる。
# 実機確認: 12/15/18ms=NG(鳴りっぱなし) / 20ms=OK。20ms が固定値での実用下限。
_HORN_LID = 0x26
_HORN_STOP_GAP = float(os.environ.get("KLINE_HORN_GAP", "0.02"))


class LiveSession:
    def __init__(self, port=None):
        self.port = port or PORT
        self._s: serial.Serial | None = None
        self._q: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._active_lids: set[int] = set()
        self._lid_iocp: dict[int, int] = {}
        self._loop_lids: set[int] = set()
        self._bpm: float = 120.0
        self._running = False
        self._locked = False
        self._last_tx = 0.0

    def start(self):
        if not _serial_lock.acquire(blocking=False):
            raise RuntimeError("K-Line port is busy")
        self._locked = True
        try:
            self._connect()
            self._running = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
        except Exception:
            self._release()
            raise

    def stop(self):
        self._running = False
        self._q.put(("quit", None, None))
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        if self._s:
            try:
                self._raw_stop_diag()
            except Exception:
                pass
            try:
                self._s.close()
            except Exception:
                pass
            self._s = None
        self._active_lids.clear()
        self._lid_iocp.clear()
        self._release()

    def _release(self):
        if self._locked:
            try:
                _serial_lock.release()
            finally:
                self._locked = False

    def _connect(self):
        s = serial.Serial(self.port, BAUD, timeout=0.05)
        s.dtr = False
        s.rts = False
        time.sleep(0.3)
        s.reset_input_buffer()
        s.break_condition = True
        time.sleep(0.025)
        s.break_condition = False
        time.sleep(0.025)
        sc_p = [0x81, GATEWAY, TESTER, 0x81]
        s.write(bytes(sc_p) + bytes([_cs(sc_p)]))
        s.flush()
        time.sleep(0.2)
        r = s.read(128)
        if not (r and 0xC1 in r):
            try:
                s.close()
            except Exception:
                pass
            raise RuntimeError(f"StartCommunication failed: {r.hex() if r else '(empty)'}")
        self._s = s

    # Commands that are pulse-only (no hold) — fire once, no note_off needed
    PULSE_CMDS = {"lock", "unlock", "trunk", "chirp", "horn_short"}

    def note_on(self, cmd_id: str, hold: bool = False):
        if cmd_id not in LIDS:
            return
        lid, iocp, _, _ = LIDS[cmd_id]
        if cmd_id in self.PULSE_CMDS:
            self._q.put(("pulse", lid, iocp))
        else:
            self._q.put(("on", lid, iocp))

    def note_off(self, cmd_id: str):
        if cmd_id not in LIDS:
            return
        lid, _, _, _ = LIDS[cmd_id]
        self._q.put(("off", lid, None))

    def all_off(self):
        self._q.put(("all_off", None, None))

    def loop_on(self, cmd_id: str):
        if cmd_id not in LIDS:
            return
        lid, _, _, _ = LIDS[cmd_id]
        self._q.put(("loop_on", lid, None))

    def loop_off(self, cmd_id: str):
        if cmd_id not in LIDS:
            return
        lid, _, _, _ = LIDS[cmd_id]
        self._q.put(("loop_off", lid, None))

    def set_bpm(self, bpm: float):
        self._bpm = max(40.0, min(240.0, bpm))

    def get_active(self) -> set[str]:
        lid_to_name = {v[0]: k for k, v in LIDS.items()}
        return {lid_to_name[lid] for lid in self._active_lids if lid in lid_to_name}

    def _pace(self, gap=None):
        """Ensure enough gap from the previous TX that the ECU's response has
        cleared the half-duplex K-Line bus before we transmit again (ISO 14230
        P2). Measured from the last TX, so an isolated command waits not at all
        while only back-to-back frames (e.g. multi-light fire) get spaced out."""
        wait = (gap if gap is not None else _TX_GAP) - (time.time() - self._last_tx)
        if wait > 0:
            time.sleep(wait)
        self._s.reset_input_buffer()

    def _send(self, frame, gap=None):
        self._pace(gap)
        self._s.write(bytes(frame) + bytes([_cs(frame)]))
        self._s.flush()
        self._last_tx = time.time()

    def _raw_fire(self, lid: int, iocp: int = 0x0F):
        p = list(_IO_CONTROL_TEMPLATE)
        p[5] = lid
        p[6] = iocp
        self._send(p)

    def _raw_stop_diag(self, gap=None):
        self._send(_STOP_DIAG, gap)

    def _raw_tester_present(self):
        self._send(_TESTER_PRESENT)

    def _refire_active(self):
        for lid in self._active_lids:
            self._raw_fire(lid, self._lid_iocp.get(lid, 0x0F))

    _LID_TL = 0x0A
    _LID_TR = 0x0B
    _LID_HZ = 0x08

    def _drain_queue(self):
        """Drain all pending messages from queue without blocking."""
        msgs = []
        while True:
            try:
                msgs.append(self._q.get_nowait())
            except queue.Empty:
                break
        return msgs

    def _process_batch(self, batch):
        """Process a batch of messages, applying state changes then syncing K-Line once."""
        before = set(self._active_lids)
        need_sync = False
        for action, lid, iocp in batch:
            if action == "quit":
                self._running = False
                return
            elif action == "pulse":
                self._raw_fire(lid, iocp)
                if lid == _HORN_LID:
                    self._raw_stop_diag(gap=_HORN_STOP_GAP)  # 鳴動を最短化
                else:
                    time.sleep(0.01)
                    self._raw_stop_diag()
                if self._active_lids:
                    self._refire_active()
            elif action == "on":
                if lid in (self._LID_TL, self._LID_TR):
                    other = self._LID_TR if lid == self._LID_TL else self._LID_TL
                    if other in self._active_lids:
                        self._active_lids.discard(other)
                        self._lid_iocp.pop(other, None)
                        self._active_lids.add(self._LID_HZ)
                        self._lid_iocp[self._LID_HZ] = 0x0F
                        need_sync = True
                        continue
                if lid not in self._active_lids:
                    self._active_lids.add(lid)
                    self._lid_iocp[lid] = iocp
            elif action == "off":
                if lid in (self._LID_TL, self._LID_TR) and self._LID_HZ in self._active_lids:
                    remaining = self._LID_TR if lid == self._LID_TL else self._LID_TL
                    self._active_lids.discard(self._LID_HZ)
                    self._lid_iocp.pop(self._LID_HZ, None)
                    self._active_lids.add(remaining)
                    self._lid_iocp[remaining] = 0x0F
                    need_sync = True
                elif lid in self._active_lids:
                    self._active_lids.discard(lid)
                    self._lid_iocp.pop(lid, None)
            elif action == "all_off":
                self._active_lids.clear()
                self._lid_iocp.clear()
                self._loop_lids.clear()
            elif action == "loop_on":
                self._loop_lids.add(lid)
            elif action == "loop_off":
                self._loop_lids.discard(lid)

        added = self._active_lids - before
        removed = before - self._active_lids

        if removed or need_sync:
            self._raw_stop_diag()
            if self._active_lids:
                time.sleep(0.005)
                self._refire_active()
        elif added:
            for lid in added:
                self._raw_fire(lid, self._lid_iocp.get(lid, 0x0F))

    _KEEPALIVE_S = 3.0

    def _worker(self):
        last_keepalive = time.time()
        last_beat = time.time()
        loop_phase = False
        while self._running:
            beat_interval = 60.0 / self._bpm / 2 if self._loop_lids else 0.0
            timeout = min(beat_interval, 0.5) if beat_interval > 0 else 0.5

            try:
                first = self._q.get(timeout=timeout)
                time.sleep(0.015)
                batch = [first] + self._drain_queue()
                self._process_batch(batch)
                last_keepalive = time.time()
            except queue.Empty:
                pass

            now = time.time()
            if now - last_keepalive > self._KEEPALIVE_S:
                if self._active_lids:
                    self._refire_active()
                else:
                    self._raw_tester_present()
                last_keepalive = now

            if self._loop_lids and beat_interval > 0:
                now = time.time()
                if now - last_beat >= beat_interval:
                    loop_phase = not loop_phase
                    self._raw_stop_diag()
                    held = self._active_lids - self._loop_lids
                    if loop_phase:
                        for lid in self._loop_lids:
                            self._raw_fire(lid)
                    for lid in held:
                        self._raw_fire(lid)
                    last_beat = now
                    last_keepalive = now
            else:
                loop_phase = False


_session: LiveSession | None = None
_session_lock = threading.Lock()


def get_session() -> LiveSession | None:
    return _session


def start_session() -> LiveSession:
    global _session
    with _session_lock:
        if _session and _session._running:
            return _session
        s = LiveSession()
        s.start()
        _session = s
        return s


def stop_session():
    global _session
    with _session_lock:
        if _session:
            _session.stop()
            _session = None
