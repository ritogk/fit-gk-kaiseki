#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1灯だけのシンプル結線図(回路の流れ理解用)を生成する。
出力: single-lamp-wiring.html
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
17ch完全版(full-wiring-17ch.html)と同じ部品・同じ回路形の「1ch分」を抜き出したもの。
"""
import io, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "single-lamp-wiring.html")
W, H = 1340, 920


def chassis(x, y, color="var(--w-neg)", s=1.0):
    w1, w2, w3 = 22 * s, 14 * s, 7 * s
    return (f'<path d="M{x} {y} V{y+4} M{x-w1} {y+4} H{x+w1} M{x-w2} {y+10} H{x+w2} '
            f'M{x-w3} {y+16} H{x+w3}" stroke="{color}" stroke-width="2" fill="none"/>')


def sqtag(x, y, label, color="var(--w-vcc)"):
    """電線サイズタグ。線の近くに置き、その区間で使う電線を示す。"""
    w = 10 + sum(11 if ord(c) > 0x2000 else 6.5 for c in label)
    return (f'<g aria-hidden="true"><rect x="{x-w/2:.0f}" y="{y-11}" width="{w:.0f}" height="16" rx="8" '
            f'fill="var(--surface)" stroke="{color}" stroke-width="1.2"/>'
            f'<text x="{x}" y="{y+1}" text-anchor="middle" font-size="10" '
            f'font-family="ui-monospace, SF Mono, Menlo, monospace" fill="{color}">{label}</text></g>')


S = []

# ============ 電力線ハイライト(最背面) ============
# 橙の淡いハイライトが乗っている線=12Vの電流が流れる電力線(太い電線で作る区間)
S.append('''
<g aria-hidden="true">
  <path class="halo" d="M200 400 H1146"/>
  <path class="halo" d="M125 470 V500"/>
  <path class="halo" d="M1180 434 V464"/>
  <path class="halo" d="M990 136 V352"/>
  <path class="halo" d="M334 400 V560"/>
  <path class="halo" d="M1180 590 H1046 V448"/>
</g>
''')

# ============ 純正系(上段・茶破線) ============
S.append(f'''
<g class="hit" data-k="stockbox" tabindex="0" role="button" aria-label="純正ヒューズボックス">
  <rect class="box" x="830" y="40" width="500" height="96" rx="10"/>
  <text class="t-ti" x="1080" y="78" text-anchor="middle">純正ヒューズBOX / 純正スイッチ(車両側)</text>
  <text class="t-cap" x="1080" y="102" text-anchor="middle">純正操作の出口 — ここからは電源を取らない</text>
</g>
<g class="hit" data-k="stockline" tabindex="0" role="button" aria-label="純正線">
  <path class="hitline" d="M990 136 V352"/>
  <path d="M990 136 V352" fill="none" stroke="var(--w-stock)" stroke-width="2.2" stroke-dasharray="9 6"/>
  <text class="t-lab" x="1004" y="330" fill="var(--w-stock)">純正線 → NC</text>
</g>
<g class="hit" data-k="tap" tabindex="0" role="button" aria-label="純正入力モニタ(分圧タップ)">
  <text class="t-lab" x="60" y="84" font-weight="700">監視タップの中身(分圧回路) — なぜ抵抗2本?</text>
  <text class="t-cap" x="60" y="106">抵抗は電流が流れた時だけ電圧を消費する部品。1本では電圧は下がらない。</text>
  <text class="t-cap" x="60" y="124">2本直列でGNDまで電流の道を作ると、12Vが抵抗の大きさの比(100:22)で分配される。</text>
  <text class="t-cap" x="60" y="142">22k側の取り分 = 12V × 22/122 ≈ 2.2V。この中間点の電圧をESPが読む。</text>

  <circle cx="990" cy="220" r="4" fill="var(--w-is)"/>
  <path class="hitline" d="M990 220 H940 V150 H680 V306 M680 236 H530 V560 M680 236 H770 V306 M680 306 H770"/>

  <path d="M990 220 H940 V150 H680 V166" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
  <text class="t-cap" x="850" y="168" text-anchor="middle" fill="var(--w-is)">純正線の12V</text>

  <rect class="box" x="664" y="166" width="32" height="40" rx="4"/>
  <text class="t-pin" x="704" y="192">100kΩ(純正線側)</text>
  <path d="M680 206 V232" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>

  <circle cx="680" cy="236" r="4" fill="var(--w-is)"/>
  <text class="t-lab" x="694" y="226" fill="var(--w-is)">中間点 ≈ 2.2V (12×22/122)</text>

  <path d="M676 236 H530 V560" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
  <text class="t-cap" x="592" y="256" fill="var(--w-is)">SENSE(ESPのSENへ)</text>

  <path d="M680 240 V250" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
  <rect class="box" x="664" y="250" width="32" height="40" rx="4"/>
  <text class="t-pin" x="656" y="274" text-anchor="end">22kΩ</text>

  <path d="M684 236 H770 M770 236 V252" fill="none" stroke="var(--w-is)" stroke-width="1.8"/>
  <path d="M756 260 L760 256 H780 L784 252" fill="none" stroke="var(--w-is)" stroke-width="2"/>
  <path d="M770 258 L760 274 H780 Z" fill="var(--w-is)"/>
  <text class="t-pin" x="788" y="262">3.3Vツェナー(帯=中間点側)</text>
  <text class="t-cap" x="788" y="278">普段は無関与・サージ時だけ働く保険</text>

  <path d="M680 290 V306 M770 274 V306 M680 306 H770" fill="none" stroke="var(--w-gnd)" stroke-width="1.8"/>
  {chassis(725, 306, "var(--w-gnd)", 0.8)}
  <text class="t-cap" x="752" y="326">GNDバスバーへ</text>
</g>
''')

# ============ 電力の道(中段・左→右) ============
S.append(f'''
<text class="t-num" x="125" y="338" text-anchor="middle">①</text>
<g class="hit" data-k="bat" tabindex="0" role="button" aria-label="バッテリー">
  <rect class="box" x="50" y="352" width="150" height="118" rx="10"/>
  <text class="t-ti" x="125" y="396" text-anchor="middle">バッテリー</text>
  <text class="t-cap" x="125" y="418" text-anchor="middle">車載 12V</text>
  <path class="hitline" d="M200 400 H240 M125 470 V500"/>
  <path d="M200 400 H240" fill="none" stroke="var(--w-vcc)" stroke-width="3"/>
  <path d="M125 470 V500" fill="none" stroke="var(--w-neg)" stroke-width="2.5"/>
  {chassis(125, 500)}
  <text class="t-cap" x="125" y="540" text-anchor="middle">−は車体へ(純正)</text>
</g>

<text class="t-num" x="274" y="372" text-anchor="middle">②</text>
<g class="hit" data-k="mainfuse" tabindex="0" role="button" aria-label="メインヒューズ20A">
  <path class="hitline" d="M240 400 H360"/>
  <rect class="box" x="240" y="386" width="68" height="28" rx="4"/>
  <text class="t-pin" x="274" y="404" text-anchor="middle">F 20A</text>
  <path d="M308 400 H360" fill="none" stroke="var(--w-vcc)" stroke-width="3"/>
</g>

<text class="t-num" x="430" y="338" text-anchor="middle">③</text>
<g class="hit" data-k="chfuse" tabindex="0" role="button" aria-label="自作ヒューズボックス">
  <rect class="box" x="360" y="352" width="140" height="96" rx="8"/>
  <text class="t-lab" x="430" y="382" text-anchor="middle" font-weight="700">自作ヒューズBOX</text>
  <rect class="box" x="398" y="394" width="64" height="26" rx="4"/>
  <text class="t-pin" x="430" y="411" text-anchor="middle">ch 5A</text>
  <text class="t-cap" x="430" y="438" text-anchor="middle">1灯=1回路=1ヒューズ</text>
  <path class="hitline" d="M500 400 H580"/>
  <path d="M500 400 H580" fill="none" stroke="var(--w-vcc)" stroke-width="2.5"/>
</g>

<text class="t-num" x="660" y="344" text-anchor="middle">④</text>
<g class="hit" data-k="sw" tabindex="0" role="button" aria-label="ハイサイドSW">
  <rect class="box" x="580" y="360" width="160" height="80" rx="8"/>
  <text class="t-lab" x="660" y="388" text-anchor="middle" font-weight="700">ハイサイドSW</text>
  <text class="t-cap" x="660" y="408" text-anchor="middle">BTS6143D</text>
  <text class="t-cap" x="660" y="426" text-anchor="middle">PWMで12Vを刻む=調光</text>
  <text class="t-pin" x="608" y="456" text-anchor="end">IN</text>
  <path class="hitline" d="M740 400 H900"/>
  <path d="M740 400 H900" fill="none" stroke="var(--w-pos)" stroke-width="2.5"/>
  <text class="t-cap" x="820" y="424" text-anchor="middle">自作出力</text>
</g>

<text class="t-num" x="1035" y="344" text-anchor="middle">⑤</text>
<g class="hit" data-k="relay" tabindex="0" role="button" aria-label="切替リレー">
  <rect class="box" x="900" y="352" width="180" height="96" rx="8"/>
  <text class="t-lab" x="990" y="398" text-anchor="middle" font-weight="700">切替リレー</text>
  <text class="t-cap" x="990" y="416" text-anchor="middle">8chリレーモジュールの1ch</text>
  <text class="t-pin" x="912" y="438">NO(自作)</text>
  <text class="t-pin" x="968" y="368">NC(純正)</text>
  <text class="t-pin" x="1068" y="438" text-anchor="end">COM(灯具)</text>
  <path d="M1056 400 L1030 376" stroke="var(--box-line)" stroke-width="1.6"/>
  <text class="t-pin" x="930" y="462" text-anchor="middle">IN</text>
  <text class="t-pin" x="1046" y="462" text-anchor="middle">JD-VCC</text>
</g>

<text class="t-num" x="1180" y="350" text-anchor="middle">⑥</text>
<g class="hit" data-k="lamp" tabindex="0" role="button" aria-label="灯具">
  <path class="hitline" d="M1080 400 H1146 M1180 434 V464"/>
  <path d="M1080 400 H1146" fill="none" stroke="var(--w-pos)" stroke-width="2.5"/>
  <circle cx="1180" cy="400" r="34" fill="var(--box)" stroke="var(--box-line)" stroke-width="1.5"/>
  <path d="M1156 376 L1204 424 M1156 424 L1204 376" stroke="var(--w-vcc)" stroke-width="2"/>
  <text class="t-lab" x="1224" y="396">灯具</text>
  <text class="t-cap" x="1224" y="414">例:フォグ 1灯=1ch</text>
  <path d="M1180 434 V464" fill="none" stroke="var(--w-neg)" stroke-width="2.2"/>
  {chassis(1180, 464, "var(--w-neg)", 0.8)}
  <text class="t-cap" x="1180" y="512" text-anchor="middle">−はボディアース(純正どおり)</text>
</g>
''')

# ============ 指示の道(下段) ============
S.append(f'''
<g class="hit" data-k="dcdc" tabindex="0" role="button" aria-label="DCDCコンバータ">
  <circle cx="334" cy="400" r="4" fill="var(--w-vcc)"/>
  <path class="hitline" d="M334 400 V560 M404 590 H470"/>
  <path d="M334 404 V560" fill="none" stroke="var(--w-vcc)" stroke-width="2"/>
  <rect class="box" x="264" y="560" width="140" height="60" rx="8"/>
  <text class="t-lab" x="334" y="586" text-anchor="middle" font-weight="700">DCDC 12V→5V</text>
  <text class="t-cap" x="334" y="606" text-anchor="middle">ESP用ロジック電源</text>
  <path d="M404 590 H470" fill="none" stroke="var(--w-vcc)" stroke-width="2"/>
</g>

<g class="hit" data-k="mac" tabindex="0" role="button" aria-label="Mac">
  <rect class="box" x="50" y="640" width="150" height="120" rx="10"/>
  <text class="t-ti" x="125" y="692" text-anchor="middle">Mac</text>
  <text class="t-cap" x="125" y="714" text-anchor="middle">操作アプリ / MIDI</text>
  <path class="hitline" d="M200 700 H470"/>
  <path d="M200 700 H470" fill="none" stroke="var(--w-pwm)" stroke-width="2"/>
  <text class="t-cap" x="330" y="692" text-anchor="middle">USBシリアル</text>
</g>

<g class="hit" data-k="esp" tabindex="0" role="button" aria-label="ESP32-S3">
  <rect class="box" x="470" y="560" width="200" height="200" rx="12"/>
  <text class="t-ti" x="570" y="652" text-anchor="middle">ESP32-S3</text>
  <text class="t-cap" x="570" y="676" text-anchor="middle">指示だけを出す</text>
  <text class="t-cap" x="570" y="694" text-anchor="middle">(電力は流さない)</text>
  <text class="t-pin" x="478" y="594">5V</text>
  <text class="t-pin" x="478" y="704">USB</text>
  <text class="t-pin" x="530" y="578" text-anchor="middle">SEN</text>
  <text class="t-pin" x="620" y="578" text-anchor="middle">PWM</text>
  <text class="t-pin" x="662" y="644" text-anchor="end">SEL</text>
  <text class="t-pin" x="570" y="752" text-anchor="middle">GND</text>
</g>

<g class="hit" data-k="pwmline" tabindex="0" role="button" aria-label="PWM指示線">
  <path class="hitline" d="M620 560 V440"/>
  <path d="M620 560 V440" fill="none" stroke="var(--w-pwm)" stroke-width="2.2" stroke-dasharray="7 5"/>
  <text class="t-lab" x="632" y="510" fill="var(--w-pwm)">PWM(明るさ指示)</text>
</g>

<g class="hit" data-k="selline" tabindex="0" role="button" aria-label="SEL指示線">
  <path class="hitline" d="M670 640 H930 V448"/>
  <path d="M670 640 H930 V448" fill="none" stroke="var(--w-en)" stroke-width="2"/>
  <text class="t-lab" x="700" y="632" fill="var(--w-en)">SEL(系統選択)</text>
</g>

<g class="hit" data-k="ig" tabindex="0" role="button" aria-label="IG電源">
  <rect class="box" x="1180" y="560" width="150" height="60" rx="8"/>
  <text class="t-lab" x="1255" y="586" text-anchor="middle" font-weight="700">IG 12V</text>
  <text class="t-cap" x="1255" y="604" text-anchor="middle">キーON時のみ通電</text>
  <path class="hitline" d="M1180 590 H1046 V448"/>
  <path d="M1180 590 H1046 V448" fill="none" stroke="var(--w-vcc)" stroke-width="2"/>
</g>

<g class="hit" data-k="gnd" tabindex="0" role="button" aria-label="GND系統">
  <path class="hitline" d="M570 760 V810 M334 620 V818 H470 M570 826 V848"/>
  <path d="M570 760 V810" fill="none" stroke="var(--w-gnd)" stroke-width="2"/>
  <path d="M334 620 V818 H470" fill="none" stroke="var(--w-gnd)" stroke-width="2"/>
  <rect class="box" x="470" y="810" width="200" height="16" rx="4"/>
  <text class="t-cap" x="686" y="824">GNDバスバー</text>
  <path d="M570 826 V848" fill="none" stroke="var(--w-neg)" stroke-width="2.5"/>
  {chassis(570, 848)}
  <text class="t-cap" x="570" y="898" text-anchor="middle">車体一点アース</text>
</g>
''')

# ============ 電線サイズタグ(全区間) ============
S.append(f'''
<g aria-hidden="true">
  {sqtag(216, 382, "2.0sq")}
  {sqtag(540, 384, "0.75sq")}
  {sqtag(820, 386, "0.75sq", "var(--w-pos)")}
  {sqtag(1105, 380, "0.75sq", "var(--w-pos)")}
  {sqtag(1222, 450, "0.75sq", "var(--w-neg)")}
  {sqtag(1113, 582, "0.5sq")}
  {sqtag(370, 520, "0.5sq")}
  {sqtag(437, 578, "0.3sq")}
  {sqtag(592, 470, "0.3sq", "var(--w-pwm)")}
  {sqtag(880, 632, "0.3sq", "var(--w-en)")}
  {sqtag(560, 228, "0.3sq", "var(--w-is)")}
  {sqtag(402, 806, "0.3sq", "var(--w-gnd)")}
  {sqtag(1052, 200, "既存線・触らない", "var(--w-stock)")}
</g>
''')

svg = (f'<svg id="schematic" viewBox="0 0 {W} {H}" role="img" aria-label="1灯シンプル結線図">'
       + "".join(S) + "</svg>")

# ============ HTML ============
CSS = """
  :root {
    color-scheme: light;
    --bg: #f2f4f3; --surface: #ffffff; --box: #f5f7f6; --box-line: #c3cdc8;
    --ink: #212723; --muted: #5e6963; --line: #dbe1de; --accent: #a87413; --dot: #e2e7e4;
    --shadow: 0 10px 30px rgba(20, 30, 25, 0.18);
    --w-pwm: #2f6fb2; --w-en: #2f8659; --w-is: #7e58be; --w-vcc: #c07a16;
    --w-gnd: #78827c; --w-pos: #c2443a; --w-neg: #464d49; --w-stock: #6f5340;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Noto Sans JP", system-ui, sans-serif;
    font-size: 14.5px; line-height: 1.75; -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 1240px; margin: 0 auto; padding: 40px 24px 64px; }
  .eyebrow { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 11.5px;
    letter-spacing: 0.08em; color: var(--accent); margin: 0 0 6px; }
  h1 { font-size: 25px; font-weight: 700; margin: 0 0 10px; text-wrap: balance; line-height: 1.4; }
  .lead { color: var(--muted); margin: 0; max-width: 46em; }
  .lead b { color: var(--ink); }
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
  .panel svg { display: block; min-width: 1100px; width: 100%; height: auto; }
  svg .box { fill: var(--box); stroke: var(--box-line); stroke-width: 1.5; }
  svg .t-ti { font: 700 14px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--ink); }
  svg .t-pin { font: 11px ui-monospace, "SF Mono", Menlo, monospace; fill: var(--ink); }
  svg .t-lab { font: 12px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--ink); }
  svg .t-cap { font: 11px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--muted); }
  svg .t-num { font: 700 18px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--accent); }
  svg text { user-select: none; }
  svg .halo { stroke: var(--w-vcc); opacity: 0.15; stroke-width: 12; fill: none; stroke-linecap: round; }
  svg .hit { cursor: pointer; outline: none; }
  svg .hitline { stroke: transparent; stroke-width: 16; fill: none; pointer-events: stroke; }
  svg .hit:hover, svg .hit:focus-visible, svg .hit.sel { filter: drop-shadow(0 0 3px var(--accent)); }
  svg .hit:hover rect.box, svg .hit:focus-visible rect.box, svg .hit.sel rect.box { stroke: var(--accent); }
  .legend { display: flex; flex-wrap: wrap; gap: 8px 20px; margin: 8px 2px 0; font-size: 12.5px; color: var(--muted); }
  .legend span { display: inline-flex; align-items: center; gap: 7px; }
  .legend i { width: 18px; height: 4px; border-radius: 2px; display: inline-block; }
  .legend i.dash { background: repeating-linear-gradient(90deg, currentColor 0 5px, transparent 5px 9px); }
  .lgroup { border: 1px solid var(--line); border-radius: 10px; padding: 12px 16px 14px; margin-top: 12px; background: var(--surface); }
  .lg-title { font-size: 13px; font-weight: 700; }
  .lg-title small { font-weight: 400; color: var(--muted); }
  .lg-pwr { border-left: 4px solid var(--w-vcc); }
  .lg-sig { border-left: 4px solid var(--w-pwm); }
  .tbl-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
  table { border-collapse: collapse; width: 100%; min-width: 640px; font-size: 13.5px; }
  th, td { text-align: left; padding: 9px 14px; border-top: 1px solid var(--line); vertical-align: top; }
  thead th { border-top: none; font-size: 12px; color: var(--muted); font-weight: 600;
    letter-spacing: 0.04em; padding-top: 12px; padding-bottom: 8px; }
  td.sig { white-space: nowrap; font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 12.5px; }
  ol.flow { margin: 0; padding-left: 24px; }
  ol.flow li { margin: 8px 0; }
  ol.flow b { color: var(--accent); }
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
  footer { margin-top: 48px; font-size: 12px; color: var(--muted); }
"""

DATA_JS = """
    bat: { title: "① バッテリー", route: "12V → F20A → B+幹線 2.0sq",
      color: "var(--w-vcc)", items: [
      "全ての電力の出発点。ここ以外に電源は無い(純正ヒューズBOXからは取らない)。",
      "−端子は車体金属につながっていて、車体全体が電気の「帰り道」になる。",
      "だから各部品は−線を長く引き回さず、近くの車体に落とせば回路が一周する。" ] },
    mainfuse: { title: "② メインヒューズ 20A", route: "バッテリー直後・幹線2.0sqを保護",
      color: "var(--w-vcc)", items: [
      "幹線がどこかでショートした時に切れる保険。負荷ではなく「電線」を守る。",
      "バッテリーの根元に置く理由: ヒューズより上流(保護されない区間)を最短にするため。" ] },
    chfuse: { title: "③ 自作ヒューズBOX(ch毎 5A)", route: "B+バス → F5A → ハイサイドSW",
      color: "var(--w-vcc)", items: [
      "ここで1灯ぶんの回路に分岐する。1灯=1回路=1ヒューズ。",
      "5Aはこの先の細い線(0.75sq)を守る値。「5Aヒューズから先は5A耐性の線でよい」の根拠。",
      "17ch版ではこのBOXに5Aが17個並ぶだけ。各回路の形は全て本図と同じ。" ] },
    dcdc: { title: "DCDC 12V→5V", route: "B+バス → DCDC → ESP 5V",
      color: "var(--w-vcc)", items: [
      "ESPは5V(内部3.3V)で動くので、車の12Vを降圧して供給する。",
      "車載サージ対策で入力にTVS+ヒューズを追加。USB給電は机上テスト専用。" ] },
    sw: { title: "④ ハイサイドSW (BTS6143D)", route: "F5A → SW → リレーNO",
      color: "var(--w-pos)", items: [
      "電気の蛇口。ESPのPWM指示どおり12Vを高速ON/OFFし、そのON比率が明るさになる。",
      "過電流・過熱・短絡保護を内蔵。ここまでが「電力を作る側」。",
      "リレーが純正側の間は出力先が切り離されているので、PWMが出ていても灯具には流れない。" ] },
    relay: { title: "⑤ 切替リレー(8chモジュールの1ch)", route: "NC=純正 / NO=自作 / COM=灯具",
      color: "var(--accent)", items: [
      "灯具の+線を「純正」と「自作」のどちらにつなぐか選ぶだけの部品。電気は作らない。",
      "無励磁=NC(純正)。ESP停止・電源断・キーOFFのどれでも納車状態に戻るフェールセーフ。",
      "ESPがINを引くとモジュール内蔵ドライバがコイルを励磁し、NO(自作)側へ切り替わる。",
      "コイル電源はJD-VCC=IG12V。ロジック(VCC)とは分離する(JD-VCCジャンパを外す)。" ] },
    lamp: { title: "⑥ 灯具", route: "リレーCOM → 灯具+ / 灯具− → ボディアース",
      color: "var(--w-pos)", items: [
      "改造は+線への割り込み1点だけ。−は純正のままボディアース。",
      "電流は バッテリー+ → ①〜⑥ → 車体 → バッテリー− と一周して回路になる。" ] },
    stockbox: { title: "純正ヒューズBOX / スイッチ(車両側)", route: "純正操作 → 純正線 → リレーNC",
      color: "var(--w-stock)", items: [
      "ライトSWなど純正操作の出口。一切改造しない。電源もここからは取らない。",
      "茶色の破線=「電力の供給元ではなく、リレーのもう一つの入口(切替の相手側)」の意味。" ] },
    stockline: { title: "純正線(茶破線)", route: "純正分岐後 → リレーNC",
      color: "var(--w-stock)", items: [
      "灯具コネクタ直前でリレーに割り込む。切断しないので原状復帰できる。",
      "リレーが無励磁の間はこの線がそのまま灯具に直結=納車状態と同一。" ] },
    tap: { title: "純正入力モニタ(分圧タップ)", route: "純正線12V → 100kΩ → ●約2.2V → 22kΩ → GND",
      color: "var(--w-is)", items: [
      "抵抗は電流が流れた時だけ電圧を消費する。2本を直列にしてGNDまで電流の道を作ると、12Vが抵抗値の比で分配される。",
      "22k側の取り分 = 12V × 22/122 ≈ 2.2V。この中間点●から1本引き出してESPのSENSEピンで読む。ESP入力は電流をほぼ吸わないので電圧は乱れない。",
      "純正線から吸う電流は約0.1mA(合計122kΩ)。純正回路への影響は無視でき、電線も0.3sq級の細線で十分。",
      "ツェナー3.3Vは22kΩと並列・帯(カソード)を中間点側に向ける。普段は何もせず、サージで3.3Vを超えそうな時だけ電流を逃がす保険。",
      "注意: 100kと22kを逆に付けると中間点が約9.8VになりESPを壊す。純正線側=100kΩ厳守。" ] },
    esp: { title: "ESP32-S3", route: "PWM / SEL / SENSE の3本だけ",
      color: "var(--accent)", items: [
      "電力は一切流さない。出すのは指示3本: PWM(明るさ)・SEL(系統選択)・SENSE(監視・入力)。",
      "起動時はPWM 0%・SEL=純正側で初期化(誤点灯防止)。" ] },
    pwmline: { title: "PWM指示線(青破線)", route: "ESP GPIO → ハイサイドSW IN",
      color: "var(--w-pwm)", items: [
      "3.3Vの信号線。流れる電流は数mAで、灯具の電力はここを通らない。",
      "1kHzでON/OFF比率(duty)を送り、SWがそれを12V側で再現する。",
      "電線は0.3sq(AWG22)級の細線でよい。" ] },
    selline: { title: "SEL指示線(緑)", route: "ESP GPIO → リレーモジュール IN",
      color: "var(--w-en)", items: [
      "「この灯を自作系に切り替えろ」の1本。ch毎に独立。",
      "コイルの駆動そのものはモジュール内蔵ドライバがやる(ESPはトリガのみ)。",
      "電線は0.3sq(AWG22)級の細線でよい。" ] },
    ig: { title: "IG 12V(コイル電源)", route: "IGヒューズ → モジュール JD-VCC",
      color: "var(--w-vcc)", items: [
      "キーONの間だけ通電する系統。リレーコイルの電源をここから取る。",
      "キーOFFでは物理的に自作側へ切り替えられない=フェールセーフの一段目。" ] },
    mac: { title: "Mac(操作点)", route: "USBシリアル → ESP",
      color: "var(--w-pwm)", items: [
      "操作アプリ/MIDIの入力を集約してESPへ送る。電源系とは無関係。" ] },
    gnd: { title: "GND(帰り道)", route: "ESP/DCDC → バスバー → 車体一点",
      color: "var(--w-gnd)", items: [
      "小信号系のGNDはバスバーに集約して車体へ一点で落とす。",
      "灯具の−は純正どおり近傍のボディアース。大電流は自作GND線を通らない。" ] }
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
  <p class="eyebrow">MICRO-CONTROL / SINGLE LAMP</p>
  <h1>1灯だけのシンプル結線図 — 回路の流れ理解用</h1>
  <p class="lead"><b>太い線=電力の道</b>(バッテリー→①〜⑥→車体で一周)、<b>細い線=指示の道</b>(ESPは蛇口とスイッチに指示を出すだけで電力を流さない)。
  純正ヒューズBOXは茶色の破線=<b>給電元ではなく</b>、リレーのもう一つの入口。17ch版はこの回路が17個並ぶだけで、形は全て同じ。</p>

  <h2>結線図</h2>
  <p class="hint"><b>部品・線をクリック</b>すると役割の詳細が出る(Escで閉じる)。<b>橙のハイライトが乗っている線=電力線(太い電線)</b>、無い細線=信号線(0.3sqでよい)。<b>線上の丸タグ=その区間で使う電線サイズ(sq)</b>。</p>
"""

BODY_BOTTOM = """
  <div class="lgroup lg-pwr">
    <div class="lg-title">🔶 電力線 = 橙のハイライトが乗っている線 <small>— 12Vの電流が流れる。太い電線(2.0sq/0.75sq)で作る区間</small></div>
    <div class="legend">
      <span><i style="background:var(--w-vcc)"></i>12V電源(バッテリー/IG)</span>
      <span><i style="background:var(--w-pos)"></i>自作出力 12V(SW→リレー→灯具)</span>
      <span><i class="dash" style="color:var(--w-stock)"></i>純正線(給電ではない・切替の相手側)</span>
      <span><i style="background:var(--w-neg)"></i>−の帰り道(車体アース)</span>
    </div>
  </div>
  <div class="lgroup lg-sig">
    <div class="lg-title">🔹 信号線 = ハイライト無しの細い線 <small>— 3.3〜5V・電流ほぼゼロ。細線(0.3sq級)でよい区間</small></div>
    <div class="legend">
      <span><i class="dash" style="color:var(--w-pwm)"></i>PWM指示(3.3V)</span>
      <span><i style="background:var(--w-en)"></i>SEL指示(リレー選択)</span>
      <span><i style="background:var(--w-is)"></i>SENSE監視</span>
      <span><i style="background:var(--w-pwm)"></i>USBシリアル(既製ケーブル)</span>
      <span><i style="background:var(--w-gnd)"></i>小信号GND</span>
    </div>
  </div>

  <h2>用意する電線は実質3種類</h2>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th>区分</th><th>図中の区間</th><th>電線</th><th>根拠</th></tr></thead>
      <tbody>
        <tr><td class="sig">電力・幹線</td><td>①バッテリー → ②20A → ③ヒューズBOX</td><td class="sig">2.0sq (AWG14)</td><td>メイン20Aヒューズに耐える太さ</td></tr>
        <tr><td class="sig">電力・ch</td><td>③5Aヒューズ → ④SW → ⑤リレー → ⑥灯具 → アース</td><td class="sig">0.75sq (AWG18)</td><td>ch5Aヒューズに耐える=「12V5A」の区間</td></tr>
        <tr><td class="sig">信号</td><td>PWM・SEL・SENSE・DCDC5V出力・小信号GND</td><td class="sig">0.3sq (AWG22)級</td><td>3.3〜5V・数mA〜数百mAしか流れない</td></tr>
      </tbody>
    </table>
  </div>
  <p class="hint" style="margin-top:10px">例外: IG→リレーコイル電源(JD-VCC)は0.5sqで可(コイル電流のみ・5Aヒューズ付き)。純正線は既存ハーネスのままで触るのは割り込み接続の1点だけ。原則は常に「電線の容量 ≥ 上流ヒューズの容量」。</p>

  <h2>回路の流れ(この順に追う)</h2>
  <ol class="flow">
    <li><b>①→②→③</b> バッテリーからメイン20A・ch用5Aヒューズまでが12Vの幹線(橙)。純正ヒューズBOXは通らない。</li>
    <li><b>④</b> ハイサイドSWがPWM指示に従って12Vを刻み、「明るさ付きの12V」を作る(ここから赤)。</li>
    <li><b>⑤</b> 切替リレーは灯具の+を純正(茶破線)と自作(赤)のどちらにつなぐか選ぶだけ。平常時・異常時は必ず純正側。</li>
    <li><b>⑥</b> 灯具を通った電流はボディアース→車体→バッテリー−へ戻って一周し、回路が成立する。</li>
    <li>細い線3本は指示のみ: <b>PWM</b>(明るさ)・<b>SEL</b>(系統選択)・<b>SENSE</b>(純正の監視 — 純正線の12Vを分圧タップで約2.2Vに落として読む)。灯具の電力はここを通らない。</li>
  </ol>

  <footer>生成元: gen_single_lamp.py(HTMLを直接編集しない)。17ch版=本回路×17: full-wiring-17ch.html / 実体配置: board-layout-17ch.html。2026-08-04。</footer>
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
        "<title>1灯シンプル結線図 — 回路の流れ理解用</title>\n"
        "<style>" + CSS + "</style>\n"
        + BODY_TOP
        + '<div class="panel">' + svg + "</div>\n"
        + BODY_BOTTOM
        + "<script>" + POPUP_JS + "</script>\n")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
