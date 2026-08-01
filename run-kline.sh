#!/usr/bin/env bash
# kline-app（K-Line 制御 API + Web UI）の薄いラッパー。`./kline-app/run.sh "$@"` と同じ。
set -euo pipefail
cd "$(dirname "$0")"
exec ./kline-app/run.sh "$@"
