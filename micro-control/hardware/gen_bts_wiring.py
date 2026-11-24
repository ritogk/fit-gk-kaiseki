#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BTS6143D 1ch分の配線図(正しいピン配置)を生成する。
出力: bts-wiring.html
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
ピン配置は BTS6143D データシート(Rev.1.0 2007-02、PG-TO252-5-11)で確認済み(2026-11-22):
  1 OUT / 2 IN(GNDへ落とすとON) / 3・タブ Vbb / 4 IS / 5 OUT(1と外部で短絡必須)。GNDピンはない。
kILIS=9700(25℃,2.5A)、IIS,fault=4.0〜7.5mA、IL(MIN)=50mA、IIN(on)=1.4〜2.2mA。
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bts-wiring.html")
RED, ORG, GRY, GRN, PUR, BLK = "var(--w-pos)", "var(--w-out)", "var(--w-gnd)", "var(--w-in)", "var(--w-is)", "#2b2b2b"


def t(x, y, s, cls="t-lab", anchor="start", extra=""):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" {extra}>{s}</text>'


def line(d, col, w=2.2):
    return f'<path d="{d}" stroke="{col}" stroke-width="{w}" fill="none" stroke-linejoin="round"/>'


def dot(x, y, col):
    return f'<circle cx="{x}" cy="{y}" r="4" fill="{col}"/>'


def res_h(x, y, w, label, val, col="#555"):
    """横向き抵抗(x..x+w の中央に本体)"""
    cx = x + w / 2
    return (line(f"M{x} {y} H{cx-18} M{cx+18} {y} H{x+w}", col) +
            f'<rect x="{cx-18}" y="{y-7}" width="36" height="14" rx="2" fill="#fff" stroke="{col}" stroke-width="1.8"/>' +
            t(cx, y - 13, label, "t-cap", "middle", 'style="font-weight:700"') + t(cx, y + 22, val, "t-cap", "middle"))


def res_v(x, y, h, label, val, col="#555"):
    cy = y + h / 2
    return (line(f"M{x} {y} V{cy-18} M{x} {cy+18} V{y+h}", col) +
            f'<rect x="{x-7}" y="{cy-18}" width="14" height="36" rx="2" fill="#fff" stroke="{col}" stroke-width="1.8"/>' +
            t(x + 13, cy - 2, label, "t-cap", "start", 'style="font-weight:700"') + t(x + 13, cy + 13, val, "t-cap"))


def gnd(x, y, col=BLK):
    return (f'<path d="M{x} {y} v8 M{x-10} {y+8} h20 M{x-6} {y+13} h12 M{x-2} {y+18} h4" '
            f'stroke="{col}" stroke-width="2" fill="none" stroke-linecap="round"/>')


# ================= 図1: 回路図 =================
S = []
GY = 450  # GNDレール
# --- XH(信号側) ---
S.append('<rect x="30" y="250" width="46" height="150" rx="4" fill="#f4f1e6" stroke="#a9a28a" stroke-width="1.5"/>')
S.append(t(53, 240, "XH 3P", "t-cap", "middle", 'style="font-weight:700"'))
S.append(t(53, 418, "ESPへ", "t-cap", "middle"))
xh = {"CTRL": 290, "IS": 330, "GND": 370}
for nm, y in xh.items():
    S.append(f'<circle cx="53" cy="{y}" r="5" fill="#fff" stroke="#a9a28a" stroke-width="1.5"/>')
S.append(t(84, 285, "CTRL", "t-cap", "start", f'style="fill:{GRN};font-weight:700"'))
S.append(t(84, 325, "IS", "t-cap", "start", f'style="fill:{PUR};font-weight:700"'))
S.append(t(84, 365, "GND", "t-cap", "start", 'style="font-weight:700"'))
# --- CTRL → R_B → Q1 ベース ---
S.append(line(f"M58 290 H130", GRN))
S.append(res_h(130, 290, 90, "R_B", "10kΩ", GRN))
S.append(line(f"M220 290 H262", GRN))
S.append(dot(240, 290, GRN))
S.append(res_v(240, 290, GY - 290, "R_BE", "47kΩ", GRY))
# Q1(NPN)
qx, qy = 280, 290
S.append(f'<circle cx="{qx+8}" cy="{qy}" r="24" fill="#fff" stroke="#333" stroke-width="1.6"/>')
S.append(line(f"M262 {qy} H{qx}", "#333", 2))
S.append(line(f"M{qx} {qy-14} V{qy+14}", "#333", 3))
S.append(line(f"M{qx} {qy-6} L{qx+18} {qy-20} V{qy-60}", "#333", 2))   # コレクタ
S.append(line(f"M{qx} {qy+6} L{qx+18} {qy+20} V{GY}", "#333", 2))      # エミッタ
S.append(f'<path d="M{qx+18} {qy+20} l-9 -2 l4 -7 z" fill="#333"/>')
S.append(t(qx + 40, qy + 4, "Q1 NPN", "t-cap", "start", 'style="font-weight:700"'))
S.append(t(qx + 40, qy + 19, "2SC1815など", "t-cap"))
# コレクタ → R_IN → IN(pin2)
S.append(line(f"M{qx+18} {qy-60} V230 H330", GRN))
S.append(res_h(330, 230, 100, "R_IN", "1kΩ", GRN))
S.append(line("M430 230 H470", GRN))

# --- BTS本体 ---
BX0, BX1, BY0, BY1 = 470, 640, 150, 390
S.append(f'<rect x="{BX0}" y="{BY0}" width="{BX1-BX0}" height="{BY1-BY0}" rx="6" fill="#33383a"/>')
S.append(t((BX0+BX1)/2, 262, "BTS6143D", "t-ti", "middle", 'style="fill:#fff"'))
S.append(t((BX0+BX1)/2, 282, "GNDピンはない", "t-cap", "middle", 'style="fill:#d6dbd8"'))
def pin(x, y, n, nm, anchor):
    dx = 10 if anchor == "start" else -10
    return (f'<circle cx="{x}" cy="{y}" r="11" fill="var(--accent)"/>' +
            t(x, y + 4.5, n, "t-cap", "middle", 'style="fill:#fff;font-weight:700;font-size:12px"') +
            t(x + (16 if anchor == "start" else -16), y + 4.5, nm, "t-cap", anchor, 'style="fill:#fff;font-weight:700"'))
S.append(pin(BX0, 230, "2", "IN", "start"))
S.append(pin(BX0, 330, "4", "IS", "start"))
S.append(pin(555, BY0, "3", "", "start"))
S.append(t(555, BY0 + 32, "Vbb(タブも同じ)", "t-cap", "middle", 'style="fill:#fff;font-weight:700"'))
S.append(pin(BX1, 220, "1", "OUT", "end"))
S.append(pin(BX1, 290, "5", "OUT", "end"))

# --- 12V(Vbb) ---
S.append(line(f"M555 {BY0-11} V90 H820", RED, 5))
S.append(f'<path class="flow" d="M820 90 H555 V{BY0-11}" stroke="var(--flow)" stroke-width="2" fill="none"/>')
S.append(t(600, 80, "12V(ヒューズ5Aを通ってくる)", "t-cap", "start", f'style="fill:{RED};font-weight:700"'))
# --- OUT 1と5を短絡 → ユーロブロックOUT ---
S.append(line(f"M{BX1+11} 220 H690 V290 H{BX1+11}", ORG, 5))
S.append(line("M690 255 H820", ORG, 5))
S.append(f'<path class="flow" d="M{BX1+11} 220 H690 V255 H820" stroke="var(--flow)" stroke-width="2" fill="none"/>')
S.append(dot(690, 255, ORG))
S.append(t(698, 312, "1と5は必ずつなぐ", "t-cap", "start", 'style="fill:var(--danger);font-weight:700"'))

# --- IS → R_IS / R_S → XH IS ---
S.append(line(f"M{BX0-11} 330 H420", PUR))
S.append(dot(420, 330, PUR))
S.append(res_v(420, 330, GY - 330, "R_IS", "1kΩ", PUR))
S.append(line("M420 330 H400", PUR))
S.append(res_h(130, 330, 0, "", "", PUR) if False else "")
S.append(line("M400 330 V420 H200", PUR))
S.append(res_h(110, 420, 90, "R_S", "10kΩ", PUR))
S.append(line("M110 420 H96 V330 H58", PUR))

# --- GNDレール ---
S.append(line(f"M58 370 H80 V{GY} H820", BLK, 2.6))
for x in (240, qx + 18, 420):
    S.append(dot(x, GY, BLK))
S.append(gnd(600, GY))

# --- ユーロブロック(電源側) ---
S.append('<rect x="820" y="60" width="46" height="410" rx="4" fill="#4a86d4" stroke="#24508c" stroke-width="1.5"/>')
S.append(t(843, 50, "ユーロブロック 3P", "t-cap", "middle", 'style="font-weight:700"'))
for y, nm, sub in ((90, "12V", "ヒューズから"), (255, "OUT", "灯具へ"), (GY, "GND", "車体へ")):
    S.append(f'<circle cx="843" cy="{y}" r="7" fill="#dfe6ee" stroke="#24508c"/><path d="M838 {y} h10" stroke="#24508c" stroke-width="1.5"/>')
    S.append(t(876, y, nm, "t-cap", "start", 'style="font-weight:700"'))
    S.append(t(876, y + 15, sub, "t-cap", "start", 'style="font-size:10px"'))
SVG1 = f'<svg viewBox="0 0 960 500" role="img" aria-label="BTS6143D 1ch の回路図">{"".join(S)}</svg>'

# ================= 図2: 部品の足と変換基板 =================
P = []
# 上から見たTO-252
P.append('<rect x="150" y="40" width="200" height="60" rx="4" fill="#b8bec4" stroke="#7d858c"/>')
P.append(t(250, 76, "タブ = 3番(Vbb)", "t-cap", "middle", 'style="font-weight:700"'))
P.append('<rect x="160" y="100" width="180" height="110" rx="4" fill="#33383a"/>')
P.append(t(250, 160, "BTS6143D", "t-lab", "middle", 'style="fill:#fff;font-weight:700"'))
P.append(t(250, 180, "刻印面を上にして見る", "t-cap", "middle", 'style="fill:#d6dbd8;font-size:10px"'))
xs = [178, 214, 250, 286, 322]
names = ["OUT", "IN", "Vbb", "IS", "OUT"]
cols = [ORG, GRN, RED, PUR, ORG]
for i, (x, nm, c) in enumerate(zip(xs, names, cols)):
    ln = 18 if i == 2 else 50
    P.append(f'<rect x="{x-5}" y="210" width="10" height="{ln}" fill="#c9cfcc" stroke="#8e969d"/>')
    P.append(t(x, 285, str(i + 1), "t-cap", "middle", 'style="font-weight:700"'))
    P.append(t(x, 302, nm, "t-cap", "middle", f'style="font-weight:700;fill:{c}"'))
P.append(t(250, 324, "3番の足は短い(切れている)ことが多い", "t-cap", "middle"))
# 変換基板の5ピン
P.append(t(560, 34, "変換基板の5本のピン(下から出る足)", "t-lab", "middle", 'style="font-weight:700"'))
P.append('<rect x="440" y="50" width="240" height="160" rx="5" fill="#2f7a4a" stroke="#1d5532"/>')
px = [480, 520, 560, 600, 640]
for i, (x, nm, c) in enumerate(zip(px, names, cols)):
    P.append(f'<circle cx="{x}" cy="180" r="9" fill="#e7b57a" stroke="#b9864a"/>')
    P.append(f'<rect x="{x-3}" y="189" width="6" height="40" fill="#c9cfcc"/>')
    P.append(t(x, 248, str(i + 1), "t-cap", "middle", 'style="font-weight:700"'))
    P.append(t(x, 265, nm, "t-cap", "middle", f'style="font-weight:700;fill:{c}"'))
P.append('<rect x="480" y="90" width="160" height="50" rx="3" fill="#33383a" fill-opacity=".8"/>')
P.append(f'<path d="M480 171 V150 H640 V171" stroke="{ORG}" stroke-width="5" fill="none"/>')
P.append(t(560, 290, "1番と5番を裏で太い線(0.5sq)でつなぐ", "t-cap", "middle", 'style="fill:var(--danger);font-weight:700"'))
SVG2 = f'<svg viewBox="0 0 760 340" role="img" aria-label="BTS6143Dの足の番号と、変換基板で1番と5番をつなぐ図">{"".join(P)}</svg>'

src_css = open(os.path.join(HERE, "gen_universal_board.py"), encoding="utf-8").read()
CSS = src_css[src_css.index('CSS = """') + 9: src_css.index('"""', src_css.index('CSS = """') + 9)]
CSS = CSS.replace("--w-pos: #c2443a;", "--w-pos: #c2443a; --w-out: #e07a1c; --w-in: #2f8a4f; --w-is: #7a4bb0;")
CSS += "\n  .panel svg { min-width: 760px; }\n"

BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / BTS6143D WIRING</p>
  <h1>BTS6143D 1ch分の配線図</h1>
  <p class="lead">データシートのピン配置で描き直した配線図です。BTS6143DにはGNDのピンがなく、1番と5番が両方OUTです。また、INは「GNDに落とすとON」で動くので、ESPとの間にトランジスタを1個入れます。</p>

  <h2>1. 回路図</h2>
  <p class="note">ESPがCTRLを3.3Vにすると、トランジスタQ1が導通してINをR_IN経由でGNDへ落とし、BTSがONになって12Vが灯具へ出ます。ISからは灯具の電流のおよそ1万分の1の電流が出て、R_ISで電圧に変わり、R_Sを通ってESPのADCに入ります。GNDはユーロブロック(車体)とXH(ESP)の両方につなぎ、モジュールの上で1本にまとめます。</p>
  <div class="panel">{SVG1}</div>

  <h2>2. 足の番号と変換基板</h2>
  <p class="note">BTSを刻印面を上にして、足を手前に向けたとき、左から1〜5番です。真ん中の3番はタブと同じVbbなので、短く切られていても問題ありません。1番と5番は、変換基板の裏で太い線でつないでください。つながないと、ONのときの抵抗が増えて発熱し、電流の検出もずれます。</p>
  <div class="panel">{SVG2}</div>

  <h2>3. 部品と値</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>記号</th><th>部品</th><th>値</th><th>役目</th></tr></thead>
    <tbody>
      <tr><td>Q1</td><td>NPNトランジスタ(2SC1815など)</td><td>小信号用</td><td>ESPの3.3VでBTSのINをGNDへ落とす</td></tr>
      <tr><td>R_B</td><td>抵抗</td><td>10kΩ</td><td>Q1のベースに流す電流を絞る</td></tr>
      <tr><td>R_BE</td><td>抵抗</td><td>47kΩ</td><td>ESPが起動する前や線が外れたときにQ1を確実にOFFにする</td></tr>
      <tr><td>R_IN</td><td>抵抗</td><td>1kΩ</td><td>INの電流(約2mA)を流しつつ、バッテリー逆接続のときにICを守る</td></tr>
      <tr><td>R_IS</td><td>抵抗</td><td>1kΩ</td><td>ISの電流を電圧に変える(2Aで約0.2V)</td></tr>
      <tr><td>R_S</td><td>抵抗</td><td>10kΩ</td><td>故障時にISが高い電圧を出してもESPのADCを守る</td></tr>
    </tbody>
  </table></div>

  <div class="warn"><b>故障時はISから4.0〜7.5mAが出るため、R_IS=1kΩでは最大7.5Vになります。</b>R_Sだけでは足りないので、ESP側のADC入力に3.3Vへのクランプ用ダイオードを入れてください。電流比はBTS6143Dのデータシートで約9,700(25℃、2.5A)なので、灯具2Aのとき R_IS の電圧は約0.2Vです。灯具の電流が50mA未満のときは、ISの値が当てになりません。</div>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>BTS6143D 配線図</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
