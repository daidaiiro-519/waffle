"""implementation_inventory — 規約が宣言した配置に在る実装ファイルと、
仕様が名指しした実装ファイルを突き合わせる純粋なドメインサービス。

いままでの突き合わせは「宣言したものが実装されているか」の一方向だけで、
宣言しなければ何を実装しても綺麗に見えた。緑は「宣言した分については
実装されている」しか意味せず、仕様が実装を説明できているかは誰も
確かめていなかった。

同じ向きは仕様どうしの検査（disk に在るが宣言に無い）と、シナリオの検査
（テストに在るが宣言に無い＝孤立）が既に持っている。語彙もそちらへ揃える。

どのファイルが実装でないか（パッケージの目印など）は言語ごとに違うので、
規約が宣言する。ここでは名前を持たない。
"""
from __future__ import annotations


def orphaned_implementation_files(
    actual_paths: list[str], expected_paths: set[str], non_implementation: list[str],
) -> list[str]:
    """配置に在るが、どの仕様からも名指しされていない実装ファイルを返す。

    Args:
        actual_paths: 宣言された配置に実在するファイルのパス。
        expected_paths: 仕様の宣言から導いた実装ファイルのパス。
        non_implementation: 実装ではないファイルの名前（規約の宣言）。

    Returns:
        名指しされていないファイルのパス。名前順。

    Raises:
        なし。
    """
    excluded = set(non_implementation)
    return sorted(
        path for path in actual_paths
        if path not in expected_paths and path.rsplit("/", 1)[-1] not in excluded
    )
