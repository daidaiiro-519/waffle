"""uc-check-surface-drift の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.python_ast_surface_extractor import PythonAstSurfaceExtractor
from waffle.application.usecases.check_surface_drift import CheckSurfaceDrift
from waffle.shared.result import Ok


def _engine() -> CheckSurfaceDrift:
    return CheckSurfaceDrift(FsDocumentRepository(), PythonAstSurfaceExtractor())


def _write_spec(root: Path, document_id: str, operation_name: str,
                inputs: list[str] | None,
                descriptions: dict[str, str] | None = None) -> None:
    content = {
        "usecase": {"blockType": "Usecase", "title": "名前",
                    "operationName": operation_name},
    }
    if inputs is not None:
        described = descriptions or {}
        content["inputs"] = {
            "blockType": "Inputs", "title": "入力",
            "items": [{"name": n, "description": described.get(n, f"{n}の説明")}
                      for n in inputs],
        }
    path = root / "usecase" / f"{document_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "documentId": document_id, "specKind": "usecase", "content": content,
    }, ensure_ascii=False), encoding="utf-8")


def _write_surface(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_declared_input_missing_from_surface(tmp_path):
    """
    Scenario: 宣言された入力が口に無いことを見つける
    Given ある入力を宣言しているユースケース仕様
    And その入力を受け取らない口
    When 受け口の食い違いを調べる
    Then その組が missing_input に現れる
    And どの口の話かが報告に含まれている
    """
    docs = tmp_path / "documents"
    _write_spec(docs, "uc-a", "DoSomething", ["対象の道"])
    surface = tmp_path / "cli.py"
    _write_surface(surface, "def run_it() -> None:\n    DoSomething().run()\n")

    result = _engine().run(str(docs), [str(surface)])
    assert isinstance(result, Ok), result
    assert result.value["missing_input"] == [
        {"documentId": "uc-a", "operationName": "DoSomething",
         "inputName": "対象の道", "surfacePath": str(surface)}
    ]
    assert result.value["undeclared_input"] == []


def test_surface_takes_undeclared_input(tmp_path):
    """
    Scenario: 宣言に無い入力を口が受け取っていることを見つける
    Given 入力を1つだけ宣言しているユースケース仕様
    And 宣言に無い入力も受け取る口
    When 受け口の食い違いを調べる
    Then その組が undeclared_input に現れる
    """
    docs = tmp_path / "documents"
    _write_spec(docs, "uc-a", "DoSomething", ["path"])
    surface = tmp_path / "cli.py"
    _write_surface(surface,
                   "def run_it(path: str, extra: str) -> None:\n"
                   "    DoSomething().run(path, extra)\n")

    result = _engine().run(str(docs), [str(surface)])
    assert isinstance(result, Ok), result
    assert result.value["undeclared_input"] == [
        {"documentId": "uc-a", "operationName": "DoSomething",
         "inputName": "extra", "surfacePath": str(surface)}
    ]
    assert result.value["missing_input"] == []


def test_spelling_differences_are_treated_as_the_same_input(tmp_path):
    """
    Scenario: 綴りが違っても同じ入力とみなす
    Given 区切り記号つきの綴りで入力を受け取る口
    And 大文字区切りの綴りで同じ入力を受け取る別の口
    When 受け口の食い違いを調べる
    Then どちらも宣言と一致したものとして扱われる
    And 2つの一覧は空のままである
    """
    docs = tmp_path / "documents"
    _write_spec(docs, "uc-a", "DoSomething", ["documents_root"])
    snake = tmp_path / "cli.py"
    camel = tmp_path / "mcp.py"
    _write_surface(snake, "def run_it(documents_root: str) -> None:\n"
                          "    DoSomething().run(documents_root)\n")
    _write_surface(camel, "def run_it(documentsRoot: str) -> None:\n"
                          "    DoSomething().run(documentsRoot)\n")

    result = _engine().run(str(docs), [str(snake), str(camel)])
    assert isinstance(result, Ok), result
    assert result.value["missing_input"] == []
    assert result.value["undeclared_input"] == []


def test_usecase_without_declared_inputs_is_skipped(tmp_path):
    """
    Scenario: 入力を宣言していないユースケースは対象外
    Given 入力を1つも宣言していないユースケース仕様
    And その操作を差し出す口
    When 受け口の食い違いを調べる
    Then そのユースケースは2つの一覧のどちらにも現れない
    """
    docs = tmp_path / "documents"
    _write_spec(docs, "uc-a", "DoSomething", None)
    surface = tmp_path / "cli.py"
    _write_surface(surface, "def run_it(whatever: str) -> None:\n"
                            "    DoSomething().run(whatever)\n")

    result = _engine().run(str(docs), [str(surface)])
    assert isinstance(result, Ok), result
    assert result.value["missing_input"] == []
    assert result.value["undeclared_input"] == []


def test_all_surfaces_agree_returns_empty(tmp_path):
    """
    Scenario: 全て揃っていれば空を返す
    Given 全ての口が宣言どおりの入力を見せている状態
    When 受け口の食い違いを調べる
    Then missing_input と undeclared_input はどちらも空である
    """
    docs = tmp_path / "documents"
    _write_spec(docs, "uc-a", "DoSomething", ["path", "language"])
    surface = tmp_path / "cli.py"
    _write_surface(surface,
                   "def run_it(path: str, language: str) -> None:\n"
                   '    """配線。\n\n'
                   "    Args:\n"
                   "        path: pathの説明\n"
                   "        language: languageの説明\n"
                   '    """\n'
                   "    DoSomething().run(path, language)\n")

    result = _engine().run(str(docs), [str(surface)])
    assert isinstance(result, Ok), result
    assert result.value == {"missing_input": [], "undeclared_input": [],
                            "description_mismatch": []}


def test_description_differs_from_declaration(tmp_path):
    """
    Scenario: 説明が宣言とずれていることを見つける
    Given ある入力の説明を宣言しているユースケース仕様
    And その入力に別の説明を見せている口
    When 受け口の食い違いを調べる
    Then その組が description_mismatch に現れる
    And 宣言された説明と口が見せている説明の両方が報告に含まれている
    """
    docs = tmp_path / "documents"
    _write_spec(docs, "uc-a", "DoSomething", ["path"], {"path": "対象の置き場所"})
    surface = tmp_path / "cli.py"
    _write_surface(surface,
                   "import typer\n"
                   'def run_it(path: str = typer.Option(..., "--path", help="古い説明")) -> None:\n'
                   "    DoSomething().run(path)\n")

    result = _engine().run(str(docs), [str(surface)])
    assert isinstance(result, Ok), result
    assert result.value["description_mismatch"] == [
        {"documentId": "uc-a", "operationName": "DoSomething", "inputName": "path",
         "declared": "対象の置き場所", "shown": "古い説明", "surfacePath": str(surface)}
    ]


def test_surface_shows_no_description(tmp_path):
    """
    Scenario: 口が説明を見せていないことを見つける
    Given ある入力の説明を宣言しているユースケース仕様
    And その入力に説明を持たない口
    When 受け口の食い違いを調べる
    Then その組が description_mismatch に現れる
    """
    docs = tmp_path / "documents"
    _write_spec(docs, "uc-a", "DoSomething", ["path"], {"path": "対象の置き場所"})
    surface = tmp_path / "cli.py"
    _write_surface(surface, "def run_it(path: str) -> None:\n"
                            "    DoSomething().run(path)\n")

    result = _engine().run(str(docs), [str(surface)])
    assert isinstance(result, Ok), result
    assert result.value["description_mismatch"] == [
        {"documentId": "uc-a", "operationName": "DoSomething", "inputName": "path",
         "declared": "対象の置き場所", "shown": "", "surfacePath": str(surface)}
    ]


def test_matching_description_is_not_reported(tmp_path):
    """
    Scenario: 説明が一致していれば報告しない
    Given ある入力の説明を宣言しているユースケース仕様
    And 同じ説明を見せている口
    When 受け口の食い違いを調べる
    Then description_mismatch は空である
    """
    docs = tmp_path / "documents"
    _write_spec(docs, "uc-a", "DoSomething", ["path"], {"path": "対象の置き場所"})
    surface = tmp_path / "cli.py"
    _write_surface(surface,
                   "def run_it(path: str) -> None:\n"
                   '    """配線。\n\n'
                   "    Args:\n"
                   "        path: 対象の置き場所\n"
                   '    """\n'
                   "    DoSomething().run(path)\n")

    result = _engine().run(str(docs), [str(surface)])
    assert isinstance(result, Ok), result
    assert result.value["description_mismatch"] == []
