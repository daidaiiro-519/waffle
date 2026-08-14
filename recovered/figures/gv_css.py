"""GraphvizのSVGへ、こちらのCSSを当てられるか試す。

見た目はCSSが持ち、Graphvizは配置だけを担う、という分け方が成り立つかを見る。
"""
import pathlib, re, sys
import pygraphviz as pgv

g = pgv.AGraph(directed=True, rankdir="LR", bgcolor="transparent")
g.graph_attr.update(nodesep="0.45", ranksep="0.75")
# 形だけGraphvizに任せ、色や書体は一切指定しない
g.node_attr.update(shape="box", style="rounded,filled", penwidth="1",
                   fontname="Noto Sans JP", fontsize="12", margin="0.22,0.14")
g.edge_attr.update(fontname="Noto Sans JP", fontsize="10", penwidth="1")

for a, b in [("調べる", "決める"), ("決める", "引き継ぐ"), ("引き継ぐ", "作る")]:
    g.add_edge(a, b)
g.add_edge("作る", "調べる", label="反証が出たら", style="dashed", constraint="false")
for n in g.nodes():
    n.attr["class"] = "box"
for e in g.edges():
    e.attr["class"] = "wire"

g.layout(prog="dot")
svg = g.draw(format="svg").decode("utf-8")

CSS = """
  .box path, .box polygon { fill: var(--surface-2, #F5F7F9); stroke: var(--rule, #C3CAD2); }
  .box text { fill: var(--ink, #171B23); }
  .box:first-of-type path { fill: var(--acc-bg, #E2EFF0); stroke: var(--acc, #16636B); }
  .wire path   { stroke: var(--line, #79828F); }
  .wire polygon{ fill: var(--line, #79828F); stroke: var(--line, #79828F); }
  .wire text   { fill: var(--ink-soft, #4B5563); }
"""
svg = re.sub(r'(width|height)="([\d.]+)pt"', r'\1="\2"', svg)
svg = svg.replace("</title>", "</title>\n<style>" + CSS + "</style>", 1) \
    if "</title>" in svg else svg.replace(">", "><style>" + CSS + "</style>", 1)
pathlib.Path(sys.argv[1]).write_text(svg, encoding="utf-8")
print("class を付けた要素:", len(re.findall(r'class="(box|wire)"', svg)), "個 /", len(svg), "bytes")