# -*- coding: utf-8 -*-
# ESP32-S3 + HW-039 + 8chリレーモジュール(2ch使用)でハイビーム左右を制御する配線図(ライトモード専用)
import io, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hibeam-relay.html")
src = io.open(os.path.join(HERE, "gen_simple_one_lamp.py"), encoding="utf-8").read()
CSS = re.search(r"<style>(.*?)</style>", src, re.S).group(1).replace("{{", "{").replace("}}", "}")
CSS += """
.stw { stroke:#7048e8; stroke-dasharray:7 5; } .selw { stroke:#e67700; }
.rly { fill:#eef4ff; stroke:#1c4fa0; stroke-width:2; } .ch { fill:#fff; stroke:#1c4fa0; stroke-width:1.5; }
.end { fill:#fff; stroke:#5b6675; stroke-width:1.5; }
"""

def gnd(x, y):
    return f'<path d="M{x-14} {y} H{x+14} M{x-9} {y+5} H{x+9} M{x-4} {y+10} H{x+4}" class="w gndw"/>'

def lamp(x, y, name):
    return (f'<circle cx="{x}" cy="{y}" r="24" class="lamp"/>'
            f'<path d="M{x-16} {y-16} L{x+16} {y+16} M{x+16} {y-16} L{x-16} {y+16}" class="w lampx"/>'
            f'<text x="{x+34}" y="{y+5}" class="ttl">{name}</text>'
            f'<path d="M{x} {y+24} V{y+36}" class="w gndw"/>' + gnd(x, y+36))

def channel(y, n):
    # NO=左, NC/COM=右
    return (f'<rect x="780" y="{y}" width="160" height="90" rx="8" class="ch"/>'
            f'<text x="860" y="{y+50}" class="ttl" text-anchor="middle">CH{n}</text>'
            f'<text x="788" y="{y+49}" class="pin">NO</text>'
            f'<text x="932" y="{y+29}" class="pin" text-anchor="end">NC</text>'
            f'<text x="932" y="{y+69}" class="pin" text-anchor="end">COM</text>')

s = ['<svg viewBox="0 0 1240 620" role="img" aria-label="HW-039とリレーモジュールでハイビーム左右を制御する配線図">']
# ESP
s.append('<rect x="40" y="140" width="170" height="310" rx="8" class="box"/>'
         '<text x="125" y="166" class="ttl" text-anchor="middle">ESP32-S3</text>')
for n, y, c in [("3V3", 190, "ctlw"), ("GPIO4", 230, "sigw"), ("GPIO6", 270, "sigw"), ("GPIO5", 310, "ctlw"), ("GND", 370, "gndw")]:
    s.append(f'<text x="200" y="{y+4}" class="pin" text-anchor="end">{n}</text><path d="M210 {y} H400" class="w {c}"/>')
s.append('<path d="M330 310 V335 H400" class="w ctlw"/><circle cx="330" cy="310" r="4" class="dot"/>')
s.append('<text x="305" y="222" class="lbl" text-anchor="middle">PWM(右)</text>'
         '<text x="305" y="262" class="lbl" text-anchor="middle">PWM(左)</text>'
         '<text x="270" y="302" class="lbl" text-anchor="middle">出力許可</text>')
s.append('<text x="200" y="414" class="pin" text-anchor="end">GPIO9</text>'
         '<path d="M210 410 H350 V470 H760 M735 470 V490 H760" class="w selw"/>'
         '<circle cx="735" cy="470" r="4" fill="#e67700"/>'
         '<text x="500" y="462" class="lbl" text-anchor="middle">純正/自作の切替</text>')
# HW-039
s.append('<rect x="400" y="110" width="240" height="320" rx="10" class="bts"/>'
         '<text x="520" y="136" class="ttl" text-anchor="middle">HW-039(IBT_2)</text>'
         '<text x="520" y="154" class="lbl" text-anchor="middle">BTS7960 ×2</text>')
for n, y in [("VCC", 190), ("RPWM", 230), ("LPWM", 270), ("R_EN", 310), ("L_EN", 335), ("GND", 370)]:
    s.append(f'<text x="410" y="{y+4}" class="pin">{n}</text>')
for n, y in [("B+", 190), ("M+", 245), ("M−", 320), ("B−", 370)]:
    s.append(f'<text x="630" y="{y+4}" class="pin" text-anchor="end">{n}</text>')
# 電源
s.append('<rect x="440" y="20" width="130" height="56" rx="8" class="box"/>'
         '<text x="505" y="44" class="ttl" text-anchor="middle">バッテリー</text>'
         '<text x="505" y="64" class="lbl" text-anchor="middle">12V +</text>')
s.append('<path d="M570 48 H700 V90 M700 120 V190 H640" class="w pw"/>'
         '<rect x="682" y="90" width="36" height="30" rx="5" class="part"/>'
         '<text x="700" y="110" class="lbl" text-anchor="middle">15A</text>'
         '<text x="676" y="110" class="lbl" text-anchor="end">ヒューズ</text>')
# リレーモジュール
s.append('<rect x="760" y="160" width="200" height="390" rx="10" class="rly"/>'
         '<text x="860" y="184" class="ttl" text-anchor="middle">8chリレーモジュール</text>')
s.append(channel(200, 1)); s.append(channel(340, 2))
for n, y in [("IN1", 470), ("IN2", 490), ("VCC(ESPの3V3へ)", 512), ("GND", 534)]:
    s.append(f'<text x="770" y="{y+4}" class="pin">{n}</text>')
s.append('<path d="M760 512 H742" class="w ctlw"/><circle cx="738" cy="512" r="4" class="end"/>')
s.append('<text x="950" y="538" class="pin" text-anchor="end">JD-VCC</text>'
         '<path d="M960 534 H990" class="w pw" style="stroke-width:3"/><circle cx="994" cy="534" r="4" class="end"/>'
         '<text x="1004" y="538" class="lbl">IG 12V(キーONで12V)へ</text>')
# HW → NO
s.append('<path d="M640 245 H780" class="w outw"/><path d="M640 320 H725 V385 H780" class="w outw"/>')
# NC ← 純正線
for y, lr in [(225, "右"), (365, "左")]:
    s.append(f'<path d="M940 {y} H1060" class="w stw"/><circle cx="1064" cy="{y}" r="4" class="end"/>'
             f'<text x="1074" y="{y+4}" class="lbl">純正の{lr}ハイビーム線(車両側)</text>')
# COM → ランプ
s.append('<path d="M940 265 H986" class="w outw"/><path d="M940 405 H986" class="w outw"/>')
s.append(lamp(1010, 265, "ハイビーム 右")); s.append(lamp(1010, 405, "ハイビーム 左"))
# GND
s.append('<path d="M640 370 H665 V580 H1150 V590 M760 534 H720 V580" class="w gndw"/>'
         '<circle cx="720" cy="580" r="4" class="dotg"/>')
s.append(gnd(1150, 590))
s.append('<text x="1120" y="602" class="lbl" text-anchor="end">車体(GND)</text>')
s.append('</svg>')
svg = "\n".join(s)

html = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HW-039とリレーでハイビーム制御</title>
<style>{CSS}</style></head><body><main>
<h1>HW-039とリレーモジュールでハイビーム左右を制御する配線</h1>
<p>リレーは、各ランプを「純正の線」と「HW-039の出力」のどちらにつなぐかを切り替えます。リレーに電気が来ていない間は、ランプは純正の線につながります。</p>
<div class="card">{svg}</div>
<p class="legend"><span><i style="background:var(--pw)"></i>12V入力</span><span><i style="background:var(--out)"></i>ランプへの出力</span><span><i style="background:#7048e8"></i>純正の線(破線)</span><span><i style="background:var(--sig)"></i>PWM信号</span><span><i style="background:#e67700"></i>切替信号</span><span><i style="background:var(--ctl)"></i>3.3V・出力許可</span><span><i style="background:var(--gnd)"></i>GND</span></p>

<h2>リレーの3つの端子</h2>
<div class="card"><table>
<tr><th>端子</th><th>つなぐ先</th><th>意味</th></tr>
<tr><td>COM</td><td>ランプの+側</td><td>常にランプへつながる共通の端子</td></tr>
<tr><td>NC</td><td>純正のハイビーム線(車両側)</td><td>リレーOFFのときにCOMとつながる</td></tr>
<tr><td>NO</td><td>HW-039のM+(右)・M−(左)</td><td>リレーONのときにCOMとつながる</td></tr>
</table></div>
<p>純正のハイビーム線は、ランプの手前で切り、車両側をNCへ、ランプ側をCOMへつなぎます。</p>

<h2>動き方</h2>
<div class="two">
  <div class="st"><b>純正モード(リレーOFF)</b><ol>
    <li>ESPの電源が無い、またはGPIO9が切替を指示していない。</li><li>ランプはNC経由で純正の線につながる。</li><li>純正のレバーで、普段どおり点く。</li></ol></div>
  <div class="st"><b>自作モード(リレーON)</b><ol>
    <li>ESPがGPIO9でリレーをONにする。</li><li>ランプはNO経由でHW-039につながる。</li><li>GPIO4(右)とGPIO6(左)のPWMで調光する。</li></ol></div>
</div>

<h2>リレーモジュールの電源と信号</h2>
<div class="card"><table>
<tr><th>端子</th><th>つなぐ先</th><th>注意</th></tr>
<tr><td>IN1・IN2</td><td>ESP GPIO9(2本を束ねる)</td><td>多くのモジュールはLOWでONになる。実機で向きを確認する</td></tr>
<tr><td>VCC</td><td>ESP 3V3</td><td>JD-VCCとのジャンパを外してからつなぐ</td></tr>
<tr><td>JD-VCC</td><td>IG 12V(キーONで12Vが来る線)</td><td>リレーのコイル用の電源。キーOFFなら必ず純正に戻る</td></tr>
<tr><td>GND</td><td>車体(GND)</td><td>ESP・HW-039と共通</td></tr>
</table></div>
<p>HW-039側の配線は hibeam-hw039.html と同じです。使うリレーは8chのうち2chで、残り6chは空きです。</p>
</main></body></html>'''
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT)
