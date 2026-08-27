"""部品の登録台帳 ── 新しい描画パターンを、コアを直さずに足すための場所。

コンポーネントは「種別名」で引く関数として登録する。核（compose.py・layout.py）は
この台帳越しにしか部品を呼ばない。だから新しい部品（アセット）は、この台帳へ
1行足すだけで使えるようになり、核の側は一切変更しない（開放閉鎖の原則）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ComponentResult:
    """描いた部品の中身と、それが申告すること。

    **満たすべき性質** ── 置く前に描く部品（`placement="own-origin"`）は、
    申告した大きさの中にインクが収まっていなければならない。外へ出ると、
    配置は空でない場所を空きと見なし、置いたものどうしが重なる（実測：名前の
    字面が y=-3.6 まではみ出しており、帯を描いて初めて見えた）。

    「最小」であることは求めない。図（棒グラフ等）は作図領域の余白を大きさに
    含むのが正しく、実測でもインクが申告の32%しかない図がある。**含むことは
    全部品に課し、詰まっていることは課さない。**
    """
    svg: str
    """この部品自身の座標系（0,0起点）で書かれたSVG断片。呼び出し側が
    `<g transform="translate(x,y)">` で望みの位置へ移す。"""

    width: float
    height: float
    """外側から見える大きさ。レイアウトが位置を計算するのに使う。"""

    placement: str = "own-origin"
    """置く前に描くか（`"own-origin"`）、置いた後に描くか（`"absolute"`）。

    節点になる部品は自分の原点で描き、どこへ置かれるかを知らない。辺・囲み・
    囲みの札は、既に置かれた節点をまたぐので、最初から絶対座標を受け取る。
    **この2系統は、申告する大きさの意味が違う** ── 前者は自分を囲む器だが、
    後者は既に決まった座標の広がりでしかなく、器としては使われない。
    だから上の性質は前者にだけ課す。"""

    labels_itself: bool = False
    """渡された名前を、この部品が自分で描いたか。

    名前を描く役目は1箇所にしか置けない。部品が描いたのに包む側も描くと、
    同じ名前が二重に出る（box・hex で実測）。包む側はこの申告を見て、
    自分では描かない。

    輪郭は申告しない ── 申告する形と実際に描いた形はずれる（11種のうち
    輪郭を申告していたのは3種だけで、残りは外接矩形で代用され、インクが
    矩形の一部にしか無い部品では辺が空白へ着いていた）。輪郭は
    geometry.outline_of() が、この svg そのものから導く。
    """


ComponentFn = Callable[[dict, dict], ComponentResult]

_REGISTRY: dict[str, ComponentFn] = {}


def component(kind: str):
    """デコレータ。この関数を種別名 `kind` の部品として登録する。

    Args:
        kind: 部品の種別名。呼び出し側はこの名前で部品を指定する。
    """
    def deco(fn: ComponentFn) -> ComponentFn:
        if kind in _REGISTRY:
            raise ValueError(f"部品 '{kind}' は既に登録されています")
        _REGISTRY[kind] = fn
        return fn
    return deco


def render_component(kind: str, props: dict, style: dict) -> ComponentResult:
    """種別名から部品を引いて描く。

    Args:
        kind: 部品の種別名（例: "box", "edge"）。
        props: 構造の入力（例: label, from, to）。色・寸法を含まない。
        style: resolve_style() が解決した見た目の値。

    Returns:
        ComponentResult。

    Raises:
        KeyError: 台帳に無い種別名を指定したとき。
    """
    if kind not in _REGISTRY:
        raise KeyError(f"知らない部品です: {kind}（台帳: {sorted(_REGISTRY)}）")
    return _REGISTRY[kind](props, style)


def known_kinds() -> list[str]:
    return sorted(_REGISTRY)
