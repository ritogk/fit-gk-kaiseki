# -*- coding: utf-8 -*-
# ESP32-S3 + HW-039(BTS7960x2) 1枚でハイビーム左右を別々に調光する配線図(ライトモード専用)
import io, os, re
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hibeam-hw039.html")
src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_simple_one_lamp.py"), encoding="utf-8").read()
CSS = re.search(r"<style>(.*?)</style>", src, re.S).group(1).replace("{{", "{").replace("}}", "}")

def gnd(x, y):
    return f'<path d="M{x-14} {y} H{x+14} M{x-9} {y+5} H{x+9} M{x-4} {y+10} H{x+4}" class="w gndw"/>'

def lamp(x, y, name):
    return (f'<circle cx="{x}" cy="{y}" r="26" class="lamp"/>'
            f'<path d="M{x-17} {y-17} L{x+17} {y+17} M{x+17} {y-17} L{x-17} {y+17}" class="w lampx"/>'
            f'<text x="{x}" y="{y-34}" class="ttl" text-anchor="middle">{name}</text>')

EP = [("3V3", 190, "ctlw"), ("GPIO4", 230, "sigw"), ("GPIO6", 270, "sigw"), ("GPIO5", 310, "ctlw"), ("GND", 370, "gndw")]
MP = [("VCC", 190), ("RPWM", 230), ("LPWM", 270), ("R_EN", 310), ("L_EN", 335), ("GND", 370)]
s = ['<svg viewBox="0 0 1000 520" role="img" aria-label="HW-039でハイビーム左右を制御する配線図">']
# ESP
s.append('<rect x="40" y="140" width="170" height="270" rx="8" class="box"/>'
         '<text x="125" y="166" class="ttl" text-anchor="middle">ESP32-S3</text>')
for n, y, c in EP:
    s.append(f'<text x="200" y="{y+4}" class="pin" text-anchor="end">{n}</text>')
    s.append(f'<path d="M210 {y} H400" class="w {c}"/>')
s.append('<path d="M330 310 V335 H400" class="w ctlw"/><circle cx="330" cy="310" r="4" class="dot"/>')
s.append('<text x="305" y="222" class="lbl" text-anchor="middle">PWM(右)</text>'
         '<text x="305" y="262" class="lbl" text-anchor="middle">PWM(左)</text>'
         '<text x="270" y="302" class="lbl" text-anchor="middle">出力許可</text>')
# HW-039
s.append('<rect x="400" y="110" width="240" height="320" rx="10" class="bts"/>'
         '<text x="520" y="136" class="ttl" text-anchor="middle">HW-039(IBT_2)</text>'
         '<text x="520" y="154" class="lbl" text-anchor="middle">BTS7960 ×2</text>')
for n, y in MP:
    s.append(f'<text x="410" y="{y+4}" class="pin">{n}</text>')
s.append('<text x="410" y="410" class="lbl dim">R_IS・L_ISはつながない</text>')
for n, y in [("B+", 190), ("M+", 250), ("M−", 310), ("B−", 370)]:
    s.append(f'<text x="630" y="{y+4}" class="pin" text-anchor="end">{n}</text>')
# 電源
s.append('<rect x="800" y="40" width="130" height="56" rx="8" class="box"/>'
         '<text x="865" y="64" class="ttl" text-anchor="middle">バッテリー</text>'
         '<text x="865" y="84" class="lbl" text-anchor="middle">12V +</text>')
s.append('<path d="M800 68 H740 V120 M740 150 V190 H640" class="w pw"/>'
         '<rect x="722" y="120" width="36" height="30" rx="5" class="part"/>'
         '<text x="740" y="140" class="lbl" text-anchor="middle">15A</text>'
         '<text x="700" y="140" class="lbl" text-anchor="end">ヒューズ</text>')
# ランプ
s.append('<path d="M640 250 H790" class="w outw"/><path d="M640 310 H700 V400 H790" class="w outw"/>')
s.append(lamp(816, 250, "ハイビーム 右")); s.append(lamp(816, 400, "ハイビーム 左"))
s.append('<path d="M842 250 H930 V470 M842 400 H930" class="w gndw"/><circle cx="930" cy="400" r="4" class="dotg"/>')
# GND
s.append('<path d="M640 370 H670 V470 H930 V486" class="w gndw"/><circle cx="930" cy="470" r="4" class="dotg"/>')
s.append(gnd(930, 486))
s.append('<text x="900" y="498" class="lbl" text-anchor="end">車体(GND)</text>')
s.append('</svg>')
svg = "\n".join(s)

html = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HW-039でハイビーム左右を制御</title>
<style>{CSS}</style></head><body><main>
<h1>HW-039 1枚でハイビーム左右を別々に調光する配線</h1>
<p>太い線が12Vの大電流、細い線がESPの信号です。M+が右、M−が左のランプを動かします(左右は入れ替えても構いません)。</p>
<div class="card">{svg}</div>
<p class="legend"><span><i style="background:var(--pw)"></i>12V入力</span><span><i style="background:var(--out)"></i>ランプへの出力</span><span><i style="background:var(--sig)"></i>PWM信号</span><span><i style="background:var(--ctl)"></i>3.3V・出力許可</span><span><i style="background:var(--gnd)"></i>GND</span></p>

<h2>つなぎ方</h2>
<div class="card"><table>
<tr><th>HW-039</th><th>つなぐ先</th><th>今の配線からの変更</th></tr>
<tr><td>VCC</td><td>ESP 3V3</td><td>変更なし</td></tr>
<tr><td>RPWM</td><td>ESP GPIO4(右の明るさ)</td><td>変更なし</td></tr>
<tr><td>LPWM</td><td>ESP GPIO6(左の明るさ)</td><td><b>GND固定をやめ、GPIO6へつなぎ替える</b></td></tr>
<tr><td>R_EN・L_EN</td><td>ESP GPIO5(2本を束ねる)</td><td>変更なし</td></tr>
<tr><td>GND</td><td>ESP GND</td><td>変更なし</td></tr>
<tr><td>B+</td><td>バッテリー12V(15Aヒューズ経由・1.25sq以上)</td><td>ヒューズ容量を確認</td></tr>
<tr><td>B−</td><td>車体(GND)</td><td>変更なし</td></tr>
<tr><td>M+</td><td>ハイビーム右の+側</td><td>変更なし</td></tr>
<tr><td>M−</td><td>ハイビーム左の+側</td><td><b>追加</b></td></tr>
</table></div>

<h2>動き方</h2>
<div class="two">
  <div class="st"><b>GPIO5 = HIGH(出力許可)</b><ol>
    <li>GPIO4のPWMで、右の明るさが決まる。</li><li>GPIO6のPWMで、左の明るさが決まる。</li><li>PWMが0%なら、そのランプは消える。</li></ol></div>
  <div class="st"><b>GPIO5 = LOW</b><ol>
    <li>両方の出力が切り離される。</li><li>PWMの値に関係なく、両方とも消える。</li><li>ESPの起動中は、必ずこの状態にする。</li></ol></div>
</div>
<p>ランプの−側は、どちらも車体(GND)につなぎます。ESPのGND、HW-039のGND、B−、車体は、すべて同じGNDです。</p>
</main></body></html>'''
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT)
