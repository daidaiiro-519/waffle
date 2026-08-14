"""同じグラフを、解き方だけ変えて描く。"""
import pathlib, re, sys
import pygraphviz as pgv

OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(exist_ok=True)
CSS = ('.node path,.node polygon,.node ellipse{fill:#F5F7F9;stroke:#C3CAD2}'
       '.node text{fill:#171B23}.edge path{stroke:#79828F}'
       '.edge polygon{fill:#79828F;stroke:#79828F}')
EDGES = [("schema","document"),("document","renderer"),("renderer","viewer"),
         ("document","validator"),("validator","schema"),("renderer","schema")]

for prog, note in [("dot","層に分けて上下に積む"),("neato","引き合う力で釣り合わせる"),
                   ("circo","輪に並べる"),("twopi","中心から放射する")]:
    g = pgv.AGraph(directed=True, bgcolor="transparent", overlap="false", splines="true")
    g.node_attr.update(shape="box", style="rounded", fontname="Noto Sans JP", fontsize="11")
    for a, b in EDGES:
        g.add_edge(a, b)
    g.layout(prog=prog)
    svg = re.sub(r'(width|height)="([\d.]+)pt"', r'\1="\2"', g.draw(format="svg").decode())
    i = svg.index(">", svg.index("<svg")) + 1
    (OUT / f"{prog}.svg").write_text(svg[:i] + "<style>" + CSS + "</style>" + svg[i:], encoding="utf-8")
    print(f"  {prog:7} {note}")