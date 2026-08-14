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
SPEC = [
 ("flowchart","順序と分岐","graph","flowchart"), ("state","状態と遷移","graph","statediagram"),
 ("class","型と関連","graph","classDiagram"), ("er","実体と関連","graph","erDiagram"),
 ("architecture","区画と部品","graph","architecture"),
 ("requirement","要求と充足","graph","requirementDiagram"),
 ("mindmap","概念の展開","graph","mindmap"),
 ("sequence","やり取りの順序","chart","sequence"), ("gantt","作業と日程","chart","gantt"),
 ("timeline","時間順の出来事","chart","timeline"), ("journey","体験の段階","chart","journey"),
 ("gitGraph","枝分かれと合流","chart","gitGraph"), ("pie","比率","chart","pie"),
 ("xychart","大小","chart","xychart-beta"), ("sankey","流れの量","chart","sankey-beta"),
 ("quadrant","2軸での位置づけ","chart","quadrantChart"), ("block","箱組み","chart","block-beta"),
]

def tree_to_graph(root):
    nodes, edges = [], []
    def walk(n):
        nodes.append({"id": n["name"], "name": n["name"], "role": n.get("role","plain")})
        for c in n.get("children") or []:
            edges.append({"from": n["name"], "to": c["name"]}); walk(c)
    walk(root); return {"kind":"graph","nodes":nodes,"edges":edges}

cards, fails = [], []
for name, what, fam, key in SPEC:
    try:
        if fam == "graph":
            fig = BY[name]
            mine = render_svg(tree_to_graph(fig["root"]) if fig["kind"] == "tree" else fig)
        else:
            mine = render_chart(DATA[name])
    except Exception as exc:
        mine = f'<p class="fail">描けなかった: {exc}</p>'; fails.append(name)
    cards.append(
        f'<section class="card"><header><h2>{name}</h2>'
        f'<span class="fam fam--{fam}">{"点と線" if fam == "graph" else "図表"}</span>'
        f'<span class="what">{what}</span></header><div class="pair">'
        f'<div class="half"><span class="tag">Mermaid</span><div class="stage">'
        f'<pre class="mermaid">{e(MMD[key])}</pre></div></div>'
        f'<div class="half"><span class="tag mine">Waffle</span>'
        f'<div class="stage">{mine}</div></div></div></section>')
pathlib.Path("artifact17_body.html").write_text(
    "".join(cards), encoding="utf-8")
pathlib.Path("artifact17_css.txt").write_text(CSS + GCSS + CCSS, encoding="utf-8")
print("組んだ", len(cards), "種 / 失敗:", fails or "なし")