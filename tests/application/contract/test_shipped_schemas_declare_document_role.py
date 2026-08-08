"""出荷する全schemaが documentRole を宣言していることの契約テスト。

documentRole は「その文書が実体（instance）か、他プロジェクトで実体化されるための
雛形（template）か」を表す、documentType と直交する軸。配置先の解決キーに含まれる
ため、特定のschemaにだけ在るとキーが揃わない。全schemaが同じ形で宣言することが
この軸の前提になる。

仕様のシナリオには対応しない、規約由来のテスト。
"""
from __future__ import annotations

import pytest

from waffle.adapters.outbound.schema_repo import PackageSchemaRepository

_SCHEMA_NAMES = [
    "AgentSchema",
    "CodingSchema",
    "DomainSpecSchema",
    "HandoffSchema",
    "HookSchema",
    "KnowledgeSchema",
    "PlatformSpec",
    "PresentationSpecSchema",
    "SkillSchema",
    "TemplateSchema",
]


def _latest_ref(repo: PackageSchemaRepository, name: str) -> str:
    versions = repo.list_versions(name)
    assert versions, f"{name} の版が1つも見つからない"
    latest = max(versions, key=lambda v: int(v.lstrip("v")))
    return f"{name}/{latest}"


@pytest.fixture
def repo() -> PackageSchemaRepository:
    return PackageSchemaRepository()


@pytest.mark.parametrize("name", _SCHEMA_NAMES)
def test_latest_schema_declares_document_role(repo, name):
    """最新版の各schemaが documentRole を properties に宣言している。"""
    schema = repo.load(_latest_ref(repo, name))
    assert "documentRole" in schema["properties"], f"{name} に documentRole が無い"


@pytest.mark.parametrize("name", _SCHEMA_NAMES)
def test_document_role_allows_instance_and_template(repo, name):
    """documentRole が取りうる値は instance と template の2つ。"""
    schema = repo.load(_latest_ref(repo, name))
    assert schema["properties"]["documentRole"]["enum"] == ["instance", "template"]


@pytest.mark.parametrize("name", _SCHEMA_NAMES)
def test_document_role_defaults_to_instance(repo, name):
    """宣言の無い既存documentは実体として扱われるよう、既定値は instance。"""
    schema = repo.load(_latest_ref(repo, name))
    assert schema["properties"]["documentRole"]["default"] == "instance"


@pytest.mark.parametrize("name", _SCHEMA_NAMES)
def test_document_role_is_not_required(repo, name):
    """既存documentを一斉に書き換えずに済むよう、必須にはしない。"""
    schema = repo.load(_latest_ref(repo, name))
    assert "documentRole" not in schema.get("required", [])


@pytest.mark.parametrize("name", _SCHEMA_NAMES)
def test_document_role_has_write_and_query_prompts(repo, name):
    """documentRoleは執筆・読解の指示を対で持つ。

    x-prompt-write が無い欄は scaffold fill の書き込み対象にならず、宣言しただけで
    値を入れられない欄になる。x-prompt-query はその値をどう読むかを運ぶ。
    """
    role = repo.load(_latest_ref(repo, name))["properties"]["documentRole"]
    assert role.get("x-prompt-write"), f"{name} の documentRole に x-prompt-write が無い"
    assert role.get("x-prompt-query"), f"{name} の documentRole に x-prompt-query が無い"
