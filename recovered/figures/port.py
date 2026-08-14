"""並びを決める口 ── 点と線から、段と段内の位置だけを返す。

通すのは大きさに依存しない整数だけ。座標も、箱の大きさも、色も返さない。
向こう側（いまは grandalf）を差し替えても、返るものは変わらない。
"""
from __future__ import annotations


def arrange(nodes, edges, groups=None, same_rank=None):
    """点と線を、段と段内の位置へ割り当てる。

    Args:
        nodes: 識別子の並び。
        edges: (から, へ) の並び。
        groups: 同じ塊に置きたい識別子の集合の並び。
        same_rank: 同じ段に置きたい識別子の集合の並び。

    Returns:
        識別子ごとの {"island": int, "rank": int, "order": int}。整数のみ。

    Raises:
        なし。
    """
    groups = groups or []
    same_rank = same_rank or []

    incoming = {n: [] for n in nodes}
    outgoing = {n: [] for n in nodes}
    for a, b in edges:
        if a in outgoing and b in incoming:
            outgoing[a].append(b)
            incoming[b].append(a)

    # 段 ── 入ってくる辺を持たないものを 0 段目に置き、そこから深さを伸ばす。
    # 輪になっている辺は段を進めない（進めると終わらない）。
    rank = {n: 0 for n in nodes}
    for _ in range(len(nodes)):
        changed = False
        for a, b in edges:
            if a in rank and b in rank and rank[b] < rank[a] + 1:
                rank[b] = rank[a] + 1
                changed = True
        if not changed:
            break

    for same in same_rank:
        members = [n for n in same if n in rank]
        if members:
            top = max(rank[n] for n in members)
            for n in members:
                rank[n] = top

    # 島 ── 辺で辿り着ける範囲をひとかたまりとする
    island = {}
    neighbours = {n: set(outgoing[n]) | set(incoming[n]) for n in nodes}
    current = 0
    for n in nodes:
        if n in island:
            continue
        stack, seen = [n], set()
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            stack.extend(neighbours[x] - seen)
        for x in seen:
            island[x] = current
        current += 1

    # 段内の位置 ── 親の位置の中央値へ寄せる。塊の要素は隣り合わせる。
    group_of = {}
    for i, g in enumerate(groups):
        for n in g:
            group_of[n] = i

    order = {}
    for r in sorted(set(rank.values())):
        row = [n for n in nodes if rank[n] == r]

        def key(n):
            parents = [order[p] for p in incoming[n] if p in order]
            centre = sum(parents) / len(parents) if parents else len(order)
            return (island[n], group_of.get(n, -1), centre, nodes.index(n))

        for i, n in enumerate(sorted(row, key=key)):
            order[n] = i

    return {n: {"island": island[n], "rank": rank[n], "order": order[n]} for n in nodes}
