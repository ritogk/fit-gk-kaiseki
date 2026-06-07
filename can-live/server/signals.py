"""DBC デコード結果（生信号 dict）→ フロント用の信号オブジェクトへの変換。

cantools が scale/offset を適用済みの物理値を渡してくる前提。
steeringRate / longAccel は DBC に無いので時間微分で派生する（前回値を保持）。
latAccel は推定元が無いため 0 固定（GForceBall は縦Gのみ動く）。
"""
import time

# 汎用ゲージ（GaugeGrid）に出さない信号名のパターン。パディング/予約/カウンタ類。
_SKIP_RAW = ("Padding", "Reserved", "RollingCnt", "Counter", "_Const", "FreeRun")


class SignalDeriver:
    """1 WS 接続につき 1 インスタンス。微分の前回値を保持する。"""

    def __init__(self) -> None:
        self._last_angle = None
        self._last_angle_t = None
        self._last_speed = None
        self._last_speed_t = None

    def build(self, raw: dict, now: float | None = None) -> dict:
        now = time.time() if now is None else now

        def g(name: str, default: float = 0.0) -> float:
            v = raw.get(name)
            return float(v) if v is not None else default

        throttle = g("THR_AccelPos")   # 0x130 B3（実車校正済み）
        # 車速 = 0x1D0 WheelSpeeds（実走解析で確定。前輪平均, km/h）
        wfl, wfr = g("WS_FL"), g("WS_FR")
        speed = (wfl + wfr) / 2.0
        angle = g("STR_Angle")         # 0x156 B0-B1 符号付（実車校正済み）
        brake_state = g("BRK_State")   # 0x1A4 B0 = 0(離)/1/2 段階（実車校正済み）

        # 水温: 旧マップ(17C)は実は RPM だった。実水温の位置は未確定 → 0。
        coolant = 0.0

        # ステア角速度 [deg/s]（派生）
        steering_rate = 0.0
        if self._last_angle is not None and self._last_angle_t is not None:
            dt = now - self._last_angle_t
            if dt > 0:
                steering_rate = (angle - self._last_angle) / dt
        self._last_angle, self._last_angle_t = angle, now

        # 前後G [m/s^2]（車速 km/h の時間微分。派生）
        long_accel = 0.0
        if self._last_speed is not None and self._last_speed_t is not None:
            dt = now - self._last_speed_t
            if dt > 0:
                long_accel = ((speed - self._last_speed) / 3.6) / dt
        self._last_speed, self._last_speed_t = speed, now

        # RPM = 0x17C B2-B3 を 16bit BE そのまま（アイドル raw≈664≒実回転で scale=1, 実車校正済み）。
        rpm = g("ENG_RPM")

        return {
            "rpm": round(rpm),
            "throttle": round(throttle, 1),
            "speed": round(speed, 2),
            "steeringAngle": round(angle, 1),
            "steeringRate": round(steering_rate, 1),
            "brake": round(brake_state),
            "brakePressed": brake_state > 0,
            "gasPressed": throttle > 0.5,
            "coolantTemp": round(coolant, 1),
            "batteryVoltage": round(g("BAT_Voltage"), 2),
            "gear": int(g("TRN_GearPos")),
            "outsideTemp": round(g("OT_Temp"), 1),
            "wheelFL": round(g("WS_FL"), 1),
            "wheelFR": round(g("WS_FR"), 1),
            "wheelRL": round(g("WS_RL"), 1),
            "wheelRR": round(g("WS_RR_Counter")),  # 速度+カウンタ混在の raw（要検証）
            "latAccel": 0.0,  # 推定元なし
            "longAccel": round(long_accel, 2),
        }


def build_raw_gauges(raw: dict, db) -> list:
    """デコード済みの全アナログ信号を {name,value,unit,min,max} のリストで返す（汎用ゲージ用）。

    パディング/カウンタ等は除外。値が来ている信号だけ列挙。
    """
    out = []
    for msg in db.messages:
        for sig in msg.signals:
            if any(s in sig.name for s in _SKIP_RAW):
                continue
            if sig.name not in raw:
                continue
            val = raw[sig.name]
            try:
                val = round(float(val), 2)
            except (TypeError, ValueError):
                continue
            out.append(
                {
                    "name": sig.name,
                    "value": val,
                    "unit": sig.unit or "",
                    "min": sig.minimum if sig.minimum is not None else 0,
                    "max": sig.maximum if sig.maximum is not None else 255,
                }
            )
    return out
