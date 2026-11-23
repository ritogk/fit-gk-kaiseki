#!/usr/bin/env bash
# lamp-live: ハイビーム左右を Web 画面からライブ操作する。can-live / kline-app とは独立。
#   start : サーバ(8200)を起動し、ブラウザで http://localhost:8200/ を開く
#   stop  : 8200 のプロセスを止める(サーバ終了時に全消灯する)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT="${LAMP_PORT:-8200}"

stop() {
  local pid
  pid=$(lsof -ti :"$PORT" 2>/dev/null || true)
  # SIGTERM で止め、lifespan の終了処理(全消灯)を必ず通す
  [ -n "$pid" ] && kill $pid 2>/dev/null && sleep 0.5 || true
}

case "${1:-start}" in
  start)
    stop
    ( sleep 1.5; open "http://localhost:$PORT/" ) &
    cd "$SCRIPT_DIR" && exec "$ROOT/.venv/bin/uvicorn" server.main:app --host 0.0.0.0 --port "$PORT"
    ;;
  stop) stop ;;
  *) echo "usage: $0 {start|stop}" >&2; exit 1 ;;
esac
