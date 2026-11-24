#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汎用BTSモジュール(1ch)の構成図を生成する。
出力: bts-module.html
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
考え方: 大電流(Vbb/OUT)はユニバーサル基板の上で ねじ端子 と裏面の太線だけで完結させ、
        ブレッドボードへは信号(GND/IN/IS、数mA)の3本だけをピンヘッダで出す。
BTS6143Dのピン順は ①GND ②IN ③Vbb ④IS ⑤OUT として描く(推測・データシートで要確認)。
"""
import io, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bts-module.html")
MONO = 'font-family="ui-monospace, SF Mono, Menlo, monospace"'
RED, ORG, GRY, GRN, PUR = "var(--w-pos)", "var(--w-out)", "var(--w-gnd)", "var(--w-in)", "var(--w-is)"


def gnd(x, y, col=GRY):
    return (f'<path d="M{x} {y} v10 M{x-11} {y+10} h22 M{x-7} {y+15} h14 M{x-3} {y+20} h6" '
            f'stroke="{col}" stroke-width="2" fill="none" stroke-linecap="round"/>')


def t(x, y, s, cls="t-lab", anchor="start", extra=""):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" {extra}>{s}</text>'


# ================= 図1: 全体の構成 =================
A = []
# 電源
A.append('<rect x="30" y="70" width="120" height="90" rx="8" fill="#fff" stroke="var(--box-line)" stroke-width="1.5"/>')
A.append(t(90, 108, "12V電源", "t-ti", "middle"))
A.append(t(90, 128, "電源装置など", "t-cap", "middle"))
A.append(t(140, 96, "+", "t-lab", "end", 'font-weight="700" fill="var(--w-pos)"'))
A.append(t(140, 145, "−", "t-lab", "end", 'font-weight="700"'))
A.append(f'<path d="M150 140 H175 V160" stroke="{GRY}" stroke-width="3" fill="none"/>' + gnd(175, 160))
# ヒューズ+12V
A.append(f'<path d="M150 100 H185 M215 100 H300" stroke="{RED}" stroke-width="5" fill="none"/>')
A.append(f'<path class="flow" d="M150 100 H185 M215 100 H300" stroke="var(--flow)" stroke-width="2" fill="none"/>')
A.append('<rect x="185" y="92" width="30" height="16" rx="3" fill="#fff4c9" stroke="#b08a1c" stroke-width="1.5"/>')
A.append(t(200, 84, "ヒューズ", "t-cap", "middle"))
# モジュール基板
A.append('<rect x="300" y="50" width="220" height="160" rx="6" fill="var(--epoxy)" stroke="var(--epoxy-line)" stroke-width="1.5"/>')
A.append(t(300, 40, "BTSモジュール(ユニバーサル基板・1ch)", "t-ti"))
A.append('<rect x="300" y="82" width="28" height="64" rx="3" fill="var(--term)" stroke="var(--term-line)" stroke-width="1.5"/>')
for y in (100, 130):
    A.append(f'<circle cx="314" cy="{y}" r="7" fill="#dfe6ee" stroke="var(--term-line)"/><path d="M309 {y} h10" stroke="var(--term-line)" stroke-width="1.5"/>')
A.append(t(336, 93, "12V", "t-cap", "start", 'style="font-size:10px"'))
A.append(t(336, 124, "GND", "t-cap", "start", 'style="font-size:10px"'))
A.append(f'<path d="M300 130 H276 V160" stroke="{GRY}" stroke-width="3" fill="none"/>' + gnd(276, 160))
# BTS
A.append(f'<path d="M328 100 H380" stroke="{RED}" stroke-width="5"/>')
A.append(f'<path class="flow" d="M328 100 H380" stroke="var(--flow)" stroke-width="2"/>')
A.append(f'<path d="M450 115 H492" stroke="{ORG}" stroke-width="5"/>')
A.append(f'<path class="flow" d="M450 115 H492" stroke="var(--flow)" stroke-width="2"/>')
A.append(f'<path d="M334 130 H372 V140 H380" stroke="{GRY}" stroke-width="1.5" fill="none"/>')
A.append('<rect x="380" y="86" width="70" height="60" rx="4" fill="#33383a"/>')
A.append(t(415, 112, "BTS", "t-ti", "middle", 'style="fill:#fff"'))
A.append(t(415, 130, "ソケットに挿す", "t-cap", "middle", 'style="fill:#d6dbd8;font-size:10px"'))
A.append('<rect x="492" y="98" width="28" height="34" rx="3" fill="var(--term)" stroke="var(--term-line)" stroke-width="1.5"/>')
A.append('<circle cx="506" cy="115" r="7" fill="#dfe6ee" stroke="var(--term-line)"/><path d="M501 115 h10" stroke="var(--term-line)" stroke-width="1.5"/>')
A.append(t(506, 90, "OUT", "t-cap", "middle"))
# 信号線とヘッダ
for x, col, nm in ((395, GRY, "GND"), (415, GRN, "IN"), (435, PUR, "IS")):
    A.append(f'<path d="M{x} 146 V204" stroke="{col}" stroke-width="1.8"/>')
A.append(t(452, 214, "GND・IN・IS", "t-cap", "start", 'style="font-size:10px"'))
A.append('<rect x="383" y="204" width="64" height="12" rx="2" fill="#2a2a2a"/>')
# 灯具
A.append(f'<path d="M520 115 H618" stroke="{ORG}" stroke-width="5"/>')
A.append(f'<path class="flow" d="M520 115 H618" stroke="var(--flow)" stroke-width="2"/>')
A.append('<circle cx="640" cy="115" r="22" fill="#fff6d6" stroke="#b08a1c" stroke-width="1.8"/>'
         '<path d="M625 100 L655 130 M655 100 L625 130" stroke="#b08a1c" stroke-width="1.6"/>')
A.append(t(640, 82, "灯具", "t-lab", "middle"))
A.append(f'<path d="M662 115 H690 V150" stroke="{GRY}" stroke-width="3" fill="none"/>' + gnd(690, 150))
A.append(t(560, 182, "大電流(数A)は", "t-lab", "start", 'style="fill:var(--danger);font-weight:700;font-size:12.5px"'))
A.append(t(560, 200, "ねじ端子と基板の上だけ", "t-lab", "start", 'style="fill:var(--danger);font-weight:700;font-size:12.5px"'))
# ブレッドボード
A.append('<rect x="330" y="244" width="400" height="82" rx="6" fill="#f7f7f2" stroke="#c9cbc0" stroke-width="1.5"/>')
for r in range(5):
    for c in range(38):
        A.append(f'<circle cx="{342+c*10}" cy="{254+r*15}" r="1.6" fill="#c3c6bb"/>')
for x in (395, 415, 435):
    A.append(f'<path d="M{x} 216 V246" stroke="#8a8a8a" stroke-width="2.5"/>')
A.append('<rect x="580" y="258" width="130" height="52" rx="5" fill="#2b5d8a"/>')
A.append(t(645, 289, "ESP32-S3", "t-ti", "middle", 'style="fill:#fff"'))
A.append(f'<path d="M435 246 V268 H580" stroke="{PUR}" stroke-width="2.2" fill="none"/>')
A.append(f'<path d="M415 246 V283 H580" stroke="{GRN}" stroke-width="2.2" fill="none"/>')
A.append(f'<path d="M395 246 V298 H580" stroke="{GRY}" stroke-width="2.2" fill="none"/>')
A.append(t(520, 263, "ADC", "t-cap", "middle", f'style="font-size:10px;fill:{PUR}"'))
A.append(t(520, 278, "GPIO", "t-cap", "middle", f'style="font-size:10px;fill:{GRN}"'))
A.append(t(520, 293, "GND", "t-cap", "middle", f'style="font-size:10px"'))
A.append(t(40, 262, "信号(数mA)の3本だけ", "t-lab", "start", 'style="fill:var(--ok);font-weight:700;font-size:12.5px"'))
A.append(t(40, 280, "ピンヘッダでブレッドボードへ", "t-lab", "start", 'style="fill:var(--ok);font-weight:700;font-size:12.5px"'))
A.append(f'<path d="M250 272 Q340 262 380 214" stroke="var(--ok)" stroke-width="1.3" fill="none" stroke-dasharray="4 3"/>')
A.append(t(40, 316, "⏚ はすべて電源の−へ(共通GND)", "t-cap"))
SVG1 = f'<svg viewBox="0 0 760 340" role="img" aria-label="12V電源からヒューズ、BTSモジュール、灯具へ大電流が流れ、信号3本だけがブレッドボードのESP32へつながる構成">{"".join(A)}</svg>'

# ================= 図2: モジュール基板の配置(部品面から透かして見る) =================
P, BX, BY = 28, 70, 70
X = lambda c: BX + c * P
Y = lambda r: BY + r * P
B = []
B.append(f'<rect x="{X(-0.6)}" y="{Y(-0.9)}" width="{10.2*P}" height="{12.5*P}" rx="6" fill="var(--epoxy)" stroke="var(--epoxy-line)" stroke-width="1.5"/>')
for r in range(12):
    for c in range(10):
        B.append(f'<circle cx="{X(c)}" cy="{Y(r)}" r="5.5" fill="var(--cu)" stroke="var(--cu-line)" stroke-width=".8"/><circle cx="{X(c)}" cy="{Y(r)}" r="2" fill="var(--hole)"/>')
# 裏面配線
def wire(pts, col, w):
    d = "M" + " L".join(f"{X(c)} {Y(r)}" for c, r in pts)
    return f'<path d="{d}" stroke="{col}" stroke-width="{w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
B.append(wire([(5, 0), (5, 3)], RED, 9))
B.append(wire([(7, 3), (7, 0)], ORG, 9))
B.append(f'<path class="flow" d="M{X(5)} {Y(0)} V{Y(3)}" stroke="var(--flow)" stroke-width="2"/>')
B.append(f'<path class="flow" d="M{X(7)} {Y(3)} V{Y(0)}" stroke="var(--flow)" stroke-width="2"/>')
B.append(wire([(3, 0), (3, 11)], GRY, 3))
B.append(wire([(4, 3), (4, 6)], GRN, 3))
B.append(wire([(4, 9), (4, 11)], GRN, 3))
B.append(wire([(6, 3), (6, 10), (5, 10), (5, 11)], PUR, 3))
# 部品(表面・半透明)
B.append(f'<rect x="{X(2.4)}" y="{Y(-0.7)}" width="{5.2*P}" height="{1.4*P}" rx="4" fill="var(--term)" fill-opacity=".55" stroke="var(--term-line)" stroke-width="1.5"/>')
for c, nm, col in ((3, "GND", "var(--ink)"), (5, "12V", RED), (7, "OUT", ORG)):
    B.append(t(X(c), Y(-1.25), nm, "t-cap", "middle", f'style="font-size:11px;font-weight:700;fill:{col}" {MONO}'))
B.append(f'<rect x="{X(2.5)}" y="{Y(3)-6}" width="{5*P}" height="12" rx="2" fill="#33383a" fill-opacity=".7"/>')
for i, c in enumerate(range(3, 8)):
    B.append(t(X(c) + 10, Y(3) + 22, "①②③④⑤"[i], "t-cap", "middle", 'style="font-size:10px"'))
# R_IS 横置き c3-c6 @ r5
B.append(f'<path d="M{X(3)} {Y(5)} H{X(6)}" stroke="#777" stroke-width="1.5"/>')
B.append(f'<rect x="{X(3.75)}" y="{Y(5)-7}" width="{1.5*P}" height="14" rx="6" fill="#e8d4a8" fill-opacity=".9" stroke="#9a7a3c"/>')
# R_IN 縦置き c4 r6-r9
B.append(f'<path d="M{X(4)} {Y(6)} V{Y(9)}" stroke="#777" stroke-width="1.5"/>')
B.append(f'<rect x="{X(4)-7}" y="{Y(6.75)}" width="14" height="{1.5*P}" rx="6" fill="#e8d4a8" fill-opacity=".9" stroke="#9a7a3c"/>')
# ヘッダ r11 c3-c5、下向きに出る
B.append(f'<rect x="{X(2.55)}" y="{Y(11)-9}" width="{2.9*P}" height="18" rx="2" fill="#2a2a2a" fill-opacity=".85"/>')
for c, nm, col in ((3, "GND", GRY), (4, "IN", GRN), (5, "IS", PUR)):
    B.append(f'<path d="M{X(c)} {Y(11)+9} V{Y(12.5)}" stroke="#8a8a8a" stroke-width="3"/>')
    B.append(t(X(c), Y(12.5) + 15, nm, "t-cap", "middle", f'style="font-size:11px;font-weight:700;fill:{col}" {MONO}'))
# 引出し
CX = 380
def callout(x0, y0, ty, text, sub=None):
    s = f'<path d="M{x0} {y0} L{CX-30} {ty-4} H{CX-6}" stroke="var(--muted)" stroke-width="1" fill="none" stroke-dasharray="3 3"/>'
    s += t(CX, ty, text)
    if sub:
        s += t(CX, ty + 17, sub, "t-cap")
    return s
B.append(callout(X(7.6), Y(0), Y(-0.6), "ねじ端子 3P(5.08mm)", "電源の−・電源の+12V・灯具へ"))
B.append(callout(X(7) + 6, Y(1.5), Y(1.3), "Vbb・OUTは裏面の0.5sq線で直結", "数Aが流れるのはこの2本だけ"))
B.append(callout(X(7.5), Y(3), Y(3.3), "丸ピンソケット 5P", "BTSカートリッジ(変換基板)を立てて挿す"))
B.append(callout(X(5.25) + 4, Y(5), Y(5.3), "R_IS: ISとGNDの間", "電流の大きさを電圧に変えてADCへ渡す"))
B.append(callout(X(4) + 8, Y(7.5), Y(7.4), "R_IN: INに直列", "ESPのGPIOを守る"))
B.append(callout(X(5.45), Y(11), Y(10.6), "ピンヘッダ 3P(下向き)", "ブレッドボードに挿す。ジャンパ線でもよい"))
B.append(t(X(-0.6), Y(13.6) + 4, "部品面から透かして見た図です。太線と色線は裏面の配線、半透明のものは表面の部品です。", "t-cap"))
SVG2 = f'<svg viewBox="0 0 760 480" role="img" aria-label="モジュール基板の部品配置と裏面配線">{"".join(B)}</svg>'

src_css = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_universal_board.py"), encoding="utf-8").read()
CSS = src_css[src_css.index('CSS = """') + 9: src_css.index('"""', src_css.index('CSS = """') + 9)]
CSS = CSS.replace("--w-pos: #c2443a;", "--w-pos: #c2443a; --w-out: #e07a1c; --w-in: #2f8a4f; --w-is: #7a4bb0; --term: #8fb6dd; --term-line: #3d6f9e;")

BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / BTS MODULE</p>
  <h1>汎用BTSモジュール(1ch)の構成</h1>
  <div class="warn" style="margin-bottom:16px"><b>この図のピン配置は誤りです(2026-11-22判明)。</b>BTS6143Dは 1 OUT・2 IN・3/タブ Vbb・4 IS・5 OUT で、GNDピンはありません。正しい配線は bts-wiring.html を見てください。</div>
  <p class="lead">BTS1個を小さなユニバーサル基板に載せ、大電流はねじ端子だけで出し入れし、ブレッドボードへは信号の3本だけを出します。こうすると、ブレッドボードに数Aが流れることがなく、同じモジュールを別の実験にもそのまま使えます。</p>

  <h2>1. 全体の構成</h2>
  <p class="note">12Vはヒューズを通ってモジュールのねじ端子に入り、BTSを通って灯具へ出ます。この大電流の道は、ねじ端子と基板の上だけで閉じています。ESP32とモジュールをつなぐのはGND・IN・ISの3本で、どれも数mAしか流れないので、ブレッドボードやジャンパ線で問題ありません。</p>
  <div class="panel">{SVG1}</div>

  <h2>2. モジュール基板の配置</h2>
  <p class="note">ねじ端子の並びをソケットのピンの並びに合わせると、12V(Vbb)とOUTの太線がまっすぐ縦の1本ずつになり、線が交差しません。R_ISは表面に寝かせて置くので、裏面を通るINの線とは触れません。基板は10×12穴(約3×4cm)を切り出せば足ります。</p>
  <div class="panel">{SVG2}</div>
  <p class="note" style="margin-top:10px;font-size:12.5px;color:var(--muted)">ピンの並び(①GND ②IN ③Vbb ④IS ⑤OUT)は説明用です。R_INとR_ISの値も未確定なので、データシートと変換基板の印字で確かめてから配線してください。</p>

  <h2>3. 各ピンの行き先</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>BTSのピン</th><th>流れる電流</th><th>つなぐ先</th><th>線</th></tr></thead>
    <tbody>
      <tr><td><span class="sw" style="background:var(--w-pos)"></span>Vbb(12V)</td><td>数A</td><td>ねじ端子 12V → ヒューズ → 電源の+</td><td>裏面 0.5sq</td></tr>
      <tr><td><span class="sw" style="background:var(--w-out)"></span>OUT</td><td>数A</td><td>ねじ端子 OUT → 灯具</td><td>裏面 0.5sq</td></tr>
      <tr><td><span class="sw" style="background:var(--w-gnd)"></span>GND</td><td>数mA</td><td>ねじ端子 GND(電源の−)とヘッダ GND(ESPのGND)</td><td>細線でよい</td></tr>
      <tr><td><span class="sw" style="background:var(--w-in)"></span>IN</td><td>1mA未満</td><td>R_IN → ヘッダ IN → ESPのGPIO</td><td>細線でよい</td></tr>
      <tr><td><span class="sw" style="background:var(--w-is)"></span>IS</td><td>数mA</td><td>R_ISでGNDへ落とし、同じ点をヘッダ IS → ESPのADCへ</td><td>細線でよい</td></tr>
    </tbody>
  </table></div>

  <div class="warn"><b>ねじ端子のGNDを電源の−へつなぎ忘れないでください。</b>つなぎ忘れると、ESP32とBTSの基準の電圧がずれて、INの信号が正しく伝わりません。灯具の−は、モジュールを通さず電源の−へ直接戻します。</div>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>汎用BTSモジュール</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
