# -*- coding: utf-8 -*-
# 「故障(ショート)とは何か」を正常・完全ショート・中途半端なショートの3枚で示す簡素な図(ライトモード専用)
import io, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fault-current.html")
src = io.open(os.path.join(HERE, "gen_simple_one_lamp.py"), encoding="utf-8").read()
CSS = re.search(r"<style>(.*?)</style>", src, re.S).group(1).replace("{{", "{").replace("}}", "}")
CSS += """
.grid3 svg{min-width:0}
.grid3 h2{margin:4px 0 8px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.flow{fill:none;stroke-width:6;stroke-linecap:round;opacity:.85}
.ok{stroke:#2f9e44}.big{stroke:#c92a2a}.mid{stroke:#e67700}
.short{fill:none;stroke:#c92a2a;stroke-width:3;stroke-dasharray:5 4}
.res{font-size:15px;font-weight:700}
.okt{fill:#2f9e44}.bigt{fill:#c92a2a}.midt{fill:#e67700}
"""

def panel(kind):
    # 共通の回路: バッテリー+ → 15A → ランプ → GND
    s = ['<svg viewBox="0 0 300 260" role="img">']
    s.append('<rect x="14" y="30" width="70" height="40" rx="6" class="box"/>'
             '<text x="49" y="55" class="lbl" text-anchor="middle">バッテリー+</text>')
    s.append('<rect x="120" y="36" width="40" height="28" rx="5" class="part"/>'
             '<text x="140" y="55" class="lbl" text-anchor="middle">15A</text>')
    s.append('<path d="M84 50 H120 M160 50 H240 V100" class="w pw"/>')
    s.append('<circle cx="240" cy="130" r="26" class="lamp"/>'
             '<path d="M222 112 L258 148 M258 112 L222 148" class="w lampx"/>'
             '<text x="240" y="86" class="lbl" text-anchor="middle"></text>')
    s.append('<path d="M240 156 V210 M60 210 H240" class="w gndw"/>')
    s.append('<path d="M46 210 H74 M51 215 H69 M56 220 H64" class="w gndw"/>'
             '<text x="60" y="238" class="lbl" text-anchor="middle">車体(−)</text>')
    if kind == "ok":
        s.append('<path d="M166 50 H240 V210 H80" class="flow ok"/>')
        s.append('<text x="150" y="130" class="res okt" text-anchor="middle">約5A</text>'
                 '<text x="150" y="150" class="lbl" text-anchor="middle">ランプを通る</text>')
    else:
        cls = "big" if kind == "big" else "mid"
        s.append(f'<path d="M166 50 H200 V210 H80" class="flow {cls}"/>')
        if kind == "big":
            s.append('<path d="M200 50 V210" class="short" style="stroke-dasharray:none"/>')
            s.append('<text x="120" y="120" class="res bigt" text-anchor="middle">数十A</text>'
                     '<text x="120" y="140" class="lbl" text-anchor="middle">近道でベタ触れ</text>')
        else:
            s.append('<path d="M200 50 V120 M200 140 V210" class="short"/>'
                     '<rect x="190" y="120" width="20" height="20" rx="3" class="part"/>')
            s.append('<text x="120" y="120" class="res midt" text-anchor="middle">10〜15A</text>'
                     '<text x="120" y="140" class="lbl" text-anchor="middle">浅い接触で近道</text>')
    s.append('</svg>')
    return "\n".join(s)

CARDS = [
    ("ok", "正常", "電気はランプを通る。ランプが流れを抑えるので約5A。", "ヒューズは切れない(正しい)"),
    ("big", "完全なショート", "+と−がしっかり触れ、ランプを通らない近道ができる。抑えがなく数十A流れる。", "15Aでもすぐ切れる(安全)"),
    ("mid", "中途半端なショート", "接触が浅く、近道に抵抗が残る。電流は10〜15Aで止まる。", "純正10Aなら切れるが、15Aは切れず流れ続ける(要注意)"),
]
cards = "".join(
    f'<div class="card"><h2>{t}</h2>{panel(k)}<p>{d}</p><p><b class="{k}t">{r}</b></p></div>'
    for k, t, d, r in CARDS)

html = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ショートと電流</title>
<style>{CSS}
.okt{{color:#2f9e44}}.bigt{{color:#c92a2a}}.midt{{color:#e67700}}</style></head><body><main>
<h1>故障(ショート)と電流のイメージ</h1>
<p>故障とは、電気がランプを通らずに近道をして車体(−)へ流れる状態です。太い線が電流の通り道です。</p>
<div class="grid3">{cards}</div>
<p>今回の実験で近道ができやすいのは、ワニ口クリップの+と−が触れる、+の線の被覆が擦れて車体に触れる、の2つです。中途半端なショートが気になる場合は、M+とM−に10Aを1つずつ足すと純正と同じ守り方になります。</p>
</main></body></html>'''
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT)
