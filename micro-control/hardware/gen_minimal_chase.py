#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小構成(8ch・ぐるぐる点灯の初回実験用)の結線図を生成する。
出力: minimal-chase-8ch.html
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
17ch確定設計(full-wiring-17ch / board-layout-17ch)から、
ハイビーム・ウィンカー4灯・バックランプの8chだけを抜き出し、
切替リレー・CAN・2台目ESP・DCDC・監視タップを省いた「差し替え式」の仮設構成。
"""
import io, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minimal-chase-8ch.html")

# ぐるぐるの順番(上から見て時計回り・左前スタート)
# (順番, 略号, 名前, 種別, GPIO, ヒューズ, 電線, 上面図の座標)
CH = [
    (1, "WIN-FL", "左前ウィンカー",   "win",  10, "5A",   "0.75sq", (168, 112)),
    (2, "HI-L",   "左ハイビーム",     "head", 11, "7.5A", "1.25sq", (222, 88)),
    (3, "HI-R",   "右ハイビーム",     "head", 12, "7.5A", "1.25sq", (298, 88)),
    (4, "WIN-FR", "右前ウィンカー",   "win",  13, "5A",   "0.75sq", (352, 112)),
    (5, "WIN-RR", "右後ウィンカー",   "win",  14, "5A",   "0.75sq", (352, 528)),
    (6, "BK-R",   "右バックランプ",   "back", 15, "5A",   "0.75sq", (298, 552)),
    (7, "BK-L",   "左バックランプ",   "back", 16, "5A",   "0.75sq", (222, 552)),
    (8, "WIN-RL", "左後ウィンカー",   "win",  17, "5A",   "0.75sq", (168, 528)),
]
CIRCLED = "①②③④⑤⑥⑦⑧"
STEP_MS = 200
LAP_MS = STEP_MS * len(CH)


def chassis(x, y, color="var(--w-neg)", s=1.0):
    w1, w2, w3 = 22 * s, 14 * s, 7 * s
    return (f'<path d="M{x} {y} V{y+4} M{x-w1} {y+4} H{x+w1} M{x-w2} {y+10} H{x+w2} '
            f'M{x-w3} {y+16} H{x+w3}" stroke="{color}" stroke-width="2" fill="none"/>')


def sqtag(x, y, label, color="var(--w-pos)"):
    w = 10 + sum(11 if ord(c) > 0x2000 else 6.5 for c in label)
    return (f'<g aria-hidden="true"><rect x="{x-w/2:.0f}" y="{y-11}" width="{w:.0f}" height="16" rx="8" '
            f'fill="var(--surface)" stroke="{color}" stroke-width="1.2"/>'
            f'<text x="{x}" y="{y+1}" text-anchor="middle" font-size="10" '
            f'font-family="ui-monospace, SF Mono, Menlo, monospace" fill="{color}">{label}</text></g>')


# ============ 図1: 上面図(ぐるぐるの順番・アニメーション) ============
T = []
T.append('<rect x="150" y="60" width="220" height="520" rx="70" fill="var(--box)" stroke="var(--box-line)" stroke-width="1.6"/>')
T.append('<rect x="178" y="190" width="164" height="120" rx="18" fill="none" stroke="var(--box-line)" stroke-width="1.2"/>')
T.append('<rect x="178" y="350" width="164" height="110" rx="18" fill="none" stroke="var(--box-line)" stroke-width="1.2"/>')
T.append('<text class="t-cap" x="260" y="44" text-anchor="middle">▲ 車両前方</text>')
T.append('<text class="t-cap" x="260" y="612" text-anchor="middle">車両後方</text>')
# 回転方向の矢印(時計回り)
T.append('<defs><marker id="arw" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0 L10 5 L0 10 z" fill="var(--accent)"/></marker></defs>')
T.append('<path d="M420 200 V440" stroke="var(--accent)" stroke-width="2" stroke-dasharray="6 6" fill="none" marker-end="url(#arw)"/>')
T.append('<path d="M100 440 V200" stroke="var(--accent)" stroke-width="2" stroke-dasharray="6 6" fill="none" marker-end="url(#arw)"/>')
T.append('<text class="t-cap" x="432" y="326" fill="var(--accent)">時計回り</text>')
for n, code, name, kind, gpio, fuse, wire, (x, y) in CH:
    delay = (n - 1) * STEP_MS
    T.append(f'<circle class="lamp k-{kind}" cx="{x}" cy="{y}" r="15" style="animation-delay:{delay}ms"/>')
    left = x < 260
    lx = x - 26 if left else x + 26
    anchor = "end" if left else "start"
    ly = y - 22 if y < 300 else y + 34
    if code.startswith("HI"):
        lx, anchor, ly = x, "middle", y + 40
    if code.startswith("BK"):
        lx, anchor, ly = x, "middle", y - 46
    T.append(f'<text class="t-num" x="{lx}" y="{ly}" text-anchor="{anchor}">{CIRCLED[n-1]}</text>')
    sub_y = ly + 16
    label = name.replace("ハイビーム", "ハイ").replace("バックランプ", "バック") if code[:2] in ("HI", "BK") else name
    T.append(f'<text class="t-cap" x="{lx}" y="{sub_y}" text-anchor="{anchor}">{label}</text>')
topview = (f'<svg viewBox="0 0 520 640" role="img" aria-label="上面図 ぐるぐる点灯の順番">'
           + "".join(T) + "</svg>")

# ============ 図2: 結線図(8行) ============
S = []
ROW0, DY = 190, 72
last = ROW0 + DY * (len(CH) - 1)
H = last + 150
W = 1260

# 見出し行
for x, t in [(330, "B+バス"), (405, "chヒューズ"), (580, "ハイサイドSW"),
             (760, "自作出力"), (880, "差し替え"), (1000, "灯具")]:
    S.append(f'<text class="t-cap" x="{x}" y="132" text-anchor="middle" font-weight="700">{t}</text>')

# バッテリー・メインヒューズ・B+バス
S.append(f'''
<g>
  <rect class="box" x="250" y="20" width="160" height="50" rx="8"/>
  <text class="t-ti" x="330" y="44" text-anchor="middle">車載バッテリー 12V</text>
  <text class="t-cap" x="330" y="61" text-anchor="middle">+ 端子直近から取る</text>
  <path d="M330 70 V84" stroke="var(--w-vcc)" stroke-width="3" fill="none"/>
  <rect class="box" x="306" y="84" width="48" height="24" rx="4"/>
  <text class="t-pin" x="330" y="100" text-anchor="middle">20A</text>
  <text class="t-cap" x="364" y="100">メイン(インライン・防水)</text>
  <path class="halo" d="M330 108 V{last-10}"/>
  <path d="M330 108 V{last-10}" stroke="var(--w-vcc)" stroke-width="3" fill="none"/>
  {sqtag(330, 150, "2.0sq", "var(--w-vcc)")}
  <path d="M410 45 H470 V64" stroke="var(--w-neg)" stroke-width="2.4" fill="none"/>
  <text class="t-cap" x="478" y="40">− 端子 → GNDバスバー</text>
  {chassis(470, 64, "var(--w-neg)", 0.7)}
</g>
''')

# Mac と ESP
S.append(f'''
<g>
  <rect class="box" x="40" y="20" width="160" height="60" rx="10"/>
  <text class="t-ti" x="120" y="46" text-anchor="middle">Mac</text>
  <text class="t-cap" x="120" y="66" text-anchor="middle">操作アプリ / シリアル</text>
  <path d="M120 80 V{ROW0-40}" stroke="var(--w-pwm)" stroke-width="2" fill="none"/>
  <text class="t-cap" x="128" y="112">USB(電源+指示)</text>
  <rect class="box" x="40" y="{ROW0-40}" width="160" height="{last-ROW0+80}" rx="12"/>
  <text class="t-ti" x="110" y="{(ROW0+last)//2-8}" text-anchor="middle">ESP32-S3</text>
  <text class="t-cap" x="110" y="{(ROW0+last)//2+12}" text-anchor="middle">1台だけ</text>
  <text class="t-cap" x="110" y="{(ROW0+last)//2+30}" text-anchor="middle">USB給電(DCDC不要)</text>
  <path d="M120 {last+40} V{last+62}" stroke="var(--w-gnd)" stroke-width="2" fill="none"/>
  <text class="t-pin" x="128" y="{last+56}">GND</text>
  {chassis(120, last+62, "var(--w-gnd)", 0.6)}
  <text class="t-cap" x="150" y="{last+80}">GNDバスバーへ(全GND共通)</text>
</g>
''')

for i, (n, code, name, kind, gpio, fuse, wire, _) in enumerate(CH):
    y = ROW0 + DY * i
    yv, yi = y - 10, y + 10
    S.append(f'''
<g>
  <text class="t-pin" x="192" y="{yi+4}" text-anchor="end">GPIO{gpio}</text>
  <path d="M200 {yi} H322 a8 8 0 0 1 16 0 H520" stroke="var(--w-pwm)" stroke-width="2" stroke-dasharray="7 5" fill="none"/>
  <path d="M480 {yi} V{yi+12}" stroke="var(--w-gnd)" stroke-width="1.4" fill="none"/>
  <rect x="476" y="{yi+12}" width="8" height="14" fill="var(--surface)" stroke="var(--w-gnd)" stroke-width="1.2"/>
  <path d="M480 {yi+26} V{yi+30} M474 {yi+30} H486" stroke="var(--w-gnd)" stroke-width="1.4" fill="none"/>
  <circle cx="480" cy="{yi}" r="2.6" fill="var(--w-pwm)"/>
  <circle cx="330" cy="{yv}" r="3.4" fill="var(--w-vcc)"/>
  <path class="halo" d="M330 {yv} H520"/>
  <path d="M330 {yv} H380 M430 {yv} H520" stroke="var(--w-vcc)" stroke-width="2.4" fill="none"/>
  <rect class="box" x="380" y="{yv-11}" width="50" height="22" rx="4"/>
  <text class="t-pin" x="405" y="{yv+4}" text-anchor="middle">{fuse}</text>
  <rect class="box" x="520" y="{y-26}" width="120" height="52" rx="6"/>
  <text class="t-pin" x="527" y="{yv+4}">Vbb</text>
  <text class="t-pin" x="527" y="{yi+4}">IN</text>
  <text class="t-pin" x="634" y="{y+4}" text-anchor="end">OUT</text>
  <text class="t-cap" x="586" y="{y-30}" text-anchor="middle">BTS6143D</text>
  <path class="halo" d="M640 {y} H990"/>
  <path d="M640 {y} H858 M902 {y} H985" stroke="var(--w-pos)" stroke-width="2.4" fill="none"/>
  {sqtag(760, y, wire)}
  <rect x="858" y="{y-9}" width="44" height="18" rx="4" fill="var(--surface)" stroke="var(--w-pos)" stroke-width="1.4"/>
  <text class="t-pin" x="880" y="{y+4}" text-anchor="middle">⇄</text>
  <circle class="lamp-static k-{kind}" cx="1000" cy="{y}" r="15"/>
  <path d="M989 {y-11} L1011 {y+11} M989 {y+11} L1011 {y-11}" stroke="var(--ink)" stroke-width="1.4" opacity="0.55"/>
  <path d="M1015 {y} H1140 V{y+8}" stroke="var(--w-neg)" stroke-width="2" fill="none"/>
  {chassis(1140, y+8, "var(--w-neg)", 0.55)}
  <text class="t-num" x="1030" y="{y-8}">{CIRCLED[n-1]}</text>
  <text class="t-lab" x="1052" y="{y-8}">{name}</text>
  <text class="t-cap" x="1170" y="{y+22}">ボディアース</text>
</g>
''')

S.append(f'<text class="t-cap" x="492" y="{last+64}" text-anchor="end">10kΩ プルダウン(全ch)</text>')
S.append(f'<text class="t-cap" x="520" y="{last+64}">BTSのGNDピン → GNDバスバー</text>')
S.append(f'<text class="t-cap" x="880" y="{last+66}" text-anchor="middle">⇄=純正カプラーを抜いて自作配線を差す</text>')

wiring = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="最小構成 8ch 結線図">'
          + "".join(S) + "</svg>")

# ============ 図3: 実体配線図(実物の見た目に近い配置) ============
P = 8
BB_W, BB_H = 544, 176


def hx(x0, c):
    return x0 + 24 + c * P


def row_y(y0, r):
    return y0 + 48 + r * P if r < 5 else y0 + 104 + (r - 5) * P


def rail_y(y0, which):
    return {"t+": y0 + 16, "t-": y0 + 24, "b+": y0 + 152, "b-": y0 + 160}[which]


def breadboard(x0, y0):
    s = [f'<rect x="{x0}" y="{y0}" width="{BB_W}" height="{BB_H}" rx="6" fill="#ebe7d8" stroke="#c2bda7" stroke-width="1.5"/>',
         f'<rect x="{x0+4}" y="{y0+88}" width="{BB_W-8}" height="12" fill="#d9d4c0"/>']
    for yy, col in ((y0 + 9, "#d64545"), (y0 + 31, "#4568d6"), (y0 + 145, "#d64545"), (y0 + 167, "#4568d6")):
        s.append(f'<line x1="{x0+16}" y1="{yy}" x2="{x0+BB_W-16}" y2="{yy}" stroke="{col}" stroke-width="1.6"/>')
    holes = []
    for c in range(63):
        x = hx(x0, c)
        if c % 6 != 5:
            for w in ("t+", "t-", "b+", "b-"):
                holes.append(f'M{x-1.4} {rail_y(y0, w)-1.4}h2.8v2.8h-2.8z')
        for r in range(10):
            holes.append(f'M{x-1.4} {row_y(y0, r)-1.4}h2.8v2.8h-2.8z')
    s.append(f'<path d="{"".join(holes)}" fill="#8a8570"/>')
    return "".join(s)


def badge(x, y, text, danger=False):
    w = 12 * len(text) + 18
    col = "var(--danger)" if danger else "#2f8659"
    return (f'<rect x="{x}" y="{y}" width="{w}" height="21" rx="10" fill="{col}"/>'
            f'<text x="{x+w/2}" y="{y+15}" text-anchor="middle" '
            f'style="font:700 11.5px Hiragino Sans,sans-serif" fill="#fff">{text}</text>')


def screw(cx, cy):
    return (f'<circle cx="{cx}" cy="{cy}" r="5.5" fill="#d9ded9" stroke="#5a6a5a" stroke-width="1.2"/>'
            f'<line x1="{cx-3.5}" y1="{cy}" x2="{cx+3.5}" y2="{cy}" stroke="#5a6a5a" stroke-width="1.5"/>')


def term1(cx, cy, label):
    return (f'<rect x="{cx-16}" y="{cy-12}" width="32" height="24" rx="3" fill="#2e7d4f" stroke="#1b5433"/>'
            + screw(cx, cy)
            + f'<text x="{cx+20}" y="{cy+4}" style="font:600 9px Menlo,monospace" fill="#d6eadc">{label}</text>')


R = []
RW, RH = 1300, 1160
FUSE_COLOR = {"5A": ("#d8b48a", "#9c7a52", "5"), "7.5A": ("#8a5a2b", "#5c3a18", "7.5")}
WIRE_W = {"0.75sq": 2.6, "1.25sq": 3.4}
RED, ORG, BLK = "#c8322a", "#e07a1c", "#2a2d31"
cxs = [390 + i * 72 for i in range(12)]

# --- ヒューズボックス(12連・バスバー内蔵) ---
fx0, fy0, fx1, fy1 = 336, 58, 1262, 176
R.append(f'<rect x="{fx0}" y="{fy0}" width="{fx1-fx0}" height="{fy1-fy0}" rx="10" fill="#2a2d32" stroke="#101215" stroke-width="1.5"/>')
R.append(f'<rect x="{fx0+12}" y="{fy0+10}" width="{fx1-fx0-80}" height="7" rx="3" fill="#b9a46a"/>')
R.append(f'<text x="{fx0+16}" y="{fy0+32}" style="font:9px Hiragino Sans,sans-serif" fill="#8f979f">内蔵バスバー(全スロットに12Vを配る)</text>')
for i, cx in enumerate(cxs):
    R.append(f'<rect x="{cx-17}" y="{fy0+40}" width="34" height="48" rx="4" fill="#17191c"/>')
    R.append(f'<circle cx="{cx+22}" cy="{fy0+46}" r="3" fill="#4a2020"/>')
    if i < len(CH):
        n, code, name, kind, gpio, fuse, wire, _ = CH[i]
        body, edge, num = FUSE_COLOR[fuse]
        R.append(f'<rect x="{cx-13}" y="{fy0+44}" width="26" height="40" rx="4" fill="{body}" stroke="{edge}" stroke-width="1.2"/>')
        R.append(f'<rect x="{cx-9}" y="{fy0+50}" width="18" height="6" rx="1.5" fill="{edge}" opacity="0.45"/>')
        R.append(f'<text x="{cx}" y="{fy0+76}" text-anchor="middle" style="font:700 11px Menlo,monospace" fill="#fff">{num}</text>')
        R.append(f'<text x="{cx}" y="{fy0-8}" text-anchor="middle" class="t-num">{CIRCLED[i]}</text>')
    else:
        R.append(f'<text x="{cx}" y="{fy0+68}" text-anchor="middle" style="font:9px Hiragino Sans,sans-serif" fill="#6b737b">予備</text>')
    R.append(screw(cx, fy0 + 104))
R.append(f'<rect x="{fx1-52}" y="{fy0+12}" width="40" height="22" rx="4" fill="#8d9499" stroke="#5f666b"/>')
R.append(f'<text x="{fx1-32}" y="{fy0+27}" text-anchor="middle" style="font:700 9px Menlo,monospace" fill="#fff">B+</text>')
R.append(f'<text class="t-ti" x="{fx0}" y="{fy0-30}">ヒューズボックス 12連(バスバー付き・平型ATO)</text>')
R.append(badge(fx0 + 360, fy0 - 46, "無はんだ"))

# --- BTS基板(ユニバーサル基板・カートリッジ8本) ---
bx0, by0, bx1, by1 = 296, 252, 948, 478
R.append(f'<rect x="{bx0}" y="{by0}" width="{bx1-bx0}" height="{by1-by0}" rx="6" fill="#25603a" stroke="#153a22" stroke-width="1.5"/>')
dots = []
for gx in range(int((bx1 - bx0) / 12) - 1):
    for gy in range(int((by1 - by0) / 12) - 1):
        dots.append(f'M{bx0+8+gx*12} {by0+8+gy*12}h1.6v1.6h-1.6z')
R.append(f'<path d="{"".join(dots)}" fill="#1b4a2c"/>')
for i in range(len(CH)):
    cx = cxs[i]
    R.append(term1(cx, 282, "Vbb"))
    R.append(f'<rect x="{cx-28}" y="{302}" width="56" height="70" rx="4" fill="#a33636" stroke="#6e1f1f"/>')
    R.append(f'<rect x="{cx-15}" y="{309}" width="30" height="9" fill="#8d9499"/>')
    R.append(f'<rect x="{cx-13}" y="{318}" width="26" height="24" rx="2" fill="#17191c"/>')
    for k in range(3):
        R.append(f'<rect x="{cx-10+k*8}" y="{342}" width="4" height="8" fill="#c9a13b"/>')
    R.append(f'<text x="{cx}" y="{364}" text-anchor="middle" style="font:600 8px Menlo,monospace" fill="#ffd9d9">BTS6143D</text>')
    R.append(term1(cx, 400, "OUT"))
# 信号ヘッダ(左端)+ プルダウン
hdr_y = [300 + k * 17 for k in range(9)]
R.append(f'<rect x="{bx0+8}" y="{hdr_y[0]-8}" width="12" height="{hdr_y[-1]-hdr_y[0]+16}" rx="2" fill="#111"/>')
for k, y in enumerate(hdr_y):
    R.append(f'<rect x="{bx0+12}" y="{y-2}" width="4" height="4" fill="#c9a13b"/>')
    lab = f"IN{CIRCLED[k]}" if k < 8 else "GND"
    R.append(f'<text x="{bx0-6}" y="{y+4}" text-anchor="end" style="font:9px Menlo,monospace" fill="var(--muted)">{lab}</text>')
    if k < 8:
        R.append(f'<rect x="{bx0+26}" y="{y-3}" width="16" height="6" rx="2.5" fill="#d8c49a" stroke="#b8a478" stroke-width="0.8"/>')
        R.append(f'<rect x="{bx0+30}" y="{y-3}" width="2" height="6" fill="#7a4a1a"/><rect x="{bx0+34}" y="{y-3}" width="2" height="6" fill="#111"/><rect x="{bx0+38}" y="{y-3}" width="2" height="6" fill="#e08a1c"/>')
R.append(f'<text x="{bx0+24}" y="{by1-30}" style="font:9px Hiragino Sans,sans-serif" fill="#cfe6d6">10kΩ×8(IN→GND)。IN①〜⑧は基板裏の配線で各BTSのINへ</text>')
R.append(term1(bx1 - 40, by1 - 22, "GND"))
R.append(f'<text class="t-ti" x="{bx0}" y="{by0-8}">BTS基板(ユニバーサル基板+差し替えカートリッジ×8)</text>')
R.append(badge(bx1 + 10, by0 + 4, "要はんだ", danger=True))

# --- ヒューズ → Vbb の配線(赤) ---
for i, (n, code, name, kind, gpio, fuse, wire, _) in enumerate(CH):
    cx = cxs[i]
    R.append(f'<path d="M{cx} {fy0+104} V{282}" stroke="{RED}" stroke-width="{WIRE_W[wire]}" fill="none" stroke-linecap="round"/>')
    R.append(sqtag(cx + 0.5, 204, wire, RED))

# --- OUT → 灯具カプラー(橙)。途中の波線=長い延長配線 ---
cy_cpl = 560
for i, (n, code, name, kind, gpio, fuse, wire, _) in enumerate(CH):
    cx = cxs[i]
    sw = WIRE_W[wire]
    R.append(f'<path d="M{cx} 400 V500 l-6 6 l12 6 l-6 6 V{cy_cpl-14}" stroke="{ORG}" stroke-width="{sw}" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')
    R.append(f'<rect x="{cx-18}" y="{cy_cpl-14}" width="36" height="28" rx="5" fill="#9aa1a6" stroke="#5f666b" stroke-width="1.2"/>')
    R.append(f'<rect x="{cx-11}" y="{cy_cpl-6}" width="7" height="10" fill="#e8c33a"/><rect x="{cx+4}" y="{cy_cpl-6}" width="7" height="10" fill="#e8c33a"/>')
    R.append(f'<path d="M{cx+18} {cy_cpl} H{cx+26} V{cy_cpl+26}" stroke="{BLK}" stroke-width="2.4" fill="none"/>')
    R.append(f'<circle cx="{cx+26}" cy="{cy_cpl+30}" r="4.5" fill="none" stroke="#8d9499" stroke-width="2.4"/>')
    R.append(f'<text x="{cx}" y="{cy_cpl+52}" text-anchor="middle" class="t-num">{CIRCLED[i]}</text>')
    for kw in ("ウィンカー", "ハイビーム", "バックランプ"):
        if kw in name:
            pos, typ = name.replace(kw, ""), kw.replace("バックランプ", "バック")
    R.append(f'<text x="{cx}" y="{cy_cpl+68}" text-anchor="middle" style="font:10.5px Hiragino Sans,sans-serif" fill="var(--ink)">{pos}</text>')
    R.append(f'<text x="{cx}" y="{cy_cpl+82}" text-anchor="middle" style="font:10.5px Hiragino Sans,sans-serif" fill="var(--ink)">{typ}</text>')
R.append(f'<text class="t-cap" x="{cxs[0]-22}" y="{cy_cpl+104}">波線=車体内を数m延長 / 灰色の箱=灯具の純正カプラーへ差すカプラー / 丸端子=灯具の−をボディアースへ</text>')

# --- バッテリー・メイン20A・GNDバスバー(右) ---
btx, bty = 1060, 640
R.append(f'<rect x="{btx}" y="{bty}" width="200" height="120" rx="8" fill="#2f3237" stroke="#15171a" stroke-width="1.5"/>')
R.append(f'<rect x="{btx}" y="{bty}" width="200" height="22" rx="8" fill="#3d4147"/>')
R.append(f'<rect x="{btx+28}" y="{bty-14}" width="28" height="16" rx="3" fill="{RED}"/>')
R.append(f'<rect x="{btx+144}" y="{bty-14}" width="28" height="16" rx="3" fill="#1d1f22"/>')
R.append(f'<text x="{btx+42}" y="{bty+40}" text-anchor="middle" style="font:700 15px Menlo" fill="#ff8a80">+</text>')
R.append(f'<text x="{btx+158}" y="{bty+40}" text-anchor="middle" style="font:700 15px Menlo" fill="#c9ced3">−</text>')
R.append(f'<text x="{btx+100}" y="{bty+84}" text-anchor="middle" style="font:700 13px Hiragino Sans" fill="#e6eae7">車載バッテリー 12V</text>')
# + → メイン20A → ヒューズボックス B+
R.append(f'<path d="M{btx+42} {bty-14} V560" stroke="{RED}" stroke-width="5" fill="none"/>')
R.append(f'<rect x="{btx+30}" y="{488}" width="24" height="72" rx="8" fill="#1d1f22"/>')
R.append(f'<rect x="{btx+34}" y="{508}" width="16" height="30" rx="3" fill="#f2c230" stroke="#b08a10"/>')
R.append(f'<text x="{btx+42}" y="{527}" text-anchor="middle" style="font:700 8px Menlo" fill="#5a4500">20</text>')
R.append(f'<text class="t-lab" x="{btx+66}" y="{518}">メイン20A</text>')
R.append(f'<text class="t-cap" x="{btx+66}" y="{534}">インライン防水ホルダー</text>')
R.append(f'<text class="t-cap" x="{btx+66}" y="{548}">バッテリー+の直近に</text>')
R.append(f'<path d="M{btx+42} 488 V228 H1288 V{fy0+23} H{fx1-12}" stroke="{RED}" stroke-width="5" fill="none" stroke-linejoin="round"/>')
R.append(sqtag(btx + 42, 440, "2.0sq", RED))
# GNDバスバー
gbx, gby = 1060, 840
R.append(f'<rect x="{gbx}" y="{gby}" width="200" height="40" rx="5" fill="#b9bec6" stroke="#82878e" stroke-width="1.5"/>')
for k in range(8):
    R.append(f'<circle cx="{gbx+18+k*23.5}" cy="{gby+20}" r="6" fill="#dde1e6" stroke="#70757c"/>')
    R.append(f'<line x1="{gbx+14+k*23.5}" y1="{gby+20}" x2="{gbx+22+k*23.5}" y2="{gby+20}" stroke="#70757c" stroke-width="1.6"/>')
R.append(f'<text class="t-ti" x="{gbx}" y="{gby+62}">GNDバスバー</text>')
R.append(f'<text class="t-cap" x="{gbx}" y="{gby+80}">ここで一点にまとめてバッテリー−へ</text>')
R.append(f'<path d="M{btx+158} {bty-14} V{bty-30} H{btx+230} V{gby+20} H{gbx+206}" stroke="{BLK}" stroke-width="5" fill="none" stroke-linejoin="round"/>')
R.append(f'<path d="M{bx1-40} {by1-10} V{by1+8} H990 V{gby+20} H{gbx}" stroke="{BLK}" stroke-width="2.6" fill="none" stroke-linejoin="round"/>')
R.append(sqtag(990, 720, "0.75sq", BLK))

# --- ブレッドボード2枚+ESP32-S3(左下) ---
ubx, uby = 30, 716
lbx, lby = 30, 892
R.append(breadboard(ubx, uby))
R.append(breadboard(lbx, lby))
yA, yB = row_y(uby, 9), row_y(lby, 0)
c0, npin = 4, 20
exl, exr = hx(ubx, c0) - 8, hx(ubx, c0 + npin - 1) + 8
for c in range(npin):
    x = hx(ubx, c0 + c)
    R.append(f'<rect x="{x-1.8}" y="{yA-2.5}" width="3.6" height="5" fill="#c9a13b"/>')
    R.append(f'<rect x="{x-1.8}" y="{yB-2.5}" width="3.6" height="5" fill="#c9a13b"/>')
R.append(f'<rect x="{exl}" y="{yA-6}" width="{exr-exl}" height="{yB-yA+12}" rx="7" fill="#1b1f26" stroke="#000" stroke-width="1.5"/>')
R.append(f'<rect x="{exl+12}" y="{yA+12}" width="62" height="{yB-yA-30}" rx="4" fill="#3d444d" stroke="#565e68"/>')
R.append(f'<rect x="{exl+12}" y="{yA+12}" width="16" height="{yB-yA-30}" fill="#2c323a"/>')
R.append(f'<rect x="{exr-6}" y="{yA+18}" width="22" height="16" rx="6" fill="#aeb6bf" stroke="#7d858e"/>')
R.append(f'<text x="{exl+84}" y="{(yA+yB)/2-2}" style="font:700 11px Menlo" fill="#dfe3e8">ESP32-S3</text>')
R.append(f'<text x="{exl+84}" y="{(yA+yB)/2+12}" style="font:8.5px Hiragino Sans" fill="#9aa2ac">2枚跨ぎ</text>')
R.append(f'<text class="t-ti" x="{ubx}" y="{uby-14}">ブレッドボード830×2(ESPを跨がせる)</text>')
R.append(badge(ubx + 330, uby - 32, "無はんだ"))
# ジャンパ(GPIO列 → BTS基板の信号ヘッダ)
JCOL = ["#2f6fb2", "#2f8659", "#7e58be", "#c07a16", "#2f6fb2", "#2f8659", "#7e58be", "#c07a16"]
gcols = [c0 + 2 + k * 2 for k in range(8)]
for k, c in enumerate(gcols):
    x = hx(ubx, c)
    y0 = row_y(uby, 5)
    ty = hdr_y[k]
    R.append(f'<circle cx="{x}" cy="{y0}" r="2.6" fill="{JCOL[k]}"/>')
    R.append(f'<path d="M{x} {y0} C{x} {y0-150}, {bx0-60} {ty}, {bx0+12} {ty}" stroke="{JCOL[k]}" stroke-width="2" fill="none" stroke-linecap="round"/>')
gx_ = hx(ubx, c0 + npin - 2)
y0 = row_y(uby, 5)
R.append(f'<circle cx="{gx_}" cy="{y0}" r="2.6" fill="{BLK}"/>')
R.append(f'<path d="M{gx_} {y0} C{gx_} {y0-120}, {bx0-40} {hdr_y[8]}, {bx0+12} {hdr_y[8]}" stroke="{BLK}" stroke-width="2" fill="none" stroke-linecap="round"/>')
R.append(f'<text class="t-lab" x="30" y="300">ジャンパ線(オス-メス)</text>')
R.append(f'<text class="t-cap" x="30" y="316">GPIO10〜17 → IN①〜⑧</text>')
R.append(f'<text class="t-cap" x="30" y="330">ESPのGND → GND</text>')
# USB → Mac
R.append(f'<path d="M{exr+16} {yA+26} H{640} V{1030}" stroke="#8d9499" stroke-width="5" fill="none" stroke-linejoin="round"/>')
R.append(f'<rect x="{600}" y="{1030}" width="160" height="92" rx="8" fill="#d5d9dd" stroke="#9aa1a6" stroke-width="1.5"/>')
R.append(f'<rect x="{612}" y="{1040}" width="136" height="64" rx="3" fill="#3a3f45"/>')
R.append(f'<rect x="{584}" y="{1122}" width="192" height="10" rx="4" fill="#bcc1c6"/>')
R.append(f'<text x="680" y="1076" text-anchor="middle" style="font:700 12px Hiragino Sans" fill="#e6eae7">Mac</text>')
R.append(f'<text class="t-cap" x="{652}" y="{970}">USB-C(UART側)</text>')
R.append(f'<text class="t-cap" x="{652}" y="{984}">給電と指示を兼ねる</text>')

realview = (f'<svg viewBox="0 0 {RW} {RH}" role="img" aria-label="最小構成 8ch 実体配線図">'
            + "".join(R) + "</svg>")

# ============ 表 ============
rows = "".join(
    f'<tr><td class="sig">{CIRCLED[n-1]}</td><td>{name}<br><span class="muted">{code}</span></td>'
    f'<td class="sig">GPIO{gpio}</td><td class="sig">{fuse}</td><td class="sig">{wire}</td>'
    f'<td class="sig">{(n-1)*STEP_MS} ms</td></tr>'
    for n, code, name, kind, gpio, fuse, wire, _ in CH)

CSS = """
  :root {
    color-scheme: light;
    --bg: #f2f4f3; --surface: #ffffff; --box: #f5f7f6; --box-line: #c3cdc8;
    --ink: #212723; --muted: #5e6963; --line: #dbe1de; --accent: #a87413; --dot: #e2e7e4;
    --w-pwm: #2f6fb2; --w-vcc: #c07a16; --w-gnd: #78827c; --w-pos: #c2443a; --w-neg: #464d49;
    --off: #e3e7e5; --on-head: #fff4c2; --on-head-line: #c9a227;
    --on-win: #f59e0b; --on-back: #ffffff; --on-back-line: #8fa39a;
    --danger: #b3372c; --danger-bg: #fbeeec; --danger-line: #ecc9c4;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
    font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Noto Sans JP", system-ui, sans-serif;
    font-size: 14.5px; line-height: 1.75; -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 1240px; margin: 0 auto; padding: 40px 16px 64px; }
  .eyebrow { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 11.5px;
    letter-spacing: 0.08em; color: var(--accent); margin: 0 0 6px; }
  h1 { font-size: 25px; font-weight: 700; margin: 0 0 10px; line-height: 1.4; }
  .lead { color: var(--muted); margin: 0; max-width: 50em; }
  .lead b { color: var(--ink); }
  h2 { font-size: 16.5px; font-weight: 700; margin: 44px 0 14px; display: flex; align-items: center; gap: 10px; }
  h2::before { content: ""; width: 5px; height: 18px; border-radius: 2px; background: var(--accent); flex: none; }
  p.note { margin: 0 0 12px; max-width: 52em; }
  .muted { color: var(--muted); font-size: 12px; }
  .panel { background: var(--surface);
    background-image: radial-gradient(var(--dot) 1px, transparent 1px); background-size: 22px 22px;
    border: 1px solid var(--line); border-radius: 10px; overflow-x: auto; padding: 10px 6px; }
  .panel svg { display: block; width: 100%; height: auto; }
  .panel.wide svg { min-width: 1080px; }
  .split { display: grid; grid-template-columns: minmax(260px, 380px) 1fr; gap: 20px; align-items: start; }
  @media (max-width: 820px) { .split { grid-template-columns: 1fr; } }
  svg .box { fill: var(--box); stroke: var(--box-line); stroke-width: 1.5; }
  svg .t-ti { font: 700 14px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--ink); }
  svg .t-pin { font: 11px ui-monospace, "SF Mono", Menlo, monospace; fill: var(--ink); }
  svg .t-lab { font: 12.5px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--ink); }
  svg .t-cap { font: 11px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--muted); }
  svg .t-num { font: 700 16px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--accent); }
  svg .halo { stroke: var(--w-vcc); opacity: 0.13; stroke-width: 11; fill: none; stroke-linecap: round; }
  svg .lamp, svg .lamp-static { stroke-width: 2; }
  svg .lamp { fill: var(--off); stroke: var(--box-line); }
  svg .lamp-static.k-head { fill: var(--on-head); stroke: var(--on-head-line); }
  svg .lamp-static.k-win { fill: var(--on-win); stroke: #b45309; }
  svg .lamp-static.k-back { fill: var(--on-back); stroke: var(--on-back-line); }
  @media (prefers-reduced-motion: no-preference) {
    svg .lamp { animation: chase LAPms linear infinite; }
  }
  @media (prefers-reduced-motion: reduce) {
    svg .lamp.k-head { fill: var(--on-head); } svg .lamp.k-win { fill: var(--on-win); }
    svg .lamp.k-back { fill: var(--on-back); }
  }
  svg .lamp.k-head { --on: var(--on-head); --onl: var(--on-head-line); }
  svg .lamp.k-win  { --on: var(--on-win);  --onl: #b45309; }
  svg .lamp.k-back { --on: var(--on-back); --onl: var(--on-back-line); }
  @keyframes chase {
    0%   { fill: var(--on); stroke: var(--onl); }
    12%  { fill: var(--on); stroke: var(--onl); }
    30%  { fill: var(--off); stroke: var(--box-line); }
    100% { fill: var(--off); stroke: var(--box-line); }
  }
  .legend { display: flex; flex-wrap: wrap; gap: 8px 20px; margin: 10px 2px 0; font-size: 12.5px; color: var(--muted); }
  .legend span { display: inline-flex; align-items: center; gap: 7px; }
  .legend i { width: 18px; height: 4px; border-radius: 2px; display: inline-block; }
  .legend i.dash { background: repeating-linear-gradient(90deg, var(--w-pwm) 0 5px, transparent 5px 9px); }
  .tbl-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
  table { border-collapse: collapse; width: 100%; min-width: 620px; font-size: 13.5px; }
  th, td { text-align: left; padding: 9px 14px; border-top: 1px solid var(--line); vertical-align: top; }
  thead th { border-top: none; font-size: 12px; color: var(--muted); font-weight: 600; padding-top: 12px; padding-bottom: 8px; }
  td.sig { white-space: nowrap; font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 12.5px; }
  ol.flow { margin: 0; padding-left: 24px; max-width: 52em; }
  ol.flow li { margin: 8px 0; }
  .warn { border: 1px solid var(--danger-line); background: var(--danger-bg); border-radius: 10px;
    padding: 12px 16px; margin-top: 14px; max-width: 52em; }
  .warn b { color: var(--danger); }
  @media print { .panel { overflow: visible; } svg .lamp { animation: none; } }
""".replace("LAPms", f"{LAP_MS}ms")

BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / MINIMAL 8CH CHASE</p>
  <h1>最小構成 8ch — 車の周りを光がぐるぐる回る初回実験</h1>
  <p class="lead">ハイビーム左右・ウィンカー4灯・バックランプ左右の<b>8灯だけ</b>を、ESP32-S3 1台とハイサイドSW(BTS6143D)8個で制御する構成です。
  17ch確定設計から<b>切替リレー・CAN・2台目のESP・DCDC・監視タップを外し</b>、灯具の純正カプラーを抜いて自作配線を差し替える仮設方式にしています。
  純正に戻すときはカプラーを差し戻すだけです。<b>停車中・パーキングでの実験専用</b>です。</p>

  <h2>ぐるぐるの順番</h2>
  <div class="split">
    <div class="panel">{topview}</div>
    <div>
      <p class="note">上から見て時計回りに、左前ウィンカーから1灯ずつ点けていきます。1灯の点灯時間は{STEP_MS}msなので、8灯で1周{LAP_MS/1000:.1f}秒になります。左の図は実際の速さで動いています。</p>
      <p class="note">ロービームは使いません。ロービームはHIDなので、点滅させるとバラストを傷め、消してから再点灯するまで数秒かかるためです。前方の「ヘッドライト」役はハイビームが担います。</p>
      <p class="note">ウィンカーやバックランプが電球(ハロゲン)の場合、点灯と消灯に数十msの遅れが出るため、光の尾を引くような見え方になります。LEDなら切れのよい動きになります。</p>
      <div class="tbl-wrap"><table>
        <thead><tr><th>順</th><th>灯具</th><th>ESPピン</th><th>chヒューズ</th><th>電線</th><th>点灯開始</th></tr></thead>
        <tbody>{rows}</tbody>
      </table></div>
    </div>
  </div>

  <h2>結線図</h2>
  <p class="note">電気の道は2本です。1本目は電力の道で、バッテリー → 20Aメインヒューズ → B+バス → chヒューズ → BTS6143D → 灯具 → ボディアースと流れます。2本目は指示の道で、Mac → USB → ESP32-S3 → 各BTSのINピンへ、点ける・消す・明るさの指示を送ります。ESPは電力を流さないので、USB給電だけで動きます。</p>
  <div class="panel wide">{wiring}</div>
  <div class="legend">
    <span><i style="background:var(--w-vcc)"></i>12V電源(B+)</span>
    <span><i style="background:var(--w-pos)"></i>自作出力(BTS → 灯具+)</span>
    <span><i style="background:var(--w-neg)"></i>灯具−・バッテリー−</span>
    <span><i class="dash"></i>指示線(3.3V・PWM)</span>
    <span><i style="background:var(--w-gnd)"></i>小信号GND</span>
    <span>指示線の小さな山形=B+バスと交差するだけで接続していない</span>
  </div>

  <h2>実体配線図</h2>
  <p class="note">上の結線図と同じ回路を、実物の見た目と置き場所に近い形で描いたものです。ヒューズの色は平型ヒューズの規格色(5A=タン、7.5A=茶、20A=黄)にそろえ、電線は太さに比例した線幅で描いています。</p>
  <p class="note">はんだ付けが要るのはBTS基板だけです。ヒューズボックス・バスバー・ブレッドボードは、ねじ止めと差し込みだけで組めます。BTSは差し替え式のカートリッジなので、壊れたときはソケットから抜いて交換できます。なお、ESPのピンの並び(ジャンパを挿す列)は説明用の配置なので、実物はボードの印字でGPIO10〜17を確かめてから挿してください。</p>
  <div class="panel wide">{realview}</div>
  <div class="legend">
    <span><i style="background:#c8322a"></i>12V電源(B+・ヒューズ → Vbb)</span>
    <span><i style="background:#e07a1c"></i>自作出力(OUT → 灯具)</span>
    <span><i style="background:#2a2d31"></i>GND・バッテリー−・灯具−</span>
    <span><i style="background:#2f6fb2"></i>ジャンパ線(信号・色は見分け用)</span>
    <span><i style="background:#8d9499"></i>USBケーブル</span>
  </div>

  <h2>17ch確定設計との違い</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>部品・機能</th><th>17ch確定設計</th><th>最小構成</th><th>省ける理由</th></tr></thead>
    <tbody>
      <tr><td>ESP32-S3</td><td class="sig">2台</td><td class="sig">1台</td><td>8chなら1台のピンで足りる</td></tr>
      <tr><td>私設CAN(トランシーバ×2)</td><td>あり</td><td>なし</td><td>前後のESP間通信が要らない</td></tr>
      <tr><td>BTS6143D</td><td class="sig">17</td><td class="sig">8</td><td>制御する灯具が8灯</td></tr>
      <tr><td>切替リレー(8chモジュール)</td><td class="sig">17ch分</td><td>なし</td><td>純正線と同時につながないので、純正との切替が要らない</td></tr>
      <tr><td>監視タップ(100k/22k+ツェナー)</td><td class="sig">17組</td><td>なし</td><td>純正側が通電しない(カプラーを抜いている)ので見張る対象がない</td></tr>
      <tr><td>DCDC 12V→5V</td><td>あり</td><td>なし</td><td>ESPはMacのUSBから給電する</td></tr>
      <tr><td>IN の10kΩプルダウン</td><td>—</td><td class="sig">8本(追加)</td><td>USBを抜いた瞬間や起動中にINが浮いて誤点灯するのを防ぐ</td></tr>
    </tbody>
  </table></div>

  <h2>やる順番</h2>
  <ol class="flow">
    <li>実車で8灯のバルブ規格と消費電流を確認します。特に、バックランプが左右2灯あるか、ハイビームがLEDかハロゲンかを確かめます。ハロゲンのハイビーム(60W級=約5A)だと7.5Aヒューズでは余裕が少ないため、ヒューズと電線を一段太くします。</li>
    <li>各灯具の純正カプラーと同じ規格の「カプラー付き配線(メス側)」を8本用意します。純正線は切らず、差し替えだけで済ませるためです。</li>
    <li>机上で1chだけ組みます。12V電源 → 5Aヒューズ → BTS6143D → テスト用電球で、ESPから点灯・消灯・調光ができることを確かめます。</li>
    <li>8chに増やし、机上でぐるぐるの点灯パターンを確かめます。ESPの起動直後とUSBを抜いた直後に、全chが消えたままであることも確かめます。</li>
    <li>実車では、エンジンを止めてキーを抜いてから8灯のカプラーを差し替えます。メイン20Aヒューズは最後に入れます。</li>
    <li>終わったら、メイン20Aヒューズを抜いてから8灯のカプラーを純正に差し戻し、ウィンカー・ハザード・ハイビーム・バックランプが純正どおり点くかを確かめます。</li>
  </ol>

  <div class="warn"><b>この構成のまま走行しないでください。</b>差し替え中の8灯は純正の操作では点かないため、ウィンカーとバックランプが働かなくなります。ブレーキランプとテールランプは触らないので純正のままです。</div>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>最小構成 8ch ぐるぐる点灯</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
