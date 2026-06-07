"""can-live 設定値。

F-CAN は 500k（実機確認済み）。低遅延優先のため固定周期プッシュはせず、
受信イベント駆動 + MAX_PUSH_HZ でコアレス上限を掛ける（main.py 参照）。
"""
import pathlib

CAN_CHANNEL = "can0"
CAN_BITRATE = 500000

DBC_PATH = pathlib.Path(__file__).resolve().parent.parent / "honda_fit_gk5_generated.dbc"

WS_PORT = 8100

# 送信のコアレス上限（Hz）。新フレーム到着で即送る／ただしこの間隔より速くは送らない。
MAX_PUSH_HZ = 250

# 最終受信からこの秒数を超えたら CAN 断（alive=false）とみなす。
STALE_SEC = 2.0

# can0 から1フレームも来ない時でも状態(alive=false)を送るためのハートビート間隔(秒)。
HEARTBEAT_SEC = 0.5
