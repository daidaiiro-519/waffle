"""agg-schema（Schema集約）のEntity/ValueObjectに対応するネイティブテスト。

agg-schema.jsonのEntities/ValueObjectsブロックが既に集約の仕様であり、ここでは
そこで宣言された構造（schemaId/version/kindProfiles、および各ValueObjectの
不変性・値による等価性）がPython実装として成立していることを検証する。
"""
import pytest

from waffle.domain.entities.schema import KindProfile, Schema, SchemaId, Version


def test_SchemaIdは値が等しければ等価():
    """
    Given 同じ値を持つ2つのSchemaId
    When 等価性を比較する
    Then 等しいと判定される
    """
    assert SchemaId("CodingSchema") == SchemaId("CodingSchema")
    assert SchemaId("CodingSchema") != SchemaId("KnowledgeSchema")


def test_SchemaIdは不変():
    """
    Given SchemaId
    When フィールドを変更しようとする
    Then FrozenInstanceErrorが発生する
    """
    schema_id = SchemaId("CodingSchema")
    with pytest.raises(Exception):
        schema_id.value = "Other"  # type: ignore[misc]


def test_Versionは値が等しければ等価():
    """
    Given 同じ値を持つ2つのVersion
    When 等価性を比較する
    Then 等しいと判定される
    """
    assert Version("v2") == Version("v2")
    assert Version("v2") != Version("v1")


def test_KindProfileは名前と必須ブロック集合の組で識別される():
    """
    Given 同じname・required_blocksを持つ2つのKindProfile
    When 等価性を比較する
    Then 等しいと判定される
    """
    a = KindProfile(name="usecase", required_blocks=frozenset({"title", "summary"}))
    b = KindProfile(name="usecase", required_blocks=frozenset({"title", "summary"}))
    c = KindProfile(name="aggregate", required_blocks=frozenset({"title", "summary"}))
    assert a == b
    assert a != c


def test_Schemaはschema_id_version_kind_profilesを持つ():
    """
    Given schemaId・version・kindProfilesを指定してSchemaを構築する
    When 各属性を参照する
    Then agg-schema.jsonが宣言する3属性がそのまま保持されている
    """
    schema = Schema(
        schema_id=SchemaId("CodingSchema"),
        version=Version("v2"),
        kind_profiles=(KindProfile(name="tech-stack", required_blocks=frozenset({"title"})),),
    )
    assert schema.schema_id == SchemaId("CodingSchema")
    assert schema.version == Version("v2")
    assert schema.kind_profiles == (KindProfile(name="tech-stack", required_blocks=frozenset({"title"})),)
