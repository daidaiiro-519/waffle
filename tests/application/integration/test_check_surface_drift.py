"""uc-check-surface-drift の操作保証テスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.python_ast_surface_extractor import PythonAstSurfaceExtractor
from waffle.application.usecases.check_surface_drift import CheckSurfaceDrift
from waffle.shared.result import Ok


def _engine() -> CheckSurfaceDrift:
    return CheckSurfaceDrift(FsDocumentRepository(), PythonAstSurfaceExtractor())


def _prepare(tmp_path: Path) -> tuple[Path, Path]:
    docs = tmp_path / "documents"
    spec = docs / "usecase" / "uc-a.json"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(json.dumps({
        "documentId": "uc-a", "specKind": "usecase",
        "content": {
            "usecase": {"blockType": "Usecase", "title": "名前",
                        "operationName": "DoSomething"},
            "inputs": {"blockType": "Inputs", "title": "入力",
                       "items": [{"name": "path", "description": "対象の道"}]},
        },
    }, ensure_ascii=False), encoding="utf-8")
    surface = tmp_path / "cli.py"
    surface.write_text("def run_it(other: str) -> None:\n"
                       "    DoSomething().run(other)\n", encoding="utf-8")
    return docs, surface


def test_checking_does_not_modify_anything(tmp_path):
    """
    Scenario: 調べても何も書き換えない
    Given 食い違いを含む仕様と口
    When 受け口の食い違いを調べる
    Then 仕様の中身は調べる前と同じである
    And 口の中身も調べる前と同じである
    """
    docs, surface = _prepare(tmp_path)
    spec_path = docs / "usecase" / "uc-a.json"
    before_spec = spec_path.read_text(encoding="utf-8")
    before_surface = surface.read_text(encoding="utf-8")

    result = _engine().run(str(docs), [str(surface)])
    assert isinstance(result, Ok), result

    assert spec_path.read_text(encoding="utf-8") == before_spec
    assert surface.read_text(encoding="utf-8") == before_surface


def test_repeated_checks_return_the_same_result(tmp_path):
    """
    Scenario: 繰り返し調べても同じ結果になる
    Given 食い違いを含む仕様と口
    When 受け口の食い違いを続けて2回調べる
    Then 2回の結果は同じである
    """
    docs, surface = _prepare(tmp_path)

    first = _engine().run(str(docs), [str(surface)])
    second = _engine().run(str(docs), [str(surface)])
    assert isinstance(first, Ok), first
    assert isinstance(second, Ok), second
    assert first.value == second.value
