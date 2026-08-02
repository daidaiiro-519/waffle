"""SchemaRepository の契約テスト。

本物（PackageSchemaRepository）と偽実装（FakeSchemaRepository）の両方に
同じスイートを当て、両者が同じ契約を満たすことを確かめる。
どちらを渡されたかはテスト側から見えない。

仕様のシナリオには対応しない、規約由来のテスト。
"""
from __future__ import annotations

import pytest


def test_load_returns_schema_for_known_ref(schema_repository_case):
    """知っている schemaRef に対して schema を返す。"""
    case = schema_repository_case
    assert isinstance(case.repo.load(case.ref), dict)


def test_load_raises_for_unknown_ref(schema_repository_case):
    """知らない schemaRef に対して FileNotFoundError を送出する。"""
    case = schema_repository_case
    with pytest.raises(FileNotFoundError):
        case.repo.load(case.missing)


def test_list_versions_includes_known_version(schema_repository_case):
    """知っている schema の版が list_versions に現れる。"""
    case = schema_repository_case
    assert case.version in case.repo.list_versions(case.name)


def test_list_versions_returns_empty_for_unknown_name(schema_repository_case):
    """知らない name に対しては空配列を返す（例外にしない）。"""
    case = schema_repository_case
    assert case.repo.list_versions("NoSuchSchema") == []


def test_list_versions_agrees_with_load(schema_repository_case):
    """list_versions が返す版は、すべて load できる。

    list_versions と load が別々の情報源を持つと、片方だけが知っている版が生まれる。
    """
    case = schema_repository_case
    for version in case.repo.list_versions(case.name):
        assert isinstance(case.repo.load(f"{case.name}/{version}"), dict)


def test_resolve_path_returns_path_for_known_ref(schema_repository_case):
    """知っている schemaRef に対して .json で終わるパスを返す。"""
    case = schema_repository_case
    assert case.repo.resolve_path(case.ref).endswith(".json")


def test_resolve_path_raises_for_unknown_ref(schema_repository_case):
    """知らない schemaRef に対して FileNotFoundError を送出する。"""
    case = schema_repository_case
    with pytest.raises(FileNotFoundError):
        case.repo.resolve_path(case.missing)
