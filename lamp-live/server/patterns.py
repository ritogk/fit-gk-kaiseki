"""演出パターン。各パターンは位相時間 t(秒) から (右%, 左%) を返す。

t は「速さ」倍率を掛けて積算した時間なので、速さを変えても波が途切れない。
PERIOD は1周期の秒数で、タップテンポで速さを合わせるときの基準になる。
"""
import math
import random


def sine01(x):
    return 0.5 - 0.5 * math.cos(2 * math.pi * x)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def noise(t, seed):
    return (math.sin(t * 0.31 + seed) * 0.5 + math.sin(t * 0.73 + seed * 2.1) * 0.3
            + math.sin(t * 1.37 + seed * 3.7) * 0.2)


class Pattern:
    key = ""
    label = ""
    period = 1.0

    def reset(self):
        pass

    def __call__(self, t, dt):
        raise NotImplementedError


class Breathe(Pattern):
    key, label, period = "breathe", "呼吸", 4.0

    def __call__(self, t, dt):
        v = 100 * sine01(t / self.period)
        return v, v


class Alt(Pattern):
    key, label, period = "alt", "左右交互", 3.0

    def __call__(self, t, dt):
        v = sine01(t / self.period)
        return 100 * v, 100 * (1 - v)


class Wave(Pattern):
    key, label, period = "wave", "ウェーブ", 2.5

    def __call__(self, t, dt):
        p = t / self.period
        return 100 * sine01(p), 100 * sine01(p - 0.25)


class FastWave(Pattern):
    key, label, period = "fastwave", "高速ウェーブ", 0.9

    def __call__(self, t, dt):
        p = t / self.period
        return 100 * sine01(p) ** 1.5, 100 * sine01(p - 0.3) ** 1.5


class Heartbeat(Pattern):
    key, label, period = "heartbeat", "鼓動", 1.2

    def __call__(self, t, dt):
        p = t % self.period
        v = 0.0
        for c, w in ((0.0, 0.08), (0.25, 0.10)):
            v = max(v, math.exp(-((p - c - 0.08) ** 2) / (2 * w * w / 4)))
        return 100 * v, 100 * v


class PingPong(Pattern):
    key, label, period = "pingpong", "ピンポン", 1.6

    def __call__(self, t, dt):
        p = (t % self.period) / self.period
        x = 1 - abs(2 * p - 1)
        return 100 * (1 - x) ** 2, 100 * x ** 2


class Strobe(Pattern):
    key, label, period = "strobe", "ストロボ", 0.25

    def __call__(self, t, dt):
        v = 100.0 if (t % self.period) < self.period * 0.3 else 0.0
        return v, v


class Flicker(Pattern):
    key, label, period = "flicker", "ゆらぎ", 1.0

    def reset(self):
        self.v = {"r": 60.0, "l": 60.0}

    def __call__(self, t, dt):
        k = min(1.0, dt * 10)
        for s in self.v:
            self.v[s] += (random.uniform(35, 95) - self.v[s]) * k
        return self.v["r"], self.v["l"]


class Sparkle(Pattern):
    key, label, period = "sparkle", "きらめき", 1.0

    def reset(self):
        self.v = {"r": 0.0, "l": 0.0}

    def __call__(self, t, dt):
        for s in self.v:
            self.v[s] *= 0.88 ** (dt * 40)
            if random.random() < 1.6 * dt:
                self.v[s] = 100.0
        return self.v["r"], self.v["l"]


class Creature(Pattern):
    """左右を両目に見立てた生き物。不規則な呼吸、まばたき、きょろきょろ、ため息。"""
    key, label, period = "creature", "いきもの", 4.5

    def reset(self):
        self.phase = 0.0
        self.per = 4.5
        self.deep = 1.0
        self.blink_at = 2.0
        self.blink_t = None
        self.blink_double = False
        self.gaze = 0.0
        self.gaze_target = 0.0
        self.gaze_at = 4.0

    def breath(self):
        p = self.phase
        if p < 0.35:
            return ease(p / 0.35)
        if p < 0.85:
            return 1 - ease((p - 0.35) / 0.5)
        return 0.0

    def __call__(self, t, dt):
        self.phase += dt / self.per
        if self.phase >= 1:
            self.phase -= 1
            sigh = random.random() < 0.15
            self.per = random.uniform(6.5, 8.0) if sigh else random.uniform(3.5, 5.0)
            self.deep = 1.35 if sigh else random.uniform(0.8, 1.05)
        lo = 22 + 6 * noise(t, 1.0)
        v = lo + (55 + 8 * noise(t, 5.0)) * self.deep * self.breath()

        if self.blink_t is None and t >= self.blink_at:
            self.blink_t = t
            self.blink_double = random.random() < 0.25
        k = 1.0
        if self.blink_t is not None:
            bt = t - self.blink_t
            if bt < (0.55 if self.blink_double else 0.3):
                c = bt % 0.3
                k = 1 - (ease(c / 0.07) if c < 0.07 else 1 - ease((c - 0.07) / 0.2))
                k = 0.05 + 0.95 * k
            else:
                self.blink_t = None
                self.blink_at = t + random.uniform(2.5, 7.0)

        if t >= self.gaze_at:
            if self.gaze_target != 0:
                self.gaze_target = 0.0
                self.gaze_at = t + random.uniform(3.0, 8.0)
            else:
                self.gaze_target = random.choice((-1, 1)) * random.uniform(0.5, 1.0)
                self.gaze_at = t + random.uniform(1.0, 2.5)
        self.gaze += (self.gaze_target - self.gaze) * min(1.0, dt * 4)

        r = v * k * (1 + 0.45 * self.gaze) + 2 * noise(t * 3, 11.0)
        l = v * k * (1 - 0.45 * self.gaze) + 2 * noise(t * 3, 23.0)
        return r, l


def xy_to_lr(x, y):
    """XYパッドと同じ変換。x=0左〜1右の配分, y=0暗〜1明。"""
    v = 100 * y
    return v * min(1.0, 2 * x), v * min(1.0, 2 * (1 - x))  # (右, 左)


class Orbit(Pattern):
    """XYパッドの端いっぱいの楕円を、点が自動でぐるぐる回る。"""
    key, label, period = "orbit", "楕円ループ", 2.0

    def reset(self):
        self.xy = (0.5, 0.5)

    def __call__(self, t, dt):
        a = 2 * math.pi * t / self.period
        x, y = 0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)
        self.xy = (x, y)
        return xy_to_lr(x, y)


ALL = [Breathe(), Alt(), Wave(), FastWave(), Heartbeat(), PingPong(),
       Strobe(), Flicker(), Sparkle(), Creature(), Orbit()]
BY_KEY = {p.key: p for p in ALL}
for _p in ALL:
    _p.reset()
