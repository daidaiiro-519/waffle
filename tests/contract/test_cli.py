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
_BLANK_TEMPLATE_PATH = Path(".waffle/templates/blank/CodingSchema/v2/coding-standard.md")


def teardown_function():
    Path(_SCAFFOLD_DEMO_PATH).unlink(missing_ok=True)
    _PATCH_FIXTURE_PATH.unlink(missing_ok=True)
    if _PATCH_FIXTURE_DIR.exists() and not any(_PATCH_FIXTURE_DIR.iterdir()):
        _PATCH_FIXTURE_DIR.rmdir()
    _BLANK_TEMPLATE_PATH.unlink(missing_ok=True)


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


def test_queryはresolve_refで参照先pathを返す():
    """
    Given waffle CLI
    When query --operation resolve_ref ... を実行する
    Then 終了コードは0で、出力JSONのvalue.pathは参照先Documentのpath
    """
    result = _runner.invoke(app, [
        "query", "--operation", "resolve_ref",
        "--path", ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json",
        "--field", "subdomainRef",
        "--targetSchemaRef", "DomainSpecSchema/v5",
        "--targetDiscriminator", "specKind=subdomain",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["value"]["path"] == (
        ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/sd-document-management.json"
    )


def test_queryはquery_pathでblockKey指定時に単一ブロックの評価結果を返す():
    """
    Given waffle CLI
    When query --operation query_path --blockKey --expression を実行する
    Then 終了コードは0で、出力JSONのvalueはJMESPath評価結果、documentIdとpromptを含む
    """
    result = _runner.invoke(app, [
        "query", "--operation", "query_path",
        "--path", ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json",
        "--blockKey", "acceptanceScenarios",
        "--expression", "scenarios[?category=='異常系']",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["documentId"] == "uc-query-document"
    assert data["prompt"]
    assert all(item["category"] == "異常系" for item in data["value"])


def test_queryはquery_pathでblockKey省略時にヒットしたブロックだけを返す():
    """
    Given waffle CLI
    When query --operation query_path --expression を blockKey なしで実行する
    Then 終了コードは0で、出力JSONのresultsにヒットしたブロックだけが含まれる
    """
    result = _runner.invoke(app, [
        "query", "--operation", "query_path",
        "--path", ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json",
        "--expression", "scenarios[?category=='異常系']",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert any(r["blockKey"] == "acceptanceScenarios" for r in data["results"])


def test_queryはquery_pathの構文エラーでINVALID_JMESPATH_EXPRESSIONを返す():
    """
    Given waffle CLI
    When query --operation query_path に構文エラーのexpressionを渡す
    Then 終了コードは1で、出力JSONのerrorはINVALID_JMESPATH_EXPRESSION
    """
    result = _runner.invoke(app, [
        "query", "--operation", "query_path",
        "--path", ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json",
        "--blockKey", "acceptanceScenarios",
        "--expression", "scenarios[?",
    ])
    assert result.exit_code == 1, result.output
    data = json.loads(result.output)
    assert data["error"] == "INVALID_JMESPATH_EXPRESSION"


def test_query_collectionはgrep_documentsで横断検索する():
    """
    Given waffle CLI
    When query-collection --operation grep_documents ... を実行する
    Then 終了コードは0で、出力JSONのvalueにpatternへ一致したDocumentのpathが含まれる
    """
    result = _runner.invoke(app, [
        "query-collection", "--operation", "grep_documents",
        "--path", ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase",
        "--pattern", "resolve_ref",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert any("uc-query-document.json" in p for p in data["value"])


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


def test_render_handoff_templateはHTMLを生成する(tmp_path):
    """
    Given waffle CLI
    When render-handoff-template --path <Handoff> --outputPath <出力先> を実行する
    Then 終了コードは0で、出力先HTMLファイルが生成される
    """
    handoff = {
        "documentId": "handoff-uc-a", "documentType": "Handoff", "schemaRef": "HandoffSchema/v1",
        "content": {
            "title": {"blockType": "Title", "title": "対象usecaseの実装引き継ぎ：handoff-uc-a"},
            "specRef": {"blockType": "SpecRef", "title": "引き継ぎ元spec", "specRef": "uc-a"},
            "designViewpoints": {"blockType": "DesignViewpoints", "title": "設計観点", "items": []},
            "implementationViewpoints": {"blockType": "ImplementationViewpoints", "title": "実装観点", "items": []},
            "constraints": {"blockType": "Constraints", "title": "既知の制約・トレードオフ", "items": []},
            "completionImage": {
                "blockType": "CompletionImage", "title": "完成イメージ",
                "layers": [{"label": "コア", "description": "説明。", "nodes": [{"id": "a", "title": "A", "sub": "既存", "status": "existing"}]}],
                "relationships": [],
            },
        },
    }
    handoff_path = tmp_path / "handoff-uc-a.json"
    handoff_path.write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")
    output_path = tmp_path / "handoff-uc-a.html"

    result = _runner.invoke(app, [
        "render-handoff-template", "--path", str(handoff_path), "--outputPath", str(output_path),
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["path"] == str(output_path)
    assert output_path.read_text(encoding="utf-8")


def test_render_blank_templateはプレースホルダーMarkdownを返す():
    """
    Given waffle CLI
    When render-blank-template --schemaRef CodingSchema/v2 --discriminator codingKind=coding-standard を実行する
    Then 終了コードは0で、出力JSONのcontentに{{...}}形式のプレースホルダーが含まれる
    """
    result = _runner.invoke(app, [
        "render-blank-template", "--schemaRef", "CodingSchema/v2", "--discriminator", "codingKind=coding-standard",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "{{" in data["content"]
    assert data["path"] == str(_BLANK_TEMPLATE_PATH)


def test_validateは適合でstatus判定を返す():
    """
    Given waffle CLI
    When validateを実行する
    Then 終了コードは0で、出力JSONのstatusはdocumentのstatusをそのまま返す
    """
    result = _runner.invoke(app, [
        "validate", "--path", ".waffle/documents/skills/tech-lead-advisor.json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "ACTIVE"


def test_scaffold_createは骨格を返す():
    """
    Given waffle CLI
    When scaffold --operation create を実行する
    Then 終了コードは0で、出力JSONのskeleton.documentTypeはSkill
    """
    result = _runner.invoke(app, [
        "scaffold", "--operation", "create",
        "--schemaRef", "SkillSchema/v1", "--documentId", "scaffold-demo",
        "--discriminator", "skillKind=custom",
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


def test_check_aggregate_class_driftは5フィールドの差分結果を返す():
    """
    Given waffle CLI
    When check-aggregate-class-drift を実行する
    Then 終了コードは0で、出力JSONは5フィールド全て空配列（Schema/Document
    両集約のEntity化が完了し自己整合済み）
    """
    result = _runner.invoke(app, ["check-aggregate-class-drift"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == {
        "missing_implementation_file": [], "class_name_mismatch": [],
        "attribute_mismatch": [], "missing_value_object": [], "value_object_attribute_mismatch": [],
    }


def test_check_domain_service_driftは1フィールドの差分結果を返す():
    """
    Given waffle CLI
    When check-domain-service-drift を実行する
    Then 終了コードは0で、出力JSONは1フィールド空配列（自己整合済み）
    """
    result = _runner.invoke(app, ["check-domain-service-drift"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == {"missing_implementation_file": []}


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


def test_check_verification_gateはstatusとreasonsを返す(tmp_path):
    """
    Given waffle CLI
    When check-verification-gate --specPath --testPath --testResultsPath を実行する
    Then 終了コードは0で、出力JSONはstatus/reasonsを持つ
    """
    results_path = tmp_path / "results.json"
    results_path.write_text(json.dumps({"passed": [], "failed": []}), encoding="utf-8")

    result = _runner.invoke(app, [
        "check-verification-gate",
        "--specPath", ".waffle/documents/specs/bc-waffle/subdomain/sd-flow-gate/usecase/uc-check-verification-gate.json",
        "--testPath", "tests/acceptance/test_uc_check_verification_gate.py",
        "--testResultsPath", str(results_path),
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "ready"
    assert data["reasons"] == []


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


def test_check_query_precedes_array_fillはCLI経由でも直接呼び出しと同じ判定になる():
    """
    Given targetPathが"X.json"であり、hasArrayValueがtrueであり、queriedPathsに"X.json"が含まれていない
    When Pythonから直接CheckQueryPrecedesArrayFillを呼び出す
    Then 拒否判定が返る
    When 同じ入力をCLI経由（waffle check-query-precedes-array-fill）で呼び出す
    Then 同じ拒否判定が返る
    """
    from waffle.application.usecases.check_query_precedes_array_fill import CheckQueryPrecedesArrayFill

    direct = CheckQueryPrecedesArrayFill().run("X.json", True, [])
    assert direct.value["allowed"] is False

    result = _runner.invoke(app, [
        "check-query-precedes-array-fill",
        "--target-path", "X.json",
        "--has-array-value",
        "--queried-paths", "[]",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == direct.value


def test_check_path_is_projectionはCLI経由でも直接呼び出しと同じ判定になる():
    """
    Given 実体パスが".waffle/skills/ddd-advisor/SKILL.md"である
    When Pythonから直接CheckPathIsProjectionを呼び出す
    Then isProjection=trueが返る
    When 同じ入力をCLI経由（waffle check-path-is-projection）で呼び出す
    Then 同じ判定結果が返る
    """
    from waffle.adapters.outbound.fs import FsDocumentRepository
    from waffle.application.usecases.check_path_is_projection import CheckPathIsProjection

    direct = CheckPathIsProjection(FsDocumentRepository()).run(".waffle/skills/ddd-advisor/SKILL.md")
    assert direct.value["isProjection"] is True

    result = _runner.invoke(app, [
        "check-path-is-projection",
        "--resolved-path", ".waffle/skills/ddd-advisor/SKILL.md",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == direct.value
