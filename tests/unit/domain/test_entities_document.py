"""agg-document（Document集約）のEntity/ValueObjectに対応するネイティブテスト。

agg-document.jsonのEntities/ValueObjectsブロックが既に集約の仕様であり、ここでは
そこで宣言された構造（17属性・5ValueObject、および各ValueObjectの不変性・値による
等価性）がPython実装として成立していることを検証する。Schema集約
（domain/entities/schema.py）と同じ「薄いEntity」方針に従う。
"""
import pytest

from waffle.domain.entities.document import (
    DiscriminatorValue,
    Document,
    DocumentId,
    DocumentType,
    SchemaRef,
    Status,
)


def test_DocumentIdは値が等しければ等価():
    """
    Given 同じ値を持つ2つのDocumentId
    When 等価性を比較する
    Then 等しいと判定される
    """
    assert DocumentId("uc-scaffold-document") == DocumentId("uc-scaffold-document")
    assert DocumentId("uc-scaffold-document") != DocumentId("uc-query-document")


def test_DocumentIdは不変():
    """
    Given DocumentId
    When フィールドを変更しようとする
    Then FrozenInstanceErrorが発生する
    """
    document_id = DocumentId("uc-scaffold-document")
    with pytest.raises(Exception):
        document_id.value = "other"  # type: ignore[misc]


def test_DocumentTypeは値が等しければ等価():
    """
    Given 同じ値を持つ2つのDocumentType
    When 等価性を比較する
    Then 等しいと判定される
    """
    assert DocumentType("DomainSpec") == DocumentType("DomainSpec")
    assert DocumentType("DomainSpec") != DocumentType("Skill")


def test_DiscriminatorValueは値が等しければ等価():
    """
    Given 同じ値を持つ2つのDiscriminatorValue
    When 等価性を比較する
    Then 等しいと判定される
    """
    assert DiscriminatorValue("usecase") == DiscriminatorValue("usecase")
    assert DiscriminatorValue("usecase") != DiscriminatorValue("aggregate")


def test_SchemaRefはnameとversionの組で識別される():
    """
    Given 同じname・versionを持つ2つのSchemaRef
    When 等価性を比較する
    Then 等しいと判定される
    """
    a = SchemaRef(name="DomainSpecSchema", version="v5")
    b = SchemaRef(name="DomainSpecSchema", version="v5")
    c = SchemaRef(name="DomainSpecSchema", version="v4")
    assert a == b
    assert a != c


def test_Statusは値が等しければ等価():
    """
    Given 同じ値を持つ2つのStatus
    When 等価性を比較する
    Then 等しいと判定される
    """
    assert Status("VALIDATED") == Status("VALIDATED")
    assert Status("VALIDATED") != Status("DRAFT")


def test_Documentは宣言された全属性を持つ():
    """
    Given agg-document.jsonが宣言する17属性を指定してDocumentを構築する
    When 各属性を参照する
    Then 全属性がそのまま保持されている
    """
    document = Document(
        document_id=DocumentId("uc-scaffold-document"),
        document_type=DocumentType("DomainSpec"),
        schema_ref=SchemaRef(name="DomainSpecSchema", version="v5"),
        status=Status("VALIDATED"),
        spec_kind=DiscriminatorValue("usecase"),
        coding_kind=None,
        skill_kind=None,
        agent_kind=None,
        template_kind=None,
        subdomain_ref=DocumentId("sd-document-management"),
        aggregate_ref=None,
        skill_ref=None,
        stack=None,
        created_at=None,
        updated_at=None,
        content={},
        tags=["context:waffle"],
    )
    assert document.document_id == DocumentId("uc-scaffold-document")
    assert document.spec_kind == DiscriminatorValue("usecase")
    assert document.tags == ["context:waffle"]
