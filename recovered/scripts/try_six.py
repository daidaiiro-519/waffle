import json, pathlib, sys
sys.path.insert(0, ".")
from build import FIGS
from svg_graph import render_svg, CSS as GCSS
from styles import CSS
from html import escape as e

MMD = json.loads((pathlib.Path("..") / "all_mermaid_themed.json").read_text(encoding="utf-8"))
PAIR = {"flowchart":"flowchart","state":"statediagram","class":"classDiagram",
        "er":"erDiagram","architecture":"architecture","requirement":"requirementDiagram",
        "mindmap":"mindmap"}
BY = {n: d for n, _w, _o, d in FIGS}

def tree_to_graph(root):
    nodes, edges = [], []
    def walk(n):
        nodes.append({"id": n["name"], "name": n["name"], "role": n.get("role", "plain")})
        for c in n.get("children") or []:
            edges.append({"from": n["name"], "to": c["name"]})
            walk(c)
    walk(root)
    return {"kind": "graph", "nodes": nodes, "edges": edges}

rows, fails = [], []
for name in PAIR:
    fig = BY[name]
    if fig["kind"] == "tree":
        fig = tree_to_graph(fig["root"])
    try:
        mine = render_svg(fig)
    except Exception as exc:
        mine = f'<p style="color:var(--warn)">描けなかった: {exc}</p>'
        fails.append(name)
    rows.append(
        f'<section class="row"><h2>{name}</h2><div class="pair">'
        f'<div class="half"><span class="tag">Mermaid</span><div class="stage">'
        f'<pre class="mermaid">{e(MMD[PAIR[name]])}</pre></div></div>'
        f'<div class="half"><span class="tag mine">Graphviz座標＋自前SVG</span>'
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
html = ('<!doctype html><meta charset="utf-8"><title>点と線の一族7種</title>'
        f'<style>{CSS}{GCSS}{PAGE}</style><main>{"".join(rows)}</main>'
        '<script type="module" src="./compare.js"></script>')
pathlib.Path("../shot/six.html").write_text(html, encoding="utf-8")
print("組んだ", len(rows), "組 / 失敗:", fails or "なし")