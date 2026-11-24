#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ユニバーサル基板で大電流(Vbb/OUT)をどう流すかの解説図を生成する。
出力: universal-board-current.html
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
内容: 図1=基板そのものの構造(穴とランドは互いにつながっていない)
      図2=断面図(BTSカートリッジ→ソケット→裏面の太線→端子台の電流経路)
      図3=裏面図の良い例/悪い例
BTS6143Dのピン順は ①GND ②IN ③Vbb ④IS ⑤OUT として描く(推測・データシートで要確認)。
"""
import io, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "universal-board-current.html")

PINS = ["GND", "IN", "Vbb", "IS", "OUT"]
BIG = {"Vbb": "var(--w-pos)", "OUT": "#e07a1c"}
MONO = 'font-family="ui-monospace, SF Mono, Menlo, monospace"'


def land(cx, cy, r=7, hole=2.6, fill="var(--cu)"):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="var(--cu-line)" stroke-width="1"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{hole}" fill="var(--hole)"/>')


def heat(x, y):
    return (f'<g><path d="M{x} {y} q6 -8 0 -16 q-6 -8 0 -16 M{x+10} {y} q6 -8 0 -16 q-6 -8 0 -16 '
            f'M{x-10} {y} q6 -8 0 -16 q-6 -8 0 -16" stroke="var(--danger)" stroke-width="2" fill="none" '
            f'stroke-linecap="round"/></g>')


def badge(x, y, text, kind="ok"):
    col = {"ok": "var(--ok)", "ng": "var(--danger)"}[kind]
    bg = {"ok": "var(--ok-bg)", "ng": "var(--danger-bg)"}[kind]
    w = 16 + sum(13 if ord(c) > 0x2000 else 7 for c in text)
    return (f'<rect x="{x}" y="{y-14}" width="{w}" height="22" rx="11" fill="{bg}" stroke="{col}" stroke-width="1.3"/>'
            f'<text x="{x+w/2:.0f}" y="{y+2}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{col}">{text}</text>')


# ================= 図1: 基板の構造 =================
F1 = []
bx, by, cols, rows, p = 40, 40, 14, 7, 30
F1.append(f'<rect x="{bx-18}" y="{by-18}" width="{(cols-1)*p+36}" height="{(rows-1)*p+36}" rx="6" fill="var(--epoxy)" stroke="var(--epoxy-line)" stroke-width="1.5"/>')
for r in range(rows):
    for c in range(cols):
        F1.append(land(bx + c * p, by + r * p))
F1.append(f'<text class="t-ti" x="{bx-18}" y="{by+(rows-1)*p+48}">ユニバーサル基板(裏面)</text>')
# 拡大
zx, zy = 560, 120
F1.append(f'<line x1="{bx+3*p}" y1="{by+2*p}" x2="{zx-70}" y2="{zy-10}" stroke="var(--muted)" stroke-dasharray="4 4"/>')
F1.append(f'<circle cx="{bx+3.5*p}" cy="{by+2*p}" r="26" fill="none" stroke="var(--muted)" stroke-dasharray="4 4"/>')
F1.append(land(zx - 40, zy, r=26, hole=9))
F1.append(land(zx + 40, zy, r=26, hole=9))
F1.append(f'<path d="M{zx-12} {zy} H{zx+12}" stroke="var(--danger)" stroke-width="2" stroke-dasharray="3 3"/>')
F1.append(f'<text x="{zx}" y="{zy-36}" text-anchor="middle" font-size="12.5" fill="var(--danger)" font-weight="700">つながっていない</text>')
F1.append(f'<text class="t-cap" x="{zx-40}" y="{zy+46}" text-anchor="middle">ランド(銅)</text>')
F1.append(f'<text class="t-cap" x="{zx+40}" y="{zy+46}" text-anchor="middle">穴</text>')
F1.append(f'<text class="t-lab" x="{zx-80}" y="{zy+84}">銅は穴のまわりの小さな丸だけです。</text>')
F1.append(f'<text class="t-lab" x="{zx-80}" y="{zy+104}">電流の道は、自分で付ける線とはんだです。</text>')
SVG1 = f'<svg viewBox="0 0 760 290" role="img" aria-label="ユニバーサル基板の裏面。穴ごとの銅ランドは互いにつながっていない">{"".join(F1)}</svg>'

# ================= 図2: 断面図(電流の道) =================
F2 = []
F2.append('<defs><marker id="ar" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
          '<path d="M0 0 L10 5 L0 10 z" fill="var(--flow)"/></marker></defs>')
# x positions of 5 pins
px0, pp = 300, 40
PX = [px0 + i * pp for i in range(5)]
# BTS chip + conversion board
F2.append(f'<rect x="{PX[0]-30}" y="70" width="{4*pp+60}" height="12" rx="2" fill="#c0392b" stroke="#8e2a20"/>')
F2.append(f'<text class="t-cap" x="{PX[0]-40}" y="80" text-anchor="end">変換基板(赤)</text>')
F2.append(f'<rect x="{PX[0]+10}" y="36" width="{4*pp-20}" height="34" rx="3" fill="#2b2f2d"/>')
F2.append(f'<rect x="{PX[0]+30}" y="66" width="{4*pp-60}" height="6" fill="#9aa3a0"/>')
F2.append(f'<text x="{PX[2]}" y="58" text-anchor="middle" fill="#fff" font-size="12" {MONO}>BTS6143D</text>')
F2.append(f'<text class="t-cap" x="{PX[4]+50}" y="56">裏の金属タブ=Vbb(はんだ付け)</text>')
# header plastic + pins
F2.append(f'<rect x="{PX[0]-16}" y="96" width="{4*pp+32}" height="12" fill="#2b2f2d"/>')
F2.append(f'<text class="t-cap" x="{PX[4]+50}" y="106">オスのピンヘッダ</text>')
# socket
F2.append(f'<rect x="{PX[0]-16}" y="132" width="{4*pp+32}" height="22" fill="#3a3f3c"/>')
F2.append(f'<text class="t-cap" x="{PX[4]+50}" y="148">丸ピンICソケット(メス)</text>')
# universal board
F2.append(f'<rect x="60" y="154" width="680" height="14" fill="var(--epoxy)" stroke="var(--epoxy-line)"/>')
F2.append(f'<text class="t-cap" x="160" y="186">ユニバーサル基板</text>')
for i, name in enumerate(PINS):
    x = PX[i]
    F2.append(f'<rect x="{x-2}" y="82" width="4" height="66" fill="#c9a227"/>')
    F2.append(f'<rect x="{x-3}" y="168" width="6" height="14" fill="#c9a227"/>')
    F2.append(f'<path d="M{x-10} 168 h20 l-4 8 h-12 z" fill="var(--solder)"/>')
    col = BIG.get(name, "var(--ink)")
    F2.append(f'<text x="{x}" y="28" text-anchor="middle" font-size="11.5" {MONO} fill="{col}" font-weight="{700 if name in BIG else 400}">{"①②③④⑤"[i]}{name}</text>')
# thick wires underneath for Vbb and OUT
yv, yo = 214, 244
# Vbb: terminal on left
F2.append(f'<path d="M{PX[2]} 182 V{yv} H120 V168" stroke="var(--w-pos)" stroke-width="7" fill="none" stroke-linejoin="round"/>')
F2.append(f'<path d="M{PX[4]} 182 V{yo} H680 V168" stroke="#e07a1c" stroke-width="7" fill="none" stroke-linejoin="round"/>')
# small signal wires
for i in (0, 1, 3):
    F2.append(f'<path d="M{PX[i]} 182 V{270+i*6}" stroke="var(--w-gnd)" stroke-width="1.6" fill="none"/>')
F2.append(f'<text class="t-cap" x="{PX[0]-8}" y="300">IN・IS・GNDは細い線で可(数mA)</text>')
# screw terminals
for tx, lab, col in ((120, "Vbb端子", "var(--w-pos)"), (680, "OUT端子", "#e07a1c")):
    F2.append(f'<rect x="{tx-24}" y="118" width="48" height="36" rx="3" fill="#2e7bd1" stroke="#1d5a9c"/>')
    F2.append(f'<circle cx="{tx}" cy="132" r="8" fill="#cfd6d3" stroke="#8a948f"/><path d="M{tx-5} 132 h10" stroke="#555" stroke-width="2"/>')
    F2.append(f'<text x="{tx}" y="108" text-anchor="middle" font-size="12" font-weight="700" fill="{col}">{lab}</text>')
F2.append(f'<text x="20" y="80" class="t-cap">ヒューズから12V</text>')
F2.append(f'<path d="M{60} 86 Q66 130 96 134" stroke="var(--w-pos)" stroke-width="3" fill="none"/>')
F2.append(f'<text x="716" y="84" class="t-cap">灯具へ</text>')
F2.append(f'<path d="M704 134 Q734 130 734 92" stroke="#e07a1c" stroke-width="3" fill="none"/>')
F2.append(f'<text x="{(120+PX[2])/2:.0f}" y="{yv+20}" text-anchor="middle" font-size="12" font-weight="700" fill="var(--w-pos)">裏面を0.5sq線で直結</text>')
F2.append(f'<text x="{(PX[4]+680)/2:.0f}" y="{yo+20}" text-anchor="middle" font-size="12" font-weight="700" fill="#b45f12">裏面を0.5sq線で直結</text>')
# current flow arrows (dashed)
F2.append(f'<path class="flow" d="M{120} 160 V{yv-10} H{PX[2]-12} V96" stroke="var(--flow)" stroke-width="2.2" fill="none" marker-end="url(#ar)"/>')
F2.append(f'<path class="flow" d="M{PX[4]+12} 96 V{yo-10} H{670} V160" stroke="var(--flow)" stroke-width="2.2" fill="none" marker-end="url(#ar)"/>')
F2.append(f'<text x="{PX[4]+24}" y="{yo-16}" font-size="11.5" fill="var(--flow)">電流の道(数A)</text>')
SVG2 = f'<svg viewBox="0 0 800 320" role="img" aria-label="断面図。12Vは端子台から裏面の太線でソケットのVbbピンへ入り、BTSを通ってOUTピンから裏面の太線で灯具端子へ出る">{"".join(F2)}</svg>'

# ================= 図3: 裏面の良い例 / 悪い例 =================
def back_view(ox, title, mode):
    G = []
    G.append(f'<rect x="{ox}" y="40" width="330" height="250" rx="8" fill="var(--epoxy)" stroke="var(--epoxy-line)" stroke-width="1.5"/>')
    for r in range(7):
        for c in range(10):
            G.append(land(ox + 30 + c * 30, 70 + r * 30, r=6, hole=2.2))
    # socket pins row at row 3 (y=160), cols 3..7
    sy = 160
    sx = [ox + 30 + (3 + i) * 30 for i in range(5)]
    for i, x in enumerate(sx):
        G.append(f'<circle cx="{x}" cy="{sy}" r="7" fill="var(--solder)" stroke="#8a948f"/>')
        col = BIG.get(PINS[i], "var(--ink)")
        G.append(f'<text x="{x}" y="{sy-14}" text-anchor="middle" font-size="10" {MONO} fill="{col}">{PINS[i]}</text>')
    # terminals: Vbb at left (col0,row5), OUT at right (col9,row5)
    tv = (ox + 30, 250); to = (ox + 300, 250)
    for (x, y), lab, col in ((tv, "Vbb端子", "var(--w-pos)"), (to, "OUT端子", "#e07a1c")):
        G.append(f'<circle cx="{x}" cy="{y}" r="8" fill="var(--solder)" stroke="#8a948f"/>')
        G.append(f'<circle cx="{x}" cy="{y-30}" r="8" fill="var(--solder)" stroke="#8a948f"/>')
        G.append(f'<text x="{x}" y="{y+26}" text-anchor="middle" font-size="11" font-weight="700" fill="{col}">{lab}</text>')
    if mode == "ok":
        G.append(f'<path d="M{sx[2]} {sy} V{tv[1]} H{tv[0]}" stroke="var(--w-pos)" stroke-width="7" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')
        G.append(f'<path d="M{sx[4]} {sy} V{to[1]-30} Q{sx[4]} {to[1]} {to[0]} {to[1]}" stroke="#e07a1c" stroke-width="7" fill="none" stroke-linecap="round"/>')
        G.append(f'<text x="{sx[2]-6}" y="{tv[1]-12}" text-anchor="end" font-size="11" fill="var(--w-pos)">0.5sq</text>')
        G.append(f'<text x="{sx[4]+10}" y="{sy+50}" font-size="11" fill="#b45f12">0.5sq</text>')
        G.append(f'<text class="t-cap" x="{ox+165}" y="320" text-anchor="middle">太い線1本で、ピンから端子までを最短でつなぐ</text>')
        G.append(badge(ox, 24, "良い例", "ok"))
    else:
        # thin tinned wire zigzag for Vbb, solder bridges for OUT
        pts = f'M{sx[2]} {sy} L{sx[2]} {sy+30} L{sx[2]-60} {sy+30} L{sx[2]-60} {sy+60} L{tv[0]+30} {sy+60} L{tv[0]+30} {tv[1]} L{tv[0]} {tv[1]}'
        G.append(f'<path d="{pts}" stroke="#9aa3a0" stroke-width="1.6" fill="none"/>')
        bridge = [(sx[4], sy + 30 * k) for k in range(0, 3)] + [(ox + 270, sy + 60), (ox + 300, sy + 60)]
        for (x1, y1), (x2, y2) in zip(bridge, bridge[1:]):
            G.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="var(--solder)" stroke-width="9" stroke-linecap="round"/>')
        G.append(f'<path d="M{ox+300} {sy+60} V{to[1]}" stroke="var(--solder)" stroke-width="9" stroke-linecap="round"/>')
        G.append(heat(sx[2] - 60, sy + 52))
        G.append(heat(sx[4] + 30, sy + 52))
        G.append(f'<text x="{sx[2]-96}" y="{sy+50}" font-size="11" font-weight="700" fill="var(--danger)">細い線</text>')
        G.append(f'<text x="{sx[4]+16}" y="{sy+86}" font-size="11" fill="var(--danger)">はんだブリッジ</text>')
        G.append(f'<text class="t-cap" x="{ox+165}" y="320" text-anchor="middle">細い線・遠回り・はんだだけでつなぐと、そこが発熱する</text>')
        G.append(badge(ox, 24, "悪い例", "ng"))
    G.append(f'<text class="t-ti" x="{ox+80}" y="30">{title}</text>')
    return "".join(G)

SVG3 = ('<svg viewBox="0 0 760 340" role="img" aria-label="裏面の良い例と悪い例">'
        + back_view(20, "裏面", "ok") + back_view(410, "裏面", "ng") + "</svg>")

CSS = """
  :root {
    color-scheme: light;
    --bg: #f2f4f3; --surface: #ffffff; --box-line: #c3cdc8;
    --ink: #212723; --muted: #5e6963; --line: #dbe1de; --accent: #a87413; --dot: #e2e7e4;
    --w-pos: #c2443a; --w-gnd: #78827c; --flow: #2f6fb2;
    --epoxy: #cfe3c4; --epoxy-line: #8fb17e; --cu: #e7b57a; --cu-line: #b9864a; --hole: #4b5a46;
    --solder: #c9cfcc; --phenol: #d9b48a; --phenol-line: #a9814f;
    --ok: #2f7d4f; --ok-bg: #e8f4ec;
    --danger: #b3372c; --danger-bg: #fbeeec; --danger-line: #ecc9c4;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
    font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Noto Sans JP", system-ui, sans-serif;
    font-size: 14.5px; line-height: 1.75; -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 1000px; margin: 0 auto; padding: 40px 16px 64px; }
  .eyebrow { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 11.5px;
    letter-spacing: 0.08em; color: var(--accent); margin: 0 0 6px; }
  h1 { font-size: 25px; font-weight: 700; margin: 0 0 10px; line-height: 1.4; }
  .lead { color: var(--muted); margin: 0; max-width: 50em; }
  h2 { font-size: 16.5px; font-weight: 700; margin: 44px 0 14px; display: flex; align-items: center; gap: 10px; }
  h2::before { content: ""; width: 5px; height: 18px; border-radius: 2px; background: var(--accent); flex: none; }
  p.note { margin: 0 0 12px; max-width: 52em; }
  .panel { background: var(--surface);
    background-image: radial-gradient(var(--dot) 1px, transparent 1px); background-size: 22px 22px;
    border: 1px solid var(--line); border-radius: 10px; overflow-x: auto; padding: 10px 6px; }
  .panel svg { display: block; width: 100%; height: auto; min-width: 640px; }
  svg .t-ti { font: 700 14px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--ink); }
  svg .t-lab { font: 13px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--ink); }
  svg .t-cap { font: 11.5px "Hiragino Sans", "Noto Sans JP", sans-serif; fill: var(--muted); }
  svg text { font-family: "Hiragino Sans", "Noto Sans JP", sans-serif; }
  @media (prefers-reduced-motion: no-preference) {
    svg .flow { stroke-dasharray: 8 6; animation: flow 0.9s linear infinite; }
  }
  @keyframes flow { to { stroke-dashoffset: -14; } }
  .tbl-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
  table { border-collapse: collapse; width: 100%; min-width: 560px; font-size: 13.5px; }
  th, td { text-align: left; padding: 9px 14px; border-top: 1px solid var(--line); vertical-align: top; }
  thead th { border-top: none; font-size: 12px; color: var(--muted); font-weight: 600; }
  .sw { display: inline-block; width: 14px; height: 14px; border-radius: 3px; vertical-align: -2px; margin-right: 6px; }
  .warn { border: 1px solid var(--danger-line); background: var(--danger-bg); border-radius: 10px;
    padding: 12px 16px; margin-top: 14px; max-width: 52em; }
  .warn b { color: var(--danger); }
  @media print { .panel { overflow: visible; } svg .flow { animation: none; } * { print-color-adjust: exact; -webkit-print-color-adjust: exact; } }
"""

BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / UNIVERSAL BOARD</p>
  <h1>ユニバーサル基板で大電流を流すしくみ</h1>
  <p class="lead">ユニバーサル基板は、そのままでは電流の道を持っていません。BTSのVbbとOUTの2本だけを、基板の裏で太い線を使って端子台へ直結すれば、数Aの灯具電流を安全に流せます。</p>

  <h2>1. 基板そのものの構造</h2>
  <p class="note">基板には格子状に穴が開いていて、穴のまわりに小さな銅の丸(ランド)が付いているだけです。ランド同士はつながっていないので、どこをつなぐかは自分で線を付けて決めます。そのため、流せる電流の大きさは、基板ではなく自分で付けた線の太さで決まります。</p>
  <div class="panel">{SVG1}</div>

  <h2>2. 横から見た電流の道</h2>
  <p class="note">12Vはヒューズから左の端子台に入り、基板の裏の太い線(赤)でソケットのVbbピンへ届きます。BTSの中を通ったあと、OUTピンから裏の太い線(橙)で右の端子台へ出て、灯具へ向かいます。ピンとソケットの接点は通り道の一部にすぎないので、それ以外の区間を太い線で短くつなぐのが要点です。</p>
  <div class="panel">{SVG2}</div>
  <p class="note" style="margin-top:10px;font-size:12.5px;color:var(--muted)">ピンの並び(①GND ②IN ③Vbb ④IS ⑤OUT)は説明用で、データシートと変換基板の印字で確かめてから配線してください。</p>

  <h2>3. 裏面の良い例と悪い例</h2>
  <p class="note">良い例は、0.5sqの被覆線(または太さ0.8mm以上のスズメッキ線)1本を、ピンのランドから端子のランドまで最短で這わせ、途中を何か所かはんだで留めたものです。悪い例のように、細い線で遠回りしたり、ランド同士をはんだの山だけでつないだりすると、細い部分に電流が集中して発熱します。</p>
  <div class="panel">{SVG3}</div>

  <h2>4. 基板の材質</h2>
  <p class="note">基板を買うときは、ガラスエポキシを選んでください。熱に強いので、はんだごてを何度当ててもランドが剥がれにくく、BTSの発熱にも耐えます。</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th>材質</th><th>見た目</th><th>熱への強さ</th><th>今回</th></tr></thead>
    <tbody>
      <tr><td><span class="sw" style="background:var(--epoxy);border:1px solid var(--epoxy-line)"></span>ガラスエポキシ</td><td>緑・黄色、硬い</td><td>強い。ランドが剥がれにくい</td><td>こちらを使う</td></tr>
      <tr><td><span class="sw" style="background:var(--phenol);border:1px solid var(--phenol-line)"></span>紙フェノール</td><td>茶色、やや柔らかい</td><td>弱い。何度も加熱するとランドが浮く</td><td>避ける</td></tr>
    </tbody>
  </table></div>

  <div class="warn"><b>Vbb・OUTの線をブレッドボードに通さないでください。</b>ブレッドボードの接点は1A程度までの想定で、ウィンカー1灯(約1.75A)でも発熱します。</div>
</div>
"""

html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>ユニバーサル基板の電流経路</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
