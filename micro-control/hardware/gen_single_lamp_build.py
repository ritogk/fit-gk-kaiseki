#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1灯ぶんの机上組み立てガイド(ブレッドボード可否の区分付き)を生成する。
出力: single-lamp-build.html
結線図SVG・CSS・ポップアップは gen_single_lamp.py から流用し、実装区分バッジと
ブレッドボード配置図・実装場所表・組立手順を追加する。
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
"""
import io, os
import gen_single_lamp as base

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "single-lamp-build.html")


def badge(x, y, kind):
    fill = {"bb": "var(--w-en)", "mod": "var(--accent)", "pwr": "var(--w-pos)"}[kind]
    label = {"bb": "BB可", "mod": "既製", "pwr": "端子"}[kind]
    return (f'<rect x="{x}" y="{y}" width="44" height="18" rx="9" fill="{fill}" opacity="0.92"/>'
            f'<text x="{x+22}" y="{y+13}" text-anchor="middle" font-size="10.5" font-weight="700" '
            f'fill="#fff" font-family="Hiragino Sans, Noto Sans JP, sans-serif">{label}</text>')


BADGES = ('<g aria-hidden="true" pointer-events="none">'
          + badge(606, 178, "bb")      # 監視タップ(分圧3点)
          + badge(58, 360, "pwr")      # バッテリー
          + badge(240, 420, "pwr")     # メインヒューズ20A
          + badge(368, 360, "pwr")     # 自作ヒューズBOX
          + badge(588, 368, "mod")     # ハイサイドSW(変換基板)
          + badge(908, 360, "mod")     # リレーモジュール
          + badge(1224, 424, "pwr")    # 灯具
          + badge(272, 568, "mod")     # DCDC
          + badge(478, 568, "bb")      # ESP32-S3
          + badge(1188, 568, "pwr")    # IG12V
          + badge(400, 806, "pwr")     # GNDバスバー
          + '</g>')

svg_badged = base.svg.replace("</svg>", BADGES + "</svg>")

# ============ ブレッドボード配置図(監視タップ+ESP) ============
BB = []
COLS = [100 + i * 32 for i in range(16)]        # col1..col16
ROWS = [100, 135, 170, 205, 240]                # a..e
NODE = COLS[6]                                  # col7 = 中間点の列

BB.append('<rect x="88" y="76" width="524" height="180" rx="10" class="box"/>')
for x in COLS:
    BB.append(f'<path d="M{x} 95 V245" stroke="var(--line)" stroke-width="1" fill="none"/>')
for y in ROWS:
    for x in COLS:
        BB.append(f'<circle cx="{x}" cy="{y}" r="3" fill="var(--box-line)"/>')

# 中間点の列ハイライト
BB.append(f'<path d="M{NODE} 90 V250" stroke="var(--w-is)" stroke-width="7" opacity="0.25" fill="none"/>')
BB.append(f'<text class="t-lab" x="{NODE}" y="66" text-anchor="middle" fill="var(--w-is)">この縦1列が中間点 ≈2.2V</text>')

# ① 12V入力 → col2 (行a)
BB.append(f'<circle cx="30" cy="100" r="4" fill="var(--w-vcc)"/>'
          f'<path d="M30 100 H{COLS[1]}" stroke="var(--w-vcc)" stroke-width="2.5" fill="none"/>'
          f'<text class="t-cap" x="30" y="86" fill="var(--w-vcc)">監視対象の12V(机上テストでは電源+)</text>'
          f'<text class="t-num" x="{COLS[1]}" y="88" text-anchor="middle" font-size="14">①</text>')

# ② 100kΩ col2→col7 (行b)
BB.append(f'<path d="M{COLS[1]} 135 H{COLS[1]+32}" stroke="var(--ink)" stroke-width="1.6" fill="none"/>'
          f'<rect x="{COLS[1]+32}" y="127" width="{NODE-COLS[1]-64}" height="16" rx="3" class="box"/>'
          f'<text class="t-pin" x="{(COLS[1]+NODE)//2}" y="139" text-anchor="middle">100kΩ</text>'
          f'<path d="M{NODE-32} 135 H{NODE}" stroke="var(--ink)" stroke-width="1.6" fill="none"/>'
          f'<text class="t-num" x="{(COLS[1]+NODE)//2}" y="118" text-anchor="middle" font-size="14">②</text>')

# ③ ツェナー col7→col10 (行c) 帯=col7側
Z_END = COLS[9]
BB.append(f'<path d="M{NODE} 170 H{NODE+18}" stroke="var(--ink)" stroke-width="1.6" fill="none"/>'
          f'<rect x="{NODE+18}" y="162" width="40" height="16" rx="3" class="box"/>'
          f'<rect x="{NODE+20}" y="162" width="6" height="16" fill="var(--w-is)"/>'
          f'<path d="M{NODE+58} 170 H{Z_END}" stroke="var(--ink)" stroke-width="1.6" fill="none"/>'
          f'<text class="t-num" x="{NODE+38}" y="156" text-anchor="middle" font-size="14">③</text>')

# ④ 22kΩ col7→col12 (行d)
K_END = COLS[11]
BB.append(f'<path d="M{NODE} 205 H{NODE+28}" stroke="var(--ink)" stroke-width="1.6" fill="none"/>'
          f'<rect x="{NODE+28}" y="197" width="{K_END-NODE-56}" height="16" rx="3" class="box"/>'
          f'<text class="t-pin" x="{(NODE+K_END)//2}" y="209" text-anchor="middle">22kΩ</text>'
          f'<path d="M{K_END-28} 205 H{K_END}" stroke="var(--ink)" stroke-width="1.6" fill="none"/>'
          f'<text class="t-num" x="{(NODE+K_END)//2}" y="190" text-anchor="middle" font-size="14">④</text>')

# ⑤ GNDジャンプ col10・col12 → −レール
BB.append(f'<path d="M{Z_END} 240 V300 M{K_END} 240 V300" stroke="var(--w-gnd)" stroke-width="2" fill="none"/>'
          f'<text class="t-num" x="{(Z_END+K_END)//2}" y="268" text-anchor="middle" font-size="14">⑤</text>')

# −レール
BB.append('<rect x="100" y="288" width="790" height="28" rx="4" class="box"/>'
          '<path d="M120 302 H870" stroke="var(--w-gnd)" stroke-width="2.5" fill="none"/>'
          '<text class="t-cap" x="120" y="334">−(GND)レール — ESPのGNDともここで共通化</text>')

# ⑥ SENSE col7 → ESP
BB.append(f'<path d="M{NODE} 240 V268 H860 V150 H900" stroke="var(--w-is)" stroke-width="2" fill="none"/>'
          f'<text class="t-num" x="620" y="260" text-anchor="middle" font-size="14">⑥</text>'
          f'<text class="t-cap" x="800" y="142" text-anchor="middle" fill="var(--w-is)">SENSE</text>')

# ESP32-S3 ブロック
BB.append('<rect x="900" y="80" width="340" height="200" rx="12" class="box"/>'
          '<text class="t-ti" x="1070" y="160" text-anchor="middle">ESP32-S3</text>'
          '<text class="t-cap" x="1070" y="186" text-anchor="middle">ブレッドボードに跨がせて挿す</text>'
          '<text class="t-cap" x="1070" y="208" text-anchor="middle">机上はUSB給電でOK(DCDC不要)</text>'
          '<text class="t-pin" x="912" y="146">SEN</text>'
          '<text class="t-pin" x="912" y="214">GND</text>')
BB.append('<path d="M900 210 H868 V300" stroke="var(--w-gnd)" stroke-width="2" fill="none"/>')

# 組み方・注意
BB.append('<text class="t-lab" x="60" y="356" font-weight="700">組み方(番号順)</text>'
          '<text class="t-cap" x="60" y="378">① 監視対象の12Vを col2 へ / ② 100kΩ: col2→col7 / ③ ツェナー: col7→col10(黒帯を col7 側に向ける)</text>'
          '<text class="t-cap" x="60" y="396">④ 22kΩ: col7→col12 / ⑤ col10・col12 から−レールへジャンプワイヤ / ⑥ col7 から ESP の SENSE ピンへ</text>'
          '<text class="t-cap" x="60" y="414">同じ縦1列(5穴)は基板内部でつながっている。足を同じ列に挿す=接続完了。</text>')

bb_svg = ('<svg id="bb" viewBox="0 0 1340 430" role="img" aria-label="ブレッドボード配置図(監視タップ)">'
          + "".join(BB) + "</svg>")

BODY_TOP = """
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / BENCH BUILD</p>
  <h1>1灯ぶんの机上組み立て — ブレッドボードで良い所・ダメな所</h1>
  <p class="lead">区分の基準は<b>流れる電流</b>。信号(mA以下)=<b>ブレッドボード可</b> /
  電力(A級)=<b>圧着・ネジ端子必須</b> / リレー・DCDC・変換基板は<b>既製基板のまま</b>使う。
  部品は選定済みの実物(KOA 100kΩ/22kΩ・1N5226B・EALE 5A平型ヒューズ 等)を前提にした。</p>

  <h2>結線図と実装区分</h2>
  <p class="hint">バッジの意味 — <b>BB可</b>=ブレッドボードで組める(信号のみ) / <b>既製</b>=既製モジュール・変換基板をそのまま使う / <b>端子</b>=圧着・ネジ端子必須(ブレッドボード禁止)。部品クリックで詳細。</p>
"""

BODY_MID = """
  <h2>ブレッドボード実装(監視タップ + ESP)</h2>
  <p class="hint">⚠ <b>電力線(12V→灯具のA級電流)は絶対にブレッドボードへ載せない</b>。接点の実力は1A程度で、3A流すと発熱・溶融する。</p>
"""

BODY_BOTTOM = """
  <h2>実装場所一覧</h2>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th>部品(選定品)</th><th>机上テスト</th><th>恒久実装</th><th>流れる電流</th></tr></thead>
      <tbody>
        <tr><td>監視タップ(100kΩ+22kΩ+1N5226B)</td><td>ブレッドボード可(上図)</td><td>ユニバーサル基板へハンダ</td><td class="sig">約0.1mA</td></tr>
        <tr><td>ESP32-S3</td><td>ブレッドボード可・USB給電</td><td>基板+ピンソケット</td><td class="sig">mA級</td></tr>
        <tr><td>信号線(PWM / SEL / SENSE)</td><td>ジャンプワイヤ</td><td>0.3sq電線</td><td class="sig">数mA</td></tr>
        <tr><td>DCDC 12V→5V</td><td>不要(USB給電で代替)</td><td>入出力とも端子・ハンダ</td><td class="sig">〜0.5A</td></tr>
        <tr><td>切替リレーモジュール(8ch)</td><td>既製基板のまま。IN=ジャンプワイヤ可 / 接点側=ネジ端子</td><td>同左</td><td class="sig">コイル約70mA / 接点は灯具電流</td></tr>
        <tr><td>ハイサイドSW BTS6143D</td><td>ブレッドボード不可 — TO-252-5変換基板に実装して端子接続</td><td>ユニバーサル基板</td><td class="sig">灯具電流 1〜3A</td></tr>
        <tr><td>ヒューズ(メイン20A / ch5A平型)</td><td>電線付きホルダー・圧着</td><td>ヒューズBOX</td><td class="sig">幹線〜20A / ch〜5A</td></tr>
        <tr><td>電力線(バッテリー→SW→リレー→灯具→GND)</td><td>2.0sq/0.75sq+圧着・ネジ端子。<b>ブレッドボード絶対禁止</b></td><td>同左</td><td class="sig">A級(最大20A)</td></tr>
      </tbody>
    </table>
  </div>

  <h2>組立手順(この順で)</h2>
  <ol class="flow">
    <li><b>準備</b> — リレーモジュールの JD-VCC ジャンパを外す(ロジックとコイル電源の分離)。</li>
    <li><b>ブレッドボード</b> — ESP32-S3 を挿し、監視タップを上図の列番号どおり組む。まず USB 給電だけで起動確認(12V系はまだつながない)。</li>
    <li><b>SENSE 単体テスト</b> — タップ入力(col2)に12Vを付け外しして、ESPのログで HIGH/LOW が切り替わること。</li>
    <li><b>信号線</b> — PWM→ハイサイドSW IN / SEL→リレーモジュール IN をジャンプワイヤで接続し、ESPのGNDとモジュールのGNDを共通化。</li>
    <li><b>電力側(ブレッドボード禁止区間)</b> — バッテリー+→20Aホルダー→5A平型→SW VS、SW OUT→リレーNO、COM→灯具+、灯具−→電源−。全て圧着・ネジ端子。</li>
    <li><b>検証</b> — 灯具レスで COM 出力電圧(体感30%≈7V / 100%≈10V)→実負荷点灯→ソフトスタート目視→30分後に SW 端子を触診(50℃以下)。</li>
    <li><b>恒久化</b> — 合格後、ブレッドボードの内容をユニバーサル基板へ移植(配置は board-layout-17ch.html)。</li>
  </ol>

  <footer>生成元: gen_single_lamp_build.py(HTMLを直接編集しない)。結線の意味: single-lamp-wiring.html / 17ch版: full-wiring-17ch.html。2026-08-04。</footer>
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
        "<title>1灯シンプル結線図 — 机上組み立てガイド</title>\n"
        "<style>" + base.CSS + "</style>\n"
        + BODY_TOP
        + '<div class="panel">' + svg_badged + "</div>\n"
        + BODY_MID
        + '<div class="panel">' + bb_svg + "</div>\n"
        + BODY_BOTTOM
        + "<script>" + base.POPUP_JS + "</script>\n")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
