"""共有アーティファクトの読み書き。

application が必要としているのは「この識別子のものを取り出す」「これを残す」
「扱えるものを並べる」であって、鍵と値を置くことではない。鍵をどう組み立て、
どんな形で並べるかは実装の関心事で、この宣言には現れない。

期限や公開状態の判断はここではしない。取り出したものを domain が判じる。

architecture: architecture-artifact-share の conceptPlacement（repository）
"""
from __future__ import annotations

from typing import Protocol


class SharedArtifactRepository(Protocol):
    """agg-shared-artifact の読み書き。集約1つに1つ。"""

    def find(self, artifact_id: str) -> dict | None:
        """その識別子の共有アーティファクトを取り出す。無ければ None。"""
        ...

    def save(self, artifact: dict) -> None:
        """共有アーティファクトを残す。既にあれば置き換える。"""
        ...

    def all(self) -> tuple[list[dict], int]:
        """あるものを全て取り出す。

        読めなかったものは飛ばし、その件数を添えて返す。1件の不具合で
        全体が失われるのを避けるため、読めないことを失敗として投げない。
        """
        ...
