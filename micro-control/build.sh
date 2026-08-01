#!/usr/bin/env bash
# micro-control: arduino-cli ラッパー (compile / upload / monitor)
#
#   ./build.sh compile <sketch>            # firmware/<sketch> をコンパイル
#   ./build.sh upload  <sketch> [port]     # コンパイル + 書き込み
#   ./build.sh flash   <sketch> [port]     # upload + monitor
#   ./build.sh monitor [port]              # シリアルモニタ (115200, Ctrl+C で終了)
#   ./build.sh ports                       # 候補ポート一覧
#
# ボード: Freenove ESP32-S3 Board Lite (FNK0099) = ESP32S3 Dev Module
#   - USB CDC On Boot: Enabled (仕様の必須設定)
#   - USB Mode: Hardware CDC and JTAG (通常時)
#     MIDI ファーム (USB Host) は MIDI=1 ./build.sh ... で USB-OTG に切替。
#     その場合 OTG ポートはシリアルにならないので書き込み/モニタは UART側(CH343)。
#   - FlashSize=8M/PSRAM=opi は N8R8 モジュール想定。書き込みで蹴られたら
#     FQBN_OPTS 環境変数で上書きする (例: FlashSize=4M,PartitionScheme=default)
set -euo pipefail
cd "$(dirname "$0")"

FQBN="esp32:esp32:esp32s3"
DEFAULT_OPTS="CDCOnBoot=cdc,USBMode=hwcdc,FlashSize=8M,PartitionScheme=default_8MB,PSRAM=opi"
[ "${MIDI:-0}" = "1" ] && DEFAULT_OPTS="CDCOnBoot=cdc,USBMode=default,FlashSize=8M,PartitionScheme=default_8MB,PSRAM=opi"
OPTS="${FQBN_OPTS:-$DEFAULT_OPTS}"
BAUD=115200

list_ports() {
  ls /dev/cu.usbmodem* /dev/cu.wchusbserial* /dev/cu.usbserial* 2>/dev/null || true
}

pick_port() {
  # 引数優先。無ければ候補の先頭を採用
  if [ -n "${1:-}" ]; then echo "$1"; return; fi
  local p
  p=$(list_ports | head -1)
  if [ -z "$p" ]; then
    echo "ERROR: シリアルポートが見つかりません (ボード未接続?)。./build.sh ports で確認" >&2
    exit 1
  fi
  echo "$p"
}

sketch_dir() {
  local d="firmware/$1"
  if [ ! -d "$d" ]; then
    echo "ERROR: $d が見つかりません。候補:" >&2
    ls firmware >&2
    exit 1
  fi
  echo "$d"
}

case "${1:-}" in
  compile)
    arduino-cli compile --fqbn "$FQBN" --board-options "$OPTS" "$(sketch_dir "${2:?sketch名が必要}")"
    ;;
  upload)
    port=$(pick_port "${3:-}")
    dir=$(sketch_dir "${2:?sketch名が必要}")
    arduino-cli compile --fqbn "$FQBN" --board-options "$OPTS" "$dir"
    arduino-cli upload -p "$port" --fqbn "$FQBN" --board-options "$OPTS" "$dir"
    ;;
  flash)
    "$0" upload "${2:?sketch名が必要}" "${3:-}"
    "$0" monitor "${3:-}"
    ;;
  monitor)
    port=$(pick_port "${2:-}")
    echo "monitor: $port @ ${BAUD}bps (Ctrl+C で終了)"
    arduino-cli monitor -p "$port" -c "baudrate=$BAUD"
    ;;
  ports)
    list_ports
    ;;
  *)
    grep '^#   \./build\.sh' "$0" | sed 's/^#   //'
    exit 1
    ;;
esac
