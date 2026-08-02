"""completion_image_layout の単体テスト（純粋関数、境界値・複数パターンのレイアウト計算）。"""
from waffle.domain.services.completion_image_layout import MARGIN_LEFT, compute_layout


def test_single_node_layer_is_horizontally_centered():
    """
    Given 1層・1ノードのlayers
    When compute_layoutを呼ぶ
    Then そのノードは左マージン（層ラベル用）を除いたノード領域の水平中央に配置される
    """
    layers = [{"label": "コア", "nodes": [{"id": "a", "title": "A", "sub": "a", "status": "existing"}]}]
    result = compute_layout(layers, [])
    node = result["nodes"][0]
    assert node["x"] + node["width"] / 2 == (MARGIN_LEFT + result["viewbox_width"]) / 2


def test_one_to_many_layer_has_containment_arrows_to_all_children():
    """
    Given 1ノードの層の直後に2ノードの層があるlayers
    When compute_layoutを呼ぶ
    Then 親ノードから子ノード両方への包含矢印が生成される
    """
    layers = [
        {"label": "上", "nodes": [{"id": "p", "title": "P", "sub": "", "status": "existing"}]},
        {"label": "下", "nodes": [
            {"id": "c1", "title": "C1", "sub": "", "status": "existing"},
            {"id": "c2", "title": "C2", "sub": "", "status": "new"},
        ]},
    ]
    result = compute_layout(layers, [])
    pairs = {(a["from_id"], a["to_id"]) for a in result["containment_arrows"]}
    assert pairs == {("p", "c1"), ("p", "c2")}


def test_equal_sized_layers_connect_one_to_one():
    """
    Given 2ノードの層が2つ連続するlayers
    When compute_layoutを呼ぶ
    Then 同じ位置インデックスのノード同士が接続される
    """
    layers = [
        {"label": "上", "nodes": [
            {"id": "a1", "title": "A1", "sub": "", "status": "existing"},
            {"id": "a2", "title": "A2", "sub": "", "status": "existing"},
        ]},
        {"label": "下", "nodes": [
            {"id": "b1", "title": "B1", "sub": "", "status": "existing"},
            {"id": "b2", "title": "B2", "sub": "", "status": "new"},
        ]},
    ]
    result = compute_layout(layers, [])
    pairs = {(a["from_id"], a["to_id"]) for a in result["containment_arrows"]}
    assert pairs == {("a1", "b1"), ("a2", "b2")}


def test_layer_label_sits_at_vertical_center():
    """
    Given ラベル付きの2層のlayers
    When compute_layoutを呼ぶ
    Then layer_labelsに各層のlabelテキストとその層の垂直中央のy座標が含まれる
    """
    layers = [
        {"label": "呼出口", "nodes": [{"id": "a", "title": "A", "sub": "", "status": "existing"}]},
        {"label": "コア", "nodes": [{"id": "b", "title": "B", "sub": "", "status": "new"}]},
    ]
    result = compute_layout(layers, [])
    labels = {l["label"]: l["y"] for l in result["layer_labels"]}
    assert set(labels.keys()) == {"呼出口", "コア"}
    a_node = next(n for n in result["nodes"] if n["id"] == "a")
    assert labels["呼出口"] == a_node["y"] + a_node["height"] / 2


def test_nodes_in_same_layer_do_not_overlap():
    """
    Given 1層に3ノードを持つlayers
    When compute_layoutを呼ぶ
    Then 3ノードのx座標範囲は互いに重ならない
    """
    layers = [{"label": "コア", "nodes": [
        {"id": "a", "title": "A", "sub": "", "status": "existing"},
        {"id": "b", "title": "B", "sub": "", "status": "existing"},
        {"id": "c", "title": "C", "sub": "", "status": "new"},
    ]}]
    result = compute_layout(layers, [])
    nodes = sorted(result["nodes"], key=lambda n: n["x"])
    for prev, nxt in zip(nodes, nodes[1:]):
        assert prev["x"] + prev["width"] <= nxt["x"]


def test_relationships_reference_node_coordinates():
    """
    Given relationshipsで依存関係を1件宣言したlayers
    When compute_layoutを呼ぶ
    Then relationship_arrowsに対応するfrom_id/to_id/kind/labelが含まれる
    """
    layers = [{"label": "コア", "nodes": [
        {"id": "a", "title": "A", "sub": "", "status": "existing"},
        {"id": "b", "title": "B", "sub": "", "status": "new"},
    ]}]
    relationships = [{"from": "b", "to": "a", "kind": "dependency", "label": "再利用"}]
    result = compute_layout(layers, relationships)
    assert result["relationship_arrows"] == [
        {"from_id": "b", "to_id": "a", "kind": "dependency", "label": "再利用"}
    ]


def test_layers_are_stacked_vertically_with_spacing():
    """
    Given 3層のlayers
    When compute_layoutを呼ぶ
    Then 各層のy座標は層の順番通りに単調増加する
    """
    layers = [
        {"label": "1", "nodes": [{"id": "a", "title": "A", "sub": "", "status": "existing"}]},
        {"label": "2", "nodes": [{"id": "b", "title": "B", "sub": "", "status": "existing"}]},
        {"label": "3", "nodes": [{"id": "c", "title": "C", "sub": "", "status": "new"}]},
    ]
    result = compute_layout(layers, [])
    by_id = {n["id"]: n for n in result["nodes"]}
    assert by_id["a"]["y"] < by_id["b"]["y"] < by_id["c"]["y"]
