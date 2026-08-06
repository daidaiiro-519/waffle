"""Document集約のEntity/ValueObject（agg-document.jsonのEntities/ValueObjects
ブロックが仕様そのもの）。

check-aggregate-class-driftが検証する対象。Schema集約（domain/entities/schema.py）
と同じ方針で、複雑な業務ロジックメソッドを持たせず、値オブジェクトの不変性・値に
よる等価性という宣言された構造のみを表現する薄いEntityとする。不変条件のうち
手続き的なもの（status遷移・SUPERSEDED終端・schemaRef必須等）は、既に
lifecycle_guard.py・schema_ref_guard.pyという純粋関数のドメインサービスとして
実装済み。
"""

from __future__ import annotations

from dataclasses import dataclass

from waffle.domain.value_objects.document import DiscriminatorValue, DocumentId, DocumentType, SchemaRef, Status


@dataclass(frozen=True)
class Document:
    """構造化された成果物の一貫性単位。"""

    document_id: DocumentId
    document_type: DocumentType
    schema_ref: SchemaRef
    status: Status
    spec_kind: DiscriminatorValue | None
    coding_kind: DiscriminatorValue | None
    skill_kind: DiscriminatorValue | None
    agent_kind: DiscriminatorValue | None
    template_kind: DiscriminatorValue | None
    hook_kind: DiscriminatorValue | None
    subdomain_ref: DocumentId | None
    aggregate_ref: DocumentId | None
    skill_ref: DocumentId | None
    skill_refs: list[DocumentId] | None
    agent_refs: list[DocumentId] | None
    knowledge_kind: DiscriminatorValue | None
    stack: list[str] | None
    created_at: str | None
    updated_at: str | None
    content: dict
    tags: list[str]
    distribution_tier: str | None
