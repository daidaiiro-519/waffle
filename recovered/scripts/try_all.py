import json, pathlib, sys
sys.path.insert(0, ".")
from build import FIGS
from chart_data import DATA
from svg_graph import render_svg, CSS as GCSS
from svg_chart import render_chart, CSS as CCSS
from styles import CSS
from html import escape as e

MMD = json.loads((pathlib.Path("..") / "all_mermaid_themed.json").read_text(encoding="utf-8"))
BY = {n: d for n, _w, _o, d in FIGS}
GRAPH = {"flowchart":"flowchart","state":"statediagram","class":"classDiagram",
         "er":"erDiagram","architecture":"architecture","requirement":"requirementDiagram",
         "mindmap":"mindmap"}
CHART = {"sequence":"sequence","gantt":"gantt","timeline":"timeline","journey":"journey",
         "gitGraph":"gitGraph","pie":"pie","xychart":"xychart-beta","sankey":"sankey-beta",
         "quadrant":"quadrantChart","block":"block-beta"}

def tree_to_graph(root):
    nodes, edges = [], []
    def walk(n):
        nodes.append({"id": n["name"], "name": n["name"], "role": n.get("role", "plain")})
        for c in n.get("children") or []:
            edges.append({"from": n["name"], "to": c["name"]}); walk(c)
    walk(root); return {"kind":"graph","nodes":nodes,"edges":edges}

rows, fails = [], []
for name in list(GRAPH) + list(CHART):
    try:
        if name in GRAPH:
            fig = BY[name]
            mine = render_svg(tree_to_graph(fig["root"]) if fig["kind"] == "tree" else fig)
        else:
            mine = render_chart(DATA[name])
    except Exception as exc:
        mine = f'<p style="color:var(--warn)">描けなかった: {exc}</p>'; fails.append(f"{name}: {exc}")
    key = GRAPH.get(name) or CHART[name]
    rows.append(f'<section class="row"><h2>{name}</h2><div class="pair">'
                f'<div class="half"><span class="tag">Mermaid</span><div class="stage">'
                f'<pre class="mermaid">{e(MMD[key])}</pre></div></div>'
                f'<div class="half"><span class="tag mine">Waffle</span>'
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
pathlib.Path("../shot/all17.html").write_text(
    '<!doctype html><meta charset="utf-8"><title>17種</title>'
    f'<style>{CSS}{GCSS}{CCSS}{PAGE}</style><main>{"".join(rows)}</main>'
    '<script type="module" src="./compare.js"></script>', encoding="utf-8")
print("組んだ", len(rows), "組 / 失敗:", fails or "なし")