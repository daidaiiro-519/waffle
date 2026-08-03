"""dependency_cycles — 依存グラフの中で閉じている部分（循環）を見つける純ロジック。

層をまたぐ循環は依存してよい先の宣言が防ぐが、同じ層の中の循環は向きの規則では
捕まらない。どちらの向きも許されているため、規則に照らしても違反にならない。

強連結成分を求めることで、始点をどこに取っても同じ循環を1件として返す。深さ優先で
辿った順に報告すると、ファイルを見る順序という本質と無関係な要因で件数が変わる。
"""
from __future__ import annotations


def find_cycles(graph: dict) -> list[list[str]]:
    """互いに辿り着ける節点の組（循環）を列挙する。

    Args:
        graph: 節点 → その節点が参照する節点の集合。

    Returns:
        循環ごとの節点の一覧。節点も循環どうしも並び順を固定して返す。
        循環が無ければ空。
    """
    nodes = sorted(set(graph) | {t for targets in graph.values() for t in targets})
    index: dict = {}
    low: dict = {}
    on_stack: set = set()
    stack: list = []
    counter = [0]
    found: list[list[str]] = []

    def targets_of(node: str) -> list[str]:
        return sorted(graph.get(node, ()))

    for root in nodes:
        if root in index:
            continue
        # 再帰ではなく明示のスタックで辿る。ファイル数の多いプロジェクトで
        # 再帰の上限に当たると、検査そのものが落ちるため
        work: list = [(root, iter(targets_of(root)))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in index:
                    index[child] = low[child] = counter[0]
                    counter[0] += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(targets_of(child))))
                    advanced = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    popped = stack.pop()
                    on_stack.discard(popped)
                    component.append(popped)
                    if popped == node:
                        break
                if len(component) > 1 or node in graph.get(node, ()):
                    found.append(sorted(component))
    return sorted(found)
