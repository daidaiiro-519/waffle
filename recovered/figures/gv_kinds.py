"""Mermaidの代表的な図を、Graphvizで作れるか試す。"""
import pathlib, re, sys
import pygraphviz as pgv

OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(exist_ok=True)
F = "Noto Sans JP"
CSS = """
  .node path, .node polygon, .node ellipse { fill:#F5F7F9; stroke:#C3CAD2; }
  .node text { fill:#171B23; }
  .edge path { stroke:#79828F; } .edge polygon { fill:#79828F; stroke:#79828F; }
  .edge text { fill:#4B5563; }
  .cluster polygon { fill:#FFFFFF; stroke:#16636B; stroke-dasharray:5 4; }
  .cluster text { fill:#16636B; }
"""

def save(g, name, prog="dot"):
    g.layout(prog=prog)
    svg = g.draw(format="svg").decode("utf-8")
    svg = re.sub(r'(width|height)="([\d.]+)pt"', r'\1="\2"', svg)
    i = svg.index(">", svg.index("<svg")) + 1
    (OUT / f"{name}.svg").write_text(svg[:i] + "<style>" + CSS + "</style>" + svg[i:], encoding="utf-8")
    print(" ", name)

def base(**kw):
    g = pgv.AGraph(directed=True, bgcolor="transparent", **kw)
    g.node_attr.update(shape="box", style="rounded", fontname=F, fontsize="11", margin="0.2,0.12")
    g.edge_attr.update(fontname=F, fontsize="9")
    return g

# 1. クラス図の代わり ── 区画つきの箱
g = base(rankdir="BT")
g.node_attr.update(shape="plaintext", style="")
def cls(title, fields, ops):
    rows = "".join(f'<TR><TD ALIGN="LEFT">{f}</TD></TR>' for f in fields)
    ops_ = "".join(f'<TR><TD ALIGN="LEFT">{o}</TD></TR>' for o in ops)
    return (f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5" STYLE="ROUNDED">'
            f'<TR><TD ALIGN="CENTER"><B>{title}</B></TD></TR><HR/>{rows}<HR/>{ops_}</TABLE>>')
g.add_node("Document", label=cls("Document", ["+documentId", "+status"], ["+validate()"]))
g.add_node("Block", label=cls("Block", ["+blockType"], []))
g.add_edge("Block", "Document", arrowhead="diamond", label="  多対1")
save(g, "1-class")

# 2. 状態遷移 ── 開始と終了の印つき
g = base(rankdir="LR")
g.add_node("start", shape="circle", style="filled", fillcolor="#171B23", label="", width="0.16", height="0.16")
g.add_node("end", shape="doublecircle", label="", width="0.16", height="0.16")
for a, b, l in [("start","DRAFT","骨格を作る"), ("DRAFT","VALIDATED","整合を確かめる"),
                ("VALIDATED","ACTIVE","確定する"), ("ACTIVE","end","使うのをやめる")]:
    g.add_edge(a, b, label=f"  {l}  ")
g.add_edge("VALIDATED", "DRAFT", label="  不備  ", constraint="false", style="dashed")
save(g, "2-state")

# 3. 概念の木
g = base(rankdir="LR")
for a, b in [("区切られた文脈","業務領域"), ("業務領域","中核"), ("業務領域","一般"), ("業務領域","補完"),
             ("区切られた文脈","同じ言葉"), ("区切られた文脈","集約")]:
    g.add_edge(a, b, arrowhead="none")
save(g, "3-tree")

# 4. 実体関連 ── 多重度つき
g = base(rankdir="LR")
g.add_edge("DOCUMENT", "BLOCK", arrowhead="none", taillabel=" 1 ", headlabel=" 多 ", label="持つ")
g.add_edge("DOCUMENT", "SCHEMA", arrowhead="none", taillabel=" 多 ", headlabel=" 1 ", label="従う")
save(g, "4-er")

# 5. 2軸の位置づけ ── 座標を自分で決める
g = pgv.AGraph(bgcolor="transparent")
g.node_attr.update(shape="box", style="rounded", fontname=F, fontsize="10")
for n, pos in {"文書の検証":"3.0,2.6!", "描画":"1.6,1.7!", "設定の読み込み":"0.5,0.5!",
               "中核":"3.4,3.0!", "補完":"0.3,0.2!"}.items():
    g.add_node(n, pos=pos)
save(g, "5-quadrant", prog="neato")