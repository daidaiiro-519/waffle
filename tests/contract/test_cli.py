"""waffle CLI（inbound adapter）の契約テスト（ネイティブpytest・CliRunner経由）。

engineの振る舞いはtests/acceptance・tests/integrationが担保する。ここは「引数成型・
出力JSON整形・終了コード」というCLI自体の公開インターフェース契約だけを固定する
（旧features/cli.featureから移行。test-standardのtestTypes.contractはtool=pytestを
宣言しており、behaveとの不一致を解消した）。
"""
import json
from pathlib import Path

from typer.testing import CliRunner

from waffle.adapters.inbound.cli.main import app

_runner = CliRunner()
_SCAFFOLD_DEMO_PATH = ".waffle/documents/skills/scaffold-demo.json"
_PATCH_FIXTURE_DIR = Path("src/waffle/domain/model/TestCliPatchSchemaFixture")
_PATCH_FIXTURE_PATH = _PATCH_FIXTURE_DIR / "v1.json"


def teardown_function():
    Path(_SCAFFOLD_DEMO_PATH).unlink(missing_ok=True)
    _PATCH_FIXTURE_PATH.unlink(missing_ok=True)
    if _PATCH_FIXTURE_DIR.exists() and not any(_PATCH_FIXTURE_DIR.iterdir()):
        _PATCH_FIXTURE_DIR.rmdir()


def test_queryはブロックを取得しvalueをJSONで返す():
    """
    Given waffle CLI
    When query --operation get_block --path ... --blockKey responseTypes を実行する
    Then 終了コードは0で、出力JSONのvalue.blockTypeはResponseTypes
    """
    result = _runner.invoke(app, [
        "query", "--operation", "get_block",
        "--path", ".waffle/documents/skills/tech-lead-advisor.json",
        "--blockKey", "responseTypes",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["value"]["blockType"] == "ResponseTypes"


def test_queryのエラーはerror_messageと非ゼロ終了で返す():
    """
    Given waffle CLI
    When 未知のoperationを実行する
    Then 終了コードは1で、出力JSONのerrorはINVALID_OPERATION
    """
    result = _runner.invoke(app, [
        "query", "--operation", "bogus",
        "--path", ".waffle/documents/skills/tech-lead-advisor.json",
    ])
    assert result.exit_code == 1, result.output
    data = json.loads(result.output)
    assert data["error"] == "INVALID_OPERATION"


def test_render_no_deployはmdフォーマットを返す():
    """
    Given waffle CLI
    When render --no-deploy を実行する
    Then 終了コードは0で、出力JSONのformatはmd
    """
    result = _runner.invoke(app, [
        "render", "--path", ".waffle/documents/skills/tech-lead-advisor.json", "--no-deploy",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["format"] == "md"


def test_validateは適合でstatus判定を返す():
    """
    Given waffle CLI
    When validateを実行する
    Then 終了コードは0で、出力JSONのstatusはDRAFT
    """
    result = _runner.invoke(app, [
        "validate", "--path", ".waffle/documents/skills/tech-lead-advisor.json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "DRAFT"


def test_scaffold_createは骨格を返す():
    """
    Given waffle CLI
    When scaffold --operation create を実行する
    Then 終了コードは0で、出力JSONのskeleton.documentTypeはSkill
    """
    result = _runner.invoke(app, [
        "scaffold", "--operation", "create",
        "--schemaRef", "SkillSchema/v1", "--documentId", "scaffold-demo",
        "--discriminator", "skillKind=engine",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["skeleton"]["documentType"] == "Skill"


def test_check_spec_integrityは10フィールドの差分結果を返す():
    """
    Given waffle CLI
    When check-spec-integrity --path bc-waffle.json を実行する
    Then 終了コードは0で、出力JSONは10フィールド全て空配列（自己整合済み）
    """
    result = _runner.invoke(app, [
        "check-spec-integrity",
        "--path", ".waffle/documents/specs/bc-waffle/bc-waffle.json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == {
        "declared_subdomains_missing_on_disk": [],
        "subdomains_on_disk_not_declared_in_bc": [],
        "usecases_orphaned_no_subdomain": [],
        "usecases_in_subdomain_not_declared_in_bc": [],
        "usecase_files_missing_on_disk": [],
        "usecase_files_orphaned_on_disk": [],
        "orphaned_value_objects": [],
        "undeclared_document_fields": [],
        "subdomain_ref_mismatches": [],
        "missing_aggregate_refs": [],
    }


def test_check_schema_version_driftは3フィールドの差分結果を返す():
    """
    Given waffle CLI
    When check-schema-version-drift を実行する
    Then 終了コードは0で、出力JSONは3フィールド全て空配列（自己整合済み）
    """
    result = _runner.invoke(app, ["check-schema-version-drift"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == {"broken_references": [], "newer_version_available": [], "missing_declared_fields": []}


def test_check_usecase_class_driftは2フィールドの差分結果を返す():
    """
    Given waffle CLI
    When check-usecase-class-drift を実行する
    Then 終了コードは0で、出力JSONは2フィールド全て空配列（自己整合済み）
    """
    result = _runner.invoke(app, ["check-usecase-class-drift"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == {"missing_implementation_file": [], "class_name_mismatch": []}


def test_check_aggregate_class_driftは4フィールドの差分結果を返す():
    """
    Given waffle CLI
    When check-aggregate-class-drift を実行する
    Then 終了コードは0で、出力JSONは4フィールドを持つ（集約Entityクラスは
    Document集約のみまだ未実装のため、現時点ではmissing_implementation_file
    にDocument集約が列挙される。Entity化のパイロットが進むごとにこの期待値を
    更新する）
    """
    result = _runner.invoke(app, ["check-aggregate-class-drift"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert {m["documentId"] for m in data["missing_implementation_file"]} == {"agg-document"}
    assert data["class_name_mismatch"] == []
    assert data["attribute_mismatch"] == []
    assert data["missing_value_object"] == []


def test_check_operation_driftは2フィールドの差分結果を返す():
    """
    Given waffle CLI
    When check-operation-drift を実行する
    Then 終了コードは0で、出力JSONは2フィールド全て空配列（自己整合済み）
    """
    result = _runner.invoke(app, ["check-operation-drift"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == {"operations_missing_in_impl": [], "operations_undocumented_in_spec": []}


def test_check_scenario_driftは4フィールドの差分結果を返す():
    """
    Given waffle CLI
    When check-scenario-drift --specPath --testPath を実行する
    Then 終了コードは0で、出力JSONは4フィールドを持つ
    """
    result = _runner.invoke(app, [
        "check-scenario-drift",
        "--specPath", ".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/usecase/uc-check-spec-integrity.json",
        "--testPath", "tests/integration/test_uc_check_spec_integrity.py",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert set(data.keys()) == {"missing_in_tests", "orphaned_in_tests", "matched", "gherkin_mismatches"}


def test_scan_source_codeは公開要素の一覧を返す(tmp_path):
    """
    Given waffle CLI
    When scan-source-code --path --kind google を実行する
    Then 終了コードは0で、出力JSONは要素の配列
    """
    sample = tmp_path / "sample.py"
    sample.write_text('def f():\n    """要約。"""\n    pass\n', encoding="utf-8")

    result = _runner.invoke(app, [
        "scan-source-code", "--path", str(tmp_path), "--kind", "google",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert any(e["name"] == "f" for e in data)


def test_patch_schemaはadd_blockの結果をJSONで返す():
    """
    Given waffle CLI
    When patch-schema --operation add_block --schemaRef ... --params '{...}' を実行する
    Then 終了コードは0で、出力JSONのchangedはtrue
    """
    _PATCH_FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    _PATCH_FIXTURE_PATH.write_text(
        json.dumps({"$defs": {"SomeContent": {"type": "object", "required": [], "properties": {}}}}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    result = _runner.invoke(app, [
        "patch-schema", "--operation", "add_block",
        "--schemaRef", "TestCliPatchSchemaFixture/v1",
        "--params", json.dumps({
            "blockName": "NoteBlock",
            "blockDef": {"type": "object", "required": ["blockType"], "properties": {"blockType": {"type": "string", "const": "Note"}}},
            "contentDefName": "SomeContent",
            "propName": "note",
        }),
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["changed"] is True


def test_lint_docstringは違反の配列を返す(tmp_path):
    """
    Given waffle CLI
    When lint-docstring --path --kind google を実行する
    Then 終了コードは0で、出力JSONは違反の配列（適合すれば空配列）
    """
    sample = tmp_path / "sample.py"
    sample.write_text('def f():\n    """要約。"""\n    pass\n', encoding="utf-8")

    result = _runner.invoke(app, [
        "lint-docstring", "--path", str(tmp_path), "--kind", "google",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert isinstance(data, list)
