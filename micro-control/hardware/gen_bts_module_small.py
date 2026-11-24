#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小型版BTSモジュール(1ch・車載用)の基板図を生成する。
出力: bts-module-small.html
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
汎用版(gen_bts_module.py)からソケット・ねじ端子・ピンヘッダを外し、線を直接はんだ付けする。
ピン順は汎用版と同じく ①GND ②IN ③Vbb ④IS ⑤OUT として描く(推測・データシートで要確認)。
寸法は部品の実物を測っていない概算。
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bts-module-small.html")
MONO = 'font-family="ui-monospace, SF Mono, Menlo, monospace"'
RED, ORG, GRY, GRN, PUR = "var(--w-pos)", "var(--w-out)", "var(--w-gnd)", "var(--w-in)", "var(--w-is)"


def t(x, y, s, cls="t-lab", anchor="start", extra=""):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" {extra}>{s}</text>'


# ================= 図1: 大きさの比較(上から見た実寸比) =================
M = 5.0  # 1mm = 5px
A = []
def box(x, y, w, h, fill, line, rx=4, op="1"):
    return f'<rect x="{x}" y="{y}" width="{w*M}" height="{h*M}" rx="{rx}" fill="{fill}" fill-opacity="{op}" stroke="{line}" stroke-width="1.5"/>'
# 汎用版
gx, gy = 40, 60
A.append(t(gx, 40, "汎用版(前回の図)", "t-ti"))
A.append(box(gx, gy, 55, 40, "#f3f4f6", "#9aa0a6", 6))
A.append(box(gx + 12.5*M, gy + 2.5*M, 30, 35, "var(--epoxy)", "var(--epoxy-line)", 3))
A.append(f'<rect x="{gx+15*M}" y="{gy+4*M}" width="{15*M}" height="{8*M}" rx="2" fill="var(--term)" stroke="var(--term-line)"/>')
A.append(f'<rect x="{gx+17*M}" y="{gy+15*M}" width="{13*M}" height="{9*M}" rx="2" fill="#33383a"/>')
A.append(f'<rect x="{gx+18*M}" y="{gy+31*M}" width="{8*M}" height="{3*M}" rx="1" fill="#2a2a2a"/>')
A.append(t(gx + 27.5*M, gy + 40*M + 22, "ケース込み 約55×40×25mm", "t-cap", "middle"))
# 小型版
sx, sy = 400, 60
A.append(t(sx, 40, "小型版(今回の図)", "t-ti"))
A.append(box(sx + 2.5*M, sy + 4.5*M, 20, 26, "#e9e3f3", "#8a76b0", 8, ".6"))
A.append(box(sx + 3.5*M, sy + 6*M, 18, 23, "var(--epoxy)", "var(--epoxy-line)", 2))
A.append(f'<rect x="{sx+6*M}" y="{sy+11*M}" width="{13*M}" height="{8*M}" rx="2" fill="#33383a"/>')
for i, col in enumerate((RED, ORG)):
    A.append(f'<path d="M{sx+(9+i*5)*M} {sy+5*M} V{sy-4*M}" stroke="{col}" stroke-width="5"/>')
for i, col in enumerate((GRY, GRN, PUR)):
    A.append(f'<path d="M{sx+(8+i*4)*M} {sy+30*M} V{sy+38*M}" stroke="{col}" stroke-width="2.2"/>')
A.append(t(sx + 12.5*M, sy + 40*M + 22, "熱収縮チューブ込み 約26×20×10mm", "t-cap", "middle"))
# 1円玉
cx, cy = 650, sy + 17.5*M
A.append(f'<circle cx="{cx}" cy="{cy}" r="{10*M}" fill="#eceef0" stroke="#a7adb3" stroke-width="1.5"/>')
A.append(t(cx, cy + 5, "1円玉", "t-cap", "middle"))
A.append(t(cx, cy + 10*M + 22, "直径20mm", "t-cap", "middle"))
# スケール
A.append(f'<path d="M40 330 h{10*M} M40 325 v10 M{40+10*M} 325 v10" stroke="var(--muted)" stroke-width="1.5"/>')
A.append(t(40 + 10*M + 8, 334, "10mm(3つとも同じ縮尺)", "t-cap"))
SVG1 = f'<svg viewBox="0 0 760 350" role="img" aria-label="汎用版と小型版と1円玉を同じ縮尺で並べた図">{"".join(A)}</svg>'

# ================= 図2: 小型版の基板(部品面から透かして見る) =================
P, BX, BY = 34, 90, 110
X = lambda c: BX + c * P
Y = lambda r: BY + r * P
COLS, ROWS = 7, 9
B = []
B.append(f'<rect x="{X(-0.55)}" y="{Y(-0.55)}" width="{(COLS-1+1.1)*P}" height="{(ROWS-1+1.1)*P}" rx="5" fill="var(--epoxy)" stroke="var(--epoxy-line)" stroke-width="1.5"/>')
for r in range(ROWS):
    for c in range(COLS):
        B.append(f'<circle cx="{X(c)}" cy="{Y(r)}" r="6.5" fill="var(--cu)" stroke="var(--cu-line)" stroke-width=".8"/><circle cx="{X(c)}" cy="{Y(r)}" r="2.4" fill="var(--hole)"/>')

def wire(pts, col, w):
    d = "M" + " L".join(f"{X(c)} {Y(r)}" for c, r in pts)
    return f'<path d="{d}" stroke="{col}" stroke-width="{w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'

# 外から来る線(基板の外)
for c, col, w, nm, sub in ((1, GRY, 3, "GND", "電源の−"), (3, RED, 9, "12V", "ヒューズから"), (5, ORG, 9, "OUT", "灯具へ")):
    B.append(f'<path d="M{X(c)} {Y(0)} V{Y(-2.2)}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>')
    B.append(t(X(c), Y(-2.2) - 22, nm, "t-cap", "middle", f'style="font-size:11.5px;font-weight:700;fill:{col if col!=GRY else "var(--ink)"}" {MONO}'))
    B.append(t(X(c), Y(-2.2) - 8, sub, "t-cap", "middle", 'style="font-size:10px"'))
B.append(f'<path class="flow" d="M{X(3)} {Y(-2.2)} V{Y(2)}" stroke="var(--flow)" stroke-width="2"/>')
B.append(f'<path class="flow" d="M{X(5)} {Y(2)} V{Y(-2.2)}" stroke="var(--flow)" stroke-width="2"/>')
for c, col, nm in ((1, GRY, "GND"), (2, GRN, "IN"), (4, PUR, "IS")):
    B.append(f'<path d="M{X(c)} {Y(8)} V{Y(10)}" stroke="{col}" stroke-width="3" stroke-linecap="round"/>')
    B.append(t(X(c), Y(10) + 18, nm, "t-cap", "middle", f'style="font-size:11.5px;font-weight:700;fill:{col if col!=GRY else "var(--ink)"}" {MONO}'))
B.append(t(X(2.5), Y(10) + 36, "ESPへ(3本をよって引き回す)", "t-cap", "middle", 'style="font-size:10px"'))

# 裏面配線
B.append(wire([(3, 0), (3, 2)], RED, 9))
B.append(wire([(5, 0), (5, 2)], ORG, 9))
B.append(wire([(1, 0), (1, 8)], GRY, 3))
B.append(wire([(2, 2), (2, 5)], GRN, 3))
B.append(wire([(2, 6), (2, 8)], GRN, 3))
B.append(wire([(4, 2), (4, 8)], PUR, 3))

# BTS(変換基板)を直接はんだ付け
B.append(f'<rect x="{X(0.55)}" y="{Y(0.9)}" width="{4.9*P}" height="{1.6*P}" rx="3" fill="#33383a" fill-opacity=".55"/>')
for i, c in enumerate(range(1, 6)):
    B.append(t(X(c) + 11, Y(2) + 20, "①②③④⑤"[i], "t-cap", "middle", 'style="font-size:10px"'))
# R_IS 横置き c1-c4 @ r4(表面)
B.append(f'<path d="M{X(1)} {Y(4)} H{X(4)}" stroke="#777" stroke-width="1.5"/>')
B.append(f'<rect x="{X(1.8)}" y="{Y(4)-8}" width="{1.4*P}" height="16" rx="7" fill="#e8d4a8" fill-opacity=".9" stroke="#9a7a3c"/>')
# R_IN 立て置き c2 r5-r6(表面)
B.append(f'<path d="M{X(2)} {Y(5)} V{Y(6)}" stroke="#777" stroke-width="1.5"/>')
B.append(f'<circle cx="{X(2)}" cy="{Y(5)}" r="9" fill="#e8d4a8" fill-opacity=".9" stroke="#9a7a3c"/>')

# 引出し
CX = 430
def callout(x0, y0, ty, text, sub=None):
    s = f'<path d="M{x0} {y0} L{CX-30} {ty-4} H{CX-6}" stroke="var(--muted)" stroke-width="1" fill="none" stroke-dasharray="3 3"/>'
    s += t(CX, ty, text)
    if sub:
        s += t(CX, ty + 17, sub, "t-cap")
    return s
B.append(callout(X(5) + 8, Y(-1), Y(-1.3), "12VとOUTは0.5sq線を直接はんだ付け", "ねじ端子をやめた分、基板が小さくなる"))
B.append(callout(X(5) + 8, Y(1), Y(0.7), "裏面でピンまで太くはんだを盛る", "数Aが流れるのはこの2本だけ"))
B.append(callout(X(5.45), Y(1.7), Y(2.4), "BTS(変換基板)を直接はんだ付け", "ソケットをやめた分、背が低くなる(交換はできない)"))
B.append(callout(X(4) + 8, Y(4), Y(4.1), "R_IS: 表面に寝かせる", "裏面のINの線とは触れない"))
B.append(callout(X(2) + 10, Y(5.3), Y(5.8), "R_IN: 立てて置く", "1穴分の幅で済む"))
B.append(callout(X(4) + 8, Y(8.6), Y(7.7), "信号3本も線を直接はんだ付け", "ピンヘッダはなし"))
B.append(t(X(-0.55), Y(12) + 4, "部品面から透かして見た図です。太線と色線は裏面の配線、半透明のものは表面の部品です。", "t-cap"))
SVG2 = f'<svg viewBox="0 0 760 540" role="img" aria-label="小型版モジュールの7×9穴の基板配置と裏面配線">{"".join(B)}</svg>'

src_css = open(os.path.join(HERE, "gen_universal_board.py"), encoding="utf-8").read()
CSS = src_css[src_css.index('CSS = """') + 9: src_css.index('"""', src_css.index('CSS = """') + 9)]
CSS = CSS.replace("--w-pos: #c2443a;", "--w-pos: #c2443a; --w-out: #e07a1c; --w-in: #2f8a4f; --w-is: #7a4bb0; --term: #8fb6dd; --term-line: #3d6f9e;")

BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / BTS MODULE (SMALL)</p>
  <h1>小型版BTSモジュール(1ch)の基板</h1>
  <div class="warn" style="margin-bottom:16px"><b>この図のピン配置は誤りです(2026-11-22判明)。</b>BTS6143Dは 1 OUT・2 IN・3/タブ Vbb・4 IS・5 OUT で、GNDピンはありません。正しい配線は bts-wiring.html を見てください。</div>
  <p class="lead">汎用版からソケット・ねじ端子・ピンヘッダを外し、線をすべて直接はんだ付けした車載用の形です。基板は7×9穴(約18×23mm)で、熱収縮チューブで包むと約26×20×10mmになります。そのかわり、BTSの交換とブレッドボードへの抜き差しはできません。</p>

  <h2>1. 大きさの比較</h2>
  <p class="note">汎用版、小型版、1円玉を同じ縮尺で上から見た図です。汎用版が大きいのは、ねじ端子、ソケット、ピンヘッダと、それを収めるケースの分です。</p>
  <div class="panel">{SVG1}</div>

  <h2>2. 小型版の基板の配置</h2>
  <p class="note">ピンの並びは汎用版と同じなので、12V(Vbb)とOUTはピンの真上の穴へ太線を直接はんだ付けし、裏面でピンまで太くつなぎます。大電流の線は上へ、信号の3本は下へ出るので、太い線と細い線が交わりません。R_INは立てて置き、R_ISは表面に寝かせて、裏面のINの線と触れないようにしています。</p>
  <div class="panel">{SVG2}</div>
  <p class="note" style="margin-top:10px;font-size:12.5px;color:var(--muted)">ピンの並び(①GND ②IN ③Vbb ④IS ⑤OUT)は説明用です。R_INとR_ISの値も未確定なので、データシートと変換基板の印字で確かめてから配線してください。寸法は部品を実測していない概算です。</p>

  <h2>3. 汎用版との違い</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>部分</th><th>汎用版</th><th>小型版</th></tr></thead>
    <tbody>
      <tr><td>BTS</td><td>変換基板ごとソケットに挿す</td><td>変換基板を直接はんだ付け</td></tr>
      <tr><td>12V・OUT・電源GND</td><td>ねじ端子 3P</td><td>線を直接はんだ付け</td></tr>
      <tr><td>GND・IN・IS</td><td>下向きピンヘッダ</td><td>線を直接はんだ付け</td></tr>
      <tr><td>基板</td><td>10×12穴(約27×32mm)</td><td>7×9穴(約18×23mm)</td></tr>
      <tr><td>外装と外形</td><td>樹脂ケース 約55×40×25mm</td><td>熱収縮チューブ 約26×20×10mm</td></tr>
    </tbody>
  </table></div>

  <div class="warn"><b>熱収縮チューブで包むと熱が逃げにくくなります。</b>灯具をつないで連続点灯し、BTSが触れないほど熱くならないかを確かめてから車に載せてください。</div>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>小型版BTSモジュール</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
