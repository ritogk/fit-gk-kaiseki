#!/usr/bin/env python3
"""HZ → HB → LB rapid chase — fast variant.

Bypasses io_control's 100ms response window by writing directly to serial,
keeping the per-step gap to ~25ms (one frame's worth of TX/echo time).
HZ relay engagement still needs ~0.15s minimum or it won't visibly fire.
"""
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kline.client import KLineClient

CYCLES = 24

ORDER = [
    (0x08, 0.12),  # hazard — push below recommended; relay may flicker
    (0x1D, 0.04),  # high beam — fast
    (0x1C, 0.04),  # low beam — fast
]
GAP = 0.015  # tight — one frame echo just barely


def _cs(d):
    return sum(d) & 0xFF


with KLineClient() as cli:
    s = cli.s

    def fire(lid, hold):
        p = [0x80, 0x10, 0xF0, 0x08, 0x30, lid, 0x0F, 0, 0, 0, 0, 0]
        s.reset_input_buffer()
        s.write(bytes(p) + bytes([_cs(p)]))
        s.flush()
        time.sleep(hold)

    def stop(hold=GAP):
        p = [0x80, 0x10, 0xF0, 0x01, 0x20]
        s.reset_input_buffer()
        s.write(bytes(p) + bytes([_cs(p)]))
        s.flush()
        time.sleep(hold)

    t0 = time.time()
    for c in range(CYCLES):
        for lid, on_s in ORDER:
            fire(lid, on_s)
            stop()
    elapsed = time.time() - t0

print(f"chase done {CYCLES} cycles in {elapsed:.2f}s ({CYCLES * len(ORDER) / elapsed:.1f} fires/sec)")
