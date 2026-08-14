"""関門1の図を、そのままGraphvizへ渡してSVGにできるか試す。"""
import pygraphviz as pgv

g = pgv.AGraph(directed=True, rankdir="TB", compound=True, fontname="Noto Sans JP")
g.node_attr.update(shape="box", style="rounded,filled", fillcolor="#F5F7F9",
                   color="#C3CAD2", fontname="Noto Sans JP", fontsize="12")
g.edge_attr.update(color="#79828F", fontname="Noto Sans JP", fontsize="10")

before = g.add_subgraph(name="cluster_before", label="変更前",
                        style="dashed", color="#9A4A21", fontcolor="#9A4A21", fontsize="10")
before.add_edge("区切られた文脈", "業務領域 ")
before.add_edge("区切られた文脈", "集約 ")
before.add_edge("業務領域 ", "業務ユースケース ")

after_p = g.add_subgraph(name="cluster_problem", label="問題空間",
                         style="dashed", color="#16636B", fontcolor="#16636B", fontsize="10")
after_p.add_edge("事業領域", "業務領域")

after_s = g.add_subgraph(name="cluster_solution", label="解決空間",
                         style="dashed", color="#16636B", fontcolor="#16636B", fontsize="10")
after_s.add_edge("区切られた文脈 ", "業務ユースケース")
after_s.add_edge("区切られた文脈 ", "集約")

g.add_edge("業務ユースケース", "業務領域", label="対応", style="dashed", color="#16636B", constraint="false")

g.layout(prog="dot")
g.draw(f"{__import__('os').path.dirname(__file__)}/graphviz-gate1.svg", format="svg")
print("Graphviz が描いた")