#!/usr/bin/env python3
"""走行中アナログ信号 自動探索。

can0 を一定秒数録り、各ID×(8bit/16bitBE)チャンネルについて:
- 連続変化の豊かさ（std, レンジ, distinct）
- カウンタらしさ（隣接サンプル差が +1 主体か）を除外
- 参照信号との相関:
    steering = 0x156 signed16 B0-1
    speedproxy = 0x1D0 u16 B0-1 (WheelSpeeds WS_FL 相当)
を計算し、「アナログ候補」をランク表示する。停車中は speedproxy≈0。

使い方: .venv/bin/python can-live/explore.py <秒>
"""
import math
import sys
import time

import can

CHANNEL = "can0"
DT = 0.05  # タイムライン解像度(20Hz)


def capture(secs: float):
    bus = can.interface.Bus(channel=CHANNEL, interface="socketcan")
    # id -> list[(t, tuple(bytes))]
    series: dict[int, list] = {}
    dlc: dict[int, int] = {}
    t0 = time.time()
    try:
        while time.time() - t0 < secs:
            try:
                m = bus.recv(timeout=1.0)
            except can.CanError as e:
                print(f"[explore] can0 drop ({e}) — 取得分で続行")
                break
            if m is None:
                continue
            i = m.arbitration_id
            if i > 0x7FF:  # 拡張ID(UDS等)は除外
                continue
            series.setdefault(i, []).append((m.timestamp, tuple(m.data)))
            dlc[i] = m.dlc
    finally:
        try:
            bus.shutdown()
        except Exception:
            pass
    return series, dlc, t0


def resample(samples, t0, t1, dt, getter):
    """(t,data)列を [t0,t1] の dt 格子に forward-fill して値列を返す。"""
    out = []
    j = 0
    cur = None
    n = len(samples)
    t = t0
    while t <= t1:
        while j < n and samples[j][0] <= t:
            v = getter(samples[j][1])
            if v is not None:
                cur = v
            j += 1
        out.append(cur)
        t += dt
    return out


def u8(data, k):
    return data[k] if k < len(data) else None


def u16(data, k):
    if k + 1 < len(data):
        return (data[k] << 8) | data[k + 1]
    return None


def s16(data, k):
    v = u16(data, k)
    if v is None:
        return None
    return v - 65536 if v >= 32768 else v


def stats(vals):
    xs = [v for v in vals if v is not None]
    if len(xs) < 5:
        return None
    n = len(xs)
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / n
    std = math.sqrt(var)
    rng = max(xs) - min(xs)
    distinct = len(set(xs))
    # カウンタらしさ: 隣接差が +1（範囲内）主体か
    deltas = [b - a for a, b in zip(xs, xs[1:])]
    plus1 = sum(1 for d in deltas if d == 1)
    counter_score = plus1 / len(deltas) if deltas else 0.0
    return {"n": n, "mean": mean, "std": std, "rng": rng, "distinct": distinct, "counter": counter_score, "xs": xs}


def corr(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 10:
        return 0.0
    xa = [p[0] for p in pairs]
    xb = [p[1] for p in pairs]
    ma = sum(xa) / len(xa)
    mb = sum(xb) / len(xb)
    num = sum((x - ma) * (y - mb) for x, y in zip(xa, xb))
    da = math.sqrt(sum((x - ma) ** 2 for x in xa))
    db = math.sqrt(sum((y - mb) ** 2 for y in xb))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    print(f"[explore] {secs}s 録画開始（運転継続でOK）…")
    series, dlc, t0 = capture(secs)
    if not series:
        print("[explore] フレーム取得できず（can0 down?）")
        return
    # タイムライン範囲
    allt = [s[0] for arr in series.values() for s in arr]
    tlo, thi = min(allt), max(allt)
    print(f"[explore] {len(series)} IDs, {sum(len(v) for v in series.values())} frames, {thi-tlo:.1f}s")

    # 参照信号
    steer = resample(series.get(0x156, []), tlo, thi, DT, lambda d: s16(d, 0))
    speed = resample(series.get(0x1D0, []), tlo, thi, DT, lambda d: u16(d, 0))
    has_speed = any(v for v in speed if v)
    # 横G/ヨー proxy: 操舵 × 速度（コーナリング力）
    lateral = [
        (st * sp) if (st is not None and sp is not None) else None
        for st, sp in zip(steer, speed)
    ]

    # 全チャンネル評価
    rows = []
    for i, arr in series.items():
        d = dlc.get(i, 8)
        for k in range(d):
            for kind, getter in (("u8", lambda dd, k=k: u8(dd, k)), ("s16", lambda dd, k=k: s16(dd, k))):
                if kind == "s16" and k + 1 >= d:
                    continue
                vals = resample(arr, tlo, thi, DT, getter)
                st = stats(vals)
                if st is None or st["std"] < 1.0:
                    continue
                if st["counter"] > 0.6:  # カウンタ除外
                    continue
                cs = corr(vals, steer)
                cv = corr(vals, speed) if has_speed else 0.0
                cl = corr(vals, lateral) if has_speed else 0.0
                rows.append((i, k, kind, st, cs, cv, cl))

    print(f"\n[explore] speedproxy(0x1D0) moving={has_speed}")

    # (A) 相関ランク: ステア/速度/横G に効く既知でない信号を上位表示
    print("\n=== 相関上位（|corr|が高い＝物理量に連動）===")
    corr_rows = sorted(rows, key=lambda r: -max(abs(r[4]), abs(r[5]), abs(r[6])))
    print(f"{'ID':>6} {'byte':>4} {'kind':>4} {'std':>8} {'dist':>5} {'cSteer':>7} {'cSpeed':>7} {'cLat':>7}")
    for i, k, kind, st, cs, cv, cl in corr_rows[:20]:
        print(f"0x{i:03X} B{k:<3} {kind:>4} {st['std']:8.1f} {st['distinct']:5d} {cs:7.2f} {cv:7.2f} {cl:7.2f}")

    # (B) アナログ豊かさランク
    print("\n=== アナログ豊かさ上位（std×log distinct, カウンタ除外済）===")
    rows.sort(key=lambda r: -(r[3]["std"] * math.log(max(2, r[3]["distinct"]))))
    print(f"{'ID':>6} {'byte':>4} {'kind':>4} {'std':>8} {'rng':>7} {'dist':>5} {'cSteer':>7} {'cSpeed':>7} {'cLat':>7}")
    for i, k, kind, st, cs, cv, cl in rows[:20]:
        print(f"0x{i:03X} B{k:<3} {kind:>4} {st['std']:8.1f} {st['rng']:7.0f} {st['distinct']:5d} {cs:7.2f} {cv:7.2f} {cl:7.2f}")


if __name__ == "__main__":
    main()
