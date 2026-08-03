# -*- coding: utf-8 -*-
# 全パーツ・全配線を省略なしで描く完全結線図の生成スクリプト
import io, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "full-wiring-17ch.html")

Y0F, Y0R, DY = 560, 2560, 150
W, H = 1660, 3830

FRONT = [
    ("ロービーム 右", "w"), ("ロービーム 左", "w"),
    ("ハイビーム 右", "w"), ("ハイビーム 左", "w"),
    ("フォグ 右", "w"), ("フォグ 左", "w"),
    ("ポジション 右", "w"), ("ポジション 左", "w"),
    ("ウィンカー 前右", "a"), ("ウィンカー 前左", "a"),
]
REAR = [
    ("テール 右", "r"), ("テール 左", "r"),
    ("ブレーキ 右", "r"), ("ブレーキ 左", "r"),
    ("ウィンカー 後右", "a"), ("ウィンカー 後左", "a"),
    ("ハイマウント", "r"),
]

def lampcol(kind):
    return {"w": "var(--w-neg)", "a": "var(--w-vcc)", "r": "var(--w-pos)"}[kind]

def chassis(x, y, color="var(--w-neg)", s=1.0):
    w1, w2, w3 = 16*s, 10*s, 5*s
    return (f'<path d="M{x-w1} {y} H{x+w1} M{x-w2} {y+5} H{x+w2} '
            f'M{x-w3} {y+10} H{x+w3}" stroke="{color}" stroke-width="2" fill="none"/>')

S = []  # svg parts

# ============ 上段: Mac / バッテリー / IG / 純正ヒューズBOX ============
S.append(f'''
<g class="hit" data-k="mac" tabindex="0" role="button" aria-label="Mac">
  <rect class="box" x="60" y="40" width="240" height="120" rx="10"/>
  <text class="t-ti" x="180" y="86" text-anchor="middle">Mac(1台で全17ch操作)</text>
  <text class="t-cap" x="180" y="110" text-anchor="middle">自作アプリ / DAW+MIDIキーボード</text>
  <text class="t-cap" x="180" y="130" text-anchor="middle">主: USBシリアル / 副: Wi-Fi</text>
  <path class="hitline" d="M140 160 V270 H240 V470"/>
  <path d="M140 160 V270 H240 V470" fill="none" stroke="var(--w-pwm)" stroke-width="2.5"/>
  <text class="t-lab" x="152" y="235" fill="var(--w-pwm)">USBシリアル(有線・主)</text>
  <path d="M310 96 q10 -12 0 -24 M322 102 q16 -18 0 -36 M334 108 q22 -24 0 -48"
        fill="none" stroke="var(--w-pwm)" stroke-width="1.8" stroke-dasharray="3 4"/>
  <text class="t-cap" x="306" y="130">Wi-Fi(副・無線)→ ESP①</text>
</g>

<g class="hit" data-k="bat" tabindex="0" role="button" aria-label="バッテリー">
  <rect class="box" x="620" y="40" width="170" height="110" rx="10"/>
  <text class="t-ti" x="705" y="82" text-anchor="middle">バッテリー</text>
  <text class="t-cap" x="705" y="104" text-anchor="middle">車載 12 V</text>
  <text class="t-pin" x="782" y="74" text-anchor="end">+</text>
  <path class="hitline" d="M790 70 H820 M884 70 H900 V190 M900 190 H540 V1870 M900 190 H1618 V2260 H540 V3420"/>
  <path d="M790 70 H820" fill="none" stroke="var(--w-vcc)" stroke-width="3"/>
  <rect class="box" x="820" y="58" width="64" height="24" rx="4"/>
  <text class="t-pin" x="852" y="74" text-anchor="middle">F 20A</text>
  <path d="M884 70 H900 V190" fill="none" stroke="var(--w-vcc)" stroke-width="3"/>
  <circle cx="900" cy="190" r="4.5" fill="var(--w-vcc)"/>
  <path d="M900 190 H540 V1870" fill="none" stroke="var(--w-vcc)" stroke-width="3"/>
  <path d="M900 190 H1618 V2260 H540 V3420" fill="none" stroke="var(--w-vcc)" stroke-width="3"/>
  <text class="t-lab" x="560" y="182" fill="var(--w-vcc)">B+ 前バス 2.0sq</text>
  <text class="t-lab" x="1130" y="182" fill="var(--w-vcc)">B+ 後トランク 2.0sq(床下配索)</text>
  <text class="t-lab" x="560" y="2250" fill="var(--w-vcc)">B+ 後バス 2.0sq</text>
  <path d="M705 150 V176" fill="none" stroke="var(--w-neg)" stroke-width="3"/>
  {chassis(705, 176)}
  <text class="t-cap" x="705" y="206" text-anchor="middle">− は車体へ</text>
</g>

<g class="hit" data-k="ig" tabindex="0" role="button" aria-label="IG電源">
  <rect class="box" x="960" y="40" width="150" height="70" rx="10"/>
  <text class="t-ti" x="1035" y="70" text-anchor="middle">IG 12 V</text>
  <text class="t-cap" x="1035" y="92" text-anchor="middle">キーON時のみ通電</text>
  <path class="hitline" d="M1035 110 V160 M1035 160 H575 V1870 M1035 160 H1600 V2280 H575 V3420"/>
  <path d="M1035 110 V160" fill="none" stroke="var(--w-vcc)" stroke-width="2.5"/>
  <circle cx="1035" cy="160" r="4" fill="var(--w-vcc)"/>
  <path d="M1035 160 H575 V1870" fill="none" stroke="var(--w-vcc)" stroke-width="2.5"/>
  <path d="M1035 160 H1600 V2280 H575 V3420" fill="none" stroke="var(--w-vcc)" stroke-width="2.5"/>
  <text class="t-cap" x="600" y="152">IG 前バス(リレーコイル用)</text>
  <text class="t-cap" x="1380" y="2272">IG 後バス</text>
</g>

<g class="hit" data-k="stockbox" tabindex="0" role="button" aria-label="純正ヒューズボックス">
  <rect class="box" x="1150" y="40" width="440" height="110" rx="10"/>
  <text class="t-ti" x="1370" y="80" text-anchor="middle">純正ヒューズBOX / 純正スイッチ(車両側)</text>
  <text class="t-cap" x="1370" y="104" text-anchor="middle">ライトSW・ウィンカーレバー・ブレーキペダル →</text>
  <text class="t-cap" x="1370" y="124" text-anchor="middle">各灯への純正線 17本(分岐後・灯具毎)</text>
</g>
''')

# 純正線: BOX下端 → ジョグ → 縦バンド(x=1005+7k)
ALL = FRONT + REAR
for k in range(17):
    xb = 1170 + 22 * k          # box 下端ピン
    yj = 200 + 6 * k            # ジョグ高さ
    xv = 1005 + 7 * k           # 縦バンド
    if k < 10:
        yrow = Y0F + k * DY
    else:
        yrow = Y0R + (k - 10) * DY
    S.append(
        f'<g class="hit" data-k="stock" tabindex="0" role="button" aria-label="純正線 {ALL[k][0]}">'
        f'<path class="hitline" d="M{xb} 150 V{yj} H{xv} V{yrow-16} H970"/>'
        f'<path d="M{xb} 150 V{yj} H{xv} V{yrow-16} H970" fill="none" stroke="var(--w-vcc)" stroke-width="1.8"/>'
        f'</g>'
    )

# ============ ユニット(前後共通ジオメトリ) ============
def unit(y0, lamps, k0, uname, uloc):
    n = len(lamps)
    esp_top, esp_bot = y0 - 90, y0 + (n - 1) * DY + 90
    parts = []

    # 点線コンテナ
    parts.append(
        f'<rect x="56" y="{y0-270}" width="660" height="{esp_bot-(y0-270)+300}" rx="14" '
        f'fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-dasharray="8 7" opacity="0.65"/>'
        f'<text class="t-ti" x="72" y="{y0-284}" fill="var(--accent)">{uname}</text>'
        f'<text class="t-cap" x="300" y="{y0-284}">{uloc}</text>'
    )

    # CANトランシーバ
    xcvr_y = y0 - 260
    parts.append(
        f'<g class="hit" data-k="can" tabindex="0" role="button" aria-label="CANトランシーバ">'
        f'<rect class="box" x="76" y="{xcvr_y}" width="150" height="60" rx="8"/>'
        f'<text class="t-lab" x="151" y="{xcvr_y+26}" text-anchor="middle">SN65HVD230</text>'
        f'<text class="t-cap" x="151" y="{xcvr_y+46}" text-anchor="middle">CANトランシーバ</text>'
        f'<path class="hitline" d="M76 {xcvr_y+16} H32 M76 {xcvr_y+36} H24 '
        f'M180 {y0-90} V{y0-186} H130 V{xcvr_y+60} M205 {y0-90} V{y0-176} H155 V{xcvr_y+60}"/>'
        f'<path d="M76 {xcvr_y+16} H32" fill="none" stroke="var(--w-pwm)" stroke-width="2"/>'
        f'<path d="M76 {xcvr_y+36} H24" fill="none" stroke="var(--w-pwm)" stroke-width="2"/>'
        f'<path d="M180 {y0-90} V{y0-186} H130 V{xcvr_y+60}" fill="none" stroke="var(--w-pwm)" stroke-width="1.6"/>'
        f'<path d="M205 {y0-90} V{y0-176} H155 V{xcvr_y+60}" fill="none" stroke="var(--w-pwm)" stroke-width="1.6"/>'
        f'<text class="t-cap" x="212" y="{y0-190}">TX/RX(3.3V)</text>'
        f'<text class="t-cap" x="40" y="{xcvr_y+10}">CANH/CANL</text>'
        f'</g>'
    )

    # DCDC
    dc_y = y0 - 180
    parts.append(
        f'<g class="hit" data-k="dcdc" tabindex="0" role="button" aria-label="DCDC">'
        f'<rect class="box" x="330" y="{dc_y}" width="160" height="64" rx="8"/>'
        f'<text class="t-lab" x="410" y="{dc_y+26}" text-anchor="middle">DCDC 12V→5V</text>'
        f'<text class="t-cap" x="410" y="{dc_y+46}" text-anchor="middle">車載対応・3A級</text>'
        f'<path class="hitline" d="M490 {dc_y+32} H540 M330 {dc_y+32} H260 V{y0-90} M410 {dc_y+64} V{y0-100} H66"/>'
        f'<path d="M490 {dc_y+32} H540" fill="none" stroke="var(--w-vcc)" stroke-width="2.5"/>'
        f'<path d="M330 {dc_y+32} H260 V{y0-90}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>'
        f'<text class="t-cap" x="268" y="{dc_y+26}">5V</text>'
        f'<path d="M410 {dc_y+64} V{y0-100} H66" fill="none" stroke="var(--w-gnd)" stroke-width="2"/>'
        f'</g>'
    )

    # ESP 本体
    parts.append(
        f'<g class="hit" data-k="esp" tabindex="0" role="button" aria-label="ESP32-S3 {uname}">'
        f'<rect class="box" x="80" y="{esp_top}" width="200" height="{esp_bot-esp_top}" rx="12"/>'
        f'<text class="t-ti" x="180" y="{esp_top+34}" text-anchor="middle">ESP32-S3</text>'
        f'<text class="t-cap" x="180" y="{esp_top+56}" text-anchor="middle">{uname.replace("ユニット","")}(TWAI内蔵)</text>'
        f'<text class="t-cap" x="180" y="{esp_top+76}" text-anchor="middle">右辺: PWM / SENSE 各{n}本</text>'
        f'<text class="t-cap" x="180" y="{esp_top+96}" text-anchor="middle">下辺: SEL {n}本 → アレイ</text>'
        f'</g>'
    )
    # ESP GND
    gy = esp_bot - 20
    parts.append(
        f'<path d="M80 {gy} H66" fill="none" stroke="var(--w-gnd)" stroke-width="2"/>'
    )

    # GND レール + バスバー + 一点アース
    bar_y = y0 + (n - 1) * DY + 90 + 202  # arrays の下
    yA = esp_bot + 30
    parts.append(
        f'<g class="hit" data-k="gnd" tabindex="0" role="button" aria-label="GND">'
        f'<path class="hitline" d="M66 {y0-100} V{bar_y+8} H110"/>'
        f'<path d="M66 {y0-100} V{bar_y+8} H110" fill="none" stroke="var(--w-gnd)" stroke-width="2"/>'
        f'<rect class="box" x="110" y="{bar_y}" width="220" height="16" rx="4"/>'
        f'<text class="t-cap" x="220" y="{bar_y+12}" text-anchor="middle">GNDバスバー</text>'
        f'<path d="M220 {bar_y+16} V{bar_y+32}" fill="none" stroke="var(--w-neg)" stroke-width="2.5"/>'
        f'{chassis(220, bar_y+32)}'
        f'<text class="t-cap" x="220" y="{bar_y+62}" text-anchor="middle">車体一点アース</text>'
        f'</g>'
    )

    # トランジスタアレイ
    arrays = []
    if n == 10:
        arrays = [("110", yA, 200, "TBD62083 ①", list(range(8))),
                  ("340", yA, 160, "TBD62083 ②", [8, 9])]
    else:
        arrays = [("110", yA, 200, "TBD62083", list(range(n)))]
    arr_svg = []
    for ax, ay, aw, aname, chs in arrays:
        axi = int(ax)
        arr_svg.append(
            f'<rect class="box" x="{ax}" y="{ay}" width="{aw}" height="110" rx="8"/>'
            f'<text class="t-lab" x="{axi+aw//2}" y="{ay+40}" text-anchor="middle">{aname}</text>'
            f'<text class="t-cap" x="{axi+aw//2}" y="{ay+60}" text-anchor="middle">8ch・還流D内蔵</text>'
            f'<text class="t-cap" x="{axi+aw//2}" y="{ay+78}" text-anchor="middle">COM→12V</text>'
        )
        # GND 落とし
        gx = axi + aw // 2 + 60 if axi > 200 else axi + 100
        if axi <= 200:
            arr_svg.append(f'<path d="M{axi+100} {ay+110} V{bar_y}" fill="none" stroke="var(--w-gnd)" stroke-width="2"/>')
        else:
            arr_svg.append(f'<path d="M{axi+80} {ay+110} V{bar_y+8} H330" fill="none" stroke="var(--w-gnd)" stroke-width="2"/>')

    # SEL 落とし(ESP下辺 → アレイ上辺)
    sel = []
    for i in range(n):
        xs = 130 + 14 * i
        if n == 10 and i >= 8:
            jy = esp_bot + 12 + (i - 8) * 8
            xt = 380 + (i - 8) * 30
            sel.append(f'<path d="M{xs} {esp_bot} V{jy} H{xt} V{yA}" fill="none" stroke="var(--w-en)" stroke-width="1.8"/>')
        else:
            sel.append(f'<path d="M{xs} {esp_bot} V{yA}" fill="none" stroke="var(--w-en)" stroke-width="1.8"/>')
    parts.append(
        f'<g class="hit" data-k="array" tabindex="0" role="button" aria-label="トランジスタアレイ">'
        + "".join(arr_svg) + "".join(sel) +
        f'<text class="t-cap" x="132" y="{esp_bot+22}">SEL×{n}(コイル選択)</text>'
        f'</g>'
    )

    # ============ チャンネル行 ============
    for i, (name, kind) in enumerate(lamps):
        y = y0 + i * DY
        k = k0 + i
        xv_coil = 610 + 9 * i
        # アレイOUTの合流先
        if n == 10 and i >= 8:
            arr_right, out_y = 500, yA + 20 + (i - 8) * 20
        else:
            arr_right, out_y = 310, yA + 12 + 12 * i
        lc = lampcol(kind)

        # PWM線+SW+5Aヒューズ+B+分岐
        parts.append(
            f'<g class="hit" data-k="sw" tabindex="0" role="button" aria-label="ハイサイドSW {name}">'
            f'<path class="hitline" d="M280 {y} H360 M540 {y-52} H453 M417 {y-52} H400 V{y-22} M500 {y} H830"/>'
            f'<path d="M280 {y} H360" fill="none" stroke="var(--w-pwm)" stroke-width="2.2" stroke-dasharray="7 5"/>'
            f'<rect class="box" x="360" y="{y-22}" width="140" height="44" rx="6"/>'
            f'<text class="t-lab" x="430" y="{y-2}" text-anchor="middle">ハイサイドSW</text>'
            f'<text class="t-cap" x="430" y="{y+15}" text-anchor="middle">ch{i+1} PWM対応</text>'
            f'<path d="M540 {y-52} H453" fill="none" stroke="var(--w-vcc)" stroke-width="2.2"/>'
            f'<rect class="box" x="417" y="{y-64}" width="36" height="24" rx="4"/>'
            f'<text class="t-pin" x="435" y="{y-48}" text-anchor="middle">5A</text>'
            f'<path d="M417 {y-52} H400 V{y-22}" fill="none" stroke="var(--w-vcc)" stroke-width="2.2"/>'
            f'<path d="M500 {y} H830" fill="none" stroke="var(--w-pos)" stroke-width="2.2"/>'
            f'</g>'
        )
        # B+/IG バス分岐点ドット
        parts.append(f'<circle cx="540" cy="{y-52}" r="3.5" fill="var(--w-vcc)"/>'
                     f'<circle cx="575" cy="{y-40}" r="3.5" fill="var(--w-vcc)"/>')

        # リレー + IG分岐
        parts.append(
            f'<g class="hit" data-k="relay" tabindex="0" role="button" aria-label="切替リレー {name}">'
            f'<path class="hitline" d="M575 {y-40} H870 V{y-32}"/>'
            f'<path d="M575 {y-40} H870 V{y-32}" fill="none" stroke="var(--w-vcc)" stroke-width="2"/>'
            f'<rect class="box" x="830" y="{y-32}" width="140" height="72" rx="6"/>'
            f'<text class="t-lab" x="900" y="{y-12}" text-anchor="middle">切替リレー</text>'
            f'<text class="t-cap" x="842" y="{y+6}">87</text>'
            f'<text class="t-cap" x="958" y="{y-16}" text-anchor="end">87a</text>'
            f'<text class="t-cap" x="958" y="{y+16}" text-anchor="end">30</text>'
            f'<text class="t-cap" x="878" y="{y-18}">86</text>'
            f'<text class="t-cap" x="922" y="{y+34}">85</text>'
            f'<path d="M962 {y-16} L946 {y+12}" stroke="var(--box-line)" stroke-width="1.6"/>'
            f'</g>'
        )

        # コイル線(85 → アレイOUT)
        parts.append(
            f'<g class="hit" data-k="coil" tabindex="0" role="button" aria-label="コイル駆動 {name}">'
            f'<path class="hitline" d="M930 {y+40} V{y+50} H{xv_coil} V{out_y} H{arr_right}"/>'
            f'<path d="M930 {y+40} V{y+50} H{xv_coil} V{out_y} H{arr_right}" fill="none" stroke="var(--w-en)" stroke-width="1.8"/>'
            f'</g>'
        )

        # 監視タップ + SENSE線
        parts.append(
            f'<g class="hit" data-k="tap" tabindex="0" role="button" aria-label="監視タップ {name}">'
            f'<circle cx="988" cy="{y-16}" r="3.5" fill="var(--w-is)"/>'
            f'<path class="hitline" d="M988 {y-16} V{y+46} M952 {y+60} H280 M988 {y+86} V{y+96}"/>'
            f'<path d="M988 {y-16} V{y+46}" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>'
            f'<rect class="box" x="952" y="{y+46}" width="72" height="40" rx="5"/>'
            f'<text class="t-cap" x="988" y="{y+62}" text-anchor="middle">100k/22k</text>'
            f'<text class="t-cap" x="988" y="{y+78}" text-anchor="middle">3.3Vz</text>'
            f'<path d="M952 {y+60} H280" fill="none" stroke="var(--w-is)" stroke-width="1.6"/>'
            f'<path d="M988 {y+86} V{y+96}" fill="none" stroke="var(--w-gnd)" stroke-width="1.6"/>'
            f'{chassis(988, y+96, "var(--w-gnd)", 0.7)}'
            f'</g>'
        )

        # 灯具
        parts.append(
            f'<g class="hit" data-k="lamp" tabindex="0" role="button" aria-label="{name}">'
            f'<path class="hitline" d="M970 {y+12} H1220 M1250 {y+42} V{y+62}"/>'
            f'<path d="M970 {y+12} H1220" fill="none" stroke="var(--w-pos)" stroke-width="2.2"/>'
            f'<circle cx="1250" cy="{y+12}" r="30" fill="var(--box)" stroke="var(--box-line)" stroke-width="1.5"/>'
            f'<path d="M1229 {y-9} L1271 {y+33} M1229 {y+33} L1271 {y-9}" stroke="{lc}" stroke-width="2"/>'
            f'<text class="t-lab" x="1292" y="{y+8}">{name}</text>'
            f'<text class="t-cap" x="1292" y="{y+26}">LED・1灯=1ch</text>'
            f'<path d="M1250 {y+42} V{y+62}" fill="none" stroke="var(--w-neg)" stroke-width="2.2"/>'
            f'{chassis(1250, y+62, "var(--w-neg)", 0.8)}'
            f'</g>'
        )
        # ESPピンラベル
        parts.append(
            f'<text class="t-pin" x="274" y="{y+4}" text-anchor="end">PWM{i+1}</text>'
            f'<text class="t-pin" x="274" y="{y+64}" text-anchor="end">SEN{i+1}</text>'
        )
    return "".join(parts)

S.append(unit(Y0F, FRONT, 0, "フロントユニット", "エンジンルーム設置・10ch"))
S.append(unit(Y0R, REAR, 10, "リアユニット", "ラゲッジ設置・7ch"))

# ============ CANトランク(前後接続) ============
xf, xr = Y0F - 260, Y0R - 260
S.append(f'''
<g class="hit" data-k="can" tabindex="0" role="button" aria-label="CANバス">
  <path class="hitline" d="M32 {xf+16} V{xr+16} M24 {xf+36} V{xr+36}"/>
  <path d="M32 {xf+16} V{xr+16}" fill="none" stroke="var(--w-pwm)" stroke-width="2"/>
  <path d="M24 {xf+36} V{xr+36}" fill="none" stroke="var(--w-pwm)" stroke-width="2"/>
  <rect class="box" x="14" y="{xf+70}" width="36" height="20" rx="4"/>
  <text class="t-cap" x="32" y="{xf+84}" text-anchor="middle">120Ω</text>
  <rect class="box" x="14" y="{xr-40}" width="36" height="20" rx="4"/>
  <text class="t-cap" x="32" y="{xr-26}" text-anchor="middle">120Ω</text>
</g>
''')
# ツイスト表現(交差グリフ)+ラベル
for ty in (900, 1400, 1900, 2150):
    S.append(f'<path d="M24 {ty} L32 {ty+18} M32 {ty} L24 {ty+18}" stroke="var(--w-pwm)" stroke-width="2" fill="none"/>')
S.append(f'<text class="t-lab" x="44" y="1360" fill="var(--w-pwm)" transform="rotate(90 44 1360)">私設CAN 500kbps ツイストペア0.3sq(車両F-CANとは非接続)</text>')

svg = (f'<svg id="schematic" viewBox="0 0 {W} {H}" role="img" aria-label="全パーツ完全結線図">'
       + "".join(S) + "</svg>")

# 印刷用: 同じ描画内容をA4横4ページに分割して見せる(切断位置はch行の隙間)
# A4横(余白9mm)の描画域279x192mm → 1ページに入る高さ = 1660*192/279 ≈ 1142px
PRINT_CUTS = [0, 974, 2026, 3124, H]   # 前ch3/4間・前ユニット末尾・後ch4/5間
PP_NOTES = ["上段電源・操作系 + 前ユニット ch1-3", "前ユニット ch4-10",
            "前ユニット アレイ/GND + 後ユニット ch1-4", "後ユニット ch5-7 + アレイ/GND"]
body_all = "".join(S)
pp = []
for pi in range(4):
    y0p, y1p = PRINT_CUTS[pi], PRINT_CUTS[pi + 1]
    pp.append(
        f'<div class="pp"><div class="pp-head">全パーツ完全結線図 {pi+1}/4 — {PP_NOTES[pi]}'
        f'<span>ページ端で切れた縦線(B+・IG・純正線・CAN・コイル)は前後のページへ続く</span></div>'
        f'<svg viewBox="0 {y0p} {W} {y1p-y0p}" role="img" aria-label="完全結線図 {pi+1}/4">'
        + body_all + '</svg></div>')
print_pages = '<div class="print-pages">' + "".join(pp) + "</div>"

# ============ HTML ============
CSS = """
  :root {
    --bg: #f2f4f3; --surface: #ffffff; --box: #f5f7f6; --box-line: #c3cdc8;
    --ink: #212723; --muted: #5e6963; --line: #dbe1de; --accent: #a87413; --dot: #e2e7e4;
    --shadow: 0 10px 30px rgba(20, 30, 25, 0.18);
    --w-pwm: #2f6fb2; --w-en: #2f8659; --w-is: #7e58be; --w-vcc: #c07a16;
    --w-gnd: #78827c; --w-pos: #c2443a; --w-neg: #464d49;
    --danger: #b3372c; --danger-bg: #fbeeec; --danger-line: #ecc9c4;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #141816; --surface: #1c211f; --box: #242a27; --box-line: #47514c;
      --ink: #e6eae7; --muted: #949e98; --line: #323a36; --accent: #d9a644; --dot: #262d2a;
      --shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
      --w-pwm: #6faee6; --w-en: #5fbe8b; --w-is: #ad8fe0; --w-vcc: #e2a952;
      --w-gnd: #8d968f; --w-neg: #aab3ae; --w-pos: #e4756a;
      --danger: #e4756a; --danger-bg: #382320; --danger-line: #5a3630;
    }
  }
  :root[data-theme="light"] {
    --bg: #f2f4f3; --surface: #ffffff; --box: #f5f7f6; --box-line: #c3cdc8;
    --ink: #212723; --muted: #5e6963; --line: #dbe1de; --accent: #a87413; --dot: #e2e7e4;
    --shadow: 0 10px 30px rgba(20, 30, 25, 0.18);
    --w-pwm: #2f6fb2; --w-en: #2f8659; --w-is: #7e58be; --w-vcc: #c07a16;
    --w-gnd: #78827c; --w-pos: #c2443a; --w-neg: #464d49;
    --danger: #b3372c; --danger-bg: #fbeeec; --danger-line: #ecc9c4;
  }
  :root[data-theme="dark"] {
    --bg: #141816; --surface: #1c211f; --box: #242a27; --box-line: #47514c;
    --ink: #e6eae7; --muted: #949e98; --line: #323a36; --accent: #d9a644; --dot: #262d2a;
    --shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    --w-pwm: #6faee6; --w-en: #5fbe8b; --w-is: #ad8fe0; --w-vcc: #e2a952;
    --w-gnd: #8d968f; --w-pos: #e4756a; --w-neg: #aab3ae;
    --danger: #e4756a; --danger-bg: #382320; --danger-line: #5a3630;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Noto Sans JP", system-ui, sans-serif;
    font-size: 14.5px; line-height: 1.75; -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 1080px; margin: 0 auto; padding: 40px 24px 64px; }
  .eyebrow { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 11.5px;
    letter-spacing: 0.08em; color: var(--accent); margin: 0 0 6px; }
  h1 { font-size: 25px; font-weight: 700; margin: 0 0 10px; text-wrap: balance; line-height: 1.4; }
  .lead { color: var(--muted); margin: 0; max-width: 46em; }
  h2 { font-size: 16.5px; font-weight: 700; margin: 44px 0 14px; display: flex; align-items: center; gap: 10px; }
  h2::before { content: ""; width: 5px; height: 18px; border-radius: 2px; background: var(--accent); flex: none; }
  .hint { margin: -8px 0 12px; font-size: 12.5px; color: var(--muted); }
  .hint b { color: var(--accent); }
  .panel {
    background: var(--surface);
    background-image: radial-gradient(var(--dot) 1px, transparent 1px);
    background-size: 22px 22px;
    border: 1px solid var(--line); border-radius: 10px;
    overflow-x: auto; padding: 10px 6px;
  }
  .panel svg { display: block; min-width: 1560px; width: 100%; height: auto; }
  svg .box { fill: var(--box); stroke: var(--box-line); stroke-width: 1.5; }
  svg .t-ti { font: 700 14px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--ink); }
  svg .t-pin { font: 11px ui-monospace, "SF Mono", Menlo, monospace; fill: var(--ink); }
  svg .t-lab { font: 12px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--ink); }
  svg .t-cap { font: 11px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--muted); }
  svg text { user-select: none; }
  svg .hit { cursor: pointer; outline: none; }
  svg .hitline { stroke: transparent; stroke-width: 16; fill: none; pointer-events: stroke; }
  svg .hit:hover, svg .hit:focus-visible, svg .hit.sel { filter: drop-shadow(0 0 3px var(--accent)); }
  svg .hit:hover rect.box, svg .hit:focus-visible rect.box, svg .hit.sel rect.box { stroke: var(--accent); }
  .legend { display: flex; flex-wrap: wrap; gap: 8px 20px; margin: 12px 2px 0; font-size: 12.5px; color: var(--muted); }
  .legend span { display: inline-flex; align-items: center; gap: 7px; }
  .legend i { width: 18px; height: 4px; border-radius: 2px; display: inline-block; }
  .veil { position: fixed; inset: 0; z-index: 40; background: transparent; }
  .pop {
    position: fixed; z-index: 50; width: min(380px, calc(100vw - 24px));
    background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
    box-shadow: var(--shadow); padding: 14px 16px 12px;
  }
  @media (prefers-reduced-motion: no-preference) {
    .pop { animation: popin 0.13s ease-out; }
    @keyframes popin { from { opacity: 0; transform: translateY(5px) scale(0.98); } to { opacity: 1; transform: none; } }
  }
  .pop-head { display: flex; gap: 10px; align-items: flex-start; }
  .pop-chip { width: 12px; height: 12px; border-radius: 4px; margin-top: 6px; flex: none; }
  .pop-title { font-weight: 700; font-size: 14.5px; line-height: 1.5; }
  .pop-route { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 11.5px; color: var(--muted); margin-top: 1px; }
  .pop-x { margin-left: auto; flex: none; border: none; background: none; color: var(--muted);
    font-size: 20px; line-height: 1; cursor: pointer; padding: 2px 4px; border-radius: 6px; }
  .pop-x:hover { color: var(--ink); background: var(--box); }
  .pop-x:focus-visible { outline: 2px solid var(--accent); }
  .pop ul { margin: 10px 0 2px; padding-left: 18px; }
  .pop li { font-size: 12.8px; margin: 6px 0; line-height: 1.7; }
  .pop li::marker { color: var(--accent); }
  .tbl-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
  table { border-collapse: collapse; width: 100%; min-width: 680px; font-size: 13.5px; }
  th, td { text-align: left; padding: 9px 14px; border-top: 1px solid var(--line); vertical-align: top; }
  thead th { border-top: none; font-size: 12px; color: var(--muted); font-weight: 600;
    letter-spacing: 0.04em; padding-top: 12px; padding-bottom: 8px; }
  td.sig { white-space: nowrap; font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 12.5px; }
  .danger { background: var(--danger-bg); border: 1px solid var(--danger-line);
    border-left: 4px solid var(--danger); border-radius: 8px; padding: 14px 18px; }
  .danger ul { margin: 0; padding-left: 20px; }
  .danger li { margin: 4px 0; font-size: 13.5px; }
  .danger li::marker { color: var(--danger); }
  footer { margin-top: 48px; font-size: 12px; color: var(--muted); }
  .print-pages { display: none; }
  @page { size: A4 landscape; margin: 9mm; }
  @media print {
    :root, :root[data-theme="dark"], :root[data-theme="light"] {
      --bg: #fff; --surface: #fff; --box: #fff; --box-line: #999;
      --ink: #111; --muted: #444; --line: #bbb; --accent: #8a6010; --dot: #fff;
      --shadow: none;
      --w-pwm: #2f6fb2; --w-en: #2f8659; --w-is: #6d48ae; --w-vcc: #a86a10;
      --w-gnd: #666; --w-pos: #b23a30; --w-neg: #333;
      --danger: #a03026; --danger-bg: #fff; --danger-line: #bbb;
    }
    body { background: #fff; font-size: 12.5px; }
    .wrap { max-width: none; padding: 0; }
    .panel { display: none; }
    .print-pages { display: block; }
    .pp { break-before: page; }
    .pp-head { display: flex; justify-content: space-between; align-items: baseline;
      font: 700 12px "Hiragino Sans", sans-serif; color: #333; margin: 0 0 4px; }
    .pp-head span { font-weight: 400; font-size: 10px; color: #777; }
    .pp svg { display: block; width: 100%; height: auto; }
    h2 { break-before: page; margin-top: 0; }
    h2, .hint { break-after: avoid; }
    .tbl-wrap, table { min-width: 0; }
    tr { break-inside: avoid; }
    thead { display: table-header-group; }
    .danger, .legend { break-inside: avoid; }
    h1 { font-size: 20px; }
    .lead { font-size: 11.5px; }
    .veil, .pop { display: none !important; }
    a { color: inherit; text-decoration: none; }
  }
"""

DATA_JS = """
    mac: { title: "Mac(唯一の操作点)", route: "USBシリアル(主) / Wi-Fi(副) → ESP①",
      color: "var(--w-pwm)", items: [
      "自作アプリ / DAW+MIDIキーボードの操作を全てここに集約。ESP側にMIDI機器は接続しない。",
      "主経路はUSBシリアル(有線・往復1〜2ms)。ケーブルはフェライト付き・車内配索長。",
      "Wi-Fiは物理配線が無いので図では波線グリフのみ。プリセット送信・モニタ用の副経路。",
      "リア側への指示はESP①がCAN経由で中継する。MacとESP②は直接つながらない。" ] },
    bat: { title: "バッテリー・B+幹線", route: "12V → F20A → 前バス / 後トランク(2.0sq)",
      color: "var(--w-vcc)", items: [
      "全灯LED化後の最大負荷は約12A。メイン20Aヒューズはバッテリー直後に配置。",
      "分岐点から前バス(x=540の縦線)と後トランクに分岐。後方へ");
      ] },
"""

# DATA_JS は文字列内にバグを作りやすいので、素直に全文をここで定義し直す
DATA_JS = """
    mac: { title: "Mac(唯一の操作点)", route: "USBシリアル(主) / Wi-Fi(副) → ESP①",
      color: "var(--w-pwm)", items: [
      "自作アプリ / DAW+MIDIキーボードの操作を全てここに集約。ESP側にMIDI機器は接続しない。",
      "主経路はUSBシリアル(有線・往復1〜2ms)。フェライト付き・車内配索長のUSB-Cケーブル。",
      "Wi-Fiは無線なので図では波線グリフのみ。プリセット・モニタ用の副経路。",
      "リアへの指示はESP①がCANで中継。MacとESP②は直接つながらない。" ] },
    bat: { title: "バッテリー・B+幹線", route: "12V → F20A → 前バス / 後トランク 2.0sq",
      color: "var(--w-vcc)", items: [
      "全LED化後の最大負荷は約12A。メイン20Aヒューズはバッテリー直後。",
      "縦線(x=540)が各ユニットのB+バス。各chはここから5Aヒューズを経てハイサイドSWへ。",
      "後トランクは右端を通って床下配索でリアユニットまで2.0sqを延長。",
      "バッテリー−は車体へ(純正のまま)。自作系のGNDも最終的に車体一点アースで合流。" ] },
    ig: { title: "IG電源(コイル用)", route: "IGヒューズ → 前後IGバス → 各リレー86",
      color: "var(--w-vcc)", items: [
      "キーONの間だけ通電する系統。リレーコイルの+側(86)は全てここから取る。",
      "キーOFFでは物理的に励磁できない=必ず純正側に戻るフェールセーフの一段目。",
      "コイル電流は約150mA×17個(全励磁時 約2.6A)。IG分岐にもヒューズを入れる。" ] },
    stockbox: { title: "純正ヒューズBOX / スイッチ(車両側)", route: "純正操作 → 各灯への純正線17本",
      color: "var(--w-vcc)", items: [
      "ライトSW・ウィンカーレバー・ブレーキペダルなど純正操作の出口。ここは一切改造しない。",
      "図の17本は分岐後の各灯への純正線。フォグ左右のように1ヒューズから分かれた後を灯具毎に扱う。",
      "ドアミラーウィンカーは17chの対象外なので、カット点より上流に残り純正のまま動く。" ] },
    stock: { title: "純正線(灯具毎・カット対象)", route: "純正分岐後 → 87a(NC)",
      color: "var(--w-vcc)", items: [
      "純正ハーネスの分岐より下流・灯具コネクタ直前でリレーに割り込む。切断せず原状復帰可能。",
      "灯具毎に切る理由: 分岐より上流で切ると、下流で+線がつながっている灯同士に別々のPWMを流せないため。",
      "無励磁の間はこの線がNC接点経由でそのまま灯具へ=納車状態と同一。" ] },
    esp: { title: "ESP32-S3(前後各1台)", route: "PWM×ch / SEL×ch / SENSE×ch / TWAI",
      color: "var(--accent)", items: [
      "右辺: PWM(灯毎の調光)とSENSE(純正入力の監視)を各ch1本ずつ。",
      "下辺: SEL(リレーコイル選択)を各ch1本。トランジスタアレイ経由でコイルを個別駆動。",
      "前=10ch(LEDC8+MCPWM2)、後=7ch(LEDC)。既存確定ピンGPIO4/5/2は使わない。",
      "起動時は全PWM 0%・全SEL LOW(純正側)で初期化。" ] },
    dcdc: { title: "DCDC 12V→5V(各ユニット1個)", route: "B+バス → DCDC → ESP 5V",
      color: "var(--accent)", items: [
      "車載対応(サージ・逆接耐性)の降圧コンバータ。USB給電は机上テスト専用。",
      "出力3A級でESP+トランシーバ+アレイのロジック分を賄う。",
      "GNDはユニットのGNDバスバーへ。" ] },
    can: { title: "私設CANリンク", route: "ESP① TWAI ↔ SN65HVD230 ↔ ツイストペア ↔ ESP②",
      color: "var(--w-pwm)", items: [
      "ESP内蔵のCANコントローラ(TWAI)は3.3VのTX/RXしか出せない。差動信号(CANH/CANL)への変換がトランシーバの役割。",
      "主目的は前後間の配線削減: リア7ch分の指示が2本のツイストペアで済む。",
      "両端に120Ω終端。基板に実装済みの製品なら重複しないよう片方を外す。",
      "車両のF-CAN(can-liveの受信対象)とは物理的に非接続。" ] },
    array: { title: "トランジスタアレイ TBD62083", route: "SEL n → IN n / OUT n → リレー85",
      color: "var(--w-en)", items: [
      "8ch/石のシンクドライバ・還流ダイオード内蔵。前10chは2石、後7chは1石。",
      "コイル片側は常時IG12V(86)、もう片側(85)をアレイがGNDへ引くと励磁=純正カット。",
      "COM端子を12VへつなぐとコイルOFF時の逆起電力を内蔵ダイオードが吸収。",
      "個別MOSFET×17と比べ部品点数と配線量を大幅削減。" ] },
    sw: { title: "スマートハイサイドSW(各ch)", route: "B+ → F5A → SW → 87(NO)",
      color: "var(--w-pos)", items: [
      "PWM 1kHz対応品番を選ぶ(BTS443P級)。過電流・過熱・短絡・逆接保護内蔵。",
      "ESPのPWM(青破線・3.3V)を受け、12Vを高速ON/OFFして調光。原理はBTS7960と同一。",
      "ch毎5Aヒューズは下流0.75sq線の保護。",
      "リレーが純正側の間は出力先が開放なので、PWMが出ていても灯具には流れない。" ] },
    relay: { title: "切替リレー(灯具毎に1個・計17個)", route: "30=灯具+ / 87a=純正 / 87=自作 / 86=IG / 85=アレイ",
      color: "var(--accent)", items: [
      "エーモン3237級(DC12V・接点20A)。C接点の排他構造で純正と自作が同時につながることはない。",
      "無励磁=87a(純正)。ESP停止・電源断・キーOFF・暴走のどれでも納車状態へ戻る。",
      "灯具毎に置く理由: 純正分岐の下流で切らないと1灯=1chの個別制御と両立しないため。",
      "切替は約10msの瞬断。演出用途では無視できる。" ] },
    coil: { title: "コイル駆動線(系統選択)", route: "リレー85 → アレイOUT n",
      color: "var(--w-en)", items: [
      "緑の線。ch毎に独立しており、割り込みたい灯のリレーだけを励磁できる。",
      "左ウィンカー演出のように前後にまたがる場合は、ESP①→CAN→ESP②で両ユニットのSELを同期。",
      "旧案の「1ピンで全回路一括切替」から変更した部分。" ] },
    tap: { title: "純正入力モニタ(分圧タップ・各ch)", route: "純正線 → 100kΩ/22kΩ+3.3Vz → SENSE n",
      color: "var(--w-is)", items: [
      "純正線の12V/0Vを約2.2V/0Vに落としてGPIOで読む。「純正が今点けようとしているか」の検出。",
      "充電中14.5Vでも約2.6V。3.3Vツェナーはサージ保護の保険。",
      "合計122kΩのハイインピーダンスで純正回路への影響は約0.1mA=無視できる。",
      "割り込み中にブレーキ踏下を検知→即時純正復帰、純正ウィンカーのリズム検出などに使う。" ] },
    lamp: { title: "LED灯具(17灯)", route: "リレー30 → 灯具+ / 灯具− → ボディアース",
      color: "var(--w-pos)", items: [
      "−は純正どおりボディアース。改造は+側への割り込み1点だけ。",
      "割り込み中は1kHz+/γ2.2/4096段階のPWMプロファイルで個別調光。",
      "テール/ブレーキ/ハイマウントは純正LEDユニット流用。調光可否はベンチ判定(最悪ON/OFF)。",
      "ウィンカーの純正復帰時はLED対応フラッシャーが必要(ハイフラ防止)。" ] },
    gnd: { title: "GND系統", route: "ESP/DCDC/アレイ → GNDバスバー → 車体一点アース",
      color: "var(--w-gnd)", items: [
      "ユニット内の小信号GNDはバスバーに集約し、車体へ一点で落とす。",
      "灯具−とタップのGNDは純正どおり近傍のボディアース。大電流は自作GND線を通らない。",
      "「灯具−はM−へ戻す」規則は旧BTS7960構成のみ。本構成では適用しない。" ] }
"""

POPUP_JS = """
(function () {
  var DATA = {%DATA%};
  var svg   = document.getElementById("schematic");
  var pop   = document.getElementById("pop");
  var veil  = document.getElementById("veil");
  var chip  = document.getElementById("pop-chip");
  var title = document.getElementById("pop-title");
  var route = document.getElementById("pop-route");
  var body  = document.getElementById("pop-body");
  var btnX  = document.getElementById("pop-x");
  var current = null;
  function closePop() {
    pop.hidden = true; veil.hidden = true;
    if (current) { current.classList.remove("sel"); current = null; }
  }
  function openPop(g, x, y) {
    var d = DATA[g.dataset.k];
    if (!d) return;
    if (current) current.classList.remove("sel");
    current = g; g.classList.add("sel");
    chip.style.background = d.color;
    title.textContent = d.title;
    route.textContent = d.route;
    body.innerHTML = "";
    d.items.forEach(function (t) {
      var li = document.createElement("li");
      li.textContent = t; body.appendChild(li);
    });
    veil.hidden = false; pop.hidden = false;
    var w = pop.offsetWidth, h = pop.offsetHeight;
    var left = Math.max(12, Math.min(x + 14, window.innerWidth - w - 12));
    var top  = y + 16;
    if (top + h > window.innerHeight - 12) top = Math.max(12, y - h - 16);
    pop.style.left = left + "px"; pop.style.top = top + "px";
  }
  svg.addEventListener("click", function (e) {
    var g = e.target.closest(".hit"); if (!g) return;
    openPop(g, e.clientX, e.clientY);
  });
  svg.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var g = e.target.closest(".hit"); if (!g) return;
    e.preventDefault();
    var r = g.getBoundingClientRect();
    openPop(g, r.left + r.width / 2, r.top + r.height / 2);
  });
  veil.addEventListener("click", closePop);
  btnX.addEventListener("click", closePop);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closePop(); });
})();
""".replace("{%DATA%}", "{" + DATA_JS + "}")

BODY_TOP = """
<div class="wrap">
  <p class="eyebrow">micro-control / full-wiring(no-omission)</p>
  <h1>全パーツ完全結線図 — 17ch個別制御+純正割り込みカット</h1>
  <p class="lead">Mac 1台 → 前後 ESP32-S3 → ハイサイドSW×17 → 切替リレー×17 → LED灯具×17。
  パーツと配線を省略せず全て図示。バス(縦の幹線)から各chへの分岐点はドットで示す。図はクリックで詳細を表示。</p>

  <h2>完全結線図(縦に長い。横スクロール・クリック対応)</h2>
  <p class="hint"><b>リレーは灯具毎に1個・計17個に変更。</b>純正分岐の下流で切らないと「1灯=1ch」と両立しないため。
  緑=コイル駆動 / 紫=純正入力の監視 / 青破線=PWM / 橙=12V電源・純正線 / 赤=自作出力。<br><b>実装方式は2026-08-03に変更あり</b>: 切替リレー+コイル駆動は既製8chリレーモジュール(ドライバ内蔵・TBD62083不要)で実装する。本図のリレー・アレイ表記は論理接続として読み、実体配置は board-layout-17ch.html を正とする。</p>
"""

BODY_BOTTOM = """
  <div class="legend">
    <span><i style="background:var(--w-vcc)"></i>12V電源系(B+・IG・純正線)</span>
    <span><i style="background:var(--w-pos)"></i>自作出力 12V(SW→リレー→灯具)</span>
    <span><i style="background:var(--w-pwm)"></i>PWM(破線)/ CAN・USB(実線)</span>
    <span><i style="background:var(--w-en)"></i>SEL・コイル駆動</span>
    <span><i style="background:var(--w-is)"></i>SENSE 監視</span>
    <span><i style="background:var(--w-gnd)"></i>GND</span>
    <span><i style="background:var(--accent)"></i>5V ロジック電源</span>
  </div>

  <h2>部品点数(この図に描かれている全て)</h2>
  <div class="tbl-wrap">
  <table>
    <thead><tr><th>パーツ</th><th>数</th><th>図中の位置</th></tr></thead>
    <tbody>
      <tr><td>Mac</td><td class="sig">1</td><td>最上段左。USBシリアルでESP①へ</td></tr>
      <tr><td>ESP32-S3</td><td class="sig">2</td><td>前後ユニットの左側の大きな箱</td></tr>
      <tr><td>CANトランシーバ SN65HVD230</td><td class="sig">2</td><td>各ESPの左上。左端の2本線が前後を結ぶ</td></tr>
      <tr><td>終端抵抗 120Ω</td><td class="sig">2</td><td>CAN線の両端</td></tr>
      <tr><td>DCDC 12V→5V</td><td class="sig">2</td><td>各ESPの右上</td></tr>
      <tr><td>トランジスタアレイ TBD62083</td><td class="sig">3</td><td>各ESPの下(前2石・後1石)</td></tr>
      <tr><td>スマートハイサイドSW</td><td class="sig">17</td><td>各ch行の中央。PWM対応品番</td></tr>
      <tr><td>ch毎ヒューズ 5A</td><td class="sig">17</td><td>各SWの左上(B+バスから分岐)</td></tr>
      <tr><td>切替リレー(エーモン3237級)</td><td class="sig">17</td><td>各ch行の右側。灯具毎に1個</td></tr>
      <tr><td>監視タップ(100k/22k+3.3Vz)</td><td class="sig">17</td><td>各リレーの右下。純正線→SENSE</td></tr>
      <tr><td>LED灯具</td><td class="sig">17</td><td>右端の丸。−はボディアース</td></tr>
      <tr><td>メインヒューズ 20A</td><td class="sig">1</td><td>バッテリー直後</td></tr>
      <tr><td>GNDバスバー</td><td class="sig">2</td><td>各ユニット最下部→車体一点アース</td></tr>
    </tbody>
  </table>
  </div>

  <h2>安全要件</h2>
  <div class="danger">
    <ul>
      <li><b>前提: 走行中は使わない(ショー・停車時専用)。</b>この前提をファームでも強制する — 停車条件を満たすショーモード中のみSELを許可するインターロック(誤操作・実装ミス対策)。</li>
      <li><b>ブレーキ系統は最優先:</b>割り込み中にSENSEでブレーキ踏下を検知したら無条件で即時純正復帰(または自作側で再現)。</li>
      <li>起動時は全SEL=LOW(純正側)+全PWM 0%で初期化。既存確定ピン GPIO4/5/2 は変更禁止。</li>
      <li>無励磁=純正のC接点構成により、ESP停止・電源断・キーOFFのどれでも納車状態に戻る。</li>
      <li>ウィンカーの純正復帰時はLED対応フラッシャー必須(ハイフラ防止)。</li>
    </ul>
  </div>

  <footer>リレー数は灯具毎17個に確定(純正分岐下流でのカットが1灯=1chの前提)。純正分岐の実配置は実車ハーネス調査で最終確認。2026-08-02(印刷対応 2026-08-03: A4横4分割・PDF版 full-wiring-17ch.pdf)。</footer>
</div>

<div id="veil" class="veil" hidden></div>
<div id="pop" class="pop" role="dialog" aria-modal="false" hidden>
  <div class="pop-head">
    <i id="pop-chip" class="pop-chip"></i>
    <div>
      <div id="pop-title" class="pop-title"></div>
      <div id="pop-route" class="pop-route"></div>
    </div>
    <button id="pop-x" class="pop-x" aria-label="閉じる">×</button>
  </div>
  <ul id="pop-body"></ul>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>全パーツ完全結線図 — 17ch+割り込みカット</title>\n"
        "<style>" + CSS + "</style>\n"
        + BODY_TOP
        + '<div class="panel">' + svg + "</div>\n"
        + print_pages + "\n"
        + BODY_BOTTOM
        + "<script>" + POPUP_JS + "</script>\n")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
