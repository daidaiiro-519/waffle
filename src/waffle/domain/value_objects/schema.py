"""スキーマそのものを指す値の型。

集約はエンティティとして entities/ にあり、ここには値だけを置く。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaId:
    """スキーマ名（例: CodingSchema）。不変。値が等しければ等価。"""

    value: str


@dataclass(frozen=True)
class Version:
    """単調増加する版識別子（例: v1, v2）。不変。値が等しければ等価。"""

    value: str


@dataclass(frozen=True)
class KindProfile:
    """kind（specKind/codingKind/skillKind/agentKind/templateKind）1つに対応する、
    必須contentブロック集合。不変。name＋required_blocksの組で識別される。"""

    name: str
    required_blocks: frozenset[str]
