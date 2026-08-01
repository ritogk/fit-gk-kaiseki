#!/usr/bin/env bash
# Start the Launchpad keyboard bridge (launchpad-kb).
#
# Thin wrapper around launchpad/run.sh so the keyboard can be launched from the
# project root, symmetric with run.sh (API + Web).
#
# Requires root (for /dev/uinput) and the binary built via `cd launchpad && make`.
# Usage: ./run-keyboard.sh {start|stop|restart}
set -euo pipefail
cd "$(dirname "$0")"

exec ./launchpad/run.sh "$@"
