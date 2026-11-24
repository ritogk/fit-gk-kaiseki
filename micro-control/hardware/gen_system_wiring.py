#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESP32-S3 込みの全体配線図(最小構成8ch・BTS6143D正ピン版)を生成する。
出力: system-wiring-8ch.html
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
ch・GPIO(CTRL)・ヒューズ・電線は gen_minimal_chase.py の CH 表と同じ。
IS用のADCピン(GPIO1〜8 = ADC1_CH0〜7)は今回の仮割り当て。
各BTSモジュールの中身(Q1・抵抗5本)は bts-wiring.html / bts-board.html を参照。
"""
import io, os, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "system-wiring-8ch.html")
RED, ORG, GRY, GRN, PUR, BLK = "var(--w-pos)", "var(--w-out)", "var(--w-gnd)", "var(--w-in)", "var(--w-is)", "#2b2b2b"

CH = [  # gen_minimal_chase.py と同じ並び
    (1, "左前ウィンカー", 10, 1, "5A", "0.75sq"),
    (2, "左ハイビーム", 11, 2, "7.5A", "1.25sq"),
    (3, "右ハイビーム", 12, 3, "7.5A", "1.25sq"),
    (4, "右前ウィンカー", 13, 4, "5A", "0.75sq"),
    (5, "右後ウィンカー", 14, 5, "5A", "0.75sq"),
    (6, "右バックランプ", 15, 6, "5A", "0.75sq"),
    (7, "左バックランプ", 16, 7, "5A", "0.75sq"),
    (8, "左後ウィンカー", 17, 8, "5A", "0.75sq"),
]
CIR = "①②③④⑤⑥⑦⑧"


def t(x, y, s, cls="t-lab", anchor="start", extra=""):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" {extra}>{s}</text>'


def ln(d, col, w=2):
    return f'<path d="{d}" stroke="{col}" stroke-width="{w}" fill="none" stroke-linejoin="round"/>'


def chassis(x, y, col=BLK):
    return (f'<path d="M{x} {y} v6 M{x-10} {y+6} h20 M{x-6} {y+11} h12 M{x-2} {y+16} h4" '
            f'stroke="{col}" stroke-width="2" fill="none" stroke-linecap="round"/>')


def fuse(x, y, lab):
    return (f'<rect x="{x-14}" y="{y-7}" width="28" height="14" rx="3" fill="#fff4c9" stroke="#b08a1c" stroke-width="1.4"/>'
            + t(x, y - 11, lab, "t-cap", "middle", 'style="font-size:10px;font-weight:700"'))


Y0, DY = 170, 74
ys = [Y0 + i * DY for i in range(len(CH))]
YL = ys[-1]
S = []
BUSX = 930
GBX = 330  # 共通GNDバス

# ---- バッテリー・メインヒューズ・B+バス ----
S.append('<rect x="840" y="28" width="110" height="52" rx="6" fill="#3a3f44"/>')
S.append(t(895, 58, "バッテリー 12V", "t-cap", "middle", 'style="fill:#fff;font-weight:700"'))
S.append(ln("M940 28 V14 H990 V110", RED, 5))
S.append(f'<rect x="976" y="85" width="28" height="14" rx="3" fill="#fff4c9" stroke="#b08a1c" stroke-width="1.4"/>' + t(970, 96, "20A", "t-cap", "end", 'style="font-size:10px;font-weight:700"'))
S.append(ln(f"M990 110 V122 H{BUSX} V{YL-30}", RED, 6))
S.append(t(BUSX + 12, 140, "B+バス", "t-cap", "start", f'style="fill:{RED};font-weight:700"'))
S.append(ln("M850 80 V96", BLK, 3) + chassis(850, 96))
S.append(t(864, 110, "車体GND", "t-cap"))

# ---- ESP32-S3 ----
S.append(f'<rect x="30" y="{Y0-90}" width="170" height="{YL-Y0+180}" rx="8" fill="#2b5d8a"/>')
S.append(t(115, Y0 - 62, "ESP32-S3", "t-ti", "middle", 'style="fill:#fff"'))
S.append(t(115, Y0 - 44, "USBでMacから給電", "t-cap", "middle", 'style="fill:#cfe0f0"'))
for (n, name, g_ctrl, g_is, fz, wr), y in zip(CH, ys):
    S.append(t(192, y - 10, f"GPIO{g_ctrl}", "t-cap", "end", 'style="fill:#fff;font-size:10.5px"'))
    S.append(t(192, y + 8, f"GPIO{g_is}", "t-cap", "end", 'style="fill:#cfe0f0;font-size:10.5px"'))
S.append(t(192, YL + 72, "GND", "t-cap", "end", 'style="fill:#fff;font-weight:700"'))
# ESPのGND → 共通GNDバス
S.append(ln(f"M200 {YL+68} H{GBX} V{ys[0]+14}", BLK, 2.6))
S.append(ln(f"M{GBX} {YL+68} V{YL+90} H700 V{YL+96}", BLK, 2.6) + chassis(700, YL + 96))
S.append(t(500, YL + 84, "ESPのGNDと車体GNDをつなぐ(共通GND)", "t-cap", "middle", 'style="font-weight:700"'))
# ADC保護
S.append(f'<rect x="232" y="{Y0-40}" width="54" height="{YL-Y0+70}" rx="5" fill="#f1ebf8" stroke="#a58bc9" stroke-dasharray="4 3"/>')
S.append(t(259, Y0 - 46, "ADC保護", "t-cap", "middle", f'style="fill:{PUR};font-weight:700"'))

# ---- 各ch ----
MX0, MX1 = 390, 540
for (n, name, g_ctrl, g_is, fz, wr), y in zip(CH, ys):
    # 信号
    S.append(ln(f"M200 {y-14} H{MX0}", GRN, 2.2))
    S.append(ln(f"M200 {y+4} H{MX0}", PUR, 2.2))
    S.append(f'<path d="M252 {y+4} l10 -6 v12 z M262 {y-2} v12" fill="{PUR}" stroke="{PUR}" stroke-width="1.5"/>')
    S.append(ln(f"M{GBX} {y+18} H{MX0}", BLK, 1.8))
    S.append(f'<circle cx="{GBX}" cy="{y+18}" r="3.5" fill="{BLK}"/>')
    # モジュール
    S.append(f'<rect x="{MX0}" y="{y-26}" width="{MX1-MX0}" height="52" rx="5" fill="var(--epoxy)" stroke="var(--epoxy-line)" stroke-width="1.5"/>')
    S.append(t(MX0 + 8, y - 8, f"BTSモジュール{CIR[n-1]}", "t-cap", "start", 'style="font-weight:700;font-size:11.5px"'))
    S.append(t(MX0 + 8, y + 9, "Q1+BTS6143D", "t-cap", "start", 'style="font-size:10px"'))
    for yy, nm, col in ((y - 14, "CTRL", GRN), (y + 4, "IS", PUR), (y + 18, "GND", BLK)):
        S.append(t(MX0 - 4, yy - 3, nm, "t-cap", "end", f'style="font-size:8.5px;fill:{col}"') if False else "")
    # 12V(B+バス → chヒューズ → モジュール上)
    S.append(ln(f"M{BUSX} {y-38} H{(MX0+MX1)//2} V{y-26}", RED, 3.5))
    S.append(f'<circle cx="{BUSX}" cy="{y-38}" r="4" fill="{RED}"/>')
    S.append(fuse(800, y - 38, fz))
    # OUT → 灯具 → 車体
    S.append(ln(f"M{MX1} {y+4} H660", ORG, 3.5))
    S.append(t(600, y + 0, wr, "t-cap", "middle", 'style="font-size:9.5px"'))
    S.append(f'<circle cx="674" cy="{y+4}" r="14" fill="#fff6d6" stroke="#b08a1c" stroke-width="1.6"/>'
             f'<path d="M664 {y-6} L684 {y+14} M684 {y-6} L664 {y+14}" stroke="#b08a1c" stroke-width="1.3"/>')
    S.append(ln(f"M688 {y+4} H706 V{y+10}", BLK, 2) + chassis(706, y + 10))
    S.append(t(726, y + 9, f"{CIR[n-1]} {name}", "t-cap", "start", 'style="font-weight:700"'))

# 凡例
S.append(t(MX0, Y0 - 80, "CTRL(緑)", "t-cap", "start", f'style="fill:{GRN};font-weight:700"'))
S.append(t(MX0 + 70, Y0 - 80, "IS(紫)", "t-cap", "start", f'style="fill:{PUR};font-weight:700"'))
S.append(t(MX0 + 125, Y0 - 80, "GND(黒)", "t-cap", "start", 'style="font-weight:700"'))
S.append(t(MX0, Y0 - 64, "モジュールの左側から上の順に入る", "t-cap", "start", 'style="font-size:10.5px"'))
SVG = f'<svg viewBox="0 0 1010 {YL+120}" role="img" aria-label="ESP32-S3、8個のBTSモジュール、ヒューズ、灯具、バッテリーをつないだ全体配線図">{"".join(S)}</svg>'

src_css = open(os.path.join(HERE, "gen_universal_board.py"), encoding="utf-8").read()
CSS = src_css[src_css.index('CSS = """') + 9: src_css.index('"""', src_css.index('CSS = """') + 9)]
CSS = CSS.replace("--w-pos: #c2443a;", "--w-pos: #c2443a; --w-out: #e07a1c; --w-in: #2f8a4f; --w-is: #7a4bb0;")
CSS += "\n  .panel svg { min-width: 860px; }\n"

rows = "".join(
    f'<tr><td>{CIR[n-1]}</td><td>{name}</td><td>GPIO{g}</td><td>GPIO{gi}(ADC1_CH{gi-1})</td><td>{fz}</td><td>{wr}</td></tr>'
    for n, name, g, gi, fz, wr in CH)

BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / SYSTEM WIRING 8CH</p>
  <h1>全体配線図(ESP32-S3込み・8ch)</h1>
  <p class="lead">最小構成8chの全体を、BTS6143Dの正しいピン配置で描き直した図です。ESP32-S3から各BTSモジュールへ信号3本(CTRL・IS・GND)を出し、モジュールはB+バスからchヒューズを通った12Vを灯具へ流します。</p>

  <h2>1. 全体の配線</h2>
  <p class="note">電気の道は2本です。電力の道は、バッテリー → 20Aメインヒューズ → B+バス → chヒューズ → BTSモジュール → 灯具 → 車体GNDと流れます。指示の道は、ESP32-S3のGPIOからモジュールのCTRLへ入り、モジュールの中のトランジスタがBTSのINをGNDへ落としてONにします。ISは灯具の電流を電圧にして返す線で、ESP側のADC保護(ダイオード)を通ってADCピンに入ります。</p>
  <div class="panel">{SVG}</div>

  <h2>2. chごとの割り当て</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>ch</th><th>灯具</th><th>CTRL(ON/OFF)</th><th>IS(電流の読み取り)</th><th>chヒューズ</th><th>電線</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <p class="note" style="margin-top:12px">CTRLのGPIO10〜17とヒューズ・電線は、最小構成8chの結線図と同じです。ISのGPIO1〜8は今回の仮の割り当てで、ESP32-S3でADCとして使える範囲から選びました。ISを使わずに点灯だけ試す段階では、IS線はつながなくても動きます。</p>

  <h2>3. 1つのモジュールの中身</h2>
  <p class="note">各BTSモジュールの中は同じで、トランジスタQ1、抵抗5本(R_B 10kΩ・R_BE 47kΩ・R_IN 1kΩ・R_IS 1kΩ・R_S 10kΩ)、BTS6143Dでできています。回路は bts-wiring.html、ユニバーサル基板上の配置は bts-board.html にあります。BTSの1番と5番(OUT)はモジュールの中でつなぎ、12Vはタブ(3番)から入れます。</p>

  <div class="warn"><b>ESPのGNDと車体GNDは必ずつないでください。</b>つながっていないと、モジュールのトランジスタがINをGNDへ落とせず、灯具が点きません。ESPをMacのUSBで給電する間は、MacのGNDも車体GNDとつながることになるので、Macを充電器につないだまま作業しないでください(推測)。</div>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>全体配線図 8ch</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
