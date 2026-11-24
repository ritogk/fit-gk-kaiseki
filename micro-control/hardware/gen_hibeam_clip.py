# -*- coding: utf-8 -*-
# 実験用: ハイビームのコネクタを抜き、ランプ側端子へHW-039の出力をワニ口クリップで直結する配線図(ライトモード専用)
import io, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hibeam-clip.html")
src = io.open(os.path.join(HERE, "gen_simple_one_lamp.py"), encoding="utf-8").read()
CSS = re.search(r"<style>(.*?)</style>", src, re.S).group(1).replace("{{", "{").replace("}}", "}")
CSS += """
.clip{fill:#fff4e6;stroke:#e67700;stroke-width:2}
.cliplbl{font-size:11px;fill:#e67700;font-weight:600}
.unplug{fill:#f1f3f5;stroke:#adb5bd;stroke-width:2;stroke-dasharray:6 4}
.term{fill:#fff;stroke:#343a40;stroke-width:2}
"""

def gnd(x, y):
    return f'<path d="M{x-14} {y} H{x+14} M{x-9} {y+5} H{x+9} M{x-4} {y+10} H{x+4}" class="w gndw"/>'

def clip(x, y):
    return (f'<rect x="{x-11}" y="{y-8}" width="22" height="16" rx="4" class="clip"/>'
            f'<text x="{x}" y="{y-12}" class="cliplbl" text-anchor="middle">クリップ</text>')

def lampunit(x, y, name):
    # ランプ側コネクタ(+,−端子)とバルブ
    return (f'<rect x="{x}" y="{y-40}" width="46" height="80" rx="6" class="box"/>'
            f'<circle cx="{x+12}" cy="{y-20}" r="6" class="term"/><text x="{x+26}" y="{y-16}" class="pin">+</text>'
            f'<circle cx="{x+12}" cy="{y+20}" r="6" class="term"/><text x="{x+26}" y="{y+24}" class="pin">−</text>'
            f'<path d="M{x+46} {y-20} H{x+70} M{x+46} {y+20} H{x+70}" class="w"/>'
            f'<circle cx="{x+96}" cy="{y}" r="26" class="lamp"/>'
            f'<path d="M{x+79} {y-17} L{x+113} {y+17} M{x+113} {y-17} L{x+79} {y+17}" class="w lampx"/>'
            f'<path d="M{x+70} {y-20} V{y-10} M{x+70} {y+20} V{y+10}" class="w"/>'
            f'<text x="{x+60}" y="{y-50}" class="ttl" text-anchor="middle">{name}</text>'
            f'<text x="{x+23}" y="{y+56}" class="lbl" text-anchor="middle">ランプ側</text>')

def unplugged(x, y):
    return (f'<rect x="{x}" y="{y-22}" width="64" height="44" rx="6" class="unplug"/>'
            f'<text x="{x+32}" y="{y-2}" class="lbl dim" text-anchor="middle">車両側</text>'
            f'<text x="{x+32}" y="{y+14}" class="lbl dim" text-anchor="middle">抜いて放置</text>')

EP = [("3V3", 190, "ctlw"), ("GPIO4", 230, "sigw"), ("GPIO6", 270, "sigw"), ("GPIO5", 310, "ctlw"), ("GND", 370, "gndw")]
MP = [("VCC", 190), ("RPWM", 230), ("LPWM", 270), ("R_EN", 310), ("L_EN", 335), ("GND", 370)]
s = ['<svg viewBox="0 0 1120 560" role="img" aria-label="ハイビームのランプ側端子へHW-039をクリップで直結する配線図">']
# ESP
s.append('<rect x="40" y="140" width="170" height="270" rx="8" class="box"/>'
         '<text x="125" y="166" class="ttl" text-anchor="middle">ESP32-S3</text>'
         '<text x="125" y="430" class="lbl" text-anchor="middle">電源はPCのUSB</text>')
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
# 電源: バッテリー → ヒューズブロック(ATO/ATC) → B+
s.append('<rect x="560" y="14" width="120" height="50" rx="8" class="box"/>'
         '<text x="620" y="36" class="ttl" text-anchor="middle">バッテリー</text>'
         '<text x="620" y="54" class="lbl" text-anchor="middle">12V +</text>')
s.append('<rect x="730" y="10" width="250" height="84" rx="8" class="box"/>'
         '<text x="855" y="30" class="ttl" text-anchor="middle">ヒューズブロック(ATO/ATC)</text>')
for i, (lb, used) in enumerate([("15A", True), ("空き", False), ("空き", False), ("空き", False)]):
    x = 750 + i*56
    cls = "part" if used else "unplug"
    s.append(f'<rect x="{x}" y="44" width="40" height="30" rx="5" class="{cls}"/>'
             f'<text x="{x+20}" y="64" class="lbl{"" if used else " dim"}" text-anchor="middle">{lb}</text>')
s.append('<path d="M680 39 H705 V59 H730" class="w pw"/>'
         '<text x="705" y="86" class="lbl" text-anchor="middle">共通+</text>')
s.append('<path d="M770 74 V190 H640" class="w pw"/>'
         '<text x="780" y="140" class="lbl">1番(15A)からB+へ</text>')
# 出力 → クリップ → ランプ側+端子
RY, LY = 250, 420
s.append(f'<path d="M640 250 H868 V{RY-20} H912" class="w outw"/>')
s.append(f'<path d="M640 310 H700 V{LY-20} H912" class="w outw"/>')
s.append(clip(800, 250)); s.append(clip(800, LY-20))
s.append(lampunit(912, RY, "ハイビーム 右")); s.append(lampunit(912, LY, "ハイビーム 左"))
# 抜いた車両側コネクタ
s.append(unplugged(1040, RY-120 if False else 120))
s.append(unplugged(1040, 520))
s.append('<text x="1072" y="160" class="lbl dim" text-anchor="middle">(右)</text>'
         '<text x="1072" y="488" class="lbl dim" text-anchor="middle">(左)</text>')
# ランプ側−端子 → GND
s.append(f'<path d="M912 {RY+20} H880 V500 M912 {LY+20} H880" class="w gndw"/><circle cx="880" cy="{LY+20}" r="4" class="dotg"/>')
s.append(clip(896, RY+20)); s.append(clip(896, LY+20))
s.append('<path d="M640 370 H670 V500 H880 V516" class="w gndw"/><circle cx="880" cy="500" r="4" class="dotg"/>')
s.append(gnd(880, 516))
s.append('<text x="860" y="540" class="lbl" text-anchor="end">バッテリー−(車体)</text>')
s.append('</svg>')
svg = "\n".join(s)

html = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ハイビーム クリップ直結実験</title>
<style>{CSS}</style></head><body><main>
<h1>ハイビームのランプ側へHW-039をクリップで直結する実験配線</h1>
<p>ハイビームのコネクタを抜き、ランプ側の端子へHW-039の出力をワニ口クリップでつなぎます。車両側の配線は切り離したままなので、ダイオードもリレーも要らず、左右の回り込みも起きません。純正の線は一切加工しません。</p>
<div class="card">{svg}</div>
<p class="legend"><span><i style="background:var(--pw)"></i>12V入力</span><span><i style="background:var(--out)"></i>ランプへの出力</span><span><i style="background:var(--sig)"></i>PWM信号</span><span><i style="background:var(--ctl)"></i>3.3V・出力許可</span><span><i style="background:var(--gnd)"></i>GND</span><span><i style="background:#e67700"></i>ワニ口クリップ</span></p>

<h2>つなぎ方</h2>
<div class="card"><table>
<tr><th>HW-039</th><th>つなぐ先</th></tr>
<tr><td>VCC</td><td>ESP 3V3</td></tr>
<tr><td>RPWM</td><td>ESP GPIO4(右の明るさ)</td></tr>
<tr><td>LPWM</td><td>ESP GPIO6(左の明るさ)。pinout.mdの更新前は、GNDに落として右だけで試す</td></tr>
<tr><td>R_EN・L_EN</td><td>ESP GPIO5(2本を束ねる)</td></tr>
<tr><td>GND</td><td>ESP GND</td></tr>
<tr><td>B+</td><td>ヒューズブロックの1番(15A)。ブロックの共通+はバッテリー+へ</td></tr>
<tr><td>B−</td><td>バッテリー−(車体)</td></tr>
<tr><td>M+</td><td>クリップで、右ハイビームのランプ側+端子</td></tr>
<tr><td>M−</td><td>クリップで、左ハイビームのランプ側+端子</td></tr>
<tr><td>(ランプ側−端子)</td><td>クリップで、左右ともバッテリー−(車体)</td></tr>
</table></div>

<h2>つなぐ前の確認</h2>
<div class="two">
  <div class="st"><b>端子の極性</b><ol>
    <li>ランプ側コネクタのどちらが+かを、テスターかバルブの刻印で確認する。</li>
    <li>ハロゲンは逆でも点く。LEDユニットは逆だと点かず、壊れる可能性がある。</li></ol></div>
  <div class="st"><b>ショート対策</b><ol>
    <li>端子の間隔が狭いので、+と−のクリップが触れない向きでつなぐ。</li>
    <li>絶縁カバー付きのクリップを使うか、平型端子を挿してからつかむ。</li>
    <li>B+は必ずヒューズブロック経由でつなぐ。</li></ol></div>
</div>

<h2>動き方</h2>
<div class="two">
  <div class="st"><b>GPIO5 = HIGH(出力許可)</b><ol>
    <li>GPIO4のPWMで、右の明るさが決まる。</li><li>GPIO6のPWMで、左の明るさが決まる。</li><li>PWMが0%なら、そのランプは消える。</li></ol></div>
  <div class="st"><b>GPIO5 = LOW</b><ol>
    <li>両方の出力が切り離される。</li><li>PWMの値に関係なく、両方とも消える。</li><li>ESPの起動中は、必ずこの状態にする。</li></ol></div>
</div>
<p>最初は低いデューティ(10%程度)で短時間だけ点け、ちらつきや異音がないことを確認してから上げます。LEDユニットは内蔵の駆動回路がPWMを受け付けない場合があるため、ちらつくときは周波数(1kHz前後)を変えて試します。</p>
</main></body></html>'''
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT)
