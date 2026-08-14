"""点と線の図を、Graphvizの座標から自前のSVGへ組み立てる。

Graphvizからは座標だけを受け取る。SVGの組み立てとクラス名は、こちら側が決める。
Graphviz が付けた class も、その語彙も、一切外へ出さない。
"""
from __future__ import annotations

import re
from html import escape as e

import pygraphviz as pgv

PT = 1.0          # Graphvizはポイントで返す。そのまま viewBox の単位に使う


def _solve(fig):
    """配置を解く。返すのは座標だけで、描画には触れない。"""
    g = pgv.AGraph(directed=True, rankdir=fig.get("direction", "TB"),
                   compound=True, splines="spline", nodesep="0.35", ranksep="0.55")
    g.node_attr.update(shape="box", fontname="Noto Sans JP", fontsize="12",
                       margin="0.16,0.09", height="0.35")
    g.edge_attr.update(fontname="Noto Sans JP", fontsize="10")

    in_group = {}
    for i, grp in enumerate(fig.get("groups", [])):
        sub = g.add_subgraph(name=f"cluster_{i}", label=grp.get("label", ""),
                             fontname="Noto Sans JP", fontsize="10", margin="12")
        for m in grp["members"]:
            in_group[m] = i
        for m in grp["members"]:
            sub.add_node(m, label=next(n["name"] for n in fig["nodes"] if n["id"] == m))
    for n in fig["nodes"]:
        if n["id"] not in in_group:
            g.add_node(n["id"], label=n["name"])
    for x in fig.get("edges", []):
        g.add_edge(x["from"], x["to"], label=f'  {x["label"]}  ' if x.get("label") else "")

    g.layout(prog="dot")

    nodes = {}
    for n in g.nodes():
        cx, cy = (float(v) for v in n.attr["pos"].split(","))
        w, h = float(n.attr["width"]) * 72, float(n.attr["height"]) * 72
        nodes[str(n)] = {"cx": cx, "cy": cy, "w": w, "h": h}

    edges = []
    for ed in g.edges():
        pos = ed.attr["pos"] or ""
        arrow = None
        pts = []
        for tok in pos.split():
            if tok.startswith("e,"):
                arrow = tuple(float(v) for v in tok[2:].split(","))
            elif tok.startswith("s,"):
                continue
            else:
                pts.append(tuple(float(v) for v in tok.split(",")))
        lp = ed.attr["lp"]
        edges.append({"from": str(ed[0]), "to": str(ed[1]), "pts": pts, "arrow": arrow,
                      "label": (ed.attr["label"] or "").strip(),
                      "lp": tuple(float(v) for v in lp.split(",")) if lp else None})

    boxes = []
    for i, grp in enumerate(fig.get("groups", [])):
        sub = g.get_subgraph(f"cluster_{i}")
        bb = sub.graph_attr["bb"] if sub is not None else None
        if bb:
            x0, y0, x1, y1 = (float(v) for v in bb.split(","))
            boxes.append({"label": grp.get("label", ""), "x0": x0, "y0": y0, "x1": x1, "y1": y1})

    _, _, W, H = (float(v) for v in g.graph_attr["bb"].split(","))
    return {"nodes": nodes, "edges": edges, "groups": boxes, "w": W, "h": H}


def _path(pts):
    """3次ベジエの制御点の並びを、そのまま経路にする。"""
    if len(pts) < 2:
        return ""
    d = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    i = 1
    while i + 2 < len(pts) + 1 and i + 2 <= len(pts):
        a, b, c = pts[i], pts[i + 1] if i + 1 < len(pts) else pts[-1], pts[i + 2] if i + 2 < len(pts) else pts[-1]
        d.append(f"C{a[0]:.1f},{a[1]:.1f} {b[0]:.1f},{b[1]:.1f} {c[0]:.1f},{c[1]:.1f}")
        i += 3
    if i < len(pts):
        d.append(f"L{pts[-1][0]:.1f},{pts[-1][1]:.1f}")
    return " ".join(d)


def render_svg(fig):
    """座標から、こちらの語彙のSVGを組み立てる。"""
    L = _solve(fig)
    role = {n["id"]: n.get("role", "plain") for n in fig["nodes"]}
    name = {n["id"]: n["name"] for n in fig["nodes"]}
    H = L["h"]
    fy = lambda y: H - y                                          # noqa: E731  上下を反転する

    out = [
        '<defs><marker id="wf-head" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path class="wf-arrow" d="M0,0 L10,5 L0,10 z"/></marker></defs>']

    for b in L["groups"]:
        out.append(f'<rect class="wf-group" x="{b["x0"]:.1f}" y="{fy(b["y1"]):.1f}" '
                   f'width="{b["x1"] - b["x0"]:.1f}" height="{b["y1"] - b["y0"]:.1f}" rx="8"/>')
        out.append(f'<text class="wf-group-label" x="{b["x0"] + 10:.1f}" '
                   f'y="{fy(b["y1"]) + 13:.1f}">{e(b["label"])}</text>')

    for ed in L["edges"]:
        pts = [(x, fy(y)) for x, y in ed["pts"]]
        if ed["arrow"]:
            pts.append((ed["arrow"][0], fy(ed["arrow"][1])))
        out.append(f'<path class="wf-edge" d="{_path(pts)}" marker-end="url(#wf-head)"/>')
        if ed["label"] and ed["lp"]:
            out.append(f'<text class="wf-edge-label" x="{ed["lp"][0]:.1f}" '
                       f'y="{fy(ed["lp"][1]) + 3:.1f}">{e(ed["label"])}</text>')

    for nid, p in L["nodes"].items():
        x, y = p["cx"] - p["w"] / 2, fy(p["cy"]) - p["h"] / 2
        out.append(f'<g class="wf-node wf-node--{role.get(nid, "plain")}">'
                   f'<rect x="{x:.1f}" y="{y:.1f}" width="{p["w"]:.1f}" height="{p["h"]:.1f}" rx="5"/>'
                   f'<text x="{p["cx"]:.1f}" y="{fy(p["cy"]) + 4:.1f}">{e(name.get(nid, nid))}</text></g>')

    return (f'<svg class="wf-fig" viewBox="0 0 {L["w"]:.0f} {L["h"]:.0f}" '
            f'role="img">{"".join(out)}</svg>')


CSS = """
  .wf-fig{display:block;width:100%;height:auto;overflow:visible}
  .wf-node rect{fill:var(--surface-2);stroke:var(--rule);stroke-width:1}
  .wf-node text{fill:var(--ink);font-family:var(--sans);font-size:12px;text-anchor:middle}
  .wf-node--focus rect{fill:var(--acc-bg);stroke:var(--acc);stroke-width:1.4}
  .wf-node--focus text{fill:var(--acc);font-weight:600}
  .wf-edge{fill:none;stroke:var(--rule);stroke-width:1.2}
  .wf-arrow{fill:var(--rule)}
  .wf-edge-label{fill:var(--ink-faint);font-family:var(--sans);font-size:10px;text-anchor:middle}
  .wf-group{fill:none;stroke:var(--acc);stroke-width:1.1;stroke-dasharray:5 4;opacity:.75}
  .wf-group-label{fill:var(--acc);font-family:var(--sans);font-size:10px}
"""
