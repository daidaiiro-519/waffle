import json, pathlib, sys
sys.path.insert(0, ".")
from chart_data import DATA
from svg_chart import render_chart, CSS as CCSS
from styles import CSS
from html import escape as e

MMD = json.loads((pathlib.Path("..") / "all_mermaid_themed.json").read_text(encoding="utf-8"))
PAIR = {"sequence":"sequence","gantt":"gantt","timeline":"timeline","journey":"journey",
        "gitGraph":"gitGraph","pie":"pie","xychart":"xychart-beta","sankey":"sankey-beta",
        "quadrant":"quadrantChart","block":"block-beta"}
rows, fails = [], []
for name, key in PAIR.items():
    try:
        mine = render_chart(DATA[name])
    except Exception as exc:
        mine = f'<p style="color:var(--warn)">描けなかった: {exc}</p>'; fails.append(f"{name}: {exc}")
    rows.append(f'<section class="row"><h2>{name}</h2><div class="pair">'
                f'<div class="half"><span class="tag">Mermaid</span><div class="stage">'
                f'<pre class="mermaid">{e(MMD[key])}</pre></div></div>'
                f'<div class="half"><span class="tag mine">自前SVG＋こちらのCSS</span>'
                f'<div class="stage">{mine}</div></div></div></section>')
PAGE = ("*{box-sizing:border-box}body{margin:0;padding:1rem;background:var(--paper);"
        "color:var(--ink);font-family:var(--sans)}"
        "h2{font-family:var(--mono);font-size:.85rem;margin:0 0 .6rem}"
        ".row{background:var(--surface);border:1px solid var(--rule);border-radius:10px;"
        "padding:.9rem;margin-bottom:1rem}"
        ".pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem;align-items:start}"
        ".half{display:flex;flex-direction:column;gap:.4rem;min-width:0}"
        ".tag{font-family:var(--mono);font-size:.6rem;color:var(--ink-faint)}"
        ".tag.mine{color:var(--acc)}"
        ".stage{background:var(--paper);border-radius:8px;padding:1rem;overflow:auto;"
        "min-height:5rem;display:flex;align-items:center;justify-content:center}"
        ".stage pre.mermaid{background:none;border:none;padding:0;margin:0}")
pathlib.Path("../shot/ten.html").write_text(
    '<!doctype html><meta charset="utf-8"><title>図表10種</title>'
    f'<style>{CSS}{CCSS}{PAGE}</style><main>{"".join(rows)}</main>'
    '<script type="module" src="./compare.js"></script>', encoding="utf-8")
print("組んだ", len(rows), "組 / 失敗:", fails or "なし")