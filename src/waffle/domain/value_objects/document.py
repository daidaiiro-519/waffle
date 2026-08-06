"""文書そのものを指す値の型。

集約はエンティティとして entities/ にあり、ここには値だけを置く。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentId:
    """一意な識別子。不変。kebab-case。値が等しければ等価。"""

    value: str


@dataclass(frozen=True)
class DocumentType:
    """Documentが属するschema家族の種別（例: DomainSpec/Skill）。不変。値が
    等しければ等価。"""

    value: str


@dataclass(frozen=True)
class DiscriminatorValue:
    """documentTypeに応じて名前が変わる分岐値（specKind/codingKind/skillKind等の
    いずれか1つのみ出現する）。不変。値が等しければ等価。"""

    value: str


@dataclass(frozen=True)
class SchemaRef:
    """適合するSchemaへの参照。nameとversionの組。両方が等しければ等価。"""

    name: str
    version: str


@dataclass(frozen=True)
class Status:
    """ライフサイクル状態。documentTypeごとに異なるenumを持つ（Spec家族は
    CREATED/VALIDATED/RENDERED/SUPERSEDED、それ以外はDRAFT/ACTIVE/DEPRECATED）。
    不変。値が等しければ等価。"""

    value: str
