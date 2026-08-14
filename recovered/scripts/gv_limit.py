"""できないと思っているところを、実際に当てて確かめる。"""
import pathlib
import pygraphviz as pgv

OUT = pathlib.Path(__file__).parent / "probe"
F = "Noto Sans JP"


def new(prog="dot", **kw):
    g = pgv.AGraph(directed=True, fontname=F, bgcolor="white", **kw)
    g.node_attr.update(shape="box", style="rounded,filled", fillcolor="#F5F7F9",
                       color="#C3CAD2", fontname=F, fontsize="12", fontcolor="#171B23")
    g.edge_attr.update(color="#79828F", fontname=F, fontsize="10", fontcolor="#4B5563")
    g._prog = prog
    return g


def save(g, name):
    g.layout(prog=getattr(g, "_prog", "dot"))
    g.draw(str(OUT / f"{name}.svg"), format="svg")
    print(f"  {name}")


# C2: ポート — 正しいAPI（tailport）で当て直す
c = new(rankdir="LR")
c.add_node("rec", shape="record", style="filled", fillcolor="white", color="#C3CAD2",
           label="Document|<f0>documentId|<f1>content|<f2>status")
c.add_node("sub", label="値オブジェクト")
c.add_node("enum", label="DRAFT / VALIDATED")
c.add_edge("rec", "sub", tailport="f1")
c.add_edge("rec", "enum", tailport="f2")
save(c, "c2-port")

# H: 長い文を渡したとき、折り返してくれるか
h = new()
h.add_node("plain", label="宣言された置き場所を正本とし、実装側の決め打ちを消す。これは長い一文である")
h.add_node("br", label="宣言された置き場所を正本とし、\n実装側の決め打ちを消す。\nこれは改行を自分で入れた場合")
h.add_edge("plain", "br")
save(h, "h-wrap")

# I: 1つの箱を2つの囲みに入れられるか（重なる集合が作れるか）
i = new()
a = i.add_subgraph(name="cluster_a", label="集合A", style="dashed", color="#9A4A21",
                   fontcolor="#9A4A21", fontsize="10", fontname=F)
a.add_node("共有")
a.add_node("Aだけ")
b = i.add_subgraph(name="cluster_b", label="集合B", style="dashed", color="#16636B",
                   fontcolor="#16636B", fontsize="10", fontname=F)
b.add_node("共有")
b.add_node("Bだけ")
save(i, "i-overlap")

# J: 座標を自分で決めて、そのまま置かせられるか
j = new(prog="neato")
j.graph_attr.update(splines="true")
for name, pos in {"左上": "0,2!", "右上": "3,2!", "中央": "1.5,1!", "左下": "0,0!", "右下": "3,0!"}.items():
    j.add_node(name, pos=pos)
j.add_edge("左上", "中央"); j.add_edge("右上", "中央")
j.add_edge("中央", "左下"); j.add_edge("中央", "右下")
save(j, "j-fixed-pos")

# K: 大きなグラフを、紙に収まる形へ畳めるか
k = new()
k.graph_attr.update(ratio="compress", size="7,4!", ranksep="0.35", nodesep="0.2")
for n in range(1, 25):
    k.add_edge(f"層{n // 6 + 1}", f"要素{n:02}")
save(k, "k-scale-compressed")