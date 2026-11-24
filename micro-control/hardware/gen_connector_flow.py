#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BTSモジュール1ch分の、実際の部品とコネクタのつながりを描いた図を生成する。
出力: connector-flow.html
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
コネクタは秋月でカートに入れた構成(2026-11-22):
  電源側 ユーロブロック5.08mm 3P(111587/111590)、信号側 XH 3P(112248/112256 + コンタクト付コード131309)。
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "connector-flow.html")
RED, ORG, GRY, GRN, PUR, BLK = "var(--w-pos)", "var(--w-out)", "var(--w-gnd)", "var(--w-in)", "var(--w-is)", "#2b2b2b"


def t(x, y, s, cls="t-lab", anchor="start", extra=""):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" {extra}>{s}</text>'


def gnd(x, y, col=GRY):
    return (f'<path d="M{x} {y} v10 M{x-11} {y+10} h22 M{x-7} {y+15} h14 M{x-3} {y+20} h6" '
            f'stroke="{col}" stroke-width="2" fill="none" stroke-linecap="round"/>')


def badge(x, y, n):
    return (f'<circle cx="{x}" cy="{y}" r="11" fill="var(--accent)"/>'
            f'<text x="{x}" y="{y+4.5}" text-anchor="middle" style="fill:#fff;font-size:12.5px;font-weight:700">{n}</text>')


S = []
# ---- 区域 ----
S.append('<rect x="20" y="380" width="330" height="190" rx="12" fill="#eef3f8" stroke="#b7c7d8" stroke-dasharray="6 4"/>')
S.append(t(36, 404, "車内", "t-ti", "start", 'style="fill:#3d6f9e"'))
S.append('<rect x="380" y="20" width="500" height="550" rx="12" fill="#f8f4ea" stroke="#d6c7a3" stroke-dasharray="6 4"/>')
S.append(t(396, 44, "灯具の近く", "t-ti", "start", 'style="fill:#8a6a24"'))

# ---- バッテリーとヒューズ ----
S.append('<rect x="40" y="70" width="120" height="74" rx="6" fill="#3a3f44"/>')
S.append('<rect x="58" y="60" width="18" height="12" rx="2" fill="#c2443a"/><rect x="124" y="60" width="18" height="12" rx="2" fill="#555"/>')
S.append(t(100, 104, "バッテリー", "t-lab", "middle", 'style="fill:#fff;font-weight:700"'))
S.append(t(100, 124, "12V", "t-cap", "middle", 'style="fill:#d6dbd8"'))
S.append(f'<path d="M133 60 V40 H60" stroke="{GRY}" stroke-width="3" fill="none"/>' + gnd(60, 40))
S.append(t(24, 36, "車体", "t-cap"))
S.append(f'<path d="M67 60 V50 H220" stroke="{RED}" stroke-width="5" fill="none"/>')
S.append('<rect x="220" y="36" width="56" height="28" rx="4" fill="#fff4c9" stroke="#b08a1c" stroke-width="1.5"/>')
S.append('<rect x="236" y="30" width="24" height="10" rx="2" fill="#e0a42a"/>')
S.append(t(248, 55, "5A", "t-cap", "middle", 'style="font-weight:700"'))
S.append(t(248, 84, "ヒューズ", "t-cap", "middle"))
# 12V線: ヒューズ → プラグ
S.append(f'<path d="M276 50 H511 V150" stroke="{RED}" stroke-width="5" fill="none"/>')
S.append(f'<path class="flow" d="M67 50 H220 M276 50 H511 V150" stroke="var(--flow)" stroke-width="2" fill="none"/>')

# ---- モジュール基板 ----
S.append('<rect x="430" y="196" width="170" height="168" rx="5" fill="var(--epoxy)" stroke="var(--epoxy-line)" stroke-width="1.5"/>')
for r in range(6):
    for c in range(6):
        S.append(f'<circle cx="{446+c*28}" cy="{232+r*24}" r="3" fill="var(--cu)" stroke="var(--cu-line)" stroke-width=".6"/>')
# ユーロブロック レセプタクル(基板側)
S.append('<rect x="463" y="192" width="96" height="26" rx="3" fill="#3d77c4" stroke="#24508c" stroke-width="1.5"/>')
# ユーロブロック プラグ(線側)
S.append('<rect x="459" y="138" width="104" height="54" rx="4" fill="#4a86d4" stroke="#24508c" stroke-width="1.5"/>')
for x in (477, 511, 545):
    S.append(f'<circle cx="{x}" cy="{156}" r="8" fill="#dfe6ee" stroke="#24508c"/><path d="M{x-5} 156 h10" stroke="#24508c" stroke-width="1.6"/>')
    S.append(f'<rect x="{x-6}" y="172" width="12" height="12" rx="2" fill="#1d3f70"/>')
# BTS(変換基板)
S.append('<rect x="476" y="240" width="78" height="62" rx="3" fill="#2f7a4a" stroke="#1d5532"/>')
S.append('<rect x="490" y="250" width="50" height="38" rx="2" fill="#2b2b2b"/>')
S.append(t(515, 273, "BTS", "t-lab", "middle", 'style="fill:#fff;font-weight:700;font-size:12px"'))
# 抵抗2本
S.append('<rect x="452" y="314" width="34" height="11" rx="5" fill="#e8d4a8" stroke="#9a7a3c"/><rect x="548" y="314" width="34" height="11" rx="5" fill="#e8d4a8" stroke="#9a7a3c"/>')
# XHポスト(基板側)
S.append('<rect x="486" y="352" width="58" height="22" rx="2" fill="#f4f1e6" stroke="#a9a28a" stroke-width="1.5"/>')
# XHハウジング(線側)
S.append('<rect x="488" y="374" width="54" height="22" rx="2" fill="#fbfaf4" stroke="#a9a28a" stroke-width="1.5"/>')
S.append(t(610, 214, "BTSモジュール", "t-ti"))
S.append(t(610, 232, "基板 約3×4cm", "t-cap"))

# ---- 線側 ----
# GND(電源の−)
S.append(f'<path d="M477 138 V112 H420 V128" stroke="{BLK}" stroke-width="3" fill="none"/>' + gnd(420, 128, BLK))
S.append(t(398, 166, "車体へ", "t-cap"))
# OUT → 灯具
S.append(f'<path d="M545 138 V100 H760" stroke="{ORG}" stroke-width="5" fill="none"/>')
S.append(f'<path class="flow" d="M545 138 V100 H760" stroke="var(--flow)" stroke-width="2" fill="none"/>')
S.append('<circle cx="790" cy="100" r="30" fill="#fff6d6" stroke="#b08a1c" stroke-width="1.8"/>'
         '<path d="M770 80 L810 120 M810 80 L770 120" stroke="#b08a1c" stroke-width="1.6"/>')
S.append(t(790, 152, "灯具", "t-lab", "middle", 'style="font-weight:700"'))
S.append(f'<path d="M820 100 H850 V130" stroke="{BLK}" stroke-width="3" fill="none"/>' + gnd(850, 130, BLK))
S.append(t(560, 92, "OUT", "t-cap", "start", f'style="fill:{ORG};font-weight:700"'))
S.append(t(300, 42, "12V", "t-cap", "start", f'style="fill:{RED};font-weight:700"'))

# ---- 信号線 ----
ys = {"GND": 470, "IN": 486, "IS": 502}
for (nm, col), x in zip((("GND", GRY), ("IN", GRN), ("IS", PUR)), (500, 515, 530)):
    y = ys[nm]
    S.append(f'<path d="M{x} 396 V{y} H300" stroke="{col}" stroke-width="2.6" fill="none"/>')
    S.append(t(306, y - 3, nm, "t-cap", "start", f'style="font-size:10px;font-weight:700;fill:{col}"'))
# 継ぎ目(コンタクト付コード200mmを半分に切り、長い線をはんだで継ぐ)
S.append('<rect x="446" y="462" width="16" height="48" rx="3" fill="#222" fill-opacity=".85"/>')
# ESPメインユニット
S.append('<rect x="60" y="430" width="240" height="110" rx="6" fill="#2b5d8a"/>')
S.append('<rect x="84" y="450" width="92" height="70" rx="3" fill="#c9ced3" stroke="#8e969d"/>')
S.append(t(130, 490, "ESP32-S3", "t-lab", "middle", 'style="font-weight:700"'))
S.append(t(240, 470, "GND", "t-cap", "middle", 'style="fill:#fff"'))
S.append(t(240, 486, "GPIO", "t-cap", "middle", 'style="fill:#fff"'))
S.append(t(240, 502, "ADC", "t-cap", "middle", 'style="fill:#fff"'))
S.append(t(60, 560, "ESPメインユニット", "t-ti"))

# ---- 番号 ----
S.append(badge(578, 165, "①"[0] if False else "1"))
S.append(badge(560, 388, "2"))
S.append(badge(454, 530, "3"))
S.append(badge(476, 255, "4") if False else "")

# ---- 凡例 ----
LX = 640
items = [
    ("1", "ユーロブロック 3P(着脱できる)", "12V・OUT・GNDの太い線。数A流れる"),
    ("2", "XHコネクタ 3P(着脱できる)", "ESPへの信号3本。数mAしか流れない"),
    ("3", "コードの継ぎ目", "はんだで継ぎ、熱収縮チューブで覆う"),
]
for i, (n, a, b) in enumerate(items):
    y = 300 + i * 56
    S.append(badge(LX + 10, y - 4, n))
    S.append(t(LX + 28, y, a, "t-lab", "start", 'style="font-weight:700;font-size:12.5px"'))
    S.append(t(LX + 28, y + 17, b, "t-cap", "start", 'style="font-size:11px"'))
SVG = f'<svg viewBox="0 0 900 580" role="img" aria-label="バッテリーからヒューズ、ユーロブロック、BTSモジュール、灯具へ大電流が流れ、ESPからXHコネクタ経由で信号3本がモジュールへつながる図">{"".join(S)}</svg>'

src_css = open(os.path.join(HERE, "gen_universal_board.py"), encoding="utf-8").read()
CSS = src_css[src_css.index('CSS = """') + 9: src_css.index('"""', src_css.index('CSS = """') + 9)]
CSS = CSS.replace("--w-pos: #c2443a;", "--w-pos: #c2443a; --w-out: #e07a1c; --w-in: #2f8a4f; --w-is: #7a4bb0;")
CSS += "\n  .panel svg { min-width: 760px; }\n"

BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / CONNECTORS</p>
  <h1>BTSモジュール1ch分のつながり</h1>
  <p class="lead">BTSモジュールには、着脱できる口が2つあります。上のユーロブロックは灯具に電気を送る太い線用で、下のXHコネクタはESPから命令を送る細い線用です。どちらも抜けば、モジュールをはんだごてなしで車から外せます。</p>

  <h2>1. 部品のつながり</h2>
  <p class="note">青い破線が動いている赤と橙の線は、灯具に数Aが流れる道です。この道はバッテリーからヒューズとユーロブロック(1)を通り、BTSで入り切りされて灯具へ出ます。ESPからの3本は数mAしか流れない信号で、XHコネクタ(2)からモジュールに入ります。</p>
  <div class="panel">{SVG}</div>

  <h2>2. 2つの口の役目</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>口</th><th>通る線</th><th>流れる電流</th><th>ないとどうなるか</th></tr></thead>
    <tbody>
      <tr><td>1 ユーロブロック 3P</td><td><span class="sw" style="background:var(--w-pos)"></span>12V、<span class="sw" style="background:var(--w-out)"></span>OUT、<span class="sw" style="background:#2b2b2b"></span>GND</td><td>数A</td><td>太い線を基板に直接はんだ付けすることになる</td></tr>
      <tr><td>2 XHコネクタ 3P</td><td><span class="sw" style="background:var(--w-gnd)"></span>GND、<span class="sw" style="background:var(--w-in)"></span>IN、<span class="sw" style="background:var(--w-is)"></span>IS</td><td>数mA</td><td>信号線を基板に直接はんだ付けすることになる</td></tr>
    </tbody>
  </table></div>
  <p class="note" style="margin-top:12px">XHコネクタは、モジュールを外すたびに信号線のはんだを外したくない場合に使います。モジュールを付けたまま外さないのであれば、XHを省いて信号線を直接はんだ付けしても動作は変わりません。</p>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>BTSモジュールのつながり</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
