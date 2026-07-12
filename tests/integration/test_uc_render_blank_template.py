"""uc-render-blank-template のguaranteeScenarios(operationGuaranteesと対)のうち、
リポジトリ解決契約(実schemaRef)に対応する統合テスト。
"""
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.render_blank_template import RenderBlankTemplate
from waffle.shared.result import Ok


def _engine() -> RenderBlankTemplate:
    return RenderBlankTemplate(PackageSchemaRepository())


def test_同じ入力なら同じ結果を返す():
    """
    Given 同一のschemaRef・discriminator
    When ブランクテンプレート描画を2回実行する
    Then 2回とも同じMarkdown文字列が返る
    """
    engine = _engine()
    first = engine.run("CodingSchema/v2", {"codingKind": "coding-standard"})
    second = engine.run("CodingSchema/v2", {"codingKind": "coding-standard"})

    assert isinstance(first, Ok), first
    assert isinstance(second, Ok), second
    assert first.value == second.value
