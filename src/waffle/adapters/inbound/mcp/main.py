"""waffle MCP サーバ — inbound(driving) adapter（fastmcp）。

CLI と並ぶもう1つの front-door。各 engine(application use case) に outbound adapter を結線し、
MCP ツールとして公開する。返り値は dict（Ok→value / Err→{error, message}）。
engine Skill の InvocationSpec が指す MCP ツール（query_document 等）の実体。
"""
from __future__ import annotations

from fastmcp import FastMCP

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.jsonschema_validator import JsonSchemaValidator
from waffle.adapters.outbound.pydoclint_linter import PydoclintLinter
from waffle.adapters.outbound.python_ast_source_scanner import PythonAstSourceScanner
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.adapters.outbound.tree_sitter_class_extractor import TreeSitterClassExtractor
from waffle.application.usecases.check_scenario_drift import CheckScenarioDrift
from waffle.application.usecases.check_schema_version_drift import CheckSchemaVersionDrift
from waffle.application.usecases.check_spec_integrity import CheckSpecIntegrity
from waffle.application.usecases.check_operation_drift import CheckOperationDrift
from waffle.application.usecases.check_usecase_class_drift import CheckUsecaseClassDrift
from waffle.application.usecases.check_verification_gate import CheckVerificationGate
from waffle.application.usecases.check_aggregate_class_drift import CheckAggregateClassDrift
from waffle.application.usecases.check_domain_service_drift import CheckDomainServiceDrift
from waffle.application.usecases.lint_docstring import LintDocstring
from waffle.application.usecases.patch_schema import PatchSchema
from waffle.application.usecases.query_document import QueryDocument
from waffle.application.usecases.query_document_collection import QueryDocumentCollection
from waffle.application.usecases.render_blank_template import RenderBlankTemplate
from waffle.application.usecases.render_document import RenderDocument
from waffle.application.usecases.scaffold_document import ScaffoldDocument
from waffle.application.usecases.scan_source_code import ScanSourceCode
from waffle.application.usecases.validate_document import ValidateDocument
from waffle.shared.result import Ok, Result

mcp = FastMCP("waffle")

def _dict(result: Result) -> dict:
    if isinstance(result, Ok):
        return result.value
    return {"error": result.details[0] if result.details else "ERROR", "message": result.message}

def _docs() -> FsDocumentRepository:
    return FsDocumentRepository()

def _schemas() -> PackageSchemaRepository:
    return PackageSchemaRepository()

def _class_extractor() -> TreeSitterClassExtractor:
    return TreeSitterClassExtractor()

@mcp.tool
def query_document(
    operation: str,
    path: str,
    blockKey: str | None = None,
    arrayField: str | None = None,
    field: str | None = None,
    idField: str | None = None,
    idValue: str | None = None,
    key: str | None = None,
    value: str | None = None,
    pattern: str | None = None,
    start: int | None = None,
    end: int | None = None,
    fieldName: str | None = None,
    nestedField: str | None = None,
    targetSchemaRef: str | None = None,
    targetDiscriminator: dict | None = None,
) -> dict:
    """document.json へのセマンティック・クエリ（uc-query-document）。"""
    raw = {
        "blockKey": blockKey, "arrayField": arrayField, "field": field,
        "idField": idField, "idValue": idValue, "key": key, "value": value,
        "pattern": pattern, "start": start, "end": end,
        "fieldName": fieldName, "nestedField": nestedField,
        "targetSchemaRef": targetSchemaRef, "targetDiscriminator": targetDiscriminator,
    }
    params = {k: v for k, v in raw.items() if v is not None}
    return _dict(QueryDocument(_docs(), _schemas()).run(operation, path, params))

@mcp.tool
def query_document_collection(
    operation: str,
    path: str,
    pattern: str | None = None,
    field: str | None = None,
    key: str | None = None,
    value: str | None = None,
    fields: list[str] | None = None,
) -> dict:
    """複数document.jsonを横断するセマンティック・クエリ（uc-query-document-collection）。pathは対象ディレクトリ。"""
    raw = {"pattern": pattern, "field": field, "key": key, "value": value, "fields": fields}
    params = {k: v for k, v in raw.items() if v is not None}
    return _dict(QueryDocumentCollection(_docs(), _schemas()).run(operation, path, params))

@mcp.tool
def render_document(path: str, deploy: bool = True) -> dict:
    """document.json を成果物にレンダリングして deploy（uc-render-document）。"""
    return _dict(RenderDocument(_docs(), _schemas()).run(path, deploy=deploy))

@mcp.tool
def render_blank_template(schemaRef: str, discriminator: dict | None = None) -> dict:
    """schemaRefが宣言する値フィールドをx-prompt-write本文のプレースホルダーとして描画する（uc-render-blank-template）。"""
    return _dict(RenderBlankTemplate(_docs(), _schemas()).run(schemaRef, discriminator or {}))

@mcp.tool
def validate_document(path: str) -> dict:
    """document を schema 適合検証（uc-validate-document）。"""
    return _dict(ValidateDocument(_docs(), _schemas(), JsonSchemaValidator()).run(path))

@mcp.tool
def scaffold_document(
    operation: str,
    schemaRef: str | None = None,
    documentId: str | None = None,
    discriminator: dict | None = None,
    contextRef: str | None = None,
    subdomainRef: str | None = None,
    documentPath: str | None = None,
    values: dict | None = None,
    fieldPath: str | None = None,
) -> dict:
    """document.json の骨格生成 / 値書き込み / フィールド削除 / schemaRef移行（uc-scaffold-document）。operation: create / fill / clear_field / migrate_schema。"""
    if operation == "create":
        params: dict = {"schemaRef": schemaRef, "documentId": documentId}
        if discriminator:
            params["discriminator"] = discriminator
        if contextRef:
            params["contextRef"] = contextRef
        if subdomainRef:
            params["subdomainRef"] = subdomainRef
    elif operation == "fill":
        params = {"documentPath": documentPath, "values": values or {}}
    elif operation == "clear_field":
        params = {"documentPath": documentPath, "path": fieldPath}
    elif operation == "migrate_schema":
        params = {"documentPath": documentPath, "schemaRef": schemaRef}
    else:
        params = {}
    return _dict(ScaffoldDocument(_docs(), _schemas()).run(operation, params))

@mcp.tool
def patch_schema(operation: str, schemaRef: str, params: dict | None = None) -> dict:
    """Schema定義ファイル自体への構造化編集（uc-patch-schema）。operation: add_block / rename_block / set_field / remove_block / add_def / add_kind_branch / create_version。"""
    p = dict(params or {})
    p["schemaRef"] = schemaRef
    return _dict(PatchSchema(_docs(), _schemas(), JsonSchemaValidator()).run(operation, p))

@mcp.tool
def check_spec_integrity(path: str, documentsRoot: str = ".waffle/documents") -> dict:
    """bc.jsonのmembers宣言とディスク上の実ファイルの参照整合性を検証（uc-check-spec-integrity）。"""
    return _dict(CheckSpecIntegrity(_docs()).run(path, documentsRoot))

@mcp.tool
def check_scenario_drift(specPath: str, testPath: str) -> dict:
    """specのシナリオとテストコードの対応関係を検証（uc-check-scenario-drift）。"""
    return _dict(CheckScenarioDrift(_docs()).run(specPath, testPath))

@mcp.tool
def check_verification_gate(specPath: str, testPath: str, testResultsPath: str) -> dict:
    """実装完了→検証フェーズへ進んでよいかを判定（uc-check-verification-gate）。"""
    return _dict(CheckVerificationGate(_docs()).run(specPath, testPath, testResultsPath))

@mcp.tool
def check_schema_version_drift(documentsRoot: str = ".waffle/documents") -> dict:
    """DocumentのschemaRefが実在し最新であるかを検証（uc-check-schema-version-drift）。"""
    return _dict(CheckSchemaVersionDrift(_docs(), _schemas()).run(documentsRoot))

@mcp.tool
def check_usecase_class_drift(documentsRoot: str = ".waffle/documents", srcRoot: str = "src/waffle/application/usecases", language: str = "python") -> dict:
    """usecase specの操作名と実装クラス名が一致しているかを検証（uc-check-usecase-class-drift）。"""
    return _dict(CheckUsecaseClassDrift(_docs(), _class_extractor()).run(documentsRoot, srcRoot, language))

@mcp.tool
def check_aggregate_class_drift(documentsRoot: str = ".waffle/documents", srcRoot: str = "src/waffle/domain/entities", language: str = "python") -> dict:
    """aggregate specの集約ルート名と実装クラス名が一致しているかを検証（uc-check-aggregate-class-drift）。"""
    return _dict(CheckAggregateClassDrift(_docs(), _class_extractor()).run(documentsRoot, srcRoot, language))

@mcp.tool
def check_domain_service_drift(documentsRoot: str = ".waffle/documents", srcRoot: str = "src/waffle/domain/services") -> dict:
    """業務サービスのgroupと実装ファイルが一致しているかを検証（uc-check-domain-service-drift）。"""
    return _dict(CheckDomainServiceDrift(_docs()).run(documentsRoot, srcRoot))

@mcp.tool
def check_operation_drift(documentsRoot: str = ".waffle/documents", srcRoot: str = "src/waffle/application/usecases") -> dict:
    """usecase specが宣言するoperation名と実装のoperation分岐が一致しているかを検証（uc-check-operation-drift）。"""
    return _dict(CheckOperationDrift(_docs()).run(documentsRoot, srcRoot))

@mcp.tool
def scan_source_code(path: str, kind: str) -> dict | list:
    """対象コードベースの公開要素のdocstringを構造化抽出（uc-scan-source-code）。"""
    return _dict(ScanSourceCode(_docs(), PythonAstSourceScanner()).run(path, kind))

@mcp.tool
def lint_docstring(path: str, kind: str) -> dict | list:
    """対象コードベースのdocstringが規約どおりか既存lintツールで検証（uc-lint-docstring）。"""
    scan_engine = ScanSourceCode(_docs(), PythonAstSourceScanner())
    return _dict(LintDocstring(scan_engine, PydoclintLinter()).run(path, kind))
