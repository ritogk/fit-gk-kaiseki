"""照明エンジン。画面からの操作を状態に反映し、毎フレーム左右の明るさを決める。

出力の決め方(上から優先):
  1. 全消灯(blackout)中は 0
  2. フラッシュ(bump)を押している間は 100
  3. それ以外は max(パターン × パターン量, 手動フェーダー) × マスター
"""
import time

from . import patterns


class Engine:
    def __init__(self):
        self.pattern = None        # 再生中のパターン key(None=停止)
        self.pattern_level = 100.0
        self.speed = 1.0           # 速さ倍率
        self.master = 100.0
        self.pwm_freq = 1000       # ESP の PWM 周波数(Hz)。ファームの起動時の値と同じ
        self.gamma = 2.2           # ESP のガンマ。1.0 で画面の%がそのまま出力の割合になる
        self.manual_r = 0.0
        self.manual_l = 0.0
        self.bump = False
        self.blackout = False
        self.out_r = 0.0
        self.out_l = 0.0
        self._pt = 0.0             # 速さを掛けて積算したパターン時間
        self._taps = []

    # ---- 画面からの操作 ----
    def handle(self, m):
        t = m.get("t")
        if t == "pattern":
            key = m.get("name")
            if key in patterns.BY_KEY:
                if key != self.pattern:
                    patterns.BY_KEY[key].reset()
                    self._pt = 0.0
                self.pattern = key
            else:
                self.pattern = None
        elif t == "manual":
            if "r" in m:
                self.manual_r = _clip(m["r"])
            if "l" in m:
                self.manual_l = _clip(m["l"])
        elif t == "set":
            k, v = m.get("key"), m.get("value")
            if k == "master":
                self.master = _clip(v)
            elif k == "pattern_level":
                self.pattern_level = _clip(v)
            elif k == "speed":
                self.speed = max(0.1, min(8.0, float(v)))
            elif k == "pwm_freq":
                self.pwm_freq = int(max(50, min(19000, float(v))))
            elif k == "gamma":
                self.gamma = round(max(0.3, min(3.0, float(v))), 2)
        elif t == "bump":
            self.bump = bool(m.get("on"))
        elif t == "blackout":
            self.blackout = bool(m.get("on"))
        elif t == "tap":
            self._tap()
        elif t == "panic":  # すべて止めて消す
            self.pattern = None
            self.manual_r = self.manual_l = 0.0
            self.bump = False
            self.blackout = False

    def _tap(self):
        """タップの間隔を、再生中パターンの1周期に合わせる。"""
        now = time.monotonic()
        self._taps = [x for x in self._taps if now - x < 2.5] + [now]
        if len(self._taps) >= 2 and self.pattern:
            iv = (self._taps[-1] - self._taps[0]) / (len(self._taps) - 1)
            self.speed = max(0.1, min(8.0, patterns.BY_KEY[self.pattern].period / iv))

    # ---- 毎フレーム ----
    def tick(self, dt):
        pr = pl = 0.0
        if self.pattern:
            self._pt += dt * self.speed
            pr, pl = patterns.BY_KEY[self.pattern](self._pt, dt * self.speed)
            k = self.pattern_level / 100.0
            pr, pl = pr * k, pl * k
        r = max(pr, self.manual_r)
        l = max(pl, self.manual_l)
        if self.bump:
            r = l = 100.0
        m = self.master / 100.0
        r, l = _clip(r * m), _clip(l * m)
        if self.blackout:
            r = l = 0.0
        self.out_r, self.out_l = r, l
        return r, l

    def snapshot(self):
        return {
            "pattern": self.pattern,
            "pattern_level": self.pattern_level,
            "speed": round(self.speed, 3),
            "master": self.master,
            "pwm_freq": self.pwm_freq,
            "gamma": self.gamma,
            "manual_r": self.manual_r,
            "manual_l": self.manual_l,
            "bump": self.bump,
            "blackout": self.blackout,
            "out": {"r": round(self.out_r, 1), "l": round(self.out_l, 1)},
            # XYパッド上を動くパターン(楕円ループ)の現在位置。画面の点を動かすのに使う
            "xy": getattr(patterns.BY_KEY.get(self.pattern), "xy", None) if self.pattern else None,
        }


def _clip(v):
    try:
        return max(0.0, min(100.0, float(v)))
    except (TypeError, ValueError):
        return 0.0
