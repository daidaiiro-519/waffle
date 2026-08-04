"""操作している人。

誰であるかと、管理者かどうかだけを持つ。どうやって本人だと確かめたか
（証明の仕組み）はここに現れない——確かめ終えた結果だけを受け取る。
そのため、この値は認証の仕組みに依存しない。

対象の仕様: agg-shared-artifact / agg-project
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Caller:
    """操作している人。誰であるかと、管理者かどうかだけを持つ。"""

    id: str
    is_admin: bool = False
