"""Fun router — beat patterns built on top of K-Line.

Patterns run in a background thread so /stop can interrupt them mid-flight.
Only one pattern can run at a time (HTTP 409 otherwise).
"""
import threading

from fastapi import APIRouter, HTTPException, Query

from kline import patterns

router = APIRouter(prefix="/api/fun", tags=["fun"])

_thread_lock = threading.Lock()
_thread = None
_last_result = None
_last_kind = None


def _is_running():
    return bool(_thread) and _thread.is_alive()


def _start(kind, func, **kwargs):
    global _thread, _last_result, _last_kind
    with _thread_lock:
        if _is_running():
            raise HTTPException(409, "another pattern is already playing")
        _last_result = None
        _last_kind = kind

        def wrap():
            global _last_result
            try:
                _last_result = func(**kwargs)
            except Exception as e:
                _last_result = {"error": str(e)}

        _thread = threading.Thread(target=wrap, daemon=True)
        _thread.start()
    return {"status": "started", "kind": kind, "params": kwargs}


@router.post("/3way")
def fun_3way(bpm: int = 120, measures: int = 8):
    return _start("3way", patterns.play_3way, bpm=bpm, measures=measures)


@router.post("/beat")
def fun_beat(bpm: int = 120, measures: int = 8):
    return _start("beat", patterns.play_beat, bpm=bpm, measures=measures)


@router.post("/stereo")
def fun_stereo(bpm: int = 120, measures: int = 8):
    return _start("stereo", patterns.play_stereo, bpm=bpm, measures=measures)


@router.post("/polyrhythm")
def fun_polyrhythm(bpm: int = 120, measures: int = 8):
    return _start("polyrhythm", patterns.play_polyrhythm, bpm=bpm, measures=measures)


@router.post("/chase")
def fun_chase(
    cycles: int = 20,
    speed: float = 1.4,
    hz_on: float = 0.15,
    hb_on: float = 0.05,
    lb_on: float = 0.05,
    gap: float = 0.025,
):
    """Rapid chase: HZ → HB → LB. speed: 1.0=default, 2.0=double, 0.5=half."""
    return _start("chase", patterns.play_chase,
                  cycles=cycles, speed=speed,
                  hz_on=hz_on, hb_on=hb_on, lb_on=lb_on, gap=gap)


def _parse_steps(raw: str):
    """Parse step notation: '[1,2],[3,4],5' → [[1,2],[3,4],[5]]."""
    import re
    steps = []
    for token in re.findall(r'\[[\d,\s]+\]|\d+', raw):
        if token.startswith('['):
            inner = token.strip('[]')
            steps.append([int(x.strip()) for x in inner.split(',') if x.strip()])
        else:
            steps.append([int(token)])
    return steps


@router.post("/sequence")
def fun_sequence(
    positions: str = "1,2,3",
    cycles: int = 80,
    speed: float = 1.4,
    on_hz: float = 0.15,
    on_hb: float = 0.05,
    on_lb: float = 0.05,
    on_ps: float = 0.05,
    on_fg: float = 0.05,
    on_tl: float = 0.15,
    on_tr: float = 0.15,
    gap: float = 0.025,
    cmd_delay: float = 0.020,
):
    """Custom step sequence — e.g. '[1,2],[3,4],5' fires groups simultaneously."""
    try:
        steps = _parse_steps(positions)
    except ValueError:
        raise HTTPException(400, f"invalid positions string: {positions!r}")
    if not steps:
        raise HTTPException(400, "positions cannot be empty")
    return _start("sequence", patterns.play_sequence,
                  steps=steps, cycles=cycles, speed=speed,
                  on_hz=on_hz, on_hb=on_hb, on_lb=on_lb, on_ps=on_ps, on_fg=on_fg,
                  on_tl=on_tl, on_tr=on_tr, gap=gap,
                  cmd_delay=cmd_delay)


@router.post("/pattern")
def fun_pattern(
    lid: int = Query(..., description="LID (0x00-0x27 supported)"),
    iocp: int = 0x0F,
    on_s: float = 0.1,
    off_s: float = 0.1,
    cycles: int = 10,
):
    return _start("pattern", patterns.play_pattern,
                  lid=lid, iocp=iocp, on_s=on_s, off_s=off_s, cycles=cycles)


@router.post("/stop")
def fun_stop():
    patterns.cancel()
    if _thread:
        _thread.join(timeout=3.0)
    return {"status": "stopped", "kind": _last_kind, "result": _last_result}


@router.get("/status")
def fun_status():
    return {
        "running": _is_running(),
        "kind": _last_kind,
        "last_result": _last_result,
    }
