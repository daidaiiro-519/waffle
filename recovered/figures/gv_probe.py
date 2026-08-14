"""Graphvizの表現の幅を、能力の軸ごとに実際に描いて測る。"""
import os
import pathlib
import pygraphviz as pgv

OUT = pathlib.Path(__file__).parent / "probe"
F = "Noto Sans JP"
INK, LINE, SURF, ACC, WARN = "#171B23", "#C3CAD2", "#F5F7F9", "#16636B", "#9A4A21"


def new(prog="dot", **kw):
    g = pgv.AGraph(directed=True, fontname=F, bgcolor="white", **kw)
    g.node_attr.update(shape="box", style="rounded,filled", fillcolor=SURF,
                       color=LINE, fontname=F, fontsize="12", fontcolor=INK)
    g.edge_attr.update(color="#79828F", fontname=F, fontsize="10", fontcolor="#4B5563")
    g._prog = prog
    return g


def save(g, name):
    g.layout(prog=getattr(g, "_prog", "dot"))
    g.draw(str(OUT / f"{name}.svg"), format="svg")
    print(f"  {name}")


# A: HTMLラベル — 箱の中に表を入れて、見出し帯と補足を持つ「カード」にできるか
a = new(rankdir="LR")
a.graph_attr.update(nodesep="0.5")
def card(title, sub, badge, color):
    return ('<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6">'
            f'<TR><TD BGCOLOR="{color}" ALIGN="LEFT"><FONT COLOR="white" POINT-SIZE="9">{badge}</FONT></TD></TR>'
            f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="13">{title}</FONT></TD></TR>'
            f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#79828F">{sub}</FONT></TD></TR>'
            '</TABLE>>')
for n, (t, s, b, c) in {
    "n1": ("業務ユースケース", "uc-render-document", "既存", "#79828F"),
    "n2": ("業務サービス", "要素の同一性を扱う", "新設", ACC),
    "n3": ("集約", "Document", "変更", WARN),
}.items():
    a.add_node(n, label=card(t, s, b, c), shape="box", style="rounded,filled",
               fillcolor="white", color=LINE)
a.add_edge("n1", "n2", label="呼ぶ")
a.add_edge("n2", "n3", label="更新する")
save(a, "a-html-card")

# B: クラスタの入れ子 — 変更後の中に問題空間と解決空間を入れられるか
b = new(compound="true")
b.graph_attr.update(newrank="true")
before = b.add_subgraph(name="cluster_before", label="変更前", style="dashed",
                        color=WARN, fontcolor=WARN, fontsize="10", fontname=F)
before.add_edge("BC", "SD")
after = b.add_subgraph(name="cluster_after", label="変更後", style="solid",
                       color=LINE, fontcolor="#79828F", fontsize="10", fontname=F)
p = after.add_subgraph(name="cluster_problem", label="問題空間", style="dashed",
                       color=ACC, fontcolor=ACC, fontsize="10", fontname=F)
p.add_edge("事業領域", "業務領域")
s = after.add_subgraph(name="cluster_solution", label="解決空間", style="dashed",
                       color=ACC, fontcolor=ACC, fontsize="10", fontname=F)
s.add_edge("区切られた文脈", "業務ユースケース")
b.add_edge("業務ユースケース", "業務領域", label="対応", style="dashed", color=ACC, constraint="false")
save(b, "b-nested-cluster")

# C: ポート — 箱の中の特定の行から線を出せるか
c = new(rankdir="LR")
c.add_node("rec", shape="record", style="filled", fillcolor="white",
           label="{Document|<f0> documentId|<f1> content|<f2> status}")
c.add_node("sub", label="値オブジェクト")
c.add_node("enum", label="DRAFT / VALIDATED")
c.add_edge("rec:f1", "sub")
c.add_edge("rec:f2", "enum")
save(c, "c-port")

# D: 横一列の強制と、順序の固定
d = new(rankdir="TB")
row = d.add_subgraph(rank="same")
for n in ("調べる", "決める", "引き継ぐ", "作る"):
    row.add_node(n)
for x, y in zip(("調べる", "決める", "引き継ぐ"), ("決める", "引き継ぐ", "作る")):
    d.add_edge(x, y)
d.add_edge("作る", "調べる", label="戻る", constraint="false", style="dashed", color=WARN)
save(d, "d-rank-same")

# E: 力学配置 — 階層でない、相互に参照し合う関係
e = new(prog="neato", overlap="false", splines="true")
pairs = [("schema", "document"), ("document", "renderer"), ("renderer", "schema"),
         ("document", "validator"), ("validator", "schema"), ("renderer", "viewer")]
for x, y in pairs:
    e.add_edge(x, y, dir="none")
save(e, "e-neato")

# F: 円環配置
f = new(prog="circo")
cycle = ["調査", "仕様", "引き継ぎ", "実装", "検証"]
for i, n in enumerate(cycle):
    f.add_edge(n, cycle[(i + 1) % len(cycle)])
save(f, "f-circo")

# G: 規模が増えたときの破綻
g = new(rankdir="TB")
g.graph_attr.update(ranksep="0.4", nodesep="0.25")
for i in range(1, 25):
    g.add_edge(f"層{i // 6 + 1}", f"要素{i:02}")
save(g, "g-scale")

print("描いた:", len(list(OUT.glob('*.svg'))), "枚")