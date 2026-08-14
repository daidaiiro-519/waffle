"""クラス図を、区画つきの表として組み直す。前回は空の区画に区切り線を入れて弾かれた。"""
import pathlib, re, sys
import pygraphviz as pgv

def compartment(title, rows):
    body = "".join(f'<TR><TD ALIGN="LEFT">{r}</TD></TR>' for r in rows) if rows else ""
    sep = "<HR/>" + body if rows else ""
    return (f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6">'
            f'<TR><TD ALIGN="CENTER"><B>{title}</B></TD></TR>{sep}</TABLE>>')

g = pgv.AGraph(directed=True, rankdir="BT", bgcolor="transparent")
g.graph_attr.update(ranksep="0.7")
g.node_attr.update(shape="box", style="rounded", fontname="Noto Sans JP", fontsize="11")
g.edge_attr.update(fontname="Noto Sans JP", fontsize="9")

g.add_node("Document", label=compartment("Document", ["+ documentId", "+ status", "+ validate()"]))
g.add_node("Block", label=compartment("Block", ["+ blockType"]))
g.add_node("Schema", label=compartment("Schema", ["+ schemaRef", "+ version"]))
g.add_edge("Block", "Document", arrowhead="diamond", taillabel=" 多 ", headlabel=" 1 ")
g.add_edge("Document", "Schema", arrowhead="vee", style="dashed", label=" 従う ")

g.layout(prog="dot")
svg = re.sub(r'(width|height)="([\d.]+)pt"', r'\1="\2"', g.draw(format="svg").decode())
CSS = ('.node path,.node polygon{fill:#F5F7F9;stroke:#C3CAD2}'
       '.node text{fill:#171B23}.edge path{stroke:#79828F}'
       '.edge polygon{fill:#79828F;stroke:#79828F}.edge text{fill:#4B5563}')
i = svg.index(">", svg.index("<svg")) + 1
pathlib.Path(sys.argv[1]).write_text(svg[:i] + "<style>" + CSS + "</style>" + svg[i:], encoding="utf-8")
print("組み直した", len(svg), "bytes")