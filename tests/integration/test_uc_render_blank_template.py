"""uc-render-blank-template のguaranteeScenarios(operationGuaranteesと対)のうち、
リポジトリ解決契約(実schemaRef・実ファイル書き込み)に対応する統合テスト。
"""
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.render_blank_template import RenderBlankTemplate
from waffle.shared.result import Ok

_WRITTEN_PATH = Path(".waffle/templates/blank/CodingSchema/v2/coding-standard.md")


def teardown_function():
    _WRITTEN_PATH.unlink(missing_ok=True)


def _engine() -> RenderBlankTemplate:
    return RenderBlankTemplate(FsDocumentRepository(), PackageSchemaRepository())


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


def test_導出したパスへ実際にファイルを書き出す():
    """
    Given 実schemaRef・discriminator
    When ブランクテンプレート描画を実行する
    Then .waffle/templates/blank/CodingSchema/v2/coding-standard.md が実際に書き出され、返り値のcontentと一致する
    """
    result = _engine().run("CodingSchema/v2", {"codingKind": "coding-standard"})

    assert isinstance(result, Ok), result
    assert _WRITTEN_PATH.exists()
    assert _WRITTEN_PATH.read_text(encoding="utf-8") == result.value["content"]
