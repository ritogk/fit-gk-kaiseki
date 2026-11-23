"""lamp-live 設定値。can-live / kline-app とは独立したアプリ(ポート 8200)。"""
import os

PORT = int(os.environ.get("LAMP_PORT", "8200"))

# ESP32 (hibeam_live ファーム) のシリアル。未指定なら /dev/cu.usbmodem* を自動検出。
SERIAL_PORT = os.environ.get("HIBEAM_PORT", "")
BAUD = 115200

# 演出の計算・送信レート(Hz)。1回の送信で r/l の2行、ESP の応答も2行返るため
# 115200bps の約4割に収まる 40Hz を上限にしている。
ENGINE_HZ = 40

# 画面への状態配信レート(Hz)
PUSH_HZ = 20

# ESP 側のフェード時間(ms)。
# 演出中: ハイビームは LED 想定(micro-control/CLAUDE.md 系統プラン)のため 40ms。
# 終了時: 安全要件の 300ms に戻す。ハロゲンを繋ぐ場合は RUN_FADE_MS も 300 にすること。
RUN_FADE_MS = int(os.environ.get("LAMP_FADE_MS", "40"))
IDLE_FADE_MS = 300
