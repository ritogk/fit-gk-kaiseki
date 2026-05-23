#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$SCRIPT_DIR/launchpad-kb"
KEYMAP="$SCRIPT_DIR/keymap-live.conf"

case "${1:-start}" in
  start)
    sudo killall -9 launchpad-kb 2>/dev/null || true
    sleep 0.3
    sudo "$BIN" -m "$KEYMAP"
    ;;
  stop)
    sudo killall -9 launchpad-kb 2>/dev/null || true
    echo "launchpad-kb stopped"
    ;;
  restart)
    "$0" stop
    sleep 0.3
    "$0" start
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
    exit 1
    ;;
esac
