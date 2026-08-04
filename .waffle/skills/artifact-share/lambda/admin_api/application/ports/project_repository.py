"""プロジェクトの読み書き。

application が必要としているのは「この識別子のものを取り出す」「これを残す」
「あるものを並べる」であって、鍵と値を置くことではない。

architecture: architecture-artifact-share の conceptPlacement（repository）
"""
from __future__ import annotations

from typing import Protocol


class ProjectRepository(Protocol):
    """agg-project の読み書き。集約1つに1つ。"""

    def find(self, project_id: str) -> dict | None:
        """その識別子のプロジェクトを取り出す。無ければ None。"""
        ...

    def save(self, project: dict) -> None:
        """プロジェクトを残す。既にあれば置き換える。"""
        ...

    def all(self) -> tuple[list[dict], int]:
        """あるものを全て取り出す。読めなかったものは飛ばし、その件数を添える。"""
        ...
