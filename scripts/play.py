#!/usr/bin/env python3
"""CLI wrapper for the kline.patterns module.

Usage:
    play.py 3way [BPM] [MEASURES]
    play.py beat [BPM] [MEASURES]
    play.py stereo [BPM] [MEASURES]
    play.py polyrhythm [BPM] [MEASURES]
    play.py pattern <LID_HEX> <IOCP_HEX> <ON_S> <OFF_S> <CYCLES>

The KLINE_PORT environment variable selects the serial device
(default /dev/ttyUSB0).
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kline import patterns


def usage():
    print(__doc__)
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if not args:
        usage()

    kind = args[0]
    rest = args[1:]

    if kind in ("3way", "beat", "stereo", "polyrhythm"):
        bpm = int(rest[0]) if len(rest) >= 1 else 120
        measures = int(rest[1]) if len(rest) >= 2 else 8
        func = getattr(patterns, f"play_{kind}")
        result = func(bpm=bpm, measures=measures)
    elif kind == "pattern":
        if len(rest) != 5:
            usage()
        lid = int(rest[0], 16)
        iocp = int(rest[1], 16)
        on_s = float(rest[2])
        off_s = float(rest[3])
        cycles = int(rest[4])
        result = patterns.play_pattern(lid, iocp, on_s, off_s, cycles)
    else:
        usage()

    print(result)


if __name__ == "__main__":
    main()
