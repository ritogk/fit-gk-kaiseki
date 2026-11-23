#!/usr/bin/env python3
"""GK前期 純正LEDロービーム駆動ユニットの信号線を記録・解析する。

ファームは firmware/led_sig_rec。

記録(ESP32 をつないだ状態で):
  .venv/bin/python micro-control/tools/ledsig.py rec lo_on 1000
  → micro-control/logs/ledsig/<日時>_lo_on.txt に保存し、続けて解析結果を表示
  ラベル例: off / pos(ポジション) / lo_on / hi_on / hi_flash(パッシング)

解析だけ(保存済みファイルを指定):
  python3 micro-control/tools/ledsig.py analyze micro-control/logs/ledsig/*.txt

簡易オシロ(ファーム led_sig_scope。電圧も分かる。2系統 A=GPIO1 / B=GPIO2):
  .venv/bin/python micro-control/tools/ledsig.py scope lo_on 200

判定の種類:
  CONST   エッジなし。ずっと High か Low(ON/OFF を電圧レベルで伝えている)
  PWM     周期がそろっている。周波数とデューティを出す
  SERIAL  区間の長さが最小単位の整数倍にそろう。通信(LIN/UART 等)の可能性。ボーレート候補を出す
  IRREG   上のどれにも当てはまらない
判定は統計からの推定なので、最終判断は区間の分布(hist)も見て行う。
"""
import datetime as dt
import os
import re
import statistics as st
import sys
import time

PORT = os.environ.get("LEDSIG_PORT", "/dev/cu.usbmodem5C630050101")
LOGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "ledsig")
STD_BAUDS = [1200, 2400, 4800, 9600, 10417, 19200, 20000, 38400, 57600, 115200]


# ── 記録 ──────────────────────────────────────────
def rec(label, ms):
    import serial  # pyserial(リポジトリの .venv に入っている)

    with serial.Serial(PORT, 115200, timeout=0.2) as s:
        time.sleep(2.0)  # ポートを開くと ESP32 がリセットされるので起動を待つ
        s.reset_input_buffer()
        s.write(f"c {label} {ms}\n".encode())
        lines, started, deadline = [], False, time.time() + ms / 1000 + 30
        while time.time() < deadline:
            ln = s.readline().decode(errors="replace").strip()
            if not ln:
                continue
            if ln.startswith("#CAP"):
                started = True
            if started:
                lines.append(ln)
            if ln == "#END":
                break
        else:
            sys.exit("タイムアウト: #END が来ませんでした(ポートやファームを確認)")
    os.makedirs(LOGDIR, exist_ok=True)
    path = os.path.join(LOGDIR, f"{dt.datetime.now():%Y%m%d-%H%M%S}_{label}.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"保存: {os.path.normpath(path)}")
    return path


# ── 読み込み ───────────────────────────────────────
def load(path):
    """ファイル内の各 #CAP ブロックを {label, meta, ch: {Y: [(lvl, us, partial)], X: [...]}} にする。"""
    caps, cur = [], None
    for ln in open(path):
        ln = ln.strip()
        if ln.startswith("#CAP"):
            meta = dict(re.findall(r"(\w+)=(\S+)", ln))
            cur = {"label": meta.get("label", "?"), "meta": meta, "ch": {"Y": [], "X": []}}
        elif ln == "#END" and cur:
            caps.append(cur)
            cur = None
        elif cur and ln:
            m = re.match(r"(\*?)([YX]) ([HL]) (\d+)$", ln)
            if m:
                cur["ch"][m[2]].append((m[3], int(m[4]), bool(m[1])))
    return caps


# ── 解析 ──────────────────────────────────────────
def cv(xs):
    return st.pstdev(xs) / st.mean(xs) if len(xs) > 1 and st.mean(xs) else 0.0


def hist(widths, nbins=8):
    """区間の長さを、近い値どうしでまとめた上位を返す(±10% を同じ山とみなす)。"""
    groups = []
    for w in sorted(widths):
        if groups and w <= groups[-1][0] * 1.1:
            groups[-1][1].append(w)
        else:
            groups.append((w, [w]))
    groups.sort(key=lambda g: -len(g[1]))
    return [(round(st.median(g[1])), len(g[1])) for g in groups[:nbins]]


def serial_guess(widths):
    """最小の山を1ビットとみなし、全区間が整数倍にそろうかを見る。"""
    if len(widths) < 10:
        return None
    small = sorted(widths)[: max(3, len(widths) // 10)]
    bit = st.median(small)
    if bit <= 0:
        return None
    for _ in range(3):  # 整数倍への当てはめで1ビット長を補正する
        use = [w for w in widths if w / bit < 12]
        bit = sum(use) / sum(max(1, round(w / bit)) for w in use)
    errs = [abs(w / bit - round(w / bit)) for w in widths if w / bit < 12]
    if len(errs) < len(widths) * 0.8:
        return None  # 長い区間(フレーム間の休み)が多すぎる
    if st.mean(errs) > 0.12:
        return None
    baud = 1e6 / bit
    near = min(STD_BAUDS, key=lambda b: abs(b - baud))
    return bit, baud, near if abs(near - baud) / near < 0.05 else None


def analyze_ch(segs, start_level):
    full = [(lvl, us) for lvl, us, partial in segs if not partial]
    total = sum(us for _, us, _ in segs)
    if len(segs) <= 1:
        lvl = segs[0][0] if segs else ("H" if start_level == "1" else "L")
        return f"CONST  ずっと {lvl}({total/1000:.0f}ms のあいだエッジなし)"
    hs = [us for lvl, us in full if lvl == "H"]
    ls = [us for lvl, us in full if lvl == "L"]
    out = [f"edges={len(segs)-1}  H区間={len(hs)}  L区間={len(ls)}"]
    # 周期 = 隣り合う H+L
    periods, duties = [], []
    for (l1, a), (l2, b) in zip(full, full[1:]):
        if l1 == "H" and l2 == "L":
            periods.append(a + b)
            duties.append(a / (a + b))
    if len(periods) >= 3 and cv(periods) < 0.05:
        f = 1e6 / st.mean(periods)
        d = st.mean(duties) * 100
        dr = (min(duties) * 100, max(duties) * 100)
        kind = "PWM    " + (f"{f:.1f}Hz  周期{st.mean(periods):.0f}µs  デューティ{d:.1f}%"
                            f"(範囲 {dr[0]:.1f}〜{dr[1]:.1f}%)")
        if dr[1] - dr[0] > 3:
            kind += "  ※デューティが動いている"
        out.insert(0, kind)
    else:
        sg = serial_guess(hs + ls)
        if sg:
            bit, baud, near = sg
            nm = f"  標準値なら {near}bps" + ("(LIN)" if near in (10417, 19200, 20000) else "") if near else ""
            out.insert(0, f"SERIAL 1ビット≒{bit:.0f}µs → 約{baud:.0f}bps{nm}")
        else:
            out.insert(0, "IRREG  周期も整数倍もそろわない(下の分布を見る)")
    if hs:
        out.append(f"H: 最小{min(hs)} 中央{st.median(hs):.0f} 最大{max(hs)} µs")
    if ls:
        out.append(f"L: 最小{min(ls)} 中央{st.median(ls):.0f} 最大{max(ls)} µs")
    out.append("H分布(µs×回): " + ", ".join(f"{w}×{n}" for w, n in hist(hs)))
    out.append("L分布(µs×回): " + ", ".join(f"{w}×{n}" for w, n in hist(ls)))
    head = " ".join(f"{lvl}{us}" for lvl, us, _ in segs[:16])
    out.append("先頭16区間: " + head)
    return "\n         ".join(out)


def analyze(paths):
    for p in paths:
        for c in load(p):
            m = c["meta"]
            print(f"\n■ {c['label']}  ({os.path.basename(p)}, {m.get('ms')}ms)")
            if m.get("overflow", "0") != "0":
                print(f"  !! overflow={m['overflow']}: エッジが多すぎて取りこぼし。ms を短くする")
            for ch in ("Y", "X"):
                print(f"  {ch}: " + analyze_ch(c["ch"][ch], m.get(f"{ch}0", "0")))


# ── 簡易オシロ(led_sig_scope) ─────────────────────────
DIV = float(os.environ.get("LEDSIG_DIV", "5.545"))  # (上+下)÷下。100k/22k の既定値


def scope_rec(label, ms):
    import serial

    with serial.Serial(PORT, 921600, timeout=0.5) as s:
        time.sleep(2.0)
        s.reset_input_buffer()
        s.write(f"s {label} {ms}\n".encode())
        lines, started, deadline = [], False, time.time() + 30
        while time.time() < deadline:
            ln = s.readline().decode(errors="replace").strip()
            if ln.startswith("#SCOPE"):
                started = True
            if started and ln:
                lines.append(ln)
            if ln == "#END":
                break
        else:
            sys.exit("タイムアウト: #END が来ませんでした(ポートやファームを確認)")
    os.makedirs(LOGDIR, exist_ok=True)
    path = os.path.join(LOGDIR, f"{dt.datetime.now():%Y%m%d-%H%M%S}_{label}.scope.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"保存: {os.path.normpath(path)}")
    return path


def scope_load(path):
    meta, ch = {}, {"A": [], "B": []}
    for ln in open(path):
        ln = ln.strip()
        if ln.startswith("#SCOPE"):
            meta = dict(re.findall(r"(\w+)=(\S+)", ln))
        elif ln[:2] in ("A ", "B "):
            h = ln[2:]
            ch[ln[0]] += [int(h[i:i + 3], 16) / 1000 * DIV for i in range(0, len(h) - 2, 3)]
    return meta, ch


def ascii_wave(v, lo, hi, width=100, rows=6):
    """先頭から width 列ぶんの波形を文字で描く(1列=複数点の最小〜最大)。"""
    step = max(1, len(v) // width)
    cols = [(min(v[i:i + step]), max(v[i:i + step])) for i in range(0, step * width, step) if v[i:i + step]]
    span = max(hi - lo, 0.1)
    out = []
    for r in range(rows - 1, -1, -1):
        y0, y1 = lo + span * r / rows, lo + span * (r + 1) / rows
        out.append("".join("█" if a < y1 and b >= y0 else " " for a, b in cols))
    return out, step


def scope_analyze(paths):
    for p in paths:
        meta, ch = scope_load(p)
        n, us = int(meta.get("n", 0)), int(meta.get("us", 1))
        if not n:
            print(f"\n■ {os.path.basename(p)}: データなし")
            continue
        dt_us = us / n
        print(f"\n■ {meta.get('label')}  ({os.path.basename(p)})  {us/1000:.0f}ms  1点={dt_us:.1f}µs  倍率×{DIV}")
        for name in ("A", "B"):
            v = ch[name]
            sv = sorted(v)
            lo, hi = sv[len(sv) // 100], sv[-1 - len(sv) // 100]
            avg = sum(v) / len(v)
            head = f"  {name}: 最小{lo:.2f}V  最大{hi:.2f}V  平均{avg:.2f}V"
            if hi - lo < 0.6:
                print(head + f"\n     CONST  ほぼ一定({avg:.1f}V)")
                continue
            th, hys = (lo + hi) / 2, (hi - lo) * 0.15
            segs, lvl, start = [], v[0] > th, 0
            for i, x in enumerate(v):
                if (lvl and x < th - hys) or (not lvl and x > th + hys):
                    segs.append(("H" if lvl else "L", round((i - start) * dt_us), not segs))
                    lvl, start = not lvl, i
            segs.append(("H" if lvl else "L", round((len(v) - start) * dt_us), True))
            print(head + f"  (Low≒{lo:.1f}V / High≒{hi:.1f}V)")
            print("     " + analyze_ch(segs, "1" if v[0] > th else "0"))
            wave, step = ascii_wave(v, lo, hi)
            print(f"     波形(先頭 {step*100*dt_us/1000:.1f}ms):")
            for i, row in enumerate(wave):
                print(f"     {hi:5.1f}V|" if i == 0 else (f"     {lo:5.1f}V|" if i == len(wave) - 1 else "           |"), row, sep="")
        if any(sorted(ch[c])[-1 - n // 100] - sorted(ch[c])[n // 100] >= 0.6 and dt_us > 20 for c in "AB"):
            print("  ※ 1点が約25µsなので、100µsより短い区間の長さは目安。細かい通信はロジアナで確認する")


def main():
    a = sys.argv[1:]
    if a and a[0] == "scope":
        # scope <label> [ms] で記録、scope <file...> で保存済みを再解析
        if len(a) >= 2 and os.path.exists(a[1]):
            scope_analyze(a[1:])
        elif len(a) >= 2:
            scope_analyze([scope_rec(a[1], int(a[2]) if len(a) > 2 else 200)])
        else:
            sys.exit("使い方: ledsig.py scope <label> [ms]  /  ledsig.py scope <file...>")
        return
    if not a or a[0] not in ("rec", "analyze"):
        sys.exit(__doc__)
    if a[0] == "rec":
        if len(a) < 2:
            sys.exit("使い方: ledsig.py rec <label> [ms]")
        path = rec(a[1], int(a[2]) if len(a) > 2 else 1000)
        analyze([path])
    else:
        analyze(a[1:])


if __name__ == "__main__":
    main()
