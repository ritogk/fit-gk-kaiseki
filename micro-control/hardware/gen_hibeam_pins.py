# -*- coding: utf-8 -*-
# ハイビーム実験(hibeam_live)のピン単位の配線図。ESPのピン → HW-039の8ピンヘッダ・ネジ端子 → ランプ(ライトモード専用)
# HW-039のヘッダ順は IBT_2 の一般的な表記(1 RPWM ... 8 GND)。基板のシルク印刷で必ず照合する。
import io, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hibeam-pins.html")
src = io.open(os.path.join(HERE, "gen_simple_one_lamp.py"), encoding="utf-8").read()
CSS = re.search(r"<style>(.*?)</style>", src, re.S).group(1).replace("{{", "{").replace("}}", "}")
CSS += """
.hdr{fill:#fff;stroke:#343a40;stroke-width:2}
.pinbox{fill:#f8f9fa;stroke:#343a40;stroke-width:1.5}
.nc{fill:#f1f3f5;stroke:#adb5bd;stroke-width:1.5;stroke-dasharray:4 3}
.clip{fill:#fff4e6;stroke:#e67700;stroke-width:2}
.unplug{fill:#f1f3f5;stroke:#adb5bd;stroke-width:2;stroke-dasharray:6 4}
"""
def gnd(x, y):
    return f'<path d="M{x-14} {y} H{x+14} M{x-9} {y+5} H{x+9} M{x-4} {y+10} H{x+4}" class="w gndw"/>'
def clip(x, y):
    return f'<rect x="{x-10}" y="{y-7}" width="20" height="14" rx="4" class="clip"/>'

s = ['<svg viewBox="0 0 1100 640" role="img" aria-label="ESP32-S3とHW-039のピン単位の配線図">']
# ---- ESP32-S3 ----
EP = {"GPIO4": 150, "GPIO6": 194, "GPIO5": 238, "3V3": 414, "GND": 458}
s.append('<rect x="40" y="100" width="170" height="400" rx="8" class="box"/>'
         '<text x="125" y="126" class="ttl" text-anchor="middle">ESP32-S3</text>'
         '<text x="125" y="520" class="lbl" text-anchor="middle">基板のシルク印刷で探す</text>'
         '<text x="125" y="540" class="lbl" text-anchor="middle">USBはUART側→Mac</text>')
for n, y in EP.items():
    s.append(f'<rect x="150" y="{y-12}" width="60" height="24" rx="4" class="pinbox"/>'
             f'<text x="180" y="{y+5}" class="pin" text-anchor="middle">{n}</text>')
# ---- HW-039 header ----
HX = 470
HP = [("1", "RPWM"), ("2", "LPWM"), ("3", "R_EN"), ("4", "L_EN"), ("5", "R_IS"), ("6", "L_IS"), ("7", "VCC"), ("8", "GND")]
HY = {n: 150 + i*44 for i, (n, _) in enumerate(HP)}
s.append(f'<rect x="{HX-30}" y="70" width="300" height="470" rx="10" class="bts"/>'
         f'<text x="{HX+120}" y="96" class="ttl" text-anchor="middle">HW-039(IBT_2)</text>'
         f'<text x="{HX+120}" y="114" class="lbl" text-anchor="middle">左: 8ピンヘッダ / 右: ネジ端子</text>')
for n, lab in HP:
    y = HY[n]; nc = n in ("5", "6")
    s.append(f'<rect x="{HX-12}" y="{y-12}" width="24" height="24" rx="3" class="{"nc" if nc else "pinbox"}"/>'
             f'<text x="{HX}" y="{y+5}" class="pin" text-anchor="middle">{n}</text>'
             f'<text x="{HX+20}" y="{y+5}" class="pin{" dim" if nc else ""}">{lab}{"(空き)" if nc else ""}</text>')
# ESP → header wires
def wire(y0, y1, cls, xm):
    return f'<path d="M210 {y0} H{xm} V{y1} H{HX-12}" class="w {cls}"/>'
s.append(wire(EP["GPIO4"], HY["1"], "sigw", 300))
s.append(wire(EP["GPIO6"], HY["2"], "sigw", 320))
s.append(wire(EP["GPIO5"], HY["3"], "ctlw", 340))
s.append(f'<path d="M340 {HY["3"]} V{HY["4"]} H{HX-12}" class="w ctlw"/><circle cx="340" cy="{HY["3"]}" r="4" class="dot"/>')
s.append(f'<text x="390" y="{HY["4"]-8}" class="lbl" text-anchor="middle">3と4を束ねる</text>')
s.append(wire(EP["3V3"], HY["7"], "ctlw", 360))
s.append(wire(EP["GND"], HY["8"], "gndw", 380))
# ---- ネジ端子(表から見て上から M−, M+, B+, B−。裏の印刷で確認済み) ----
TX = 700
TP = [("M−", 180), ("M+", 250), ("B+", 340), ("B−", 420)]
for n, y in TP:
    s.append(f'<rect x="{TX-22}" y="{y-16}" width="44" height="32" rx="4" class="part"/>'
             f'<circle cx="{TX}" cy="{y}" r="7" class="pinbox"/><path d="M{TX-5} {y} H{TX+5}" class="w"/>'
             f'<text x="{TX-30}" y="{y+5}" class="pin" text-anchor="end">{n}</text>')
s.append(f'<text x="{TX}" y="470" class="lbl" text-anchor="middle">上から M−・M+・B+・B−</text>')
def hop(x):  # 縦線をまたぐ半円
    return f" H{x-8} A8 8 0 0 1 {x+8}"
# 電源(上): バッテリー → ヒューズブロック15A → B+
s.append('<rect x="770" y="20" width="130" height="50" rx="8" class="box"/>'
         '<text x="835" y="42" class="ttl" text-anchor="middle">バッテリー</text>'
         '<text x="835" y="60" class="lbl" text-anchor="middle">12V +</text>')
s.append('<rect x="930" y="16" width="150" height="80" rx="8" class="box"/>'
         '<text x="1005" y="36" class="ttl" text-anchor="middle">ヒューズ</text>'
         '<rect x="985" y="50" width="40" height="30" rx="5" class="part"/><text x="1005" y="70" class="lbl" text-anchor="middle">15A</text>')
s.append('<path d="M900 45 H930" class="w pw"/>')
s.append(f'<path d="M1005 80 V120 H760 V340 H{TX+22}" class="w pw"/>')
s.append('<text x="880" y="114" class="lbl" text-anchor="middle">2.0sq</text>')
# ランプ
def lamp(y, name):
    x = 930
    return (f'<rect x="{x}" y="{y-34}" width="40" height="68" rx="6" class="box"/>'
            f'<text x="{x+14}" y="{y-12}" class="pin">+</text><text x="{x+14}" y="{y+26}" class="pin">−</text>'
            f'<circle cx="{x+90}" cy="{y}" r="24" class="lamp"/>'
            f'<path d="M{x+74} {y-16} L{x+106} {y+16} M{x+106} {y-16} L{x+74} {y+16}" class="w lampx"/>'
            f'<path d="M{x+40} {y-16} H{x+66} M{x+40} {y+16} H{x+66}" class="w"/>'
            f'<text x="{x+60}" y="{y-44}" class="ttl" text-anchor="middle">{name}</text>')
LY, RY = 210, 350
s.append(f'<path d="M{TX+22} 180{hop(760)} 180 H820 V{LY-16} H930" class="w outw"/>' + clip(880, LY-16))
s.append(f'<path d="M{TX+22} 250{hop(760)} 250 H800 V{RY-16}{hop(905)} {RY-16} H930" class="w outw"/>' + clip(870, RY-16))
s.append(lamp(LY, "ハイビーム 左(M−)")); s.append(lamp(RY, "ハイビーム 右(M+)"))
s.append(f'<path d="M930 {LY+16} H905 V{RY+16} H930" class="w gndw"/>' + clip(918, LY+16) + clip(918, RY+16))
s.append(f'<path d="M905 {RY+16} V580" class="w gndw"/><circle cx="905" cy="{RY+16}" r="4" class="dotg"/>')
s.append(f'<path d="M{TX+22} 420 H740 V580 H905" class="w gndw"/><circle cx="905" cy="580" r="4" class="dotg"/>')
s.append('<path d="M905 580 V596" class="w gndw"/>' + gnd(905, 596))
s.append('<text x="885" y="624" class="lbl" text-anchor="end">バッテリー−(車体)</text>')
s.append('</svg>')
svg = "\n".join(s)

html = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ハイビーム ピン配線</title>
<style>{CSS}</style></head><body><main>
<h1>ハイビーム調光(hibeam_live)のピン配線図</h1>
<p>ESP32-S3のピン、HW-039の8ピンヘッダ、ネジ端子、ランプ側コネクタの順に、1本ずつ行き先を描いています。ファームウェアは firmware/hibeam_live です。</p>
<div class="card">{svg}</div>
<p class="legend"><span><i style="background:var(--pw)"></i>12V入力</span><span><i style="background:var(--out)"></i>ランプへの出力</span><span><i style="background:var(--sig)"></i>PWM信号</span><span><i style="background:var(--ctl)"></i>3.3V・出力許可</span><span><i style="background:var(--gnd)"></i>GND</span><span><i style="background:#e67700"></i>ワニ口クリップ</span></p>

<h2>信号線(ESP32-S3 → HW-039ヘッダ)</h2>
<div class="card"><table>
<tr><th>ESP32-S3</th><th>HW-039ヘッダ</th><th>役割</th></tr>
<tr><td>GPIO4</td><td>1 RPWM</td><td>右の明るさ(PWM 1kHz)</td></tr>
<tr><td>GPIO6</td><td>2 LPWM</td><td>左の明るさ(PWM 1kHz)</td></tr>
<tr><td>GPIO5</td><td>3 R_EN と 4 L_EN(束ねる)</td><td>出力許可。起動時はLOW</td></tr>
<tr><td>(なし)</td><td>5 R_IS・6 L_IS</td><td>つながない</td></tr>
<tr><td>3V3</td><td>7 VCC</td><td>ロジック電源</td></tr>
<tr><td>GND</td><td>8 GND</td><td>信号の基準</td></tr>
</table></div>

<h2>電源線・出力線(ネジ端子)</h2>
<div class="card"><table>
<tr><th>端子(上から)</th><th>つなぐ先</th><th>線</th></tr>
<tr><td>1 M−</td><td>クリップで、左ハイビームのランプ側+端子</td><td>2.0sq</td></tr>
<tr><td>2 M+</td><td>クリップで、右ハイビームのランプ側+端子</td><td>2.0sq</td></tr>
<tr><td>3 B+</td><td>15Aヒューズ → バッテリー+</td><td>2.0sq</td></tr>
<tr><td>4 B−</td><td>バッテリー−(車体)</td><td>2.0sq</td></tr>
<tr><td>(ランプ側−端子)</td><td>クリップで、左右ともバッテリー−(車体)</td><td>2.0sq</td></tr>
</table></div>
<p>HW-039のヘッダの並び(1 RPWM〜8 GND)は、IBT_2の一般的な表記に合わせています。基板によって印刷が異なる場合があるため、つなぐ前に基板のシルク印刷と照合してください。ネジ端子の並びは基板裏の印刷(M−、M+、B+、B−)で確認済みで、表から見ると上からこの順になります(B−がコンデンサ寄り)。</p>
</main></body></html>'''
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT)
