"""層状グラフ描画 ── Graphvizの`dot`と同じ系統（Sugiyama法）の、本格版。

`layout.py`の簡易版に欠けていた4点を埋める:

1. サイクルの分断 ── DFSで逆流する辺を見つけ、段の計算時だけ向きを仮に反転する
2. 複数段をまたぐ辺の経路 ── またぐ段の分だけ「仮の節点」を挟み、隣接段だけを結ぶ
   単位辺の鎖にする。これが無いと、長い辺が中間の節点を突っ切って描かれる
3. 交差の最小化 ── 中央値法と転置法を、上り下り交互に何度も反復し、
   交差の数が一番少なかった並びを採用する
4. 座標の整列 ── 親の位置へ寄せる中央値ヒューリスティックを、下り・上り
   両方向で繰り返し平均する（Brandes-Köpf法の簡略版。本家ほど厳密ではないが、
   反復するたびに収束するので正しさを目で確かめやすい）

どの段も、宣言（nodes/edges）を型として持つだけで、Waffle固有の語彙は知らない。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .geometry import shift_to_origin


@dataclass
class LayoutResult:
    positions: dict[str, tuple[float, float]]   # 実節点id → (x, y) 左上
    edge_paths: dict[int, list[tuple[float, float]]]  # 辺の通し番号 → 通る点の並び
    width: float
    height: float


# ── 1. サイクルの分断 ──────────────────────────────────────

def _break_cycles(nodes: list[str], edges: list[tuple[str, str]]) -> list[tuple[str, str, bool]]:
    """DFSで逆流する辺(後退辺)を見つけ、(from, to, reversed)の並びを返す。

    reversed=True の辺は、段の計算では (to, from) として扱う。実際の矢印の
    向きは元のまま (from→to) で描くので、呼び出し側はここのreversedを見て
    経路の点列を反転させ直す。
    """
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for a, b in edges:
        if a in adj and b in adj:
            adj[a].append(b)

    WHITE, GRAY, BLACK = 0, 1, 2
    out: list[tuple[str, str, bool]] = []

    # 明示的スタックで深さ優先を辿る（再帰深度の上限を気にせずに済むように）。
    state = {n: WHITE for n in nodes}
    for start in nodes:
        if state[start] != WHITE:
            continue
        stack = [(start, iter(adj[start]))]
        state[start] = GRAY
        while stack:
            u, it = stack[-1]
            advanced = False
            for v in it:
                if v not in state:
                    continue
                if state[v] == WHITE:
                    state[v] = GRAY
                    stack.append((v, iter(adj[v])))
                    advanced = True
                    break
                elif state[v] == GRAY:
                    out.append((v, u, True))  # 後退辺。段の計算では逆向きに使う
                else:
                    out.append((u, v, False))
            if not advanced:
                state[u] = BLACK
                stack.pop()
    # 上のループは「u→v」を辿るたびに1本ずつoutへ積むが、同じ(u,v)を後退辺
    # 判定のときと通常時とで二重に積まないよう、辺の集合から作り直す。
    result = []
    seen = set()
    rank_edges = {}
    for a, b, rev in out:
        rank_edges[(a, b) if not rev else (b, a)] = rev
    for a, b in edges:
        if a not in adj or b not in adj:
            continue
        key = (a, b)
        rev = rank_edges.get(key)
        if rev is None:
            # DFSで辿らなかった辺（多重辺等）は非後退として扱う
            rev = False
        result.append((a, b, rev))
    return result


# ── 2. 段の割り当て（縦の伸びを長すぎず短すぎずに寄せる軽い調整つき） ──────

def _assign_ranks(nodes: list[str], dag_edges: list[tuple[str, str]]) -> dict[str, int]:
    rank = {n: 0 for n in nodes}
    for _ in range(len(nodes) + 1):
        changed = False
        for a, b in dag_edges:
            if rank[b] < rank[a] + 1:
                rank[b] = rank[a] + 1
                changed = True
        if not changed:
            break
    # 引き締め ── 出て行く辺を持たない節点は、それ以上下げても誰も困らない
    # ので、最も近い子の1つ上まで引き上げて縦の間延びを削る。
    children = {n: [] for n in nodes}
    for a, b in dag_edges:
        children[a].append(b)
    for n in reversed(nodes):
        if children[n]:
            rank[n] = min(rank[n], min(rank[c] for c in children[n]) - 1)
        rank[n] = max(rank[n], 0)
    return rank


# ── 3. 複数段をまたぐ辺へ仮の節点を挟む ────────────────────────

@dataclass
class ExpandedGraph:
    all_nodes: list[str]
    real: set[str]
    rank: dict[str, int]
    unit_edges: list[tuple[str, str]]
    # 元の辺(通し番号)ごとの、通る節点id列（実節点＋仮節点、rank昇順）
    chains: dict[int, list[str]]
    reversed_flags: dict[int, bool]


def _expand(nodes: list[str], edges_with_rev: list[tuple[str, str, bool]],
            rank: dict[str, int]) -> ExpandedGraph:
    all_nodes = list(nodes)
    unit_edges: list[tuple[str, str]] = []
    chains: dict[int, list[str]] = {}
    reversed_flags: dict[int, bool] = {}
    vcount = 0

    for idx, (a, b, rev) in enumerate(edges_with_rev):
        ra, rb = rank[a], rank[b]
        lo, hi = (a, b) if ra <= rb else (b, a)
        chain = [lo]
        cur = lo
        for r in range(lo_r := rank[lo] + 1, rank[hi]):
            vid = f"__v{vcount}"
            vcount += 1
            rank[vid] = r
            all_nodes.append(vid)
            unit_edges.append((cur, vid))
            chain.append(vid)
            cur = vid
        unit_edges.append((cur, hi))
        chain.append(hi)
        if lo != a:
            chain = list(reversed(chain))
        chains[idx] = chain
        reversed_flags[idx] = rev

    return ExpandedGraph(all_nodes=all_nodes, real=set(nodes), rank=rank,
                          unit_edges=unit_edges, chains=chains, reversed_flags=reversed_flags)


# ── 4. 段内の並び順 ── 中央値法＋転置法を反復し、交差が最少の結果を採る ──

def _block_of(node: str, groups: list[list[str]]) -> int:
    """その節点が属する群の番号。属さないなら -1。

    入れ子（群の中の群）は、より内側＝より後に宣言された群を優先する。
    """
    found = -1
    for i, members in enumerate(groups):
        if node in members:
            found = i
    return found


def _order_within_ranks(expanded: ExpandedGraph,
                         groups: list[list[str]] | None = None) -> dict[str, int]:
    """段内の並びを解く。

    群があるときは階層的に解く ── まず同じ群の要素をひとつの塊として扱い、
    塊どうしの並びを交差が減るよう決め、次に塊の中の並びを同じやり方で決める。
    こうすると「同じ群の要素が隣り合う」ことが構造的に保証されたうえで、
    交差の最小化が群の外と内の両方で効く。

    隣り合うことは優先度ではなく要件である ── 離れて置かれた要素を箱で囲むと、
    間に居る非メンバーまで囲んでしまい、その囲みは意味を成さない。
    """
    groups = groups or []
    by_rank: dict[int, list[str]] = {}
    for n in expanded.all_nodes:
        by_rank.setdefault(expanded.rank[n], []).append(n)

    incoming: dict[str, list[str]] = {n: [] for n in expanded.all_nodes}
    outgoing: dict[str, list[str]] = {n: [] for n in expanded.all_nodes}
    for a, b in expanded.unit_edges:
        outgoing[a].append(b)
        incoming[b].append(a)

    order: dict[str, int] = {}
    for r in sorted(by_rank):
        for i, n in enumerate(by_rank[r]):
            order[n] = i

    def median_pass(neighbours: dict[str, list[str]], ranks_seq):
        for r in ranks_seq:
            row = by_rank[r]

            def med(n):
                ords = sorted(order[p] for p in neighbours[n] if p in order)
                if not ords:
                    return order[n]
                m = len(ords) // 2
                if len(ords) % 2 == 1:
                    return float(ords[m])
                if len(ords) == 2:
                    return (ords[0] + ords[1]) / 2
                left = ords[m - 1] - ords[0]
                right = ords[-1] - ords[m]
                if left + right == 0:
                    return (ords[m - 1] + ords[m]) / 2
                return (ords[m - 1] * right + ords[m] * left) / (left + right)

            if groups:
                # 階層的に解く。塊（＝同じ群の要素の集まり）を単位に並べてから、
                # 塊の中をもう一度並べる。塊は分断されないので隣接が保たれる。
                blocks: dict[int, list[str]] = {}
                for n in row:
                    blocks.setdefault(_block_of(n, groups), []).append(n)
                free = [(-1, [n]) for n in blocks.pop(-1, [])]
                units = free + [(gi, members) for gi, members in blocks.items()]

                def unit_med(unit):
                    _, members = unit
                    return sum(med(m) for m in members) / len(members)

                keyed = []
                for _, members in sorted(units, key=unit_med):
                    keyed.extend(sorted(members, key=med) if len(members) > 1 else members)
            else:
                keyed = sorted(row, key=med)
            for i, n in enumerate(keyed):
                order[n] = i

    def transpose():
        """隣り合う2つを入れ替えて交差が減るなら採用する。局所改善のダメ押し。

        ただし群をまたぐ入れ替えはしない ── それをすると塊が分断され、
        階層的に解いて得た隣接が壊れる。
        """
        improved = True
        while improved:
            improved = False
            for r in sorted(by_rank):
                row = by_rank[r]
                for i in range(len(row) - 1):
                    n1, n2 = row[i], row[i + 1]
                    if groups and _block_of(n1, groups) != _block_of(n2, groups):
                        continue
                    before = _local_crossings(n1, n2, order, incoming, outgoing)
                    after = _local_crossings(n2, n1, order, incoming, outgoing)
                    if after < before:
                        row[i], row[i + 1] = n2, n1
                        order[n1], order[n2] = i + 1, i
                        improved = True

    ranks_sorted = sorted(by_rank)
    best_order = dict(order)
    best_score = _crossing_total(expanded, by_rank, order)
    # 回数は決め打ちにしない。良くならなくなったら止める ── 交差が0になるか、
    # 上りと下りを1往復しても並びが変わらなくなった（不動点に達した）ら終わり。
    # 上限は節点の数から取る。交差の入れ替えは1回につき少なくとも1組しか
    # 直さないので、節点の数を超えて改善が続くことはない（保険であって閾値ではない）。
    limit = max(len(expanded.rank), 1)
    it = 0
    while it < limit * 2 and best_score > 0:
        before_cycle = dict(order)
        for direction_pass in (0, 1):
            seq = ranks_sorted if direction_pass == 0 else list(reversed(ranks_sorted))
            median_pass(incoming if direction_pass == 0 else outgoing, seq)
            transpose()
            score = _crossing_total(expanded, by_rank, order)
            if score < best_score:
                best_score = score
                best_order = dict(order)
        if order == before_cycle:
            break            # 一往復して何も動かなかった＝これ以上良くならない
        it += 1
    return best_order


def _local_crossings(n1, n2, order, incoming, outgoing) -> int:
    """n1がn2の左（順序が小さい）に居るとして、隣接段との間で何本交差するか。"""
    c = 0
    for neigh in (incoming, outgoing):
        for p1 in neigh.get(n1, []):
            for p2 in neigh.get(n2, []):
                if order.get(p1, 0) > order.get(p2, 0):
                    c += 1
    return c


def _crossing_total(expanded: ExpandedGraph, by_rank: dict[int, list[str]],
                     order: dict[str, int]) -> int:
    total = 0
    ranks = sorted(by_rank)
    edges_by_top_rank: dict[int, list[tuple[str, str]]] = {r: [] for r in ranks}
    for a, b in expanded.unit_edges:
        ra = expanded.rank[a]
        edges_by_top_rank.setdefault(ra, []).append((a, b))
    for r in ranks[:-1]:
        pairs = [(order[a], order[b]) for a, b in edges_by_top_rank.get(r, [])]
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                (a1, b1), (a2, b2) = pairs[i], pairs[j]
                if (a1 - a2) * (b1 - b2) < 0:
                    total += 1
    return total


# ── 5. 座標の整列 ── 上下の中央値へ寄せる反復平均（簡略版） ──────────

def _assign_coordinates(expanded: ExpandedGraph, order: dict[str, int],
                         sizes: dict[str, tuple[float, float]],
                         gap_rank: float, gap_order: float,
                         direction: str, tolerance: float,
                         groups: list[list[str]] | None = None,
                         group_margin: float = 0.0) -> dict[str, tuple[float, float]]:
    groups = groups or []
    by_rank: dict[int, list[str]] = {}
    for n in expanded.all_nodes:
        by_rank.setdefault(expanded.rank[n], []).append(n)
    for r in by_rank:
        by_rank[r].sort(key=lambda n: order[n])

    def size_of(n):
        return sizes.get(n, (2.0, 2.0))

    def gap_between(prev: str, cur: str) -> float:
        """隣り合う2つの間に空ける量。群の境目だけ、枠が入るぶんを余分に空ける。

        全体の間隔を一律に広げると、群の内側まで間延びする。境目にだけ足す。
        """
        if groups and _block_of(prev, groups) != _block_of(cur, groups):
            return gap_order + group_margin
        return gap_order

    # 初期位置 ── 段内をそのまま均等配置
    cross = {}
    for r in sorted(by_rank):
        row = by_rank[r]
        cursor = 0.0
        for i, n in enumerate(row):
            w = size_of(n)[0 if direction == "TB" else 1]
            if i > 0:
                cursor += gap_between(row[i - 1], n) - gap_order
            cross[n] = cursor + w / 2
            cursor += w + gap_order

    incoming: dict[str, list[str]] = {n: [] for n in expanded.all_nodes}
    outgoing: dict[str, list[str]] = {n: [] for n in expanded.all_nodes}
    for a, b in expanded.unit_edges:
        outgoing[a].append(b)
        incoming[b].append(a)

    def resolve_overlaps(row):
        """段の中の重なりを解く。解いたあと、段全体を元の重心へ戻す。

        右へ押すだけだと左端が固定され、同じ位置を望む要素どうしが右へ
        偏る ── 2つの親が1つの子を指すとき、子の真上に来るのは左の親だけで、
        対の中心は右へずれる（実測：親が246と330、子が246）。押した量の
        平均だけ段ごと戻せば、望んだ位置の重心と一致する。ずらす量は
        押した結果から出るので、決め打ちの数は要らない。
        """
        wanted = [cross[n] for n in row]
        for i in range(1, len(row)):
            prev, cur = row[i - 1], row[i]
            min_gap = size_of(prev)[0 if direction == "TB" else 1] / 2 + \
                      size_of(cur)[0 if direction == "TB" else 1] / 2 + gap_between(prev, cur)
            if cross[cur] - cross[prev] < min_gap:
                cross[cur] = cross[prev] + min_gap
        if row:
            shift = (sum(wanted) - sum(cross[n] for n in row)) / len(row)
            for n in row:
                cross[n] += shift

    ranks_sorted = sorted(by_rank)
    # 回数は決め打ちにしない。1回の往復で動いた最大の量が、描いても見えない
    # 大きさ（線の太さ）を下回ったら止める。上限は節点の数（保険）。
    limit = max(len(order), 1)
    it = -1
    moved = tolerance + 1
    while it + 1 < limit * 2 and moved > tolerance:
        it += 1
        snapshot = dict(cross)
        neigh = incoming if it % 2 == 0 else outgoing
        seq = ranks_sorted if it % 2 == 0 else list(reversed(ranks_sorted))
        for r in seq:
            row = by_rank[r]
            for n in row:
                ns = neigh.get(n, [])
                if ns:
                    cross[n] = sum(cross[p] for p in ns) / len(ns)
            # 位置で並べ替え直すと、順序の段で解いた群の隣接が壊れる。
            # 群があるときは塊ごと動かし、塊の中だけを並べ替える。
            if groups:
                units: list[tuple[int, list[str]]] = []
                for n in row:
                    gi = _block_of(n, groups)
                    if units and units[-1][0] == gi and gi != -1:
                        units[-1][1].append(n)
                    else:
                        units.append((gi, [n]))
                units.sort(key=lambda u: sum(cross[m] for m in u[1]) / len(u[1]))
                row[:] = [m for _, members in units
                          for m in sorted(members, key=lambda n: cross[n])]
            else:
                row.sort(key=lambda n: cross[n])
            resolve_overlaps(row)
        moved = max((abs(cross[k] - snapshot[k]) for k in cross), default=0.0)

    main = {}
    cursor = 0.0
    for r in ranks_sorted:
        row = by_rank[r]
        extent = max(size_of(n)[1 if direction == "TB" else 0] for n in row)
        for n in row:
            main[n] = cursor
        cursor += extent + gap_rank

    positions = {}
    for n in expanded.all_nodes:
        w, h = size_of(n)
        if direction == "TB":
            positions[n] = (cross[n] - w / 2, main[n])
        else:
            positions[n] = (main[n], cross[n] - h / 2)
    return positions


# ── 公開API ────────────────────────────────────────────

def layout_graph(node_sizes: dict[str, tuple[float, float]],
                  edges: list[tuple[str, str]],
                  gap_rank: float, gap_order: float,
                  direction: str = "TB",
                  tolerance: float = 1.0,
                  groups: list[list[str]] | None = None,
                  group_margin: float = 0.0) -> LayoutResult:
    """点と辺から、実座標つきの完全なレイアウトを解く。

    サイクル・複数段をまたぐ辺・交差する辺のいずれにも耐える
    （耐える、とは＝クラッシュしない、かつ辺が節点を突っ切らないことを指す。
    Graphviz本家と全く同じ美しさになる保証はしない）。

    Args:
        node_sizes: 実節点idごとの (width, height)。
        edges: (from, to) の並び。
        gap_rank: 段と段の間隔。
        gap_order: 段内の要素どうしの間隔。
        direction: "TB" または "LR"。
        tolerance: 座標の整列を止める動きの大きさ。描いても見えない大きさ
            （線の太さ）を渡す。回数ではなく、この量で打ち切る。
        groups: 隣り合わせる識別子の集合の並び（囲みの要素）。与えると、
            各段でその要素が必ず隣り合うよう階層的に順序を解く。箱で囲む以上
            隣接は要件であり、離れて置くと非メンバーまで囲んでしまう。
        group_margin: 群の境目にだけ余分に空ける量（枠の線と余白が入る幅）。

    Returns:
        LayoutResult。edge_pathsのキーは edges の通し番号(0始まり)で、
        値はその辺が実際に通る点列（元のfrom→toの向きで、始点・終点とも
        節点の中心座標）。

    Raises:
        なし。
    """
    nodes = list(node_sizes)
    edges_with_rev = _break_cycles(nodes, edges)
    dag_edges = [((b, a) if rev else (a, b)) for a, b, rev in edges_with_rev]
    rank = _assign_ranks(nodes, dag_edges)
    expanded = _expand(nodes, edges_with_rev, dict(rank))
    order = _order_within_ranks(expanded, groups)

    sizes = dict(node_sizes)
    for n in expanded.all_nodes:
        if n not in sizes:
            sizes[n] = (1.0, 1.0)  # 仮節点は点として扱う

    positions = _assign_coordinates(expanded, order, sizes, gap_rank, gap_order,
                                     direction, tolerance, groups, group_margin)

    # 段ごとに重心へ戻すと、左（または上）へはみ出すことがある。原点を左上へ
    # 取り直す ── 呼び出し側は座標が0から始まる前提で画布を決めるため。
    positions, _ = shift_to_origin(positions)

    def centre(n):
        x, y = positions[n]
        w, h = sizes[n]
        return (x + w / 2, y + h / 2)

    # 仮節点は点（1×1）なので、その段が背の高いもの（畳んだ群など）を含むと、
    # 段の上端だけを経由して斜めに降り、間の箱を切ってしまう。仮節点では
    # 段の入口と出口の2点を出し、辺がその段の高さぶん並走するようにする。
    axis = 1 if direction == "TB" else 0
    rank_lo: dict[int, float] = {}
    rank_hi: dict[int, float] = {}
    for n in nodes:
        r = expanded.rank[n]
        lo = positions[n][axis]
        hi = lo + sizes[n][1 if axis == 1 else 0]
        rank_lo[r] = min(rank_lo.get(r, lo), lo)
        rank_hi[r] = max(rank_hi.get(r, hi), hi)

    edge_paths: dict[int, list[tuple[float, float]]] = {}
    for idx, chain in expanded.chains.items():
        pts: list[tuple[float, float]] = []
        for n in chain:
            if n in expanded.real:
                pts.append(centre(n))
                continue
            r = expanded.rank[n]
            cx, cy = centre(n)
            lo = rank_lo.get(r, cy if axis == 1 else cx)
            hi = rank_hi.get(r, cy if axis == 1 else cx)
            if axis == 1:
                pts.append((cx, lo))
                pts.append((cx, hi))
            else:
                pts.append((lo, cy))
                pts.append((hi, cy))
        edge_paths[idx] = pts

    real_positions = {n: positions[n] for n in nodes}
    max_x = max((positions[n][0] + sizes[n][0] for n in expanded.all_nodes), default=0)
    max_y = max((positions[n][1] + sizes[n][1] for n in expanded.all_nodes), default=0)
    return LayoutResult(positions=real_positions, edge_paths=edge_paths,
                         width=max_x, height=max_y)
