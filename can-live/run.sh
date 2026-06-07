#!/usr/bin/env bash
# can-live: ライブ F-CAN テレメトリ可視化（既存 K-Line アプリとは別ポートで独立）。
#   start   : can0 を up（必要なら）→ WS サーバ(8100) + Vite(5273) を起動
#   stop    : 8100/5273 のプロセスを kill（can0 は up のまま）
#   restart : stop → start
#
# 通常起動では uvicorn に --reload を付けない（低遅延・受信スレッド二重起動回避）。
# 開発時にホットリロードしたい場合のみ `./run.sh start --dev`。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CAN_IF="can0"
CAN_BITRATE=500000
API_PORT=8100
WEB_PORT=5273

kill_port() {
  local pid
  pid=$(lsof -ti :"$1" 2>/dev/null || true)
  if [ -n "$pid" ]; then
    echo "Killing process on port $1 (PID: $pid)"
    kill -9 $pid 2>/dev/null || true
    sleep 0.3
  fi
}

ensure_can0() {
  if ! ip link show "$CAN_IF" >/dev/null 2>&1; then
    echo "ERROR: $CAN_IF が見つかりません（CAN-USB アダプタ未接続？）" >&2
    exit 1
  fi
  local state
  state=$(ip -br link show "$CAN_IF" | awk '{print $2}')
  if [ "$state" != "UP" ]; then
    echo "Bringing up $CAN_IF @ ${CAN_BITRATE}bps (sudo)..."
    sudo ip link set "$CAN_IF" up type can bitrate "$CAN_BITRATE"
  else
    echo "$CAN_IF is already UP"
  fi
}

start() {
  local dev=""
  [ "${1:-}" = "--dev" ] && dev="--reload --reload-include '*.py'"

  ensure_can0
  kill_port "$API_PORT"
  kill_port "$WEB_PORT"

  # バックエンド（can-live ディレクトリから server.main:app を起動）
  ( cd "$SCRIPT_DIR" && eval "\"$ROOT/.venv/bin/uvicorn\" server.main:app --host 0.0.0.0 --port $API_PORT $dev" ) &

  # フロント（Vite dev）
  cd "$SCRIPT_DIR/web" && exec npx vite --host 0.0.0.0 --port "$WEB_PORT"
}

stop() {
  kill_port "$API_PORT"
  kill_port "$WEB_PORT"
}

case "${1:-start}" in
  start)   start "${2:-}" ;;
  stop)    stop ;;
  restart) stop; sleep 0.3; start "${2:-}" ;;
  *) echo "usage: $0 {start|stop|restart} [--dev]" >&2; exit 1 ;;
esac
