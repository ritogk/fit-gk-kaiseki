#!/usr/bin/env python3
"""実車校正ヘルパ。can0 を一定秒数録って、ID×バイトごとの変動を測る。

使い方:
  rec  : 録画して「動いたバイト」を表示＋JSON保存
         .venv/bin/python can-live/calib.py rec <秒> <out.json>
  diff : ベースライン(無操作)に対し、操作中に「新たに動いた」バイトだけ抽出
         .venv/bin/python can-live/calib.py diff <base.json> <action.json>

socketcan は複数ソケットで同時購読できるので can-live 本体と並行に動かせる。
"""
import collections
import json
import sys
import time

import can

CHANNEL = "can0"


def record(secs: float) -> dict:
    bus = can.interface.Bus(channel=CHANNEL, interface="socketcan")
    seen: dict[int, list[set]] = {}
    dlc: dict[int, int] = {}
    cnt: collections.Counter = collections.Counter()
    last: dict[int, list[int]] = {}
    t0 = time.time()
    aborted = False
    try:
        while time.time() - t0 < secs:
            try:
                m = bus.recv(timeout=1.0)
            except can.CanError as e:
                # USB 再列挙等で can0 が落ちた。取れた分で打ち切る。
                print(f"[rec] can0 が途中で切れました ({e}) — 取得済み分で続行")
                aborted = True
                break
            if m is None:
                continue
            i = m.arbitration_id
            d = list(m.data)
            dlc[i] = m.dlc
            cnt[i] += 1
            last[i] = d
            if i not in seen:
                seen[i] = [set() for _ in range(8)]
            for k, b in enumerate(d):
                seen[i][k].add(b)
    finally:
        try:
            bus.shutdown()
        except Exception:
            pass
    if aborted and not seen:
        print("[rec] 1フレームも取れませんでした（can0 が up していない可能性）")

    out: dict[str, dict] = {}
    for i, arr in seen.items():
        binfo = {}
        for k, s in enumerate(arr):
            if not s:
                continue
            binfo[str(k)] = {"n": len(s), "min": min(s), "max": max(s)}
        out[str(i)] = {
            "dlc": dlc[i],
            "count": cnt[i],
            "last": last.get(i, []),
            "bytes": binfo,
        }
    return out


def moving(rec: dict, min_distinct: int = 2) -> set:
    """distinct >= min_distinct のバイト集合 (id, byte)。"""
    a = set()
    for i, info in rec.items():
        for k, bi in info["bytes"].items():
            if bi["n"] >= min_distinct:
                a.add((int(i), int(k)))
    return a


def hexid(i: int) -> str:
    return f"0x{i:03X}"


def print_moving(rec: dict, only: set | None = None) -> None:
    rows = []
    for i, info in rec.items():
        ii = int(i)
        for k, bi in info["bytes"].items():
            kk = int(k)
            if only is not None and (ii, kk) not in only:
                continue
            if bi["n"] < 2:
                continue
            rows.append((ii, kk, bi["n"], bi["min"], bi["max"], info["count"]))
    rows.sort(key=lambda r: (-r[2], r[0], r[1]))
    if not rows:
        print("  (動いたバイトなし)")
        return
    print(f"  {'ID':>6} {'byte':>4} {'distinct':>8} {'min':>4} {'max':>4} {'frames':>7}")
    for ii, kk, n, mn, mx, c in rows:
        print(f"  {hexid(ii):>6} B{kk:<3} {n:>8} {mn:>4} {mx:>4} {c:>7}")


def cmd_rec(secs: float, out: str | None) -> None:
    print(f"[rec] {secs}s 録画中… (この間に対象操作を続けてください)")
    rec = record(secs)
    print(f"[rec] {len(rec)} IDs 受信。動いたバイト:")
    print_moving(rec)
    if out:
        with open(out, "w") as f:
            json.dump(rec, f)
        print(f"[rec] saved -> {out}")


def cmd_diff(base_path: str, act_path: str) -> None:
    with open(base_path) as f:
        base = json.load(f)
    with open(act_path) as f:
        act = json.load(f)
    b = moving(base)
    a = moving(act)
    new = a - b  # ベースでは動かず、操作中に動いたバイト＝対象信号の候補
    print(f"[diff] baseline動き={len(b)} / 操作中動き={len(a)} / 新規={len(new)}")
    print("[diff] ★操作で新たに動いたバイト（=その操作の信号候補）:")
    print_moving(act, only=new)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "rec":
        secs = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
        out = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_rec(secs, out)
    elif cmd == "diff":
        cmd_diff(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
