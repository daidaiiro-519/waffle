"""waffle MCPサーバ（inbound adapter）の契約テスト（ネイティブpytest・fastmcp in-memory Client経由）。

CLIと並ぶ第2のfront-door。engineの振る舞いはtests/acceptance・tests/integrationが担保する。
ここは「MCPツール経由でengineが正しく呼ばれdictを返す」というMCP自体の公開インターフェース契約
だけを固定する（旧features/mcp.featureから移行）。
"""
import asyncio
import json
from pathlib import Path

from fastmcp import Client

from waffle.adapters.inbound.mcp.main import mcp

_PATCH_FIXTURE_DIR = Path("src/waffle/domain/model/TestMcpPatchSchemaFixture")
_PATCH_FIXTURE_PATH = _PATCH_FIXTURE_DIR / "v1.json"
_BLANK_TEMPLATE_PATH = Path(".waffle/templates/blank/CodingSchema/v2/coding-standard.md")


def teardown_function():
    _PATCH_FIXTURE_PATH.unlink(missing_ok=True)
    if _PATCH_FIXTURE_DIR.exists() and not any(_PATCH_FIXTURE_DIR.iterdir()):
        _PATCH_FIXTURE_DIR.rmdir()
    _BLANK_TEMPLATE_PATH.unlink(missing_ok=True)


async def _call(tool: str, args: dict):
    async with Client(mcp) as client:
        result = await client.call_tool(tool, args)
        return result.data


def test_query_documentはquery_pathでブロックを取得する():
    """
    Given waffle MCPサーバ
    When query_documentツールをoperation=query_path・blockKey・expression=@で呼ぶ
    Then MCP出力のvalue.blockTypeはResponseTypes
    """
    out = asyncio.run(_call("query_document", {
        "operation": "query_path",
        "path": ".waffle/documents/skills/tech-lead-advisor.json",
        "blockKey": "responseTypes",
        "expression": "@",
    }))
    assert out["value"]["blockType"] == "ResponseTypes"


def test_query_documentのエラーはerror_messageを返す():
    """
    Given waffle MCPサーバ
    When query_documentツールを未知のoperationで呼ぶ
    Then MCP出力のerrorはINVALID_OPERATION
    """
    out = asyncio.run(_call("query_document", {
        "operation": "bogus",
        "path": ".waffle/documents/skills/tech-lead-advisor.json",
    }))
    assert out["error"] == "INVALID_OPERATION"


def test_query_documentはresolve_refで参照先pathを返す():
    """
    Given waffle MCPサーバ
    When query_documentツールをoperation=resolve_refで呼ぶ
    Then MCP出力のvalue.pathは参照先Documentのpath
    """
    out = asyncio.run(_call("query_document", {
        "operation": "resolve_ref",
        "path": ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json",
        "field": "subdomainRef",
        "targetSchemaRef": "DomainSpecSchema/v5",
        "targetDiscriminator": {"specKind": "subdomain"},
    }))
    assert out["value"]["path"] == (
        ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/sd-document-management.json"
    )


def test_query_documentはquery_pathでblockKey指定時に単一ブロックの評価結果を返す():
    """
    Given waffle MCPサーバ
    When query_documentツールをoperation=query_path・blockKey・expressionで呼ぶ
    Then MCP出力のvalueはJMESPath評価結果、documentIdとpromptを含む
    """
    out = asyncio.run(_call("query_document", {
        "operation": "query_path",
        "path": ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json",
        "blockKey": "acceptanceScenarios",
        "expression": "scenarios[?category=='異常系']",
    }))
    assert out["documentId"] == "uc-query-document"
    assert out["prompt"]
    assert all(item["category"] == "異常系" for item in out["value"])


def test_query_documentはquery_pathでblockKey省略時にヒットしたブロックだけを返す():
    """
    Given waffle MCPサーバ
    When query_documentツールをoperation=query_path・expressionのみで呼ぶ（blockKey省略）
    Then MCP出力のresultsにヒットしたブロックだけが含まれる
    """
    out = asyncio.run(_call("query_document", {
        "operation": "query_path",
        "path": ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json",
        "expression": "scenarios[?category=='異常系']",
    }))
    assert any(r["blockKey"] == "acceptanceScenarios" for r in out["results"])


def test_query_document_collectionはgrep_documentsで横断検索する():
    """
    Given waffle MCPサーバ
    When query_document_collectionツールをoperation=grep_documentsで呼ぶ
    Then MCP出力のvalueにpatternへ一致したDocumentのpathが含まれる
    """
    out = asyncio.run(_call("query_document_collection", {
        "operation": "grep_documents",
        "path": ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase",
        "pattern": "resolve_ref",
    }))
    assert any("uc-query-document.json" in p for p in out["value"])


def test_validate_documentは適合でstatus判定を返す():
    """
    Given waffle MCPサーバ
    When validate_documentツールを呼ぶ
    Then MCP出力のstatusはdocumentのstatusをそのまま返す
    """
    out = asyncio.run(_call("validate_document", {
        "path": ".waffle/documents/skills/tech-lead-advisor.json",
    }))
    assert out["status"] == "ACTIVE"


def test_render_documentはmdフォーマットを返す():
    """
    Given waffle MCPサーバ
    When render_documentツールをdeploy=falseで呼ぶ
    Then MCP出力のformatはmd
    """
    out = asyncio.run(_call("render_document", {
        "path": ".waffle/documents/skills/tech-lead-advisor.json",
        "deploy": False,
    }))
    assert out["format"] == "md"


def test_render_handoff_templateはHTMLを生成する(tmp_path):
    """
    Given waffle MCPサーバ
    When render_handoff_templateツールをHandoffのpathで呼ぶ
    Then 出力先HTMLファイルが生成される
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

    out = asyncio.run(_call("render_handoff_template", {
        "path": str(handoff_path),
        "outputPath": str(output_path),
    }))
    assert out["path"] == str(output_path)
    assert output_path.read_text(encoding="utf-8")


def test_render_document_viewerはHTMLを生成する(tmp_path):
    """
    Given waffle MCPサーバ
    When render_document_viewerツールを既存Documentのpathで呼ぶ
    Then 出力先HTMLファイルが生成される
    """
    output_path = tmp_path / "viewer.html"
    out = asyncio.run(_call("render_document_viewer", {
        "path": ".waffle/documents/skills/tech-lead-advisor.json",
        "outputPath": str(output_path),
    }))
    assert out["path"] == str(output_path)
    assert output_path.read_text(encoding="utf-8")


def test_render_blank_templateはプレースホルダーMarkdownを返す():
    """
    Given waffle MCPサーバ
    When render_blank_templateツールをschemaRef=CodingSchema/v2で呼ぶ
    Then MCP出力のcontentに{{...}}形式のプレースホルダーが含まれる
    """
    out = asyncio.run(_call("render_blank_template", {
        "schemaRef": "CodingSchema/v2",
        "discriminator": {"codingKind": "coding-standard"},
    }))
    assert "{{" in out["content"]
    assert out["path"] == str(_BLANK_TEMPLATE_PATH)


def test_patch_schemaはadd_blockの結果をdictで返す():
    """
    Given waffle MCPサーバ
    When patch_schemaツールをoperation=add_blockで呼ぶ
    Then MCP出力のchangedはTrue
    """
    _PATCH_FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    _PATCH_FIXTURE_PATH.write_text(
        json.dumps({"$defs": {"SomeContent": {"type": "object", "required": [], "properties": {}}}}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    out = asyncio.run(_call("patch_schema", {
        "operation": "add_block",
        "schemaRef": "TestMcpPatchSchemaFixture/v1",
        "params": {
            "blockName": "NoteBlock",
            "blockDef": {"type": "object", "required": ["blockType"], "properties": {"blockType": {"type": "string", "const": "Note"}}},
            "contentDefName": "SomeContent",
            "propName": "note",
        },
    }))
    assert out["changed"] is True


def test_check_spec_integrityは10フィールドの差分結果を返す():
    """
    Given waffle MCPサーバ
    When check_spec_integrityツールをbc-waffle.jsonで呼ぶ
    Then MCP出力は10フィールド全て空配列（自己整合済み）
    """
    out = asyncio.run(_call("check_spec_integrity", {
        "path": ".waffle/documents/specs/bc-waffle/bc-waffle.json",
    }))
    assert out == {
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
    Given waffle MCPサーバ
    When check_schema_version_driftツールを呼ぶ
    Then MCP出力は3フィールド全て空配列（自己整合済み）
    """
    out = asyncio.run(_call("check_schema_version_drift", {}))
    assert out == {"broken_references": [], "newer_version_available": [], "missing_declared_fields": []}


def test_check_usecase_class_driftは2フィールドの差分結果を返す():
    """
    Given waffle MCPサーバ
    When check_usecase_class_driftツールを呼ぶ
    Then MCP出力は2フィールド全て空配列（自己整合済み）
    """
    out = asyncio.run(_call("check_usecase_class_drift", {}))
    assert out == {"missing_implementation_file": [], "class_name_mismatch": []}


def test_check_aggregate_class_driftは5フィールドの差分結果を返す():
    """
    Given waffle MCPサーバ
    When check_aggregate_class_driftツールを呼ぶ
    Then MCP出力は5フィールド全て空配列（Schema/Document両集約のEntity化が
    完了し自己整合済み）
    """
    out = asyncio.run(_call("check_aggregate_class_drift", {}))
    assert out == {
        "missing_implementation_file": [], "class_name_mismatch": [],
        "attribute_mismatch": [], "missing_value_object": [], "value_object_attribute_mismatch": [],
    }


def test_check_domain_service_driftは1フィールドの差分結果を返す():
    """
    Given waffle MCPサーバ
    When check_domain_service_driftツールを呼ぶ
    Then MCP出力は1フィールド空配列（自己整合済み）
    """
    out = asyncio.run(_call("check_domain_service_drift", {}))
    assert out == {"missing_implementation_file": []}


def test_check_operation_driftは2フィールドの差分結果を返す():
    """
    Given waffle MCPサーバ
    When check_operation_driftツールを呼ぶ
    Then MCP出力は2フィールド全て空配列（自己整合済み）
    """
    out = asyncio.run(_call("check_operation_drift", {}))
    assert out == {"operations_missing_in_impl": [], "operations_undocumented_in_spec": []}


def test_check_scenario_driftは4フィールドの差分結果を返す():
    """
    Given waffle MCPサーバ
    When check_scenario_driftツールを呼ぶ
    Then MCP出力は4フィールドを持つ
    """
    out = asyncio.run(_call("check_scenario_drift", {
        "specPath": ".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/usecase/uc-check-spec-integrity.json",
        "testPath": "tests/integration/test_uc_check_spec_integrity.py",
    }))
    assert set(out.keys()) == {"missing_in_tests", "orphaned_in_tests", "matched", "gherkin_mismatches"}


def test_check_verification_gateはstatusとreasonsを返す(tmp_path):
    """
    Given waffle MCPサーバ
    When check_verification_gateツールを呼ぶ
    Then MCP出力はstatus/reasonsを持つ
    """
    results_path = tmp_path / "results.json"
    results_path.write_text(json.dumps({"passed": [], "failed": []}), encoding="utf-8")

    out = asyncio.run(_call("check_verification_gate", {
        "specPath": ".waffle/documents/specs/bc-waffle/subdomain/sd-flow-gate/usecase/uc-check-verification-gate.json",
        "testPath": "tests/acceptance/test_uc_check_verification_gate.py",
        "testResultsPath": str(results_path),
    }))
    assert out["status"] == "ready"
    assert out["reasons"] == []


def test_scan_source_codeは公開要素の一覧を返す(tmp_path):
    """
    Given waffle MCPサーバ
    When scan_source_codeツールをkind=googleで呼ぶ
    Then MCP出力は要素の配列
    """
    sample = tmp_path / "sample.py"
    sample.write_text('def f():\n    """要約。"""\n    pass\n', encoding="utf-8")

    out = asyncio.run(_call("scan_source_code", {"path": str(tmp_path), "kind": "google"}))
    assert any(e["name"] == "f" for e in out)


def test_lint_docstringは違反の配列を返す(tmp_path):
    """
    Given waffle MCPサーバ
    When lint_docstringツールをkind=googleで呼ぶ
    Then MCP出力は違反の配列（適合すれば空配列）
    """
    sample = tmp_path / "sample.py"
    sample.write_text('def f():\n    """要約。"""\n    pass\n', encoding="utf-8")

    out = asyncio.run(_call("lint_docstring", {"path": str(tmp_path), "kind": "google"}))
    assert isinstance(out, list)
