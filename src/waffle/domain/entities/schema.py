"""Schema集約のEntity/ValueObject（agg-schema.jsonのEntities/ValueObjectsブロックが
仕様そのもの）。

check-aggregate-class-driftが検証する対象。ddd-advisorの判断（agg-schema.jsonの
Invariants 9件中8件は静的構造制約でありJSON Schema自体が担保、手続き的な1件
（後方互換性）は既にschema_patch.pyのcheck_backward_compatible()が担う）に基づき、
ここでは複雑な業務ロジックメソッドを持たせず、値オブジェクトの不変性・値による
等価性という宣言された構造のみを表現する薄いEntityとする。
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


@dataclass(frozen=True)
class Schema:
    """Documentの型定義（構造・描画・記入/読取指示）の一貫性単位。"""

    schema_id: SchemaId
    version: Version
    kind_profiles: tuple[KindProfile, ...]
