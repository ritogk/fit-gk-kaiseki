#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ユニバーサル基板への集約図(1灯ぶん・恒久実装用)を生成する。
出力: single-lamp-board.html
CSS・部品ヘルパは gen_single_lamp.py から流用。静的図(ポップアップ無し)。
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
"""
import io, os
import gen_single_lamp as base

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "single-lamp-board.html")
sqtag, chassis = base.sqtag, base.chassis

S = []

S.append('''
<defs><pattern id="grid" width="18" height="18" patternUnits="userSpaceOnUse">
<circle cx="9" cy="9" r="1.4" fill="var(--box-line)" opacity="0.5"/></pattern></defs>
''')

# ============ 基板本体 ============
S.append('''
<rect x="300" y="200" width="640" height="560" rx="12" fill="var(--box)" stroke="var(--box-line)" stroke-width="1.5"/>
<rect x="300" y="200" width="640" height="560" rx="12" fill="url(#grid)"/>
<text class="t-lab" x="300" y="188" font-weight="700">ユニバーサル基板(1灯ぶん・約9×7cm) — 車載・恒久用。全てハンダ実装</text>
''')

# ============ 外部: 電源チェーン(左上) ============
S.append(f'''
<rect class="box" x="40" y="60" width="130" height="64" rx="8"/>
<text class="t-lab" x="105" y="96" text-anchor="middle" font-weight="700">バッテリー 12V</text>
<path d="M170 92 H200" fill="none" stroke="var(--w-vcc)" stroke-width="3"/>
<rect class="box" x="200" y="78" width="64" height="28" rx="4"/>
<text class="t-pin" x="232" y="96" text-anchor="middle">F 20A</text>
<path d="M264 92 H300" fill="none" stroke="var(--w-vcc)" stroke-width="3"/>
<rect class="box" x="300" y="78" width="68" height="28" rx="4"/>
<text class="t-pin" x="334" y="96" text-anchor="middle">F 5A 平型</text>
<path d="M368 92 H375 V206" fill="none" stroke="var(--w-vcc)" stroke-width="2.5"/>
<text class="t-cap" x="40" y="144">20A=インラインホルダー / 5A=自作ヒューズBOXの1口</text>
{sqtag(185, 64, "2.0sq")}
{sqtag(412, 150, "0.75sq")}
''')

# ============ 外部: 純正線とタップ分岐(上) ============
S.append(f'''
<path d="M960 40 V160 H1020" fill="none" stroke="var(--w-stock)" stroke-width="2.2" stroke-dasharray="9 6"/>
<text class="t-cap" x="960" y="32" text-anchor="middle" fill="var(--w-stock)">純正線(既存ハーネスのまま)</text>
<circle cx="960" cy="70" r="4" fill="var(--w-is)"/>
<path d="M960 70 H555 V206" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
{sqtag(750, 62, "0.3sq", "var(--w-is)")}
''')

# ============ 外部: リレーモジュール・灯具・IG(右) ============
S.append(f'''
<rect class="box" x="1020" y="120" width="280" height="180" rx="10"/>
<text class="t-lab" x="1160" y="146" text-anchor="middle" font-weight="700">切替リレーモジュール</text>
<text class="t-cap" x="1160" y="166" text-anchor="middle">既製基板のまま使う</text>
<text class="t-pin" x="1032" y="164">NC(純正)</text>
<text class="t-pin" x="1032" y="214">NO(自作)</text>
<text class="t-pin" x="1288" y="214" text-anchor="end">COM(灯具)</text>
<text class="t-pin" x="1080" y="290" text-anchor="middle">IN</text>
<text class="t-pin" x="1200" y="290" text-anchor="middle">JD-VCC</text>
<path d="M465 206 V150 H990 V210 H1020" fill="none" stroke="var(--w-pos)" stroke-width="2.2"/>
{sqtag(750, 142, "0.75sq", "var(--w-pos)")}
<path d="M1300 210 H1320 V400 H1274" fill="none" stroke="var(--w-pos)" stroke-width="2.2"/>
{sqtag(1282, 312, "0.75sq", "var(--w-pos)")}
<circle cx="1240" cy="400" r="34" fill="var(--box)" stroke="var(--box-line)" stroke-width="1.5"/>
<path d="M1216 376 L1264 424 M1216 424 L1264 376" stroke="var(--w-vcc)" stroke-width="2"/>
<text class="t-lab" x="1240" y="352" text-anchor="middle">灯具</text>
<path d="M1240 434 V460" fill="none" stroke="var(--w-neg)" stroke-width="2.2"/>
{chassis(1240, 460, "var(--w-neg)", 0.8)}
<text class="t-cap" x="1240" y="510" text-anchor="middle">−はボディアース(純正どおり)</text>
<rect class="box" x="1160" y="420" width="150" height="56" rx="8"/>
<text class="t-lab" x="1235" y="444" text-anchor="middle" font-weight="700">IG 12V</text>
<text class="t-cap" x="1235" y="462" text-anchor="middle">キーON時のみ</text>
<path d="M1235 420 V340 H1200 V300" fill="none" stroke="var(--w-vcc)" stroke-width="2"/>
{sqtag(1272, 384, "0.5sq")}
<path d="M926 590 H1080 V300" fill="none" stroke="var(--w-en)" stroke-width="2"/>
{sqtag(1000, 582, "0.3sq", "var(--w-en)")}
<text class="t-cap" x="1090" y="372">VCC/GNDは基板から0.3sqで供給</text>
''')

# ============ 外部: DCDC(左下)とGND ============
S.append(f'''
<circle cx="280" cy="92" r="4" fill="var(--w-vcc)"/>
<path d="M280 92 V500 H150 V530" fill="none" stroke="var(--w-vcc)" stroke-width="2"/>
{sqtag(255, 300, "0.5sq")}
<rect class="box" x="60" y="530" width="180" height="70" rx="8"/>
<text class="t-lab" x="150" y="560" text-anchor="middle" font-weight="700">DCDC 12V→5V</text>
<text class="t-cap" x="150" y="580" text-anchor="middle">既製モジュール</text>
<path d="M240 552 H302" fill="none" stroke="var(--w-vcc)" stroke-width="2"/>
{sqtag(271, 538, "0.3sq")}
<path d="M302 492 H288 M272 492 H140 M140 492 V640" fill="none" stroke="var(--w-gnd)" stroke-width="2"/>
{sqtag(210, 484, "0.3sq", "var(--w-gnd)")}
{chassis(140, 640, "var(--w-neg)", 1.0)}
<text class="t-cap" x="140" y="690" text-anchor="middle">電源− / 車体一点アース(DCDCの−もここへ)</text>
''')

# ============ 基板上: ネジ端子台 ============
def term(x, y, color, screw_cx, screw_cy):
    return (f'<rect class="box" x="{x}" y="{y}" width="70" height="44" rx="4"/>'
            f'<rect x="{x}" y="{y}" width="70" height="6" fill="{color}"/>'
            f'<circle cx="{screw_cx}" cy="{screw_cy}" r="8" fill="var(--surface)" stroke="var(--box-line)" stroke-width="1.5"/>'
            f'<path d="M{screw_cx-5} {screw_cy} H{screw_cx+5}" stroke="var(--box-line)" stroke-width="1.5"/>')

def term_v(x, y, color, screw_cx, screw_cy):
    return (f'<rect class="box" x="{x}" y="{y}" width="56" height="44" rx="4"/>'
            f'<rect x="{x}" y="{y}" width="6" height="44" fill="{color}"/>'
            f'<circle cx="{screw_cx}" cy="{screw_cy}" r="8" fill="var(--surface)" stroke="var(--box-line)" stroke-width="1.5"/>'
            f'<path d="M{screw_cx-5} {screw_cy} H{screw_cx+5}" stroke="var(--box-line)" stroke-width="1.5"/>')

S.append(term(340, 206, "var(--w-vcc)", 375, 228)
         + '<text class="t-pin" x="375" y="264" text-anchor="middle">12V IN</text>'
         + term(430, 206, "var(--w-pos)", 465, 228)
         + '<text class="t-pin" x="465" y="264" text-anchor="middle">OUT→リレーNO</text>'
         + term(520, 206, "var(--w-is)", 555, 228)
         + '<text class="t-pin" x="555" y="264" text-anchor="middle">TAP IN</text>'
         + term_v(302, 470, "var(--w-gnd)", 330, 492)
         + '<text class="t-pin" x="330" y="526" text-anchor="middle">GND</text>'
         + term_v(302, 530, "var(--w-vcc)", 330, 552)
         + '<text class="t-pin" x="330" y="588" text-anchor="middle">5V IN</text>')

# ============ 基板上: 監視タップ区画 ============
S.append('''
<rect x="540" y="265" width="180" height="205" rx="8" fill="none" stroke="var(--box-line)" stroke-dasharray="5 4"/>
<text class="t-cap" x="630" y="286" text-anchor="middle">監視タップ</text>
<path d="M555 250 V280 H620 V300" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
<rect class="box" x="612" y="300" width="16" height="50" rx="3"/>
<text class="t-pin" x="636" y="330">100kΩ</text>
<path d="M620 350 V370" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
<circle cx="620" cy="370" r="3.5" fill="var(--w-is)"/>
<text class="t-pin" x="604" y="366" text-anchor="end">≈2.2V</text>
<path d="M620 370 H500 V470" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
<text class="t-cap" x="548" y="362" fill="var(--w-is)">SENSE</text>
<path d="M620 374 V390" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
<rect class="box" x="612" y="390" width="16" height="50" rx="3"/>
<text class="t-pin" x="636" y="420">22kΩ</text>
<path d="M620 440 V460" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
<path d="M624 370 H660 V382" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
<path d="M648 390 L652 386 H668 L672 382" fill="none" stroke="var(--w-is)" stroke-width="2.2"/>
<path d="M660 388 L652 402 H668 Z" fill="var(--w-is)"/>
<path d="M660 402 V460" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
<text class="t-pin" x="676" y="398">3.3Vz</text>
''')

# ============ 基板上: BTS区画 ============
S.append('''
<rect x="720" y="260" width="200" height="160" rx="8" fill="none" stroke="var(--box-line)" stroke-dasharray="5 4"/>
<text class="t-cap" x="820" y="282" text-anchor="middle">TO-252-5変換基板ごと実装</text>
<rect class="box" x="760" y="300" width="120" height="70" rx="6"/>
<text class="t-lab" x="820" y="330" text-anchor="middle" font-weight="700">BTS6143D</text>
<text class="t-cap" x="820" y="350" text-anchor="middle">ハイサイドSW</text>
<text class="t-pin" x="752" y="316" text-anchor="end">Vbb</text>
<text class="t-pin" x="752" y="359" text-anchor="end">IN</text>
<text class="t-pin" x="828" y="388">OUT</text>
<text class="t-cap" x="820" y="474" text-anchor="middle">裏面: Vbb/OUT経路はスズメッキ線で補強</text>
''')

# ============ 基板上: 配線(ハンダ面) ============
S.append('''
<path d="M375 250 V270 M375 270 H457 M473 270 H547 M563 270 H760 V320" fill="none" stroke="var(--w-vcc)" stroke-width="2"/>
<path d="M820 370 V446 H748 M732 446 H668 M652 446 H628 M612 446 H465 V250" fill="none" stroke="var(--w-pos)" stroke-width="2"/>
<path d="M660 460 H508 M492 460 H473 M457 460 H360 M360 460 V544 M360 560 V620 H380 M360 492 H358" fill="none" stroke="var(--w-gnd)" stroke-width="2"/>
<path d="M680 540 H740 V355 H760" fill="none" stroke="var(--w-pwm)" stroke-width="1.8"/>
<path d="M680 590 H898" fill="none" stroke="var(--w-en)" stroke-width="1.8"/>
<path d="M358 552 H380" fill="none" stroke="var(--w-vcc)" stroke-width="2"/>
''')

# ============ 基板上: ESP・信号ヘッダ ============
S.append('''
<rect class="box" x="380" y="470" width="300" height="200" rx="12"/>
<text class="t-ti" x="530" y="560" text-anchor="middle">ESP32-S3</text>
<text class="t-cap" x="530" y="584" text-anchor="middle">ピンソケットで着脱可</text>
<text class="t-pin" x="500" y="486" text-anchor="middle">SEN</text>
<text class="t-pin" x="668" y="544" text-anchor="end">PWM</text>
<text class="t-pin" x="668" y="594" text-anchor="end">SEL</text>
<text class="t-pin" x="392" y="556">5V</text>
<text class="t-pin" x="392" y="624">GND</text>
<rect class="box" x="898" y="550" width="28" height="80" rx="4"/>
<text class="t-cap" x="912" y="544" text-anchor="middle">信号ヘッダ</text>
<circle cx="912" cy="590" r="3" fill="var(--w-en)"/>
<circle cx="912" cy="610" r="3" fill="var(--w-gnd)"/>
''')

# ============ 基板内注記 ============
S.append('''
<text class="t-cap" x="320" y="706">○=2.54mmグリッド。部品は表面・配線はハンダ面。電力経路(12V IN→BTS→OUT)は太めのスズメッキ線で引く。</text>
<text class="t-cap" x="320" y="728">机上検証はブレッドボードで先に(single-lamp-build.html)。この基板は車載・恒久用 — 振動でも緩まないハンダ実装。</text>
<text class="t-cap" x="320" y="750">17ch化: 監視タップ+BTSの区画を×17に複製(前10/後7)。ESP・端子台は共用。実体は board-layout-17ch.html。</text>
''')

svg = ('<svg id="board" viewBox="0 0 1340 790" role="img" aria-label="ユニバーサル基板集約図(1灯)">'
       + "".join(S) + "</svg>")

BODY = """
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / SINGLE BOARD</p>
  <h1>ユニバーサル基板への集約 — 1灯ぶん実装図</h1>
  <p class="lead">基板に集約するのは<b>ネジ端子台・監視タップ・BTS6143D(変換基板ごと)・ESP32-S3(ソケット)</b>の4つ。
  リレーモジュールとDCDCは既製基板のまま外置き。電力・電圧が入る線は必ずネジ端子台を経由する。
  この基板は<b>車載・恒久用</b> — 机上検証はブレッドボード(組み立てガイド)で先に済ませる。</p>

  <h2>実装図</h2>
  <p class="hint">丸タグ=その区間の電線サイズ。破線枠=部品区画。基板内の細線=ハンダ面の配線(交差の切れ目=非接続)。</p>
  <div class="panel">%SVG%</div>

  <h2>載せる物・載せない物</h2>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th>区分</th><th>部品</th><th>実装方法</th></tr></thead>
      <tbody>
        <tr><td class="sig">基板に載せる</td><td>ネジ端子台 5口(12V IN / OUT / TAP IN / GND / 5V IN)</td><td>外部との境界。電力・電圧はすべてここ経由で出入りする</td></tr>
        <tr><td class="sig">〃</td><td>監視タップ(100kΩ・22kΩ・1N5226B)</td><td>TAP IN端子の直後に直接ハンダ(分岐点から抵抗までを短く)</td></tr>
        <tr><td class="sig">〃</td><td>BTS6143D</td><td>TO-252-5変換基板に載せピンヘッダで実装。裏面のVbb/OUTはスズメッキ線で補強</td></tr>
        <tr><td class="sig">〃</td><td>ESP32-S3</td><td>ピンソケットで着脱可(書き込み・交換用)</td></tr>
        <tr><td class="sig">〃</td><td>信号ピンヘッダ(SEL/GND)</td><td>リレーモジュールへの信号をここから出す</td></tr>
        <tr><td class="sig">外(既製基板)</td><td>切替リレーモジュール / DCDC</td><td>既製のまま。ネジ端子・ヘッダで接続</td></tr>
        <tr><td class="sig">外(配線部材)</td><td>ヒューズ(20Aホルダー / 5A BOX)・灯具・電力線</td><td>圧着・ネジ端子。基板には載せない</td></tr>
      </tbody>
    </table>
  </div>

  <footer>生成元: gen_single_board.py(HTMLを直接編集しない)。回路の意味: single-lamp-wiring.html / 机上検証: single-lamp-build.html / 17ch実体: board-layout-17ch.html。2026-08-04。</footer>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>ユニバーサル基板集約図 — 1灯ぶん</title>\n"
        "<style>" + base.CSS + "</style>\n"
        + BODY.replace("%SVG%", svg))

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
