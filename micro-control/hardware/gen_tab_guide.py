#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""変換基板に付けたBTS6143Dの「タブ」と、12Vを入れる場所を写真に書き込んだ図を生成する。
出力: tab-guide.html(写真は img/bts-adapter-photo.jpg を埋め込む)
図の修正はHTMLを直接編集せず、このスクリプトを編集して再実行する。
写真上の座標は 600×600 に縮小した写真での位置。
"""
import base64, io, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tab-guide.html")
IMG = base64.b64encode(open(os.path.join(HERE, "img", "bts-adapter-photo.jpg"), "rb").read()).decode()
RED, ORG, GRN, PUR = "#d23b2e", "#e07a1c", "#2f8a4f", "#7a4bb0"


def t(x, y, s, size=15, col="#212723", w=700, anchor="start"):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'style="font-size:{size}px;font-weight:{w};fill:{col};paint-order:stroke;stroke:#fff;stroke-width:4px">{s}</text>')


S = [f'<image href="data:image/jpeg;base64,{IMG}" x="0" y="0" width="600" height="600"/>']
# タブ
S.append(f'<rect x="140" y="52" width="200" height="58" rx="6" fill="{RED}" fill-opacity=".18" stroke="{RED}" stroke-width="4"/>')
S.append(f'<path d="M340 80 H640" stroke="{RED}" stroke-width="2"/>')
S.append(t(650, 76, "タブ = 12V(Vbb)", 19, RED))
S.append(t(650, 100, "チップ裏の放熱板の端。はんだ付け済み", 14, "#5e6963", 500))
S.append(t(650, 120, "12Vはここから入る", 14, "#5e6963", 500))
# 真ん中の短い足
S.append(f'<circle cx="230" cy="326" r="18" fill="none" stroke="{ORG}" stroke-width="4"/>')
S.append(f'<path d="M248 326 H640" stroke="{ORG}" stroke-width="2"/>')
S.append(t(650, 322, "3番の足(短く切られている)", 17, ORG))
S.append(t(650, 344, "浮いていてよい。はんだ付けしない", 14, "#5e6963", 500))
# 下のピン番号
pins = [(70, "1", "OUT"), (150, "2", "IN"), (230, "3", "Vbb"), (310, "4", "IS"), (393, "5", "OUT")]
for x, n, nm in pins:
    S.append(f'<circle cx="{x}" cy="462" r="22" fill="none" stroke="#2f6fb2" stroke-width="3" stroke-dasharray="{"0" if n=="3" else "5 4"}"/>')
    S.append(t(x, 515, n, 17, "#2f6fb2", 700, "middle"))
    S.append(t(x, 535, nm, 13, "#2f6fb2", 700, "middle"))
# 導通チェック
S.append(f'<path d="M250 108 C330 200 330 380 245 448" stroke="{GRN}" stroke-width="3.5" fill="none" stroke-dasharray="8 6"/>')
S.append(f'<circle cx="250" cy="100" r="7" fill="{GRN}"/><circle cx="240" cy="452" r="7" fill="{GRN}"/>')
S.append(f'<path d="M318 260 H640" stroke="{GRN}" stroke-width="2"/>')
S.append(t(650, 236, "テスターでここ同士の導通を確認", 17, GRN))
S.append(t(650, 258, "タブの銀色の部分と、下の3番ピン", 14, "#5e6963", 500))
S.append(t(650, 278, "ピッと鳴れば3番ピンから12Vを入れてよい", 14, "#5e6963", 500))
# 12V線を直接付ける場合
S.append(f'<path d="M560 14 C470 14 360 30 318 66" stroke="{RED}" stroke-width="9" fill="none" stroke-linecap="round" stroke-opacity=".85"/>')
S.append(f'<circle cx="318" cy="68" r="8" fill="{RED}"/>')
S.append(t(650, 162, "鳴らなければ、12Vの線をここへ直接", 17, RED))
S.append(t(650, 184, "赤線のように、タブの銀色の部分に0.5sq線を", 14, "#5e6963", 500))
S.append(t(650, 204, "はんだ付けする(3番ピンは使わない)", 14, "#5e6963", 500))
SVG = f'<svg viewBox="0 0 1000 600" role="img" aria-label="変換基板に付けたBTS6143Dの写真に、タブ、短い3番の足、5本のピン、導通確認の位置、12Vの線を付ける位置を書き込んだ図">{"".join(S)}</svg>'

src_css = open(os.path.join(HERE, "gen_universal_board.py"), encoding="utf-8").read()
CSS = src_css[src_css.index('CSS = """') + 9: src_css.index('"""', src_css.index('CSS = """') + 9)]
CSS += "\n  .panel svg { min-width: 760px; }\n"

BODY = f"""
<div class="wrap">
  <p class="eyebrow">MICRO-CONTROL / BTS6143D TAB</p>
  <h1>タブの場所と12Vの入れ方</h1>
  <p class="lead">手元の変換基板の写真に、タブ(12Vの端子)、短い3番の足、下の5本のピンを書き込みました。12Vは足ではなくタブから入ります。</p>
  <div class="panel">{SVG}</div>
  <p class="note" style="margin-top:12px">手順は2段階です。最初に、テスターの導通モードで、タブの銀色の部分と下の3番ピンを当てます。鳴れば、基板配置図のとおり3番ピンから12Vを入れます。鳴らなければ、12Vの0.5sq線をタブに直接はんだ付けし、3番ピンには何もつなぎません。</p>
</div>
"""
html = ('<!doctype html>\n<html lang="ja">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>BTSのタブの場所</title>\n"
        "<style>" + CSS + "</style>\n<body>" + BODY + "</body></html>\n")
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, len(html), "bytes")
