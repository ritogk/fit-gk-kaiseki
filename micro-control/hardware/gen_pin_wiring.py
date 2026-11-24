#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手元の変換基板の写真を使い、BTS6143Dの各ピンから行き先までを描いた1ch配線図を生成する。
出力: pin-wiring.html(写真は img/bts-adapter-photo.jpg を埋め込む)
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
回路は bts-wiring.html と同じ。ピン: 1 OUT / 2 IN / 3・タブ Vbb / 4 IS / 5 OUT(BTS6143D データシート Rev.1.0)。
"""
import base64, io, os, sys

SIMPLE = "--simple" in sys.argv  # 1灯を点けるだけの版(ISを使わない)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "one-lamp-wiring.html" if SIMPLE else "pin-wiring.html")
IMG = base64.b64encode(open(os.path.join(HERE, "img", "bts-adapter-photo.jpg"), "rb").read()).decode()
RED, ORG, GRN, PUR, BLK, BLU = "#d23b2e", "#e07a1c", "#2f8a4f", "#7a4bb0", "#2b2b2b", "#2f6fb2"

PX, PY, SC = 330, 10, 0.867
def pp(x, y):
    return PX + x * SC, PY + y * SC
PINX = [pp(x, 0)[0] for x in (70, 150, 230, 310, 393)]
PINY = pp(0, 462)[1]
TAB = pp(240, 81)


def t(x, y, s, size=13, col="#212723", w=700, anchor="start"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" '
            f'style="font-size:{size}px;font-weight:{w};fill:{col};paint-order:stroke;stroke:#fff;stroke-width:4px">{s}</text>')


def ln(d, col, w=2.6):
    return f'<path d="{d}" stroke="{col}" stroke-width="{w}" fill="none" stroke-linejoin="round" stroke-linecap="round"/>'


def hline_hops(x0, x1, y, hops, col, w):
    """x0→x1 の横線。hops の x で半円を描いて縦線をまたぐ"""
    d = f"M{x0:.1f} {y}"
    for h in sorted(hops):
        d += f" H{h-8:.1f} A8 8 0 0 1 {h+8:.1f} {y}"
    d += f" H{x1:.1f}"
    return ln(d, col, w)


def res_h(x0, x1, y, lab, val, col):
    c = (x0 + x1) / 2
    return (ln(f"M{x0} {y} H{c-20} M{c+20} {y} H{x1}", col) +
            f'<rect x="{c-20}" y="{y-8}" width="40" height="16" rx="3" fill="#fff" stroke="{col}" stroke-width="2"/>' +
            t(c, y - 14, lab, 12, col, 700, "middle") + t(c, y + 26, val, 11.5, "#5e6963", 500, "middle"))


def res_v(x, y0, y1, lab, val, col):
    c = (y0 + y1) / 2
    return (ln(f"M{x} {y0} V{c-20} M{x} {c+20} V{y1}", col) +
            f'<rect x="{x-8}" y="{c-20}" width="16" height="40" rx="3" fill="#fff" stroke="{col}" stroke-width="2"/>' +
            t(x + 14, c - 2, lab, 12, col) + t(x + 14, c + 14, val, 11.5, "#5e6963", 500))


def chassis(x, y):
    return ln(f"M{x} {y} v8 M{x-11} {y+8} h22 M{x-7} {y+13} h14 M{x-3} {y+18} h6", BLK, 2)


S = [f'<image href="data:image/jpeg;base64,{IMG}" x="{PX}" y="{PY}" width="{600*SC:.0f}" height="{600*SC:.0f}"/>']
P1, P2, P3, P4, P5 = PINX
GY = 790   # GNDレール
JY = 468   # OUT(1と5)をつなぐ線
ISY = 520  # IS線

# ピン番号ラベル(写真の上)
for x, n, nm, col in zip(PINX, "12345", ("OUT", "IN", "Vbb", "IS", "OUT"), (ORG, GRN, RED, PUR, ORG)):
    S.append(f'<circle cx="{x:.1f}" cy="{PINY:.1f}" r="15" fill="none" stroke="{col}" stroke-width="3"/>')
    S.append(t(x - 18, PINY - 22, f"{n} {nm}", 13, col, 700, "end" if n in "12" else "start") if False else "")

# ---- 12V: バッテリー → ヒューズ → タブ ----
S.append('<rect x="980" y="24" width="150" height="56" rx="6" fill="#3a3f44"/>')
S.append(t(1055, 58, "バッテリー 12V", 14, "#fff", 700, "middle").replace("stroke:#fff", "stroke:#3a3f44"))
S.append(ln(f"M980 52 H920 M880 52 H{TAB[0]+60:.0f} L{TAB[0]:.0f} {TAB[1]:.0f}", RED, 6))
S.append('<rect x="880" y="42" width="40" height="20" rx="4" fill="#fff4c9" stroke="#b08a1c" stroke-width="1.6"/>')
S.append(t(900, 36, "ヒューズ 5A", 12, "#8a6a24", 700, "middle"))
S.append(f'<circle cx="{TAB[0]:.0f}" cy="{TAB[1]:.0f}" r="9" fill="{RED}"/>')
S.append(t(TAB[0] + 70, 100, "タブ(=3番) 12V入力", 15, RED))
S.append(t(TAB[0] + 70, 120, "導通があれば3番ピンからでもよい", 12, "#5e6963", 500))
S.append(ln("M1130 52 H1160 V70", BLK, 3) + chassis(1160, 70))
S.append(t(1160, 112, "−は車体へ", 11.5, "#5e6963", 500, "middle"))

# ---- 1と5 → ランプ ----
S.append(ln(f"M{P1:.1f} {PINY+15:.1f} V{JY}", ORG, 5))
S.append(ln(f"M{P5:.1f} {PINY+15:.1f} V{JY}", ORG, 5))
S.append(hline_hops(P1, 1040, JY, [P2] if SIMPLE else [P2, P4], ORG, 5))
S.append(f'<circle cx="{P5:.1f}" cy="{JY}" r="5" fill="{ORG}"/>')
S.append(t(820, JY - 12, "1と5をつないでランプの+へ", 14, ORG))
S.append(f'<circle cx="1062" cy="{JY}" r="22" fill="#fff6d6" stroke="#b08a1c" stroke-width="2"/>'
         f'<path d="M1046 {JY-16} L1078 {JY+16} M1078 {JY-16} L1046 {JY+16}" stroke="#b08a1c" stroke-width="1.8"/>')
S.append(t(1062, JY + 44, "ランプ", 14, "#212723", 700, "middle"))
S.append(ln(f"M1084 {JY} H1120 V{JY+16}", BLK, 3) + chassis(1120, JY + 16))
S.append(t(1120, JY + 56, "車体へ", 11.5, "#5e6963", 500, "middle"))

# ---- 3番ピン(使わない) ----
S.append(t(P3, PINY + 40, "3:何もつながない", 11.5, RED, 700, "middle") if False else "")

# ---- 2 IN → R_IN → Q1 C ----
QX, QY = 236, 650           # Q1 の中心
CX_, EX_ = QX + 14, QX + 14
S.append(ln(f"M{P2:.1f} {PINY+15:.1f} V560 H360", GRN))
S.append(res_h(268, 360, 560, "R_IN", "1kΩ", GRN))
S.append(ln(f"M268 560 H{CX_} V{QY-24}", GRN))
# Q1
S.append(f'<circle cx="{QX+4}" cy="{QY}" r="26" fill="#fff" stroke="#333" stroke-width="1.8"/>')
S.append(ln(f"M{QX-12} {QY-15} V{QY+15}", "#333", 3.5))
S.append(ln(f"M{QX-12} {QY-6} L{CX_} {QY-24}", "#333", 2.2))
S.append(ln(f"M{QX-12} {QY+6} L{EX_} {QY+24} V{GY}", "#333", 2.2))
S.append(f'<path d="M{EX_} {QY+24} l-10 -2 l5 -8 z" fill="#333"/>')
S.append(t(QX + 40, QY - 2, "Q1", 13) + t(QX + 40, QY + 14, "2SC1815", 11.5, "#5e6963", 500))
S.append(t(CX_ + 6, QY - 30, "C", 11.5, "#333") + t(QX - 30, QY - 8, "B", 11.5, "#333") + t(EX_ + 6, QY + 36, "E", 11.5, "#333"))
# ベース ← R_B ← ESP GPIO
S.append(ln(f"M{QX-12} {QY} H190", GRN))
S.append(f'<circle cx="190" cy="{QY}" r="4" fill="{GRN}"/>')
S.append(res_h(120, 190, QY, "R_B", "10kΩ", GRN))
S.append(res_v(190, QY, GY, "R_BE", "47kΩ", "#5e6963"))

# ---- 4 IS → R_IS / R_S → ESP ADC ----
if SIMPLE:
    S.append(t(P4 + 22, PINY + 44, "4番(IS)は今回つながない", 13, PUR))
else:
  if True:
    S.append(ln(f"M{P4:.1f} {PINY+15:.1f} V{ISY}", PUR))
    S.append(f'<circle cx="{P4:.1f}" cy="{ISY}" r="5" fill="{PUR}"/>')
    S.append(hline_hops(120, P4, ISY, [P2], PUR, 2.6))
    S.append(f'<rect x="150" y="{ISY-8}" width="40" height="16" rx="3" fill="#fff" stroke="{PUR}" stroke-width="2"/>')
    S.append(t(170, ISY - 14, "R_S", 12, PUR, 700, "middle") + t(170, ISY + 26, "10kΩ", 11.5, "#5e6963", 500, "middle"))
    S.append(res_v(P4, ISY, GY, "R_IS", "1kΩ", PUR))

# ---- ESP ----
S.append(f'<rect x="10" y="470" width="110" height="{GY-440}" rx="8" fill="#2b5d8a"/>')
S.append(t(65, 496, "ESP32", 15, "#fff", 700, "middle").replace("stroke:#fff", "stroke:#2b5d8a"))
for y, s in (((QY, "GPIO"), (GY - 10, "GND")) if SIMPLE else ((ISY, "ADC"), (QY, "GPIO"), (GY - 10, "GND"))):
    S.append(t(112, y + 4, s, 12, "#fff", 700, "end").replace("stroke:#fff", "stroke:#2b5d8a"))
if not SIMPLE: S.append(t(65, ISY + 22, "3.3Vクランプ", 10.5, "#cfe0f0", 500, "middle").replace("stroke:#fff", "stroke:#2b5d8a"))

# ---- GNDレール ----
S.append(ln(f"M120 {GY-10} H140 V{GY} H1120 V{GY+4}", BLK, 3) + chassis(1120, GY + 4))
for x in ((190, EX_) if SIMPLE else (190, EX_, P4)):
    S.append(f'<circle cx="{x:.1f}" cy="{GY}" r="4.5" fill="{BLK}"/>')
S.append(t(640, GY + 24, "GND(ESPのGNDと車体をつなぐ)", 13, BLK, 700, "middle"))
SVG = f'<svg viewBox="0 0 1200 830" role="img" aria-label="変換基板の写真の各ピンから、バッテリー、トランジスタ、ESP32、ランプへの配線を描いた図">{"".join(S)}</svg>'

src_css = open(os.path.join(HERE, "gen_universal_board.py"), encoding="utf-8").read()
CSS = src_css[src_css.index('CSS = """') + 9: src_css.index('"""', src_css.index('CSS = """') + 9)]
CSS += "\n  .panel svg { min-width: 900px; }\n"

IS_ROW = ('<tr><td>4</td><td style="color:#7a4bb0;font-weight:700">IS</td><td>今回は何もつながない(電流を読むときに使う)</td></tr>' if SIMPLE else
          '<tr><td>4</td><td style="color:#7a4bb0;font-weight:700">IS</td><td>R_IS 1kΩでGNDへ。同じ点からR_S 10kΩを通してESPのADCへ</td></tr>')
TITLE = "まず1灯を点ける配線" if SIMPLE else "BTSのピンごとの配線"
LEAD = ("ランプ1個をESP32で点けたり消したりするだけの配線です。電流を読むIS(4番)は使わないので、部品はトランジスタ1個と抵抗3本だけです。" if SIMPLE else
        "手元の変換基板の写真の、下に並ぶ5本のピン(左から1〜5)とタブから、それぞれの行き先までを線で描きました。丸で囲んだのが各ピンで、色は線の種類と同じです。")
BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / BTS6143D PIN WIRING</p>
  <h1>{TITLE}</h1>
  <p class="lead">{LEAD}</p>
  <div class="panel">{SVG}</div>
  <div class="tbl-wrap" style="margin-top:16px"><table>
    <thead><tr><th>ピン</th><th>名前</th><th>つなぐ先</th></tr></thead>
    <tbody>
      <tr><td>タブ(3)</td><td style="color:{RED};font-weight:700">Vbb 12V</td><td>ヒューズ5Aを通してバッテリーの+へ。3番ピンは何もつながなくてよい</td></tr>
      <tr><td>1・5</td><td style="color:{ORG};font-weight:700">OUT</td><td>2本をつないで、ランプの+へ。ランプの−は車体へ</td></tr>
      <tr><td>2</td><td style="color:{GRN};font-weight:700">IN</td><td>R_IN 1kΩ → トランジスタQ1のC。Q1のBはR_B 10kΩを通してESPのGPIO、EはGND</td></tr>
      {IS_ROW}
    </tbody>
  </table></div>
  <p class="note" style="margin-top:12px">線が半円でまたいでいる所は、つながっていません。黒い点がある所だけがつながっています。</p>
</div>
"""
html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{TITLE}</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
