"""層1 ── 配置の計算そのもの。SVGを1文字も作らずに座標と個数を確かめる。"""
from __future__ import annotations

import math

import pytest

from svg_engine.nesting import UnsupportedByStrategy, layout_nested
from svg_engine.radial import layout_radial
from svg_engine.sugiyama import layout_graph
from svg_engine.tree import layout_tree

SIZE = (80.0, 40.0)


def _sizes(*ids: str) -> dict[str, tuple[float, float]]:
    return {i: SIZE for i in ids}


def _no_overlap(boxes: dict[str, tuple[float, float]],
                sizes: dict[str, tuple[float, float]]) -> bool:
    ks = list(boxes)
    for i, a in enumerate(ks):
        ax, ay = boxes[a]
        aw, ah = sizes[a]
        for b in ks[i + 1:]:
            bx, by = boxes[b]
            bw, bh = sizes[b]
            if ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by:
                return False
    return True


class TestRank:
    def test_辺の向きに沿って段が下る(self):
        r = layout_graph(_sizes("a", "b", "c"), [("a", "b"), ("b", "c")], 40, 30)
        ys = [r.positions[k][1] for k in ("a", "b", "c")]
        assert ys[0] < ys[1] < ys[2]

    def test_横向きにすると段は横へ下る(self):
        r = layout_graph(_sizes("a", "b"), [("a", "b")], 40, 30, direction="LR")
        assert r.positions["a"][0] < r.positions["b"][0]
        assert r.positions["a"][1] == pytest.approx(r.positions["b"][1])


class TestCycle:
    def test_輪になっていても解けて節点が重ならない(self):
        sizes = _sizes("a", "b", "c")
        r = layout_graph(sizes, [("a", "b"), ("b", "c"), ("c", "a")], 40, 30)
        assert len(r.positions) == 3
        assert _no_overlap(r.positions, sizes)

    def test_自分へ戻る辺があっても解ける(self):
        r = layout_graph(_sizes("a"), [("a", "a")], 40, 30)
        assert "a" in r.positions


class TestMultiRankEdge:
    def test_段を飛ぶ辺は途中に折れ点を持つ(self):
        """仮節点を経由するから、2点の直線ではなくなる。"""
        r = layout_graph(_sizes("a", "b", "c"),
                         [("a", "b"), ("b", "c"), ("a", "c")], 40, 30)
        skip = r.edge_paths[2]
        assert len(skip) > 2


class TestNested:
    def test_入れ子の群は外側が内側を完全に含む(self):
        sizes = _sizes("a", "b", "c", "d")
        _, groups, _, _, _ = layout_nested(
            sizes, [("a", "b"), ("c", "d")],
            [{"label": "外", "members": ["a", "b", "c", "d"]},
             {"label": "内", "members": ["c", "d"]}],
            gap_rank=40, gap_order=30, direction="TB", frame_pad=12, label_h=16)
        boxes = sorted(groups.values(), key=lambda b: b.width * b.height)
        inner, outer = boxes[0], boxes[-1]
        assert outer.x <= inner.x and outer.y <= inner.y
        assert outer.x + outer.width >= inner.x + inner.width
        assert outer.y + outer.height >= inner.y + inner.height

    def test_入れ子でない重なりは黙って崩さず断る(self):
        """1つの節点が2つの群に半端に属す形は、この戦略では解けない。"""
        with pytest.raises(UnsupportedByStrategy):
            layout_nested(_sizes("a", "b", "c"), [],
                          [{"label": "甲", "members": ["a", "b"]},
                           {"label": "乙", "members": ["b", "c"]}],
                          gap_rank=40, gap_order=30, direction="TB",
                          frame_pad=12, label_h=16)


class TestRadial:
    def test_節点は同じ輪の上に等間隔で並ぶ(self):
        sizes = _sizes("a", "b", "c", "d")
        r = layout_radial(sizes, [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")], 40, 30)
        cx = [r.positions[k][0] + SIZE[0] / 2 for k in sizes]
        cy = [r.positions[k][1] + SIZE[1] / 2 for k in sizes]
        ox, oy = sum(cx) / 4, sum(cy) / 4
        radii = [((x - ox) ** 2 + (y - oy) ** 2) ** 0.5 for x, y in zip(cx, cy)]
        assert max(radii) - min(radii) < 1.0

    def test_節点が大きいほど輪も大きい(self):
        """半径を決め打ちしていないことを、大きさを変えて確かめる。"""
        small = layout_radial({k: (40.0, 20.0) for k in "abcd"}, [], 40, 30)
        big = layout_radial({k: (200.0, 100.0) for k in "abcd"}, [], 40, 30)
        assert big.width > small.width

    def test_どの大きさでも節点は重ならない(self):
        for w, h in [(40.0, 20.0), (200.0, 100.0), (300.0, 30.0)]:
            sizes = {k: (w, h) for k in "abcde"}
            r = layout_radial(sizes, [], 40, 30)
            assert _no_overlap(r.positions, sizes)

    def test_層状配置と同じ戻り値の形をしている(self):
        """戦略を差し替えられる、という主張の根拠。"""
        sizes = _sizes("a", "b")
        a = layout_graph(sizes, [("a", "b")], 40, 30)
        b = layout_radial(sizes, [("a", "b")], 40, 30)
        assert type(a) is type(b)
        assert set(a.positions) == set(b.positions)

    def test_輪の並び順は宣言順でなく辺から決まる(self):
        """宣言順に従うと、隣り合うべき節点が輪の反対側へ行き、
        絵はもつれた星になる。幾何的な崩れは出ないので検査は通ってしまう。"""
        keys = [f"n{i}" for i in range(8)]
        cyc = [(keys[i], keys[(i + 1) % 8]) for i in range(8)]
        shuffled = keys[::2] + keys[1::2]
        r = layout_radial({k: SIZE for k in shuffled}, cyc, 40, 30)
        ox = sum(r.positions[k][0] for k in keys) / 8 + SIZE[0] / 2
        oy = sum(r.positions[k][1] for k in keys) / 8 + SIZE[1] / 2

        def angle(k):
            return math.atan2(r.positions[k][1] + SIZE[1] / 2 - oy,
                              r.positions[k][0] + SIZE[0] / 2 - ox)

        # 輪でつながっている隣どうしは、輪の上でも隣（1周／8 の角度）に居る
        step = 2 * math.pi / 8
        for a, b in cyc:
            d = abs(angle(a) - angle(b)) % (2 * math.pi)
            d = min(d, 2 * math.pi - d)
            assert d == pytest.approx(step, abs=step * 0.1)

    def test_輪に並べきれない形は黙って歪めず断る(self):
        """1つの節点から3方向以上へ分かれる木は、輪の上に並べきれない。"""
        sizes = {"root": SIZE}
        edges = []
        for i in range(3):
            sizes[f"a{i}"] = SIZE
            edges.append(("root", f"a{i}"))
            for j in range(3):
                sizes[f"b{i}{j}"] = SIZE
                edges.append((f"a{i}", f"b{i}{j}"))
        with pytest.raises(UnsupportedByStrategy):
            layout_radial(sizes, edges, 40, 30)


def _mindmap(branches: int, leaves: int = 3):
    ids = ["root"]
    edges = []
    for i in range(branches):
        a = f"a{i}"
        ids.append(a)
        edges.append(("root", a))
        for j in range(leaves):
            b = f"b{i}{j}"
            ids.append(b)
            edges.append((a, b))
    return {i: SIZE for i in ids}, edges


class TestTree:
    def test_根が中心に来る(self):
        sizes, edges = _mindmap(4)
        r = layout_tree(sizes, edges, 40, 30)
        cx = [r.positions[k][0] + SIZE[0] / 2 for k in sizes]
        cy = [r.positions[k][1] + SIZE[1] / 2 for k in sizes]
        rx = r.positions["root"][0] + SIZE[0] / 2
        ry = r.positions["root"][1] + SIZE[1] / 2
        assert abs(rx - sum(cx) / len(cx)) < SIZE[0]
        assert abs(ry - sum(cy) / len(cy)) < SIZE[1]

    def test_深いほど中心から遠い(self):
        """深さを輪で表す、ということの座標での言い方。"""
        sizes, edges = _mindmap(4)
        r = layout_tree(sizes, edges, 40, 30)
        ox = r.positions["root"][0] + SIZE[0] / 2
        oy = r.positions["root"][1] + SIZE[1] / 2

        def dist(k):
            return ((r.positions[k][0] + SIZE[0] / 2 - ox) ** 2
                    + (r.positions[k][1] + SIZE[1] / 2 - oy) ** 2) ** 0.5

        assert max(dist(f"a{i}") for i in range(4)) < min(
            dist(f"b{i}{j}") for i in range(4) for j in range(3))

    def test_節点は重ならない(self):
        for br in (2, 4, 10):
            sizes, edges = _mindmap(br)
            r = layout_tree(sizes, edges, 40, 30)
            assert _no_overlap(r.positions, sizes)

    def test_枝を増やしても帯にならない(self):
        """層状配置はここで細長い帯になる。放射木は正方形に近いまま。

        比べるのは形（縦横比）と大きさの向きだけで、何倍という数は置かない
        ── 配置が良くなると倍率は変わるが、主張は変わらないため。
        """
        sizes, edges = _mindmap(10)
        t = layout_tree(sizes, edges, 40, 30)
        g = layout_graph(sizes, edges, 40, 30)
        tree_ratio = max(t.width, t.height) / min(t.width, t.height)
        graph_ratio = max(g.width, g.height) / min(g.width, g.height)
        assert tree_ratio < 2                    # 正方形に近い
        assert graph_ratio > tree_ratio * 2      # 層状は明らかに細長い
        assert max(t.width, t.height) < max(g.width, g.height)

    def test_輪になっていても解ける(self):
        """木に入らない辺があっても落ちない。"""
        sizes = _sizes("a", "b", "c")
        r = layout_tree(sizes, [("a", "b"), ("b", "c"), ("c", "a")], 40, 30)
        assert len(r.positions) == 3

    def test_根から届かない節点も置かれる(self):
        sizes = _sizes("a", "b", "x")
        r = layout_tree(sizes, [("a", "b")], 40, 30)
        assert set(r.positions) == {"a", "b", "x"}

    def test_層状配置と同じ戻り値の形をしている(self):
        sizes = _sizes("a", "b")
        assert type(layout_tree(sizes, [("a", "b")], 40, 30)) is type(
            layout_graph(sizes, [("a", "b")], 40, 30))


class Test札の逃げ場:
    """段の間隔は、その間を通る辺の札が収まるだけ空ける。

    「札どうしが重ならない」だけを性質にしていたため、逃げ場が足りるかを
    誰も見ていなかった。実測：3節点の鎖に長い札を付けると、札が節点の名前へ
    重なった（4件）。札を短くすると0件になるので、足りないのは逃げ場の側。
    """

    def _faults(self, label, direction):
        from svg_engine.compose import render_figure
        from svg_engine.verify import check, check_attachment, check_shapes
        svg = render_figure(
            nodes=[{"id": "a", "label": "概念"}, {"id": "b", "label": "満たすべき性質"},
                   {"id": "c", "label": "アルゴリズム"}],
            edges=[{"from": "a", "to": "b", "label": label},
                   {"from": "b", "to": "c", "label": label}],
            direction=direction)
        return check(svg) + check_shapes(svg) + check_attachment(svg)

    def test_短い札は重ならない(self):
        assert self._faults("保証", "LR") == []

    def test_段の間隔より長い札でも重ならない(self):
        """既定の段の間隔（48）より明らかに長い札。"""
        assert self._faults("何が成り立てばその概念かを言う", "LR") == []

    def test_縦向きでも重ならない(self):
        assert self._faults("何が成り立てばその概念かを言う", "TB") == []
