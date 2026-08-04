"""寄せられた反応の読み書き。

追記しかしない。書いたものを消す手立ては持たない——指摘を受けて直し、また
見てもらうという往復の記録が、あとから書き換えられては意味を持たないため。

差し替えの区切りは、反応と同じ並びに載る印であって反応そのものではない。
数えるときは含めない。この区別は port の約束として持ち、どう見分けるかは
実装の関心事。

architecture: architecture-artifact-share の conceptPlacement（repository）
"""
from __future__ import annotations

from typing import Protocol


class CommentRepository(Protocol):
    """agg-comment の読み書き。集約1つに1つ。"""

    def list_of(self, artifact_id: str) -> tuple[list[dict], int]:
        """寄せられた順に返す。差し替えの区切りも同じ並びに含める。

        読めなかったものは飛ばし、その件数を添える。1件の不具合でその共有
        アーティファクトの反応がすべて見えなくなるのを避けるため。
        """
        ...

    def count_of(self, artifact_id: str) -> int:
        """寄せられた反応の件数。差し替えの区切りは数えない。"""
        ...

    def add_replacement_divider(self, artifact_id: str, at: int) -> None:
        """中身を差し替えたことを、反応と同じ並びに1件の印として残す。"""
        ...
