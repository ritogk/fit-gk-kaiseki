#!/usr/bin/env python3
"""ハイビーム左右のライト演出を Mac から流す。

使い方:
  python3 hibeam_show.py                # 全パターンを順番に再生
  python3 hibeam_show.py wave alt 15    # 指定パターンを各15秒
パターン: breathe alt wave heartbeat pingpong flicker sparkle
終了時(Ctrl+C を含む)は必ず全消灯して fade を 300ms に戻す。
"""
import math
import os
import random
import select
import sys
import termios
import time

PORT = os.environ.get("HIBEAM_PORT", "/dev/cu.usbmodem5C630050101")
HZ = 40  # 送信レート


class Lamp:
    def __init__(self, port):
        self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        a = termios.tcgetattr(self.fd)
        a[0] = 0; a[1] = 0; a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL; a[3] = 0
        a[4] = a[5] = termios.B115200
        termios.tcsetattr(self.fd, termios.TCSANOW, a)

    def send(self, cmd):
        os.write(self.fd, (cmd + "\n").encode())
        self.drain()

    def drain(self):
        while select.select([self.fd], [], [], 0)[0]:
            try:
                if not os.read(self.fd, 4096):
                    break
            except BlockingIOError:
                break

    def set(self, r, l):
        r = max(0.0, min(100.0, r)); l = max(0.0, min(100.0, l))
        self.send(f"r{r:.1f}")
        self.send(f"l{l:.1f}")

    def close(self):
        self.send("t300")
        self.send("0")
        os.close(self.fd)


def sine01(x):
    return 0.5 - 0.5 * math.cos(2 * math.pi * x)


# 各パターンは t(秒) -> (右%, 左%) を返す
def breathe(t):  # 左右そろって、ふわっと呼吸
    v = 100 * sine01(t / 4.0)
    return v, v


def alt(t):  # 左右が逆位相の波(片方が明るいと片方が暗い)
    v = sine01(t / 3.0)
    return 100 * v, 100 * (1 - v)


def wave(t):  # 右から左へ波が流れる(位相を1/4ずらす)
    return 100 * sine01(t / 2.5), 100 * sine01(t / 2.5 - 0.25)


FAST_PERIOD = float(os.environ.get("HIBEAM_PERIOD", "0.9"))  # 秒/往復


def fastwave(t):  # 高速で、ふわっと右→左へ流れる波を繰り返す
    p = t / FAST_PERIOD
    return 100 * sine01(p) ** 1.5, 100 * sine01(p - 0.3) ** 1.5


def heartbeat(t):  # ドクン、ドクン
    p = (t % 1.2)
    v = 0
    for c, w in ((0.0, 0.08), (0.25, 0.10)):
        v = max(v, math.exp(-((p - c - 0.08) ** 2) / (2 * w * w / 4)))
    return 100 * v, 100 * v


def pingpong(t):  # 光が左右を行き来する
    p = (t % 1.6) / 1.6
    x = 1 - abs(2 * p - 1)  # 0→1→0
    return 100 * (1 - x) ** 2, 100 * x ** 2


_fl = {"r": 60.0, "l": 60.0}


def flicker(t):  # ろうそく風のゆらぎ
    for k in _fl:
        _fl[k] += (random.uniform(35, 95) - _fl[k]) * 0.25
    return _fl["r"], _fl["l"]


_sp = {"r": 0.0, "l": 0.0}


def sparkle(t):  # ランダムに左右がパッと光って余韻で消える
    for k in _sp:
        _sp[k] *= 0.88
        if random.random() < 0.04:
            _sp[k] = 100.0
    return _sp["r"], _sp["l"]


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _noise(t, seed):  # 周期のそろわない正弦を重ねた、ゆっくりしたゆらぎ(-1..1)
    return (math.sin(t * 0.31 + seed) * 0.5 + math.sin(t * 0.73 + seed * 2.1) * 0.3
            + math.sin(t * 1.37 + seed * 3.7) * 0.2)


class Creature:
    """左右を「目」に見立てた生き物。不規則な呼吸、まばたき、きょろきょろ、ため息。"""

    def __init__(self):
        self.last = None
        self.phase = 0.0          # 呼吸の位相 0..1
        self.period = 4.5
        self.deep = 1.0           # 今回の呼吸の深さ(ため息で大きくなる)
        self.blink_at = 2.0       # 次のまばたき時刻
        self.blink_t = None
        self.blink_double = False
        self.gaze = 0.0           # -1=左を見る, +1=右を見る
        self.gaze_target = 0.0
        self.gaze_at = 4.0

    def breath(self):  # 吸う(短い)→吐く(長い)→少し止まる
        p = self.phase
        if p < 0.35:
            return _ease(p / 0.35)
        if p < 0.85:
            return 1 - _ease((p - 0.35) / 0.5)
        return 0.0

    def __call__(self, t):
        dt = 0 if self.last is None else t - self.last
        self.last = t

        # 呼吸: 周期を毎回少し変え、たまに深いため息
        self.phase += dt / self.period
        if self.phase >= 1:
            self.phase -= 1
            sigh = random.random() < 0.15
            self.period = random.uniform(6.5, 8.0) if sigh else random.uniform(3.5, 5.0)
            self.deep = 1.35 if sigh else random.uniform(0.8, 1.05)
        lo = 22 + 6 * _noise(t, 1.0)
        v = lo + (55 + 8 * _noise(t, 5.0)) * self.deep * self.breath()

        # まばたき: 不規則な間隔、ときどき2回続けて
        if self.blink_t is None and t >= self.blink_at:
            self.blink_t = t
            self.blink_double = random.random() < 0.25
        k = 1.0
        if self.blink_t is not None:
            bt = t - self.blink_t
            dur = 0.55 if self.blink_double else 0.3
            if bt < dur:
                c = bt % 0.3
                k = 1 - (_ease(c / 0.07) if c < 0.07 else 1 - _ease((c - 0.07) / 0.2))
                k = 0.05 + 0.95 * k
            else:
                self.blink_t = None
                self.blink_at = t + random.uniform(2.5, 7.0)

        # 視線: ときどき左右どちらかを見て、しばらくして戻る
        if t >= self.gaze_at:
            self.gaze_target = 0.0 if self.gaze_target != 0 else random.choice((-1, 1)) * random.uniform(0.5, 1.0)
            self.gaze_at = t + (random.uniform(1.0, 2.5) if self.gaze_target else random.uniform(3.0, 8.0))
        self.gaze += (self.gaze_target - self.gaze) * min(1.0, dt * 4)

        r = v * k * (1 + 0.45 * self.gaze) + 2 * _noise(t * 3, 11.0)
        l = v * k * (1 - 0.45 * self.gaze) + 2 * _noise(t * 3, 23.0)
        return r, l


def creature(t, _c=[None]):
    if _c[0] is None or t < (_c[0].last or 0):
        _c[0] = Creature()
    return _c[0](t)


PATTERNS = {f.__name__: f for f in (breathe, alt, wave, fastwave, heartbeat, pingpong, flicker, sparkle, creature)}


def run(lamp, name, sec):
    print(f"▶ {name} ({sec}s)", flush=True)
    f = PATTERNS[name]
    t0 = time.time()
    while (t := time.time() - t0) < sec:
        r, l = f(t)
        lamp.set(r, l)
        time.sleep(1 / HZ)


def main():
    args = sys.argv[1:]
    sec = 12.0
    if args and args[-1].replace(".", "").isdigit():
        sec = float(args.pop())
    names = args or list(PATTERNS)
    for n in names:
        if n not in PATTERNS:
            sys.exit(f"未知のパターン: {n} / 使えるもの: {' '.join(PATTERNS)}")
    lamp = Lamp(PORT)
    try:
        lamp.send("t40")  # 送信間隔の段差をならす程度の短いフェード
        lamp.set(0, 0)
        time.sleep(0.5)
        for n in names:
            run(lamp, n, sec)
    except KeyboardInterrupt:
        pass
    finally:
        lamp.close()
        print("■ 全消灯", flush=True)


if __name__ == "__main__":
    main()
