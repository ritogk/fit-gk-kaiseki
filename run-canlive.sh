#!/usr/bin/env bash
# can-live（ライブ F-CAN 可視化）の薄いラッパー。`./can-live/run.sh "$@"` と同じ。
set -euo pipefail
cd "$(dirname "$0")"
exec ./can-live/run.sh "$@"
