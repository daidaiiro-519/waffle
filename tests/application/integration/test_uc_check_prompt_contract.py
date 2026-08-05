"""uc-check-prompt-contract の操作保証テスト（ネイティブpytest、実schemaを使用）。

確かめるのは1回の結果ではなく、この操作が全体として守る約束。
"""
import copy

from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.check_prompt_contract import CheckPromptContract
from waffle.shared.result import Ok

_SCHEMA_REF = "DomainSpecSchema/v8"


def _engine() -> CheckPromptContract:
    return CheckPromptContract(PackageSchemaRepository())


def test_何度確かめても結果が変わらない():
    """
    Scenario: 何度確かめても結果が変わらない
    Given 同じスキーマ
    When 確認を2回続けて求める
    Then 2回目の結果は1回目と完全に同一である
    """
    first = _engine().run(_SCHEMA_REF)
    assert isinstance(first, Ok), first

    second = _engine().run(_SCHEMA_REF)

    assert isinstance(second, Ok), second
    assert second.value == first.value


def test_確かめてもスキーマは変わらない():
    """
    Scenario: 確かめてもスキーマは変わらない
    Given 指示の欠落があるスキーマ
    When 確認を求める
    Then スキーマの中身は確認の前後で一致する
    """
    schemas = PackageSchemaRepository()
    before = copy.deepcopy(schemas.load(_SCHEMA_REF))

    result = CheckPromptContract(schemas).run(_SCHEMA_REF)

    assert isinstance(result, Ok), result
    assert schemas.load(_SCHEMA_REF) == before
