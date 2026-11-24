#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BTS6143D(変換基板・下に5ピン)をユニバーサル基板に載せる部品配置図を生成する。
出力: bts-board.html
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
回路は bts-wiring.html(gen_bts_wiring.py)と同じ。
変換基板の5ピン: 1 OUT / 2 IN / 3 Vbb / 4 IS / 5 OUT(3番の足はチップ側で短いがタブ経由でVbb)。
Q1 は 2SC1815(平らな面を手前にして左から E・C・B)。
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bts-board.html")
MONO = 'font-family="ui-monospace, SF Mono, Menlo, monospace"'
RED, ORG, GRY, GRN, PUR, BLK = "var(--w-pos)", "var(--w-out)", "var(--w-gnd)", "var(--w-in)", "var(--w-is)", "#3a3f3c"

P, BX, BY = 30, 40, 70
X = lambda c: BX + c * P
Y = lambda r: BY + r * P
C0, C1, R0, R1 = 2, 11, 0, 13


def t(x, y, s, cls="t-lab", anchor="start", extra=""):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" {extra}>{s}</text>'


def wire(pts, col, w):
    d = "M" + " L".join(f"{X(c)} {Y(r)}" for c, r in pts)
    return f'<path d="{d}" stroke="{col}" stroke-width="{w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'


def stand(c1, r1, c2, r2):
    """立てた抵抗: 1本目の足に本体(丸)、2本目へ足を折り返す"""
    return (f'<path d="M{X(c1)} {Y(r1)} L{X(c2)} {Y(r2)}" stroke="#777" stroke-width="1.6"/>'
            f'<circle cx="{X(c1)}" cy="{Y(r1)}" r="10" fill="#e8d4a8" fill-opacity=".92" stroke="#9a7a3c"/>')


B = []
B.append(f'<rect x="{X(C0-0.6)}" y="{Y(R0-0.6)}" width="{(C1-C0+1.2)*P}" height="{(R1-R0+1.2)*P}" rx="6" fill="var(--epoxy)" stroke="var(--epoxy-line)" stroke-width="1.5"/>')
for r in range(R0, R1 + 1):
    for c in range(C0, C1 + 1):
        B.append(f'<circle cx="{X(c)}" cy="{Y(r)}" r="6" fill="var(--cu)" stroke="var(--cu-line)" stroke-width=".8"/><circle cx="{X(c)}" cy="{Y(r)}" r="2.2" fill="var(--hole)"/>')

# ---- 裏面配線 ----
B.append(wire([(3, 1), (3, 6)], ORG, 9))                 # OUT(ピン1)→ユーロOUT
B.append(wire([(5, 1), (5, 6)], RED, 9))                 # 12V→ピン3
B.append(wire([(7, 6), (7, 4)], ORG, 9))                 # ピン5→ジャンパ
B.append(f'<path class="flow" d="M{X(5)} {Y(1)} V{Y(6)}" stroke="var(--flow)" stroke-width="2"/>')
B.append(f'<path class="flow" d="M{X(3)} {Y(6)} V{Y(1)}" stroke="var(--flow)" stroke-width="2"/>')
B.append(wire([(7, 1), (11, 1), (11, 12), (3, 12)], BLK, 3))   # GND
B.append(wire([(3, 9), (3, 12)], BLK, 3))                # Q1 E
B.append(wire([(5, 11), (5, 12)], BLK, 3))               # R_BE→GND
B.append(wire([(10, 5), (11, 5)], BLK, 3))               # R_IS→GND
B.append(wire([(10, 10), (11, 10)], BLK, 3))             # XH GND
B.append(wire([(4, 6), (4, 7)], GRN, 3))                 # IN→R_IN
B.append(wire([(4, 8), (4, 9)], GRN, 3))                 # R_IN→Q1 C
B.append(wire([(5, 9), (5, 10)], GRN, 3))                # Q1 B→R_BE
B.append(wire([(5, 9), (6, 9), (6, 10)], GRN, 3))        # Q1 B→R_B
B.append(wire([(9, 10), (9, 9), (10, 9)], GRN, 3))       # R_B→XH CTRL
B.append(wire([(6, 6), (6, 3), (8, 3), (8, 8)], PUR, 3)) # IS
B.append(wire([(8, 5), (9, 5)], PUR, 3))                 # IS→R_IS
B.append(wire([(9, 8), (10, 8)], PUR, 3))                # R_S→XH IS

# ---- 表面の部品(半透明) ----
# ユーロブロック レセプタクル
B.append(f'<rect x="{X(2.3)}" y="{Y(0.25)}" width="{5.4*P}" height="{1.5*P}" rx="4" fill="#4a86d4" fill-opacity=".5" stroke="#24508c" stroke-width="1.5"/>')
for c, nm, col in ((3, "OUT", ORG), (5, "12V", RED), (7, "GND", "var(--ink)")):
    B.append(t(X(c), Y(-0.85), nm, "t-cap", "middle", f'style="font-size:11px;font-weight:700;fill:{col}" {MONO}'))
# OUTジャンパ(表面・被覆線)
B.append(f'<path d="M{X(3)} {Y(4)} C{X(3.5)} {Y(3.2)} {X(6.5)} {Y(3.2)} {X(7)} {Y(4)}" stroke="{ORG}" stroke-width="7" fill="none" stroke-opacity=".55" stroke-dasharray="10 5"/>')
# 変換基板(立てて挿す)
B.append(f'<rect x="{X(2.55)}" y="{Y(6)-10}" width="{4.9*P}" height="20" rx="3" fill="#2a5fb0" fill-opacity=".75"/>')
for i, c in enumerate(range(3, 8)):
    B.append(t(X(c) + 10, Y(6) + 24, str(i + 1), "t-cap", "middle", 'style="font-size:10.5px;font-weight:700"'))
# Q1 2SC1815 (E C B)
B.append(f'<path d="M{X(2.6)} {Y(9)+8} H{X(5.4)} A{1.4*P} {1.4*P} 0 0 0 {X(2.6)} {Y(9)+8} Z" fill="#2b2b2b" fill-opacity=".7"/>')
for c, nm in ((3, "E"), (4, "C"), (5, "B")):
    B.append(t(X(c), Y(9) - 10, nm, "t-cap", "middle", f'style="font-size:10.5px;font-weight:700;fill:#fff" {MONO}'))
# 抵抗
B.append(stand(4, 7, 4, 8))      # R_IN
B.append(stand(5, 10, 5, 11))    # R_BE
B.append(stand(9, 5, 10, 5))     # R_IS
B.append(stand(8, 8, 9, 8))      # R_S
B.append(f'<path d="M{X(6)} {Y(10)} H{X(9)}" stroke="#777" stroke-width="1.6"/>'
         f'<rect x="{X(6.8)}" y="{Y(10)-7}" width="{1.4*P}" height="14" rx="6" fill="#e8d4a8" fill-opacity=".92" stroke="#9a7a3c"/>')  # R_B
# XH ポスト(縦向き)
B.append(f'<rect x="{X(9.6)}" y="{Y(7.55)}" width="{0.8*P}" height="{2.9*P}" rx="2" fill="#f4f1e6" fill-opacity=".8" stroke="#a9a28a" stroke-width="1.5"/>')
for r, nm, col in ((8, "IS", PUR), (9, "CTRL", GRN), (10, "GND", "var(--ink)")):
    B.append(t(X(11.6), Y(r) + 4, nm, "t-cap", "start", f'style="font-size:11px;font-weight:700;fill:{col}" {MONO}'))

# ---- 引き出し線 ----
CX = 560
def callout(x0, y0, ty, text, sub=None):
    s = f'<path d="M{x0} {y0} L{CX-30} {ty-4} H{CX-6}" stroke="var(--muted)" stroke-width="1" fill="none" stroke-dasharray="3 3"/>'
    s += t(CX, ty, text)
    if sub:
        s += t(CX, ty + 17, sub, "t-cap")
    return s
B.append(callout(X(7.7), Y(1), Y(0.3), "ユーロブロック 3P(基板側)", "穴が狭ければ1.5mmに広げる"))
B.append(callout(X(6.5), Y(3.4), Y(2.2), "ピン1と5をつなぐ被覆線(表面)", "0.5sqの線で裏の12Vの線をまたぐ"))
B.append(callout(X(7.45), Y(6), Y(4.3), "変換基板付きBTS(立てて挿す)", "1 OUT・2 IN・3 Vbb・4 IS・5 OUT"))
B.append(callout(X(10.4), Y(5), Y(6.2), "R_IS 1kΩ:ISとGNDの間", "灯具の電流を電圧に変える"))
B.append(callout(X(10.4), Y(8.6), Y(8.1), "XHポスト 3P(ESPへ)", "上からIS・CTRL・GND"))
B.append(callout(X(9.2), Y(10), Y(10.0), "R_B 10kΩ(寝かせる)", "CTRLからQ1のベースへ"))
B.append(callout(X(5.5), Y(9.6), Y(11.9), "Q1 2SC1815:左からE・C・B", "平らな面を手前(下)に向ける"))
B.append(t(X(C0-0.6), Y(R1+1.6) + 6, "部品面から透かして見た図です。太線と色線は裏面の配線、半透明のものは表面の部品です。丸い抵抗は立てて付けます。", "t-cap"))
SVG = f'<svg viewBox="0 0 860 560" role="img" aria-label="BTS6143Dモジュールのユニバーサル基板上の部品配置と裏面配線">{"".join(B)}</svg>'

src_css = open(os.path.join(HERE, "gen_universal_board.py"), encoding="utf-8").read()
CSS = src_css[src_css.index('CSS = """') + 9: src_css.index('"""', src_css.index('CSS = """') + 9)]
CSS = CSS.replace("--w-pos: #c2443a;", "--w-pos: #c2443a; --w-out: #e07a1c; --w-in: #2f8a4f; --w-is: #7a4bb0;")
CSS += "\n  .panel svg { min-width: 720px; }\n"

BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / BTS6143D BOARD</p>
  <h1>BTS6143Dモジュールの基板配置</h1>
  <p class="lead">変換基板に付けたBTS6143D(下に5本のピン)を、ユニバーサル基板に立てて挿す配置です。回路は bts-wiring.html と同じで、基板は10×14穴(約25×36mm)を切り出せば足ります。</p>

  <h2>1. 部品の配置と裏面の配線</h2>
  <p class="note">12V(Vbb)とOUTの太線は、ユーロブロックから変換基板のピンへまっすぐ縦に1本ずつ下ろします。ピン1とピン5はどちらもOUTなので、ピン5側を裏で上へ伸ばし、表面の被覆線で12Vの線をまたいでピン1側とつなぎます。信号の部品(Q1と抵抗5本)は変換基板の下と右にまとめ、ESPへの3本はXHポストから出します。</p>
  <div class="panel">{SVG}</div>

  <h2>2. 穴ごとのつながり</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>線</th><th>つなぐ点</th><th>線の太さ</th></tr></thead>
    <tbody>
      <tr><td><span class="sw" style="background:var(--w-pos)"></span>12V</td><td>ユーロブロック12V → 変換基板ピン3</td><td>0.5sq</td></tr>
      <tr><td><span class="sw" style="background:var(--w-out)"></span>OUT</td><td>ユーロブロックOUT → ピン1。ピン5 → 表面の被覆線 → ピン1の線</td><td>0.5sq</td></tr>
      <tr><td><span class="sw" style="background:var(--w-in)"></span>IN・CTRL</td><td>ピン2 → R_IN → Q1のC。Q1のB → R_B → XHのCTRL。Q1のB → R_BE → GND</td><td>細線</td></tr>
      <tr><td><span class="sw" style="background:var(--w-is)"></span>IS</td><td>ピン4 → R_IS → GND。同じ点 → R_S → XHのIS</td><td>細線</td></tr>
      <tr><td><span class="sw" style="background:#3a3f3c"></span>GND</td><td>ユーロブロックGND、XHのGND、Q1のE、R_BE、R_IS を1本にまとめる</td><td>細線</td></tr>
    </tbody>
  </table></div>

  <div class="warn"><b>12Vの線の上を通るOUTの被覆線は、必ず被覆のある線を使ってください。</b>裸線で渡すと、12VとOUTがショートし、BTSがONのままの状態と同じになって灯具が消せなくなります。抵抗の値は仮の値で、2SC1815の足の並び(E・C・B)も手持ちの部品の印字で確かめてください。</div>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>BTSモジュール基板配置</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
