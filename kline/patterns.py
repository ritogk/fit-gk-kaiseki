"""Beat patterns built on top of the K-Line client.

All patterns honour a process-wide cancel flag so a /stop endpoint can
interrupt a running pattern between beats.
"""
import threading
import time

from .client import KLineClient


HZ = 0x08  # hazard
HB = 0x1D  # high beam
LB = 0x1C  # low beam
TL = 0x0A  # turn left
TR = 0x0B  # turn right
PS = 0x25  # position light


_cancel = threading.Event()


def cancel():
    _cancel.set()


def reset():
    _cancel.clear()


def is_cancelled():
    return _cancel.is_set()


def _fire(cli, lid, iocp=0x0F, dur=0.08):
    cli.io_control(lid, iocp)
    if dur > 0.03:
        time.sleep(dur - 0.03)
    cli.stop_diag()


def _wait_until(start, target_offset):
    """Sleep until start+target_offset, polling cancel every 50ms."""
    while True:
        if _cancel.is_set():
            return False
        rem = (start + target_offset) - time.time()
        if rem <= 0:
            return True
        time.sleep(min(rem, 0.05))


def _run_events(events):
    reset()
    with KLineClient() as cli:
        start = time.time()
        played = 0
        for offset, lid, dur in events:
            if not _wait_until(start, offset):
                break
            _fire(cli, lid, 0x0F, dur)
            played += 1
        return {
            "played": played,
            "total": len(events),
            "elapsed_s": round(time.time() - start, 3),
            "cancelled": _cancel.is_set(),
        }


def play_3way(bpm=120, measures=8):
    """HB on every quarter, LB on every offbeat, HZ accent on beats 1 & 3."""
    HB_DUR = LB_DUR = 0.08
    HZ_DUR = 0.18
    beat = 60.0 / bpm
    events = []
    for m in range(measures):
        base = m * 4 * beat
        events.append((base + 0 * beat - 0.001, HZ, HZ_DUR))
        events.append((base + 2 * beat - 0.001, HZ, HZ_DUR))
        for i in range(4):
            events.append((base + i * beat + 0.20, HB, HB_DUR))
        for i in range(4):
            events.append((base + (i + 0.5) * beat, LB, LB_DUR))
    events.sort()
    return _run_events(events)


def play_beat(bpm=120, measures=8):
    """Four-on-the-floor: HB on every quarter + PS on every offbeat."""
    DUR = 0.08
    beat = 60.0 / bpm
    events = []
    for m in range(measures):
        base = m * 4 * beat
        for i in range(4):
            events.append((base + i * beat, HB, DUR))
        for i in range(4):
            events.append((base + (i + 0.5) * beat, PS, DUR))
    events.sort()
    return _run_events(events)


def play_stereo(bpm=120, measures=8):
    """Alternating L/R turn signals + HB accent on beat 1."""
    DUR = 0.08
    beat = 60.0 / bpm
    events = []
    for m in range(measures):
        base = m * 4 * beat
        for i in range(4):
            events.append((base + i * beat, TL if i % 2 == 0 else TR, DUR))
        events.append((base, HB, DUR))
    events.sort()
    return _run_events(events)


def play_polyrhythm(bpm=120, measures=8):
    """4-against-3: HB on every quarter, HZ on triplet boundaries."""
    beat = 60.0 / bpm
    events = []
    for m in range(measures):
        base = m * 4 * beat
        for i in range(4):
            events.append((base + i * beat, HB, 0.08))
        for i in range(3):
            events.append((base + i * (4 * beat / 3), HZ, 0.18))
    events.sort()
    return _run_events(events)


def play_chase(cycles=20, hz_on=0.15, hb_on=0.05, lb_on=0.05, gap=0.025, speed=1.4):
    """Rapid chase: HZ → HB → LB.

    Bypasses io_control's response-read window for tighter timing.
    `speed` multiplies the tempo: 1.0 = default, 2.0 = twice as fast, 0.5 = half.
    HZ is clamped to 0.15s minimum (physical relay floor).
    """
    reset()
    speed = max(0.1, float(speed))
    hz_on_a = max(0.15, hz_on / speed)
    hb_on_a = max(0.025, hb_on / speed)
    lb_on_a = max(0.025, lb_on / speed)
    gap_a = max(0.010, gap / speed)

    def _cs(d):
        return sum(d) & 0xFF

    order = [(HZ, hz_on_a), (HB, hb_on_a), (LB, lb_on_a)]
    with KLineClient() as cli:
        s = cli.s
        t0 = time.time()
        played = 0
        for _ in range(cycles):
            if _cancel.is_set():
                break
            for lid, on_s in order:
                if _cancel.is_set():
                    break
                p = [0x80, 0x10, 0xF0, 0x08, 0x30, lid, 0x0F, 0, 0, 0, 0, 0]
                s.reset_input_buffer()
                s.write(bytes(p) + bytes([_cs(p)]))
                s.flush()
                time.sleep(on_s)
                p2 = [0x80, 0x10, 0xF0, 0x01, 0x20]
                s.reset_input_buffer()
                s.write(bytes(p2) + bytes([_cs(p2)]))
                s.flush()
                time.sleep(gap_a)
            played += 1
        return {
            "played": played,
            "total": cycles,
            "elapsed_s": round(time.time() - t0, 3),
            "cancelled": _cancel.is_set(),
            "speed": speed,
        }


FG = 0x20  # fog

SEQUENCE_LIDS = {1: HZ, 2: HB, 3: LB, 4: PS, 5: FG, 6: TL, 7: TR}


def play_sequence(steps=None, cycles=80, on_hz=0.15, on_hb=0.05, on_lb=0.05, on_ps=0.05, on_fg=0.05, on_tl=0.15, on_tr=0.15, gap=0.025, speed=1.4, cmd_delay=0.020):
    """Run a custom step sequence where 1=HZ, 2=HB, 3=LB, 4=PS, 5=FG.

    Each step is a list of position numbers to fire simultaneously.
    e.g. [[1,2], [2,3,4], [5]] — step 1 fires HZ+HB together, etc.
    """
    if steps is None:
        steps = [[1], [2], [3]]
    reset()
    speed = max(0.1, float(speed))
    gap_a = max(0.010, gap / speed)

    def _cs(d):
        return sum(d) & 0xFF

    on_for = {
        1: max(0.15, on_hz / speed),
        2: max(0.025, on_hb / speed),
        3: max(0.025, on_lb / speed),
        4: max(0.025, on_ps / speed),
        5: max(0.025, on_fg / speed),
        6: max(0.15, on_tl / speed),
        7: max(0.15, on_tr / speed),
    }

    with KLineClient() as cli:
        s = cli.s
        t0 = time.time()
        played = 0
        for _ in range(cycles):
            if _cancel.is_set():
                break
            for step in steps:
                if _cancel.is_set():
                    break
                lids = [SEQUENCE_LIDS[p] for p in step if p in SEQUENCE_LIDS]
                if not lids:
                    continue
                for lid in lids:
                    p = [0x80, 0x10, 0xF0, 0x08, 0x30, lid, 0x0F, 0, 0, 0, 0, 0]
                    s.reset_input_buffer()
                    s.write(bytes(p) + bytes([_cs(p)]))
                    s.flush()
                    time.sleep(cmd_delay)
                    s.reset_input_buffer()
                on_s = max(on_for.get(pos, 0.05) for pos in step if pos in SEQUENCE_LIDS)
                time.sleep(on_s)
                p2 = [0x80, 0x10, 0xF0, 0x01, 0x20]
                s.reset_input_buffer()
                s.write(bytes(p2) + bytes([_cs(p2)]))
                s.flush()
                time.sleep(gap_a)
                played += 1
        return {
            "played": played,
            "total": cycles * len(steps),
            "elapsed_s": round(time.time() - t0, 3),
            "cancelled": _cancel.is_set(),
            "speed": speed,
        }


def play_pattern(lid, iocp, on_s, off_s, cycles):
    """Generic single-LID ON/OFF cycler."""
    reset()
    with KLineClient() as cli:
        played = 0
        for _ in range(cycles):
            if _cancel.is_set():
                break
            cli.io_control(lid, iocp)
            on_remain = on_s - 0.1
            t_end = time.time() + max(0.0, on_remain)
            while time.time() < t_end:
                if _cancel.is_set():
                    break
                time.sleep(min(t_end - time.time(), 0.05))
            cli.stop_diag()
            played += 1
            if _cancel.is_set():
                break
            t_off = time.time() + off_s
            while time.time() < t_off:
                if _cancel.is_set():
                    break
                time.sleep(min(t_off - time.time(), 0.05))
        return {
            "played": played,
            "total": cycles,
            "cancelled": _cancel.is_set(),
        }
