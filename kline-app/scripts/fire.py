#!/usr/bin/env python3
"""CLI wrapper for the kline.commands module.

Usage:
    fire.py <name> [duration_s]
    fire.py list

Examples:
    fire.py hazard 5         # hazard for 5 seconds
    fire.py chirp            # single chirp pulse
    fire.py high_beam 0.5    # 0.5s high-beam blip
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kline import commands


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    if args[0] == "list":
        for name, meta in commands.list_commands().items():
            print(f"  {name:12s}  LID 0x{meta['lid']:02X}  IOCP 0x{meta['iocp']:02X}  {meta['description']}")
        return

    name = args[0]
    duration_s = float(args[1]) if len(args) >= 2 else None
    result = commands.fire(name, duration_s)
    print(result)


if __name__ == "__main__":
    main()
