"""completion_image_layout — Handoffのcompletion Image（layers/relationships）から、
SVG描画に必要な座標を機械的に計算する純粋関数。uc-render-handoff-templateが使う
（tech-lead-advisorの助言により、座標計算はusecase自身ではなくdomain/servicesへ切り出す）。

layers間の包含矢印は、隣接層のノード数の組み合わせから機械的に決める:
- 片方が1ノードなら、そのノードから他方の全ノードへ（fan）
- 両方が同数なら、位置インデックスが同じノード同士（1対1）
- それ以外は全対全（フォールバック）
"""
from __future__ import annotations

VIEWBOX_WIDTH = 700
MARGIN_LEFT = 96  # 層ラベル（呼出口・コア等）を描画する左マージン。折り返し表示前提の幅。
NODE_AREA_WIDTH = VIEWBOX_WIDTH - MARGIN_LEFT
NODE_HEIGHT = 50
NODE_GAP = 20
LAYER_GAP = 64
MARGIN_TOP = 10


def _layer_containment_pairs(prev_nodes: list[dict], next_nodes: list[dict]) -> list[tuple[str, str]]:
    prev_ids = [n["id"] for n in prev_nodes]
    next_ids = [n["id"] for n in next_nodes]
    if len(prev_ids) == 1:
        return [(prev_ids[0], nid) for nid in next_ids]
    if len(next_ids) == 1:
        return [(pid, next_ids[0]) for pid in prev_ids]
    if len(prev_ids) == len(next_ids):
        return list(zip(prev_ids, next_ids))
    return [(pid, nid) for pid in prev_ids for nid in next_ids]


def compute_layout(layers: list[dict], relationships: list[dict]) -> dict:
    """layers/relationshipsから、ノードのx/y/width/height・包含矢印・関係矢印を計算する。"""
    nodes: list[dict] = []
    layer_node_lists: list[list[dict]] = []
    layer_labels: list[dict] = []

    for layer_index, layer in enumerate(layers):
        layer_nodes = layer["nodes"]
        layer_node_lists.append(layer_nodes)
        y = MARGIN_TOP + layer_index * (NODE_HEIGHT + LAYER_GAP)
        layer_labels.append({"label": layer["label"], "y": y + NODE_HEIGHT / 2})
        count = len(layer_nodes)
        total_gap = NODE_GAP * (count - 1) if count > 1 else 0
        width = (NODE_AREA_WIDTH - total_gap) / count
        for node_index, node in enumerate(layer_nodes):
            x = MARGIN_LEFT + node_index * (width + NODE_GAP)
            nodes.append({
                "id": node["id"],
                "title": node["title"],
                "sub": node["sub"],
                "status": node["status"],
                "x": x,
                "y": y,
                "width": width,
                "height": NODE_HEIGHT,
            })

    containment_arrows = []
    for prev_nodes, next_nodes in zip(layer_node_lists, layer_node_lists[1:]):
        for from_id, to_id in _layer_containment_pairs(prev_nodes, next_nodes):
            containment_arrows.append({"from_id": from_id, "to_id": to_id})

    relationship_arrows = [
        {"from_id": rel["from"], "to_id": rel["to"], "kind": rel["kind"], "label": rel["label"]}
        for rel in relationships
    ]

    viewbox_height = MARGIN_TOP + len(layers) * NODE_HEIGHT + max(0, len(layers) - 1) * LAYER_GAP + MARGIN_TOP

    return {
        "nodes": nodes,
        "containment_arrows": containment_arrows,
        "relationship_arrows": relationship_arrows,
        "layer_labels": layer_labels,
        "viewbox_width": VIEWBOX_WIDTH,
        "viewbox_height": viewbox_height,
    }
