#!/usr/bin/env bash
# Start the API server (with hot reload).
#
# Requires read/write on the K-Line port (default /dev/ttyUSB0).
# If the port is owned by root:dialout, the user must be in the dialout group
# or run `sudo chmod 666 /dev/ttyUSB0` once after each USB reconnect.
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --reload-include '*.py'
