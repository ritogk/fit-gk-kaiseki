#!/usr/bin/env bash
# Launchpad キーボードブリッジの薄いラッパー。`./kline-app/run-keyboard.sh "$@"` と同じ。
set -euo pipefail
cd "$(dirname "$0")"
exec ./kline-app/run-keyboard.sh "$@"
