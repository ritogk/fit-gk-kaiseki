# -*- coding: utf-8 -*-
# 実装レイアウト図(ブレッドボード仮設構成・実体配置)の生成スクリプト
# 図の修正はこのスクリプトを編集して再実行する。HTML直接編集禁止。
import io, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "board-layout-17ch.html")

P = 8          # 2.54mm ピッチ = 8px
BB_W, BB_H = 544, 176

# ---------------- ブレッドボード ----------------
def hx(x0, c):  return x0 + 24 + c * P
def row_y(y0, r):
    # r: 0-4 = a-e, 5-9 = f-j
    return y0 + 48 + r * P if r < 5 else y0 + 104 + (r - 5) * P
def rail_y(y0, which):
    # "t+","t-","b+","b-"
    return {"t+": y0 + 16, "t-": y0 + 24, "b+": y0 + 152, "b-": y0 + 160}[which]

def breadboard(x0, y0, label=""):
    s = [f'<rect x="{x0}" y="{y0}" width="{BB_W}" height="{BB_H}" rx="6" '
         f'fill="#e7e3d4" stroke="#c2bda7" stroke-width="1.5"/>']
    # 中央溝
    s.append(f'<rect x="{x0+4}" y="{y0+88}" width="{BB_W-8}" height="12" fill="#d6d1bd"/>')
    # レール線
    for yy, col in ((y0+9, "#d64545"), (y0+31, "#4568d6"), (y0+145, "#d64545"), (y0+167, "#4568d6")):
        s.append(f'<line x1="{x0+16}" y1="{yy}" x2="{x0+BB_W-16}" y2="{yy}" stroke="{col}" stroke-width="1.6"/>')
    holes = []
    for c in range(63):
        x = hx(x0, c)
        if c % 6 != 5:  # レールは5穴グループ
            for w in ("t+", "t-", "b+", "b-"):
                holes.append(f'M{x-1.4} {rail_y(y0,w)-1.4}h2.8v2.8h-2.8z')
        for r in range(10):
            holes.append(f'M{x-1.4} {row_y(y0,r)-1.4}h2.8v2.8h-2.8z')
    s.append(f'<path d="{"".join(holes)}" fill="#8a8570"/>')
    if label:
        s.append(f'<text class="t-cap" x="{x0+2}" y="{y0-6}">{label}</text>')
    return "".join(s)

# ---------------- 汎用パーツ ----------------
def badge(x, y, text, danger=False):
    w = 12 * len(text) + 18
    col = "var(--danger)" if danger else "var(--w-en)"
    return (f'<rect x="{x}" y="{y}" width="{w}" height="21" rx="10" fill="{col}"/>'
            f'<text x="{x+w/2}" y="{y+15}" text-anchor="middle" '
            f'style="font:700 11.5px Hiragino Sans,sans-serif" fill="#fff">{text}</text>')

def jumper(x1, y1, x2, y2, color, sag=16, w=2):
    mx, my = (x1 + x2) / 2, max(y1, y2) + sag
    return f'<path d="M{x1} {y1} Q{mx} {my} {x2} {y2}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'

def head(x, y, ang, color):
    return (f'<path d="M0 0 L-11 -4.5 L-11 4.5 Z" fill="{color}" '
            f'transform="translate({x} {y}) rotate({ang})"/>')

def flow(d, color, hx_, hy_, ang, label=None, lx=0, ly=0, dash=None, w=3):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    s = f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" opacity="0.85"{da}/>' + head(hx_, hy_, ang, color)
    if label:
        s += f'<text class="t-lab" x="{lx}" y="{ly}" fill="{color}">{label}</text>'
    return s

def resistor_v(x, y1, y2, bands):
    ym = (y1 + y2) / 2
    s = [f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="#9a9a9a" stroke-width="1.6"/>',
         f'<rect x="{x-4.5}" y="{ym-11}" width="9" height="22" rx="4" fill="#d8c49a" stroke="#b8a478" stroke-width="1"/>']
    for i, b in enumerate(bands):
        s.append(f'<rect x="{x-4.5}" y="{ym-8+i*5}" width="9" height="3" fill="{b}"/>')
    return "".join(s)

def zener_v(x, y1, y2):
    ym = (y1 + y2) / 2
    return (f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="#9a9a9a" stroke-width="1.6"/>'
            f'<rect x="{x-3.5}" y="{ym-8}" width="7" height="16" rx="3" fill="#3a2a20"/>'
            f'<rect x="{x-3.5}" y="{ym-6}" width="7" height="2.6" fill="#ddd"/>')

def dip(x0bb, y0bb, c0, ncols, name, sub=""):
    xl, xr = hx(x0bb, c0) - 5, hx(x0bb, c0 + ncols - 1) + 5
    yt, yb = row_y(y0bb, 4) - 3, row_y(y0bb, 5) + 3
    s = []
    for c in range(ncols):  # ピン
        x = hx(x0bb, c0 + c)
        s.append(f'<rect x="{x-1.6}" y="{row_y(y0bb,4)-2}" width="3.2" height="4" fill="#c9a13b"/>')
        s.append(f'<rect x="{x-1.6}" y="{row_y(y0bb,5)-2}" width="3.2" height="4" fill="#c9a13b"/>')
    s.append(f'<rect x="{xl}" y="{yt}" width="{xr-xl}" height="{yb-yt}" rx="3" fill="#23262b" stroke="#000"/>')
    s.append(f'<circle cx="{xl+7}" cy="{yt+7}" r="2.5" fill="#555"/>')
    s.append(f'<text x="{(xl+xr)/2}" y="{(yt+yb)/2+1}" text-anchor="middle" '
             f'style="font:600 10px Menlo,monospace" fill="#dfe3e8">{name}</text>')
    if sub:
        s.append(f'<text x="{(xl+xr)/2}" y="{(yt+yb)/2+13}" text-anchor="middle" '
                 f'style="font:9px Hiragino Sans,sans-serif" fill="#9aa2ac">{sub}</text>')
    return "".join(s)

def esp32(xA, yA, xB, yB, c0, npin, name):
    # 上段ボードの j 行(yA)と下段ボードの a 行(yB)に跨がせる
    xl, xr = hx(xA, c0) - 8, hx(xA, c0 + npin - 1) + 8
    s = []
    for c in range(npin):
        x = hx(xA, c0 + c)
        s.append(f'<rect x="{x-1.8}" y="{yA-2.5}" width="3.6" height="5" fill="#c9a13b"/>')
        s.append(f'<rect x="{x-1.8}" y="{yB-2.5}" width="3.6" height="5" fill="#c9a13b"/>')
    s.append(f'<rect x="{xl}" y="{yA-6}" width="{xr-xl}" height="{yB-yA+12}" rx="7" '
             f'fill="#1b1f26" stroke="#000" stroke-width="1.5"/>')
    # WROOM シールド缶
    s.append(f'<rect x="{xl+14}" y="{yA+14}" width="86" height="{yB-yA-40}" rx="4" fill="#3d444d" stroke="#565e68"/>')
    s.append(f'<rect x="{xl+14}" y="{yA+14}" width="20" height="{yB-yA-40}" fill="#2c323a"/>')  # アンテナ部
    # USB-C ×2
    s.append(f'<rect x="{xr-46}" y="{yA+10}" width="30" height="16" rx="6" fill="#aeb6bf" stroke="#7d858e"/>')
    s.append(f'<rect x="{xr-46}" y="{yB-26}" width="30" height="16" rx="6" fill="#aeb6bf" stroke="#7d858e"/>')
    s.append(f'<text x="{xr-52}" y="{yA+22}" text-anchor="end" style="font:8.5px Menlo" fill="#9aa2ac">UART(書込)</text>')
    s.append(f'<text x="{xr-52}" y="{yB-14}" text-anchor="end" style="font:8.5px Menlo" fill="#9aa2ac">OTG</text>')
    s.append(f'<text x="{xl+120}" y="{(yA+yB)/2-2}" style="font:700 12px Menlo" fill="#dfe3e8">{name}</text>')
    s.append(f'<text x="{xl+120}" y="{(yA+yB)/2+13}" style="font:9.5px Hiragino Sans" fill="#9aa2ac">Freenove Board Lite(2枚跨ぎ)</text>')
    return "".join(s)

def can_module(x0bb, y0bb, c0, note):
    # 1x4ヘッダを c 行に挿した SN65HVD230 モジュール(上に張り出す)
    xl = hx(x0bb, c0) - 6
    w = 10 * P + 12
    yb = row_y(y0bb, 2)
    yt = yb - 46
    s = [f'<line x1="{hx(x0bb,c0+2+i)}" y1="{yb}" x2="{hx(x0bb,c0+2+i)}" y2="{yt+38}" stroke="#c9a13b" stroke-width="2.4"/>' for i in range(4)]
    s.append(f'<rect x="{xl}" y="{yt}" width="{w}" height="40" rx="4" fill="#1c4f8a" stroke="#0e3057"/>')
    s.append(f'<rect x="{xl+6}" y="{yt+8}" width="18" height="14" rx="2" fill="#23262b"/>')
    s.append(f'<rect x="{xl+w-26}" y="{yt+6}" width="20" height="18" rx="2" fill="#2e7d4f"/>')  # CANH/L端子
    s.append(f'<text x="{xl+w/2-4}" y="{yt+18}" text-anchor="middle" style="font:600 9.5px Menlo" fill="#dfe8f4">SN65HVD230</text>')
    s.append(f'<text x="{xl+w/2-4}" y="{yt+31}" text-anchor="middle" style="font:8.5px Hiragino Sans" fill="#aac4e0">{note}</text>')
    return "".join(s), xl, yt

def wago(x, y, n, label=""):
    s = []
    for i in range(n):
        s.append(f'<rect x="{x+i*24}" y="{y}" width="20" height="28" rx="3" fill="#e07820" stroke="#a85510"/>')
        s.append(f'<rect x="{x+i*24+4}" y="{y+3}" width="12" height="8" rx="2" fill="#f5ead9"/>')
    if label:
        s.append(f'<text class="t-cap" x="{x}" y="{y-6}">{label}</text>')
    return "".join(s)

def relay_module(x, y, n, used, title, chnames, badge_on=True):
    w = 32 + n * 52
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="170" rx="8" fill="#134e7e" stroke="#0a3050" stroke-width="1.5"/>']
    for i in range(n):
        rx_ = x + 16 + i * 52
        # ねじ端子 NC/C/NO
        s.append(f'<rect x="{rx_}" y="{y+8}" width="44" height="22" rx="3" fill="#2e7d4f" stroke="#1b5433"/>')
        for k in range(3):
            s.append(f'<circle cx="{rx_+8+k*14}" cy="{y+19}" r="4" fill="#cfd8cf" stroke="#5a6a5a"/>')
        s.append(f'<text x="{rx_+22}" y="{y+41}" text-anchor="middle" style="font:8px Menlo" fill="#9fc4e4">NC C NO</text>')
        # リレー本体
        dim = ' opacity="0.4"' if i >= used else ""
        s.append(f'<g{dim}><rect x="{rx_}" y="{y+48}" width="44" height="52" rx="3" fill="#2456a8" stroke="#12315f"/>'
                 f'<text x="{rx_+22}" y="{y+70}" text-anchor="middle" style="font:600 8.5px Menlo" fill="#fff">SRD</text>'
                 f'<text x="{rx_+22}" y="{y+82}" text-anchor="middle" style="font:8px Menlo" fill="#cfe0ff">12VDC</text></g>')
        # オプトカプラ・LED
        s.append(f'<rect x="{rx_+6}" y="{y+112}" width="16" height="10" rx="1.5" fill="#111"/>')
        s.append(f'<circle cx="{rx_+36}" cy="{y+117}" r="3" fill="#d43a3a"/>')
    # 入力ヘッダ(オプト側 VCC は 3V3。JD-VCC はジャンパ除去して IG12V)
    hw = used * 11 + 34
    s.append(f'<rect x="{x+16}" y="{y+140}" width="{hw}" height="12" rx="2" fill="#111"/>')
    for i in range(used + 2):
        s.append(f'<rect x="{x+22+i*11}" y="{y+143}" width="3.4" height="6" fill="#c9a13b"/>')
    s.append(f'<text x="{x+24+hw}" y="{y+151}" style="font:8.5px Menlo" fill="#9fc4e4">IN1-{used} GND VCC←3V3</text>')
    # JD-VCCジャンパ
    s.append(f'<rect x="{x+w-42}" y="{y+140}" width="26" height="12" rx="2" fill="#e0c030"/>')
    s.append(f'<text x="{x+w-16}" y="{y+136}" text-anchor="end" style="font:8px Menlo" fill="#9fc4e4">JD-VCC←IG12V(ジャンパ除去)</text>')
    s.append(f'<text class="t-ti" x="{x}" y="{y-26}">{title}</text>')
    s.append(f'<text class="t-cap" x="{x}" y="{y-8}">{chnames}</text>')
    if badge_on:
        s.append(badge(x + w - 84, y - 44, "無はんだ"))
    return "".join(s), w

def bts_island(x, y, n, cols=5, title=""):
    rows = (n + cols - 1) // cols
    w, h = 40 + cols * 88, 90 + rows * 128
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#25603a" stroke="#153a22" stroke-width="1.5"/>']
    dots = []
    for gx in range(int(w / 12) - 1):
        for gy in range(int(h / 12) - 1):
            dots.append(f'M{x+8+gx*12} {y+8+gy*12}h1.6v1.6h-1.6z')
    s.append(f'<path d="{"".join(dots)}" fill="#1b4a2c"/>')
    for i in range(n):
        col, row = i % cols, i // cols
        ax, ay = x + 26 + col * 88, y + 52 + row * 128
        # ねじ端子(OUT) 上段は島の上端・下段は下端
        ty = y + 10 if row == 0 else y + h - 34
        s.append(f'<rect x="{ax+12}" y="{ty}" width="42" height="24" rx="3" fill="#2e7d4f" stroke="#1b5433"/>')
        s.append(f'<circle cx="{ax+24}" cy="{ty+12}" r="4.5" fill="#cfd8cf" stroke="#5a6a5a"/>')
        s.append(f'<circle cx="{ax+42}" cy="{ty+12}" r="4.5" fill="#cfd8cf" stroke="#5a6a5a"/>')
        # DPAK変換基板(赤)+ BTS6143D
        s.append(f'<rect x="{ax}" y="{ay}" width="66" height="74" rx="4" fill="#a33636" stroke="#6e1f1f"/>')
        s.append(f'<rect x="{ax+16}" y="{ay+8}" width="34" height="10" fill="#8d9499"/>')   # タブ(VS)
        s.append(f'<rect x="{ax+18}" y="{ay+18}" width="30" height="26" rx="2" fill="#17191c"/>')
        for k in range(3):
            s.append(f'<rect x="{ax+22+k*9}" y="{ay+44}" width="4" height="8" fill="#c9a13b"/>')
        s.append(f'<text x="{ax+33}" y="{ay+64}" text-anchor="middle" style="font:600 8.5px Menlo" fill="#ffd9d9">BTS6143D</text>')
    # 左端: 信号ヘッダ
    s.append(f'<rect x="{x+8}" y="{y+44}" width="10" height="{h-88}" rx="2" fill="#111"/>')
    s.append(f'<text x="{x+2}" y="{y+h/2}" style="font:9px Hiragino Sans" fill="#cfe6d6" '
             f'transform="rotate(90 {x+2} {y+h/2})">PWM×{n}・IS・GND ヘッダ</text>')
    s.append(f'<text class="t-ti" x="{x}" y="{y-26}">{title}</text>')
    s.append(badge(x + w - 96, y - 44, "要はんだ", danger=True))
    return "".join(s), w, h

def fuse_block(x, y, n, title, sub):
    h = 44 + n * 19
    s = [f'<rect x="{x}" y="{y}" width="190" height="{h}" rx="8" fill="#26292e" stroke="#101215"/>']
    for i in range(n):
        fy = y + 26 + i * 19
        s.append(f'<rect x="{x+24}" y="{fy}" width="56" height="13" rx="2.5" fill="#e8c33a" stroke="#a8871a"/>')
        s.append(f'<rect x="{x+34}" y="{fy+3}" width="8" height="7" fill="#d8d8d8"/>')
        s.append(f'<rect x="{x+62}" y="{fy+3}" width="8" height="7" fill="#d8d8d8"/>')
        s.append(f'<text x="{x+92}" y="{fy+11}" style="font:8.5px Menlo" fill="#aab2ba">{"5A ch%d" % (i+1) if i < n-2 else ("5A IGコイル" if i == n-2 else "予備")}</text>')
    s.append(f'<text class="t-ti" x="{x}" y="{y-26}">{title}</text>')
    s.append(f'<text class="t-cap" x="{x}" y="{y-8}">{sub}</text>')
    s.append(badge(x + 110, y - 44, "無はんだ"))
    return "".join(s), h

def bus_bar(x, y, title):
    s = [f'<rect x="{x}" y="{y}" width="190" height="40" rx="5" fill="#b9bec6" stroke="#82878e" stroke-width="1.5"/>']
    for i in range(8):
        s.append(f'<circle cx="{x+18+i*23}" cy="{y+20}" r="6" fill="#dde1e6" stroke="#70757c"/>')
        s.append(f'<line x1="{x+14+i*23}" y1="{y+20}" x2="{x+22+i*23}" y2="{y+20}" stroke="#70757c" stroke-width="1.6"/>')
    s.append(f'<text class="t-ti" x="{x}" y="{y-8}">{title}</text>')
    return "".join(s)

def dcdc(x, y):
    s = [f'<rect x="{x}" y="{y}" width="150" height="72" rx="6" fill="#1c4f8a" stroke="#0e3057" stroke-width="1.5"/>',
         f'<rect x="{x+14}" y="{y+14}" width="34" height="26" rx="3" fill="#e8c33a"/>',   # インダクタ
         f'<circle cx="{x+70}" cy="{y+27}" r="13" fill="#17191c" stroke="#444"/>',        # 電解コン
         f'<text x="{x+75}" y="{y+60}" text-anchor="middle" style="font:600 9px Menlo" fill="#dfe8f4">GYVRM 8-40V→5V 5A</text>',
         # 裸線 → WAGO
         f'<path d="M{x-4} {y+20} h-24" stroke="#c0392b" stroke-width="3"/>',
         f'<path d="M{x-4} {y+34} h-24" stroke="#26292e" stroke-width="3"/>',
         f'<path d="M{x+154} {y+20} h24" stroke="#c0392b" stroke-width="3"/>',
         f'<path d="M{x+154} {y+34} h24" stroke="#26292e" stroke-width="3"/>']
    s.append(wago(x - 76, y + 12, 2))
    s.append(wago(x + 182, y + 12, 2))
    s.append(f'<text class="t-ti" x="{x-76}" y="{y-10}">DCDC 12V→5V(IP68・WAGO接続)</text>')
    s.append(badge(x + 240, y + 44, "無はんだ"))
    return "".join(s)

def twist(x, y, color):
    return (f'<path d="M{x} {y} L{x+8} {y+16} M{x+8} {y} L{x} {y+16}" '
            f'stroke="{color}" stroke-width="2" fill="none"/>')

# ---------------- ユニット1枚分の SVG ----------------
def unit_svg(front):
    n = 10 if front else 7
    labels = (["ローR", "ローL", "ハイR", "ハイL", "フォグR", "フォグL", "ポジR", "ポジL", "WFR", "WFL"]
              if front else
              ["テールR", "テールL", "ブレーキR", "ブレーキL", "WRR", "WRL", "ハイM"])
    uname = "前ユニット — ESP32-S3 ①(10ch)" if front else "後ユニット — ESP32-S3 ②(7ch)"
    S = []

    # ==== ブレッドボード3枚(左列) ====
    bbA, bbB, bbC = (40, 130), (40, 310), (40, 560)
    S.append(breadboard(*bbA, "BB-1(830点)"))
    S.append(breadboard(*bbB, "BB-2(830点) — BB-1と密着させてESPを跨がせる"))
    S.append(breadboard(*bbC, "BB-3(830点) — 分圧タップ×%d" % n))
    S.append(badge(500, 100, "無はんだ"))

    # ESP32(BB-1のj行 と BB-2のa行に跨ぐ)
    S.append(esp32(bbA[0], row_y(bbA[1], 9), bbB[0], row_y(bbB[1], 0), 4, 22,
                   "ESP32-S3 ①" if front else "ESP32-S3 ②"))

    # CAN モジュール(BB-2 右側)
    canS, canx, cany = can_module(bbB[0], bbB[1], 33, "終端120Ω実装品×2で両端終端")
    S.append(canS)
    # ESP⇔CANモジュール ジャンパ4本(3V3・GND・CTX・CRX)
    for i, col in enumerate(("#c0392b", "#26548a", "var(--w-pwm)", "var(--w-pwm)")):
        S.append(jumper(hx(bbB[0], 22 + i), row_y(bbB[1], 1), hx(bbB[0], 35 + i), row_y(bbB[1], 3) + 6,
                        col, sag=12 + 3 * i, w=1.8))
    S.append(f'<text class="t-cap" x="{hx(bbB[0],26)}" y="{row_y(bbB[1],5)+2}">ESP⇔CAN: 3V3・GND・CTX・CRX(4本)</text>')
    # CAN ペア線(左端へ)
    ex = 14
    S.append(f'<path d="M{canx+8} {cany+10} C {canx-80} {cany-6} 60 96 {ex} 96" fill="none" stroke="var(--w-pwm)" stroke-width="2.2"/>')
    S.append(f'<path d="M{canx+8} {cany+22} C {canx-90} {cany+8} 70 110 {ex} 110" fill="none" stroke="var(--w-pwm)" stroke-width="2.2"/>')
    S.append(twist(30, 88, "var(--w-pwm)"))
    S.append(f'<text class="t-lab" x="52" y="88" fill="var(--w-pwm)">私設CAN(ツイストペア) {"→ 後ユニットへ" if front else "→ 前ユニットへ"}</text>')

    if front:
        # マルチプレクサ(BB-1 右側)
        S.append(dip(bbA[0], bbA[1], 34, 12, "CD74HC4067", "SENSE×10→SIG1本"))
        S.append(f'<text class="t-cap" x="{hx(bbA[0],34)-6}" y="{bbA[1]+42}">C0–C9←SENSE / SIG+S0–S3⇔ESP(5本)</text>')
        # ESP⇔mux ジャンパ5本(SIG + S0-S3)
        for i in range(5):
            S.append(jumper(hx(bbA[0], 26 + i), row_y(bbA[1], 9) - 4, hx(bbA[0], 35 + i), row_y(bbA[1], 5) + 4,
                            "var(--w-is)", sag=-24 - i * 4, w=1.8))
    # Mac / USB(前のみ)
    if front:
        S.append(flow(f"M14 246 H70", "var(--w-pwm)", 76, 246, 0,
                      "Mac → USBシリアル(UART側)", 14, 234))

    # レール連結ジャンパ(右端)
    for (ya, yb) in ((rail_y(bbA[1], "b+"), rail_y(bbB[1], "t+")), (rail_y(bbB[1], "b+"), rail_y(bbC[1], "t+"))):
        S.append(jumper(hx(bbA[0], 60), ya, hx(bbA[0], 60), yb, "#c0392b", sag=0, w=2.2))
        S.append(jumper(hx(bbA[0], 62), ya + 8, hx(bbA[0], 62), yb + 8, "#26548a", sag=0, w=2.2))
    S.append(f'<text class="t-cap" x="446" y="548">レール渡り(5V/GND)</text>')
    # BB-3: 上レール→下レール GND 渡り(分圧タップのGND用)
    S.append(f'<line x1="552" y1="{rail_y(bbC[1],"t-")}" x2="552" y2="{rail_y(bbC[1],"b-")}" stroke="#26548a" stroke-width="2"/>')
    S.append(f'<text class="t-cap" x="175" y="120">5V=赤レール / GND=青レール(レール渡りで3枚に共有)</text>')

    # ==== BB-3: 分圧タップ ====
    step = 6 if front else 8
    y0c = bbC[1]
    # WAGO 入力列
    S.append(wago(44, 508, n, "灯具線からの分圧タップ入力(各ch・WAGOで割込み)"))
    S.append(f'<text class="t-cap" x="{56+n*24}" y="530">←各chの灯具線(右上の「COM→灯具」の各線)から分岐</text>')
    outxs = []
    for i in range(n):
        c = 3 + i * step
        x = hx(bbC[0], c)
        wx = 54 + i * 24
        # タップ線(WAGO→a行)
        S.append(jumper(wx, 536, x, row_y(y0c, 0), "var(--w-vcc)", sag=6, w=2))
        # 100k(上半分d → 下半分f)
        S.append(resistor_v(x, row_y(y0c, 3), row_y(y0c, 5), ("#8a5a2b", "#222", "#e0c030")))
        # 22k(g → 下青レール)
        S.append(resistor_v(x - 0.5 * P, row_y(y0c, 6), rail_y(y0c, "b-"), ("#c33", "#c33", "#e08020")))
        S.append(jumper(x, row_y(y0c, 6), x - 0.5 * P, row_y(y0c, 6), "#9a9a9a", sag=0, w=1.6))
        # ツェナー3.3V(h → 下青レール)
        S.append(zener_v(x + P, row_y(y0c, 7), rail_y(y0c, "b-")))
        S.append(jumper(x, row_y(y0c, 7), x + P, row_y(y0c, 7), "#9a9a9a", sag=0, w=1.6))
        # 出力(i行 → 下バスへ)
        S.append(f'<path d="M{x} {row_y(y0c,8)} V756" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>')
        outxs.append(x)
        S.append(f'<text x="{x}" y="{y0c-8}" text-anchor="middle" style="font:9px Hiragino Sans" fill="var(--muted)">{labels[i]}</text>')
    # SENSE バンドル
    S.append(f'<path d="M{outxs[0]} 756 H614" fill="none" stroke="var(--w-is)" stroke-width="2.4"/>')
    if front:
        S.append(flow("M614 756 V236 H432", "var(--w-is)", 426, 236, 180,
                      "SENSE×10 → CD74HC4067 C0–C9", 620, 700))
    else:
        S.append(flow("M614 756 V300 H300", "var(--w-is)", 294, 300, 180,
                      "SENSE×7 → GPIO直結(ブレーキ2chは最優先監視)", 620, 700))

    # ==== 右列: リレーモジュール ====
    if front:
        r1, w1 = relay_module(640, 156, 8, 8, "リレーモジュール① 8ch(Reland Sun 12V)",
                              "ch1-8: ローR ローL ハイR ハイL フォグR フォグL ポジR ポジL")
        S.append(r1)
        r2, w2 = relay_module(1100, 156, 8, 2, "②(5枚組の2枚目)",
                              "ch9-10: WFR WFL(残6ch=予備)", badge_on=False)
        S.append(r2)
    else:
        r1, w1 = relay_module(640, 156, 8, 7, "リレーモジュール③ 8ch(Reland Sun 12V)",
                              "ch1-7: テールR テールL ブレーキR ブレーキL WRR WRL ハイM")
        S.append(r1)

    # ==== BTS 島(唯一のはんだ) ====
    bts, bw, bh = bts_island(640, 420, n, 5, "BTS6143D×%d — TO-252-5変換基板カートリッジ式" % n)
    S.append(bts)
    S.append(f'<text class="t-cap" x="640" y="{420+bh+18}">VS: ch毎ヒューズ→タブ / OUT: 緑端子→リレーNO / 左ヘッダ: PWM・IS / 各BTSは丸ピンヘッダ+丸ピンソケットで抜き挿し交換可</text>')

    # ==== ヒューズブロック・バスバー・DCDC ====
    fb, fh = fuse_block(1210, 420, n + 2, "ヒューズブロック 12way", "5A×%d + IGコイル + 予備" % n)
    S.append(fb)
    S.append(bus_bar(1210, 460 + fh, "GNDバスバー → 車体一点アース"))
    S.append(dcdc(756, 420 + bh + 52))
    dy = 420 + bh + 52   # DCDC上端(前後とも818)

    # ==== フロー矢印 ====
    # バッ直 → ヒューズブロック
    S.append(flow(f"M1305 350 V414", "var(--w-vcc)", 1305, 416, 90,
                  "バッ直 12V(F20A)", 1320, 342, w=3.5))
    # ヒューズブロック → BTS VS
    S.append(flow(f"M1204 500 H{640+bw+8}", "var(--w-vcc)", 640 + bw + 6, 500, 180,
                  "ch毎5A → VS×%d" % n, 1010, 490))
    # ESP PWM → BTS 左ヘッダ
    S.append(flow(f"M292 380 C 480 380 560 470 632 486", "var(--w-pwm)", 636, 487, 12,
                  "PWM×%d+IS(破線)" % n, 306, 438, dash="7 5"))
    # ESP SEL → リレーIN
    if front:
        S.append(flow("M292 344 C 520 344 560 312 648 302", "var(--w-en)", 652, 302, -5,
                      "SEL×8+3V3/GND → ①IN", 620, 344))
        S.append(flow("M300 356 C 650 416 1000 380 1132 312", "var(--w-en)", 1134, 308, -55,
                      "SEL×2 → ②IN", 700, 412))
    else:
        S.append(flow("M292 344 C 520 344 560 312 648 302", "var(--w-en)", 652, 302, -5,
                      "SEL×7+3V3/GND → IN", 620, 344))
    # BTS OUT → リレーNO
    S.append(flow(f"M880 414 V344", "var(--w-pos)", 880, 340, -90,
                  "OUT×%d → ①のNOねじ端子" % min(n, 8) if front else "OUT×%d → NOねじ端子" % n, 890, 408))
    if front:
        S.append(flow("M1105 414 V334", "var(--w-pos)", 1105, 330, -90, "OUT×2 → ②NO", 1115, 408))
    # 純正線 → NC
    S.append(flow(f"M1540 96 H1000 V146", "var(--w-vcc)", 1000, 150, 90,
                  "純正線×%d → NC(灯具コネクタ直前で割込み)" % n, 1090, 88))
    # COM → 灯具
    S.append(flow(f"M985 152 V104 H1536", "var(--w-pos)", 1540, 104, 0,
                  "COM → 灯具×%d" % n, 1240, 120))
    # IG12V → リレーモジュール JD-VCC(コイル電源)
    if front:
        S.append(flow("M1540 370 H1058 V316", "var(--w-vcc)", 1058, 314, -90,
                      "IG12V → JD-VCC ①②(キーOFF=無励磁=NC=純正)", 1150, 360, w=2.5))
        S.append(flow("M1518 370 V316", "var(--w-vcc)", 1518, 314, -90, None, w=2.5))
    else:
        S.append(flow("M1540 370 H1058 V316", "var(--w-vcc)", 1058, 314, -90,
                      "IG12V → JD-VCC ③(キーOFF=無励磁=NC=純正)", 1150, 360, w=2.5))
    # IG12V → DCDC入力(ヒューズ+TVS経由)・DCDC出力 → BB-3上レール
    S.append(flow(f"M1540 898 H690 V{dy+44}", "var(--w-vcc)", 690, dy + 42, -90,
                  "IG12V+GND(5Aヒューズ+SMBJ24A) → DCDC入力WAGO", 1050, 890, w=2.5))
    S.append(flow(f"M948 {dy+8} V808 H600 V{rail_y(560,'t+')} H572", "#c0392b", 570, rail_y(560, "t+"), 180, None, w=2.6))
    S.append(flow(f"M972 {dy+8} V816 H608 V{rail_y(560,'t-')} H572", "#26548a", 570, rail_y(560, "t-"), 180, None, w=2.6))
    S.append(f'<text class="t-lab" x="250" y="800" fill="var(--muted)">DCDC出力 5V/GND → BB-3上レール(右端) →</text>')

    # 外枠
    S.append(f'<rect x="6" y="60" width="1548" height="844" rx="14" fill="none" '
             f'stroke="var(--accent)" stroke-width="1.5" stroke-dasharray="8 7" opacity="0.6"/>')
    S.append(f'<text class="t-ti" x="20" y="48" fill="var(--accent)">{uname}</text>')
    S.append(f'<text class="t-cap" x="360" y="48">ベース板(MDF/アクリル)にマウントし、まとめて設置・撤去する</text>')

    return (f'<svg viewBox="0 0 1560 912" role="img" aria-label="{uname} 実装レイアウト">'
            + "".join(S) + "</svg>")

# ---------------- HTML ----------------
CSS = """
  :root {
    color-scheme: light;
    --bg: #f2f4f3; --surface: #ffffff; --box: #f5f7f6; --box-line: #c3cdc8;
    --ink: #212723; --muted: #5e6963; --line: #dbe1de; --accent: #a87413; --dot: #e2e7e4;
    --w-pwm: #2f6fb2; --w-en: #2f8659; --w-is: #7e58be; --w-vcc: #c07a16;
    --w-gnd: #78827c; --w-pos: #c2443a; --w-neg: #464d49;
    --danger: #b3372c; --danger-bg: #fbeeec; --danger-line: #ecc9c4;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
    font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", system-ui, sans-serif;
    font-size: 14.5px; line-height: 1.75; }
  .wrap { max-width: 1080px; margin: 0 auto; padding: 40px 24px 64px; }
  .eyebrow { font-family: ui-monospace, Menlo, monospace; font-size: 11.5px;
    letter-spacing: 0.08em; color: var(--accent); margin: 0 0 6px; }
  h1 { font-size: 25px; font-weight: 700; margin: 0 0 10px; line-height: 1.4; }
  .lead { color: var(--muted); margin: 0; max-width: 46em; }
  h2 { font-size: 16.5px; font-weight: 700; margin: 44px 0 14px; display: flex; align-items: center; gap: 10px; }
  h2::before { content: ""; width: 5px; height: 18px; border-radius: 2px; background: var(--accent); flex: none; }
  .hint { margin: -8px 0 12px; font-size: 12.5px; color: var(--muted); }
  .hint b { color: var(--accent); }
  .panel { background: var(--surface); border: 1px solid var(--line); border-radius: 10px;
    overflow-x: auto; padding: 10px 6px; }
  .panel svg { display: block; min-width: 1560px; width: 100%; height: auto; }
  svg .t-ti { font: 700 13px "Hiragino Sans", sans-serif; fill: var(--ink); }
  svg .t-lab { font: 12px "Hiragino Sans", sans-serif; fill: var(--ink); }
  svg .t-cap { font: 11px "Hiragino Sans", sans-serif; fill: var(--muted); }
  svg text { user-select: none; }
  .legend { display: flex; flex-wrap: wrap; gap: 8px 20px; margin: 12px 2px 0; font-size: 12.5px; color: var(--muted); }
  .legend span { display: inline-flex; align-items: center; gap: 7px; }
  .legend i { width: 18px; height: 4px; border-radius: 2px; display: inline-block; }
  .tbl-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
  table { border-collapse: collapse; width: 100%; min-width: 680px; font-size: 13.5px; }
  th, td { text-align: left; padding: 9px 14px; border-top: 1px solid var(--line); vertical-align: top; }
  thead th { border-top: none; font-size: 12px; color: var(--muted); font-weight: 600; padding-top: 12px; }
  td.sig { white-space: nowrap; font-family: ui-monospace, Menlo, monospace; font-size: 12.5px; }
  .danger { background: var(--danger-bg); border: 1px solid var(--danger-line);
    border-left: 4px solid var(--danger); border-radius: 8px; padding: 14px 18px; }
  .danger ul { margin: 0; padding-left: 20px; }
  .danger li { margin: 4px 0; font-size: 13.5px; }
  .danger li::marker { color: var(--danger); }
  footer { margin-top: 48px; font-size: 12px; color: var(--muted); }
  @page { size: A4 landscape; margin: 9mm; }
  @media print {
    :root, :root[data-theme="dark"] {
      --bg: #fff; --surface: #fff; --box: #fff; --box-line: #999;
      --ink: #111; --muted: #444; --line: #bbb; --accent: #8a6010; --dot: #fff;
      --w-pwm: #2f6fb2; --w-en: #2f8659; --w-is: #6d48ae; --w-vcc: #a86a10;
      --w-gnd: #666; --w-pos: #b23a30; --w-neg: #333;
      --danger: #a03026; --danger-bg: #fff; --danger-line: #bbb;
    }
    body { background: #fff; font-size: 12.5px; }
    .wrap { max-width: none; padding: 0; }
    .panel { overflow: visible; border: none; padding: 0; }
    .panel svg { min-width: 0; width: 94%; margin: 0 auto; }
    h2 { break-before: page; margin-top: 0; }
    h2:first-of-type { break-before: auto; }
    h2, .hint { break-after: avoid; }
    .tbl-wrap, table { min-width: 0; }
    a { color: inherit; text-decoration: none; }
    .legend { break-inside: avoid; margin-top: 6px; font-size: 11px; }
    .panel, .danger { break-inside: avoid; }
    tr { break-inside: avoid; }
    thead { display: table-header-group; }
    h1 { font-size: 20px; }
    .lead { font-size: 11.5px; }
    footer { break-before: avoid; }
  }
"""

LEGEND = """
  <div class="legend">
    <span><i style="background:var(--w-vcc)"></i>12V(バッ直・IG・純正線)=太物</span>
    <span><i style="background:var(--w-pos)"></i>自作出力 12V(OUT→NO / COM→灯具)=太物</span>
    <span><i style="background:var(--w-pwm)"></i>PWM(破線)/ CAN・USB</span>
    <span><i style="background:var(--w-en)"></i>SEL(リレートリガ)</span>
    <span><i style="background:var(--w-is)"></i>SENSE 監視</span>
    <span><i style="background:#c0392b"></i>5V(DCDC出力→赤レール)</span>
    <span><i style="background:#26548a"></i>ロジックGND(青レール)</span>
    <span><i style="background:#2e7d4f;height:10px;border-radius:3px"></i>ねじ端子(無はんだ・太物の接続点)</span>
  </div>
"""

BODY_TOP = """
<div class="wrap">
  <p class="eyebrow">micro-control / board-layout(temporary-rig)</p>
  <h1>実装レイアウト図 — ブレッドボード仮設構成(解体前提)</h1>
  <p class="lead">「使い終わったら解体する」前提の実体配置。ロジックは全てブレッドボード、
  リレーは既製モジュール(Reland Sun 8ch×5枚組・ねじ端子)、BTS6143DはTO-252-5変換基板+丸ピンソケットの
  カートリッジ式で、<b>はんだ付けは BTS の島だけ</b>に閉じ込める。
  配線の正解は <a href="full-wiring-17ch.html">全パーツ完全結線図</a> が正で、この図は「何をどこに載せるか」を示す。</p>

  <h2>前ユニット(10ch)</h2>
  <p class="hint"><b>ブレッドボードに流してよいのは信号だけ</b>(PWM・SEL・SENSE・CAN・5V)。
  灯具電流(〜2A/ch)はリレーモジュール・BTS島・ヒューズブロックのねじ端子側だけを通す。
  太い矢印は「×n」の束線(実配線はn本)。1本ずつの行き先は完全結線図を参照。</p>
"""

BODY_MID = """
  <h2>後ユニット(7ch)</h2>
  <p class="hint">マルチプレクサ無し(GPIOが足りるためSENSE×7は直結)。それ以外は前ユニットの縮小版。
  モジュール③の空き1chと5枚組の残り2枚は予備。</p>
"""

BODY_BOTTOM = """
  <h2>配線ルール — 図の色 = 線の太さ</h2>
  <p class="hint">太線はすべて<b>ねじ端子(図中の緑の太いマーク)だけ</b>を通り、ブレッドボードには一切入らない。</p>
  <div class="tbl-wrap">
  <table>
    <thead><tr><th>図の色</th><th>何の線か</th><th>実際に使う線材</th></tr></thead>
    <tbody>
      <tr><td class="sig" style="color:var(--w-vcc)">■ オレンジ</td>
          <td>12V給電 — バッテリー→ヒューズブロック→BTS島 / IG→リレーモジュール / 純正線→NC</td>
          <td><b>太物</b>: 幹線2.0sq(AWG14)・分岐0.75sq以上+ネジ端子・圧着端子</td></tr>
      <tr><td class="sig" style="color:var(--w-pos)">■ 赤</td>
          <td>自作出力12V — BTS OUT→リレーNO / リレーCOM→灯具</td>
          <td><b>太物</b>: 0.75〜1.25sq(18AWG)+ネジ端子</td></tr>
      <tr><td class="sig" style="color:var(--w-pwm)">■ 青</td>
          <td>PWM(破線)・CAN・USB の信号</td>
          <td>細線(ジャンパ線)可。ただしCANはツイストペア(CAT5e 1ペア)</td></tr>
      <tr><td class="sig" style="color:var(--w-en)">■ 緑</td>
          <td>SEL — リレーモジュールへの切替指示</td>
          <td>細線(ジャンパ線)可</td></tr>
      <tr><td class="sig" style="color:var(--w-is)">■ 紫</td>
          <td>SENSE — 各灯具の電圧監視</td>
          <td>細線(ジャンパ線)可</td></tr>
      <tr><td class="sig" style="color:#c0392b">■ 赤(細)</td>
          <td>5V — DCDC出力→ブレッドボード赤レール</td>
          <td>細線可(流れるのは数百mA)</td></tr>
      <tr><td class="sig" style="color:#26548a">■ 青(細)</td>
          <td>ロジックGND — ESP32⇔IC間・青レール</td>
          <td>細線可</td></tr>
      <tr><td class="sig">■ GND幹線</td>
          <td>バッテリーへ戻るマイナス幹線・灯具のマイナス</td>
          <td><b>太物</b>: 2.0sq。GNDバスバーに一点集約(GNDだけ2種類あるのに注意)</td></tr>
    </tbody>
  </table>
  </div>

  <h2>部品と役割 — かんたん解説(回路が読めなくても分かる用)</h2>
  <p class="hint">数量は「使用数(予備込みの推奨購入数)」。</p>
  <div class="tbl-wrap">
  <table>
    <thead><tr><th>部品</th><th>数量</th><th>役割(ひとことで)</th></tr></thead>
    <tbody>
      <tr><td>ESP32-S3(Freenove Board Lite)</td><td class="sig">2(3)</td><td>頭脳。操作(MIDI/シリアル/Web)を受けて17灯の明るさ・切替を決めるマイコン</td></tr>
      <tr><td>SN65HVD230 モジュール</td><td class="sig">2(4)</td><td>前後ユニットの通信係(CAN)。ツイストペア2本で会話する</td></tr>
      <tr><td>CD74HC4067</td><td class="sig">1(2)</td><td>監視線10本を1本にまとめる16接点の電子切替スイッチ(前ユニットのピン不足対策)。通信部品ではない</td></tr>
      <tr><td>Reland Sun 8chリレーモジュール(12V)</td><td class="sig">3(5枚組)</td><td>「純正配線⇔自作回路」の切替スイッチ。電源が切れると勝手に純正側へ戻る(フェールセーフ)。ドライバ内蔵なのでTBD62083は不要</td></tr>
      <tr><td>BTS6143D</td><td class="sig">17(20〜25)</td><td>各灯具のON/OFF・調光を実際に行うパワースイッチ。過電流・過熱の自己保護つき</td></tr>
      <tr><td>TO-252-5変換基板+丸ピンソケット</td><td class="sig">17(21)</td><td>BTSを「差し替えできるカートリッジ」にする下駄。故障時はんだごて不要で交換</td></tr>
      <tr><td>GYVRM DCDC 8-40V→5V/5A</td><td class="sig">2(3)</td><td>車の12VからESP32用の5Vを作る電源。入力にヒューズ+TVSを自前追加</td></tr>
      <tr><td>ヒューズブロック+ブレード5A</td><td class="sig">2台・17+IG2(30)</td><td>配線の安全装置。ショート時に電線が焼ける前に切れる。<b>この設計の保護の本命</b></td></tr>
      <tr><td>メイン20Aヒューズ+ホルダ</td><td class="sig">1(2)</td><td>幹線の安全装置(バッテリー直後に入れる)</td></tr>
      <tr><td>GNDバスバー</td><td class="sig">2</td><td>マイナス線の集合場所。ユニット毎に一点にまとめて車体へ戻す</td></tr>
      <tr><td>抵抗100k/22k+ツェナー3.3V</td><td class="sig">各17(30)</td><td>12Vの監視信号をESP32が読める電圧(約2.2V)に下げ、3.3V超を止める保護(分圧タップ)</td></tr>
      <tr><td>セラコン0.1µF・電解100µF・TVS SMBJ24A</td><td class="sig">適量</td><td>電源のノイズ・サージ(車の電圧の暴れ)対策</td></tr>
      <tr><td>WAGO級レバーコネクタ(2穴)</td><td class="sig">30</td><td>工具・はんだ無しで線を分岐/接続するコネクタ。灯具線への割込みに使う</td></tr>
      <tr><td>ブレッドボード830点</td><td class="sig">6</td><td>ロジック部品の差し込み台(はんだ不要・解体後に再利用可)</td></tr>
      <tr><td>ジャンパ線・単芯線キット</td><td class="sig">1式</td><td>信号用の細線(青・緑・紫・5V/GNDの線)</td></tr>
      <tr><td>車載用電線 2.0sq / 0.75〜1.25sq</td><td class="sig">10m / 各5m</td><td>太物ゾーン(オレンジ・赤・GND幹線)の線材</td></tr>
      <tr><td>CAT5e ツイストペア</td><td class="sig">6m+</td><td>CAN通信線(LANケーブルの1ペアを流用)</td></tr>
      <tr><td>ベース板(MDF/アクリル)</td><td class="sig">2</td><td>ユニット全体を固定する土台。まとめて設置・撤去する</td></tr>
      <tr><td>USB-Cケーブル 3m</td><td class="sig">1(2)</td><td>Mac→前ユニットの書き込み・シリアル操作</td></tr>
    </tbody>
  </table>
  </div>

  <h2>実装方式まとめ</h2>
  <div class="tbl-wrap">
  <table>
    <thead><tr><th>ブロック</th><th>載せ方</th><th>はんだ</th></tr></thead>
    <tbody>
      <tr><td>ESP32-S3×2・SN65HVD230×2・CD74HC4067・分圧タップ(100k/22k/ツェナー×17組)</td>
          <td>ブレッドボード830点×6枚(各ユニット3枚)。ESPは幅が広いので2枚跨ぎ</td><td class="sig">不要</td></tr>
      <tr><td>切替リレー×17</td>
          <td><b>既製リレーモジュール</b> 8ch×3枚(12Vコイル・オプトカプラ・NC/C/NOねじ端子)。空き7ch=予備</td><td class="sig">不要</td></tr>
      <tr><td>BTS6143D×17</td>
          <td>DPAK変換基板→ユニバーサル基板2枚+2Pねじ端子。<b>唯一のはんだ作業</b>(17個×約6点≒100点)</td><td class="sig" style="color:var(--danger)">必要</td></tr>
      <tr><td>電源分配・タップ割込み</td>
          <td>ヒューズブロック(ブレード)・GNDバスバー・WAGO級レバーコネクタ</td><td class="sig">不要</td></tr>
      <tr><td>DCDC 12V→5V</td>
          <td>裸線をWAGOで受ける</td><td class="sig">不要</td></tr>
    </tbody>
  </table>
  </div>

  <h2>仮設構成で確定した差分(2026-08-03)</h2>
  <p class="hint">リレーモジュールと変換基板はAmazonで品番確定。<b>parts-list.md 本体の全面改訂と発注は未実施</b>(次回)。</p>
  <div class="tbl-wrap">
  <table>
    <thead><tr><th>変更</th><th>内容</th><th>金額(概算)</th></tr></thead>
    <tbody>
      <tr><td class="sig">削除</td><td>SRD-12VDC-SL-C 20個セット / TBD62083APG×3+DIP18ソケット×3(モジュールがドライバ内蔵) / マイナスバスバー一体型ヒューズブロックを選ぶ場合はGNDバスバーも省略可</td><td class="sig">−約2,300円</td></tr>
      <tr><td class="sig">追加(品番確定)</td><td>Reland Sun 8chリレーモジュール12V 5枚組[Amazon] / a bit better circuit TO-252-5ピッチ変換基板 3枚×7パック=21枚[Amazon] / 丸ピンヘッダ1×40×4+丸ピンICソケット40P分割×3[秋月]</td><td class="sig">2,800+2,002+約500円</td></tr>
      <tr><td class="sig">変更(品番確定)</td><td>DCDC を GYVRM 8-40V→5V/5A(IP68・Amazon 420円/個)に変更(旧 DGXBY L2-T2405 620円)。入力へのヒューズ+SMBJ24A自前追加は従来通り</td><td class="sig">−200円×3</td></tr>
      <tr><td class="sig">追加(汎用)</td><td>ブレッドボード830×6(≈1,500円) / ジャンパ・単芯線キット(≈700円) / レバーコネクタ2穴×30(≈1,200円) / ベース板MDF×2(HC, ≈600円)</td><td class="sig">+約4,000円</td></tr>
      <tr><td class="sig">差引</td><td>はんだはBTS島(約100点+ヘッダ/ソケット)のみ。BTSはカートリッジ式で現場差し替え可。解体後はブレッドボード・モジュール・WAGOを全て再利用できる</td><td class="sig">総額≈3.1〜3.3万円(灯具側除く)</td></tr>
    </tbody>
  </table>
  </div>

  <h2>注意(この構成で効いてくるもの)</h2>
  <div class="danger">
    <ul>
      <li><b>ブレッドボードに灯具電流を流さない。</b>接点定格は約1A。通してよいのは信号と5V(数百mA)のみ。灯具系はすべてねじ端子。</li>
      <li><b>リレーモジュールは JD-VCC ジャンパを除去し、入力側VCC=3V3・JD-VCC=IG12V の分離給電にする。</b>ジャンパを付けたまま(VCC=12V)だと 3.3V GPIO の HIGH でオプトカプラが消灯しきれず、リレーが切れなくなる。</li>
      <li><b>リレーモジュール(Reland Sun 12V)は到着後ベンチで実測:</b> 3.3V GPIOで確実にON/OFFできるか / 入力フロート(ESP停止相当)で非励磁=NC復帰するか。コイル電源はIG12V(キーOFF=無励磁=NC=純正のフェールセーフ維持)。</li>
      <li>ヒューズブロックとヒューズは<b>ATO標準ブレードで規格統一</b>(ミニ・低背と混ぜない)。バスバー内蔵・切れLED表示付きを選ぶ。</li>
      <li>Freenove Board Lite は幅広で1枚では穴が残らない → 図の通り2枚のブレッドボードに跨がせる。</li>
      <li>仮設でもブレッドボードはベース板に固定し、ジャンパは束ねて抜け止め。ショー・停車時専用の前提は変わらず。</li>
      <li>丸ピンソケットは接点が1段増えるため、組付け後に各chの電圧降下を一度実測して接触を確認。</li>
    </ul>
  </div>

  <footer>2026-08-03。図の修正は gen_board_layout.py を編集して再実行(HTML直接編集禁止)。配線の正は full-wiring-17ch.html。印刷はA4横(このページはprint CSS対応・PDF版 board-layout-17ch.pdf あり)。</footer>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>実装レイアウト図 — 17chブレッドボード仮設構成</title>\n"
        "<style>" + CSS + "</style>\n"
        + BODY_TOP
        + '<div class="panel">' + unit_svg(front=True) + "</div>\n" + LEGEND
        + BODY_MID
        + '<div class="panel">' + unit_svg(front=False) + "</div>\n" + LEGEND
        + BODY_BOTTOM)

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
