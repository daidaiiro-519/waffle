"""共有の偽実装（tests/fakes.py）を fixture として配る。

偽実装の本体は tests/fakes.py にある。ここは pytest への配線だけを持つ。
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from waffle.adapters.outbound.schema_repo import PackageSchemaRepository

from tests.fakes import (
    CONTRACT_SCHEMA_NAME,
    CONTRACT_SCHEMA_REF,
    CONTRACT_SCHEMA_VERSION,
    MISSING_SCHEMA_REF,
    FakeSchemaRepository,
)


@pytest.fixture(params=["real", "fake"])
def schema_repository_case(request):
    """契約テスト用に、本物と偽実装を順に返す。

    どちらも CONTRACT_SCHEMA_REF を知っており、MISSING_SCHEMA_REF を知らない
    状態にそろえてある。契約テストはこの2点だけを前提に書く。

    Returns:
        repo（実装本体）・name・version・ref・missing を持つ名前空間。
        契約テスト側が偽実装の素性を知らずに済むよう、前提の値も同梱する。
    """
    if request.param == "real":
        repo = PackageSchemaRepository()
    else:
        repo = FakeSchemaRepository({CONTRACT_SCHEMA_REF: {"$id": CONTRACT_SCHEMA_REF}})
    return SimpleNamespace(
        repo=repo,
        name=CONTRACT_SCHEMA_NAME,
        version=CONTRACT_SCHEMA_VERSION,
        ref=CONTRACT_SCHEMA_REF,
        missing=MISSING_SCHEMA_REF,
    )
