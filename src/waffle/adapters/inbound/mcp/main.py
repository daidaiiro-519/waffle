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
from waffle.adapters.outbound.tree_sitter_test_function_extractor import (
    TreeSitterTestFunctionExtractor,
)
from waffle.adapters.outbound.coding_preset_repo import PackageCodingPresetRepository
from waffle.application.usecases.check_path_is_projection import CheckPathIsProjection
from waffle.application.usecases.check_query_precedes_array_fill import (
    CheckQueryPrecedesArrayFill,
)
from waffle.application.usecases.check_scenario_drift import CheckScenarioDrift
from waffle.application.usecases.init_coding_preset import InitCodingPreset
from waffle.application.usecases.update_coding_preset import UpdateCodingPreset
from waffle.application.usecases.check_prompt_contract import CheckPromptContract
from waffle.application.usecases.check_schema_version_drift import CheckSchemaVersionDrift
from waffle.application.usecases.check_spec_integrity import CheckSpecIntegrity
from waffle.application.usecases.check_operation_drift import CheckOperationDrift
from waffle.application.usecases.check_usecase_class_drift import CheckUsecaseClassDrift
from waffle.application.usecases.check_verification_gate import CheckVerificationGate
from waffle.application.usecases.check_aggregate_class_drift import CheckAggregateClassDrift
from waffle.application.usecases.check_domain_service_drift import CheckDomainServiceDrift
from waffle.application.usecases.check_layer_drift import CheckLayerDrift
from waffle.adapters.outbound.tree_sitter_import_extractor import TreeSitterImportExtractor
from waffle.application.usecases.lint_docstring import LintDocstring
from waffle.application.usecases.patch_schema import PatchSchema
from waffle.application.usecases.query_document import QueryDocument
from waffle.application.usecases.query_document_collection import QueryDocumentCollection
from waffle.application.usecases.render_blank_template import RenderBlankTemplate
from waffle.application.usecases.render_document import RenderDocument
from waffle.application.usecases.render_handoff_template import RenderHandoffTemplate
from waffle.application.usecases.render_document_viewer import RenderDocumentViewer
from waffle.application.usecases.scaffold_document import ScaffoldDocument
from waffle.application.usecases.scan_source_code import ScanSourceCode
from waffle.application.usecases.validate_document import ValidateDocument
from waffle.application.services.source_root_resolution import (
    resolve_directory_scoped_root,
    resolve_search_unit,
    resolve_src_root,
)
from waffle.application.services.stack_resolution import (
    resolve_covered_documents_root,
    resolve_naming,
    resolve_scenario_binding,
)
from waffle.shared.result import Err, Ok, Result

mcp = FastMCP("waffle")

def _dict(result: Result) -> dict:
    if isinstance(result, Ok):
        return result.value
    return {"error": result.details[0] if result.details else "ERROR", "message": result.message}

def _docs() -> FsDocumentRepository:
    return FsDocumentRepository()

def _schemas() -> PackageSchemaRepository:
    return PackageSchemaRepository()

def _resolve_src_root(src_root: str | None, architecture_ref: str | None, concept: str) -> str | dict:
    """配置ルートの解決を application へ委ね、失敗ならエラーdictへ翻訳する。"""
    result = resolve_src_root(_docs(), src_root, architecture_ref, concept)
    if isinstance(result, Err):
        return {"error": result.details[0], "message": result.message}
    return result.value

def _class_extractor() -> TreeSitterClassExtractor:
    return TreeSitterClassExtractor()

def _resolve_naming(architecture_ref: str | None) -> dict:
    """命名規約の解決を application へ委ね、失敗ならエラーdictへ翻訳する。"""
    if not architecture_ref:
        return {"error": "MISSING_PARAM",
                "message": "命名規約を引くために architectureRef が必要です"}
    result = resolve_naming(_docs(), architecture_ref)
    if isinstance(result, Err):
        return {"error": result.details[0], "message": result.message}
    return result.value


def _resolve_binding(architecture_ref: str | None) -> dict:
    """シナリオ照合の規約を application へ委ね、失敗ならエラーdictへ翻訳する。"""
    if not architecture_ref:
        return {"error": "MISSING_PARAM",
                "message": "シナリオ照合の規約を引くために architectureRef が必要です"}
    result = resolve_scenario_binding(_docs(), architecture_ref)
    if isinstance(result, Err):
        return {"error": result.details[0], "message": result.message}
    return result.value


def _resolve_documents_root(documents_root: str | None, architecture_ref: str | None):
    """仕様側の走査範囲を決める。明示指定が無ければ規約の宣言から決める。"""
    if documents_root:
        return documents_root
    if not architecture_ref:
        return {"error": "MISSING_PARAM",
                "message": "documentsRoot または architectureRef のいずれかが必要です"}
    result = resolve_covered_documents_root(_docs(), architecture_ref)
    if isinstance(result, Err):
        return {"error": result.details[0], "message": result.message}
    return result.value


@mcp.tool(description="document.json へのセマンティック・クエリ（uc-query-document）。")
def query_document(
    operation: str,
    path: str,
    blockKey: str | None = None,
    field: str | None = None,
    fieldName: str | None = None,
    targetSchemaRef: str | None = None,
    targetDiscriminator: dict | None = None,
    expression: str | None = None,
) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        operation: documentに対して行う読み取りの種類
        path: 読み取る対象のdocumentの置き場所
        blockKey: 読み取る対象を1つのブロックへ絞るときの、そのブロックの識別子
        field: 読み取る対象を1つの欄へ絞るときの、その欄の名前
        fieldName: 欄そのものではなく、欄の名前で探すときの手がかり
        targetSchemaRef: 読み取りの解釈に使うschemaを、documentの宣言とは別に指定する参照
        targetDiscriminator: key=value 形式（例: specKind=subdomain）
        expression: query_path用のJMESPath式（1ブロックの内側を起点とした相対式）。document.json自体のパスは--pathのため別名にしている

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    raw = {
        "blockKey": blockKey, "field": field,
        "fieldName": fieldName,
        "targetSchemaRef": targetSchemaRef, "targetDiscriminator": targetDiscriminator,
        "expression": expression,
    }
    params = {k: v for k, v in raw.items() if v is not None}
    return _dict(QueryDocument(_docs(), _schemas()).run(operation, path, params))

@mcp.tool(description="複数document.jsonを横断するセマンティック・クエリ（uc-query-document-collection）。pathは対象ディレクトリ。")
def query_document_collection(
    operation: str,
    path: str,
    pattern: str | None = None,
    field: str | None = None,
    key: str | None = None,
    value: str | None = None,
    fields: list[str] | None = None,
) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        operation: 複数のdocumentをまたいで行う読み取りの種類
        path: 対象ディレクトリ
        pattern: 対象とするdocumentを絞り込む道の形
        field: 各documentから取り出す欄の名前
        key: 絞り込みに使う欄の名前
        value: その欄が取るべき値
        fields: カンマ区切りのフィールド名一覧

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    raw = {"pattern": pattern, "field": field, "key": key, "value": value, "fields": fields}
    params = {k: v for k, v in raw.items() if v is not None}
    return _dict(QueryDocumentCollection(_docs(), _schemas()).run(operation, path, params))

@mcp.tool(description="document.json を成果物にレンダリングして deploy（uc-render-document）。")
def render_document(path: str, deploy: bool = True) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        path: 描画する対象のdocumentの置き場所
        deploy: 描画した成果物を、schemaが定める配置先へ置くかどうか

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(RenderDocument(_docs(), _schemas()).run(path, deploy=deploy))

@mcp.tool(description="HandoffのDocument.jsonを固定HTMLテンプレートへ描画する（uc-render-handoff-template）。")
def render_handoff_template(path: str, outputPath: str) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        path: 引き継ぎ文書の置き場所
        outputPath: 引き継ぎの成果物を書き出す先

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(RenderHandoffTemplate(_docs()).run(path, outputPath))

@mcp.tool(description="document.jsonのMD正本をCSS付きの自己完結HTMLへ変換する（uc-render-document-viewer）。")
def render_document_viewer(path: str, outputPath: str) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        path: 閲覧用の形にする対象のdocumentの置き場所
        outputPath: 閲覧用の成果物を書き出す先

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(RenderDocumentViewer(_docs(), RenderDocument(_docs(), _schemas())).run(path, outputPath))

@mcp.tool(description="schemaRefが宣言する値フィールドをx-prompt-write本文のプレースホルダーとして描画する（uc-render-blank-template）。")
def render_blank_template(schemaRef: str, discriminator: dict | None = None) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        schemaRef: どのschemaの雛形を書き出すかを指す参照
        discriminator: key=value 形式（例: codingKind=coding-standard）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(RenderBlankTemplate(_docs(), _schemas()).run(schemaRef, discriminator or {}))

@mcp.tool(description="document を schema 適合検証（uc-validate-document）。")
def validate_document(path: str) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        path: 適合を確かめる対象のdocumentの置き場所

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(ValidateDocument(_docs(), _schemas(), JsonSchemaValidator()).run(path))

@mcp.tool(description="document.json の骨格生成 / 値書き込み / フィールド削除 / schemaRef移行（uc-scaffold-document）。operation: create / fill / clear_field / migrate_schema。")
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
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        operation: documentに対して行う書き込みの種類
        schemaRef: 骨格を作るときに従うschemaを指す参照
        documentId: 作るdocumentを一意に指す識別子
        discriminator: key=value 形式（例: skillKind=engine）
        contextRef: 所属する bounded-context の documentId（ネストしたx-source-targetが要求する場合）
        subdomainRef: usecase が属する subdomain の documentId
        documentPath: 既にあるdocumentの置き場所。値の書き込み・欄の除去・版の移行の対象になる
        values: fill する値の JSON オブジェクト
        fieldPath: clear_field で削除する値フィールドのドットパス

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
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
        params = {"documentPath": documentPath, "fieldPath": fieldPath}
    elif operation == "migrate_schema":
        params = {"documentPath": documentPath, "schemaRef": schemaRef}
    else:
        params = {}
    return _dict(ScaffoldDocument(_docs(), _schemas()).run(operation, params))

@mcp.tool(description="Schema定義ファイル自体への構造化編集（uc-patch-schema）。operation: add_block / rename_block / set_field / remove_field / remove_block / add_def / add_kind_branch / create_version。")
def patch_schema(operation: str, schemaRef: str, params: dict | None = None) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        operation: add_block / rename_block / set_field / remove_field / remove_block / add_def / add_kind_branch / create_version
        schemaRef: 編集する対象のschemaを指す参照
        params: operation固有パラメータのJSONオブジェクト

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    p = dict(params or {})
    p["schemaRef"] = schemaRef
    return _dict(PatchSchema(_docs(), _schemas(), JsonSchemaValidator()).run(operation, p))

@mcp.tool(description="bc.jsonのmembers宣言とディスク上の実ファイルの参照整合性を検証（uc-check-spec-integrity）。")
def check_spec_integrity(path: str, documentsRoot: str = ".waffle/documents") -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        path: bounded-context の bc.json のパス
        documentsRoot: Document集約の実インスタンス群を走査する対象ディレクトリ

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(CheckSpecIntegrity(_docs()).run(path, documentsRoot))

@mcp.tool(description="specのシナリオとテストコードの対応関係を検証（uc-check-scenario-drift）。  specPath と testPath で1組だけ検査するか、documentsRoot と testsRoot で 全体を走査するかのどちらか一方を指定する。")
def check_scenario_drift(specPath: str = None, testPath: str = None,
                         documentsRoot: str = None, testsRoot: str = None,
                         architectureRef: str = None) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        specPath: spec.json のパス（1組だけ検査する）
        testPath: 対応するテストファイルのパス（1組だけ検査する）
        documentsRoot: spec documentの置き場所（全体を検査する）
        testsRoot: テストの配置ルート（全体を検査する）
        architectureRef: シナリオ照合の規約を引くarchitecture documentのdocumentId

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    binding = _resolve_binding(architectureRef)
    if "error" in binding:
        return binding
    scope = documentsRoot
    if scope is None and architectureRef and (specPath is None) != (testPath is None):
        scope = _resolve_documents_root(None, architectureRef)
        if isinstance(scope, dict):
            return scope
    return _dict(CheckScenarioDrift(_docs(), TreeSitterTestFunctionExtractor()).run(
        binding=binding, spec_path=specPath, test_file_path=testPath,
        documents_root=scope, tests_root=testsRoot))

@mcp.tool(description="実装完了→検証フェーズへ進んでよいかを判定（uc-check-verification-gate）。")
def check_verification_gate(specPath: str, testPath: str, testResultsPath: str, architectureRef: str = None) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        specPath: spec.json のパス
        testPath: 対応するテストファイル(.py)のパス
        testResultsPath: テスト実行結果({"passed": [...], "failed": [...]})のパス
        architectureRef: シナリオ照合の規約を引くarchitecture documentのdocumentId

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(CheckVerificationGate(_docs(), TreeSitterTestFunctionExtractor()).run(
        specPath, testPath, testResultsPath, _resolve_binding(architectureRef)))

@mcp.tool(description="Schemaの指示が然るべき場所に然るべき名前で置かれているかを検証（uc-check-prompt-contract）。")
def check_prompt_contract(schemaRef: str) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        schemaRef: 確かめる対象のschemaRef（例: DomainSpecSchema/v8）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(CheckPromptContract(_schemas()).run(schemaRef))

@mcp.tool(description="DocumentのschemaRefが実在し最新であるかを検証（uc-check-schema-version-drift）。")
def check_schema_version_drift(documentsRoot: str = ".waffle/documents") -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        documentsRoot: Document集約の実インスタンス群を走査する対象ディレクトリ

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(CheckSchemaVersionDrift(_docs(), _schemas()).run(documentsRoot))

@mcp.tool(description="usecase specの操作名と実装クラス名が一致しているかを検証（uc-check-usecase-class-drift）。srcRoot省略時はarchitectureRefが指すarchitecture documentから動的解決する。")
def check_usecase_class_drift(
    documentsRoot: str = None, srcRoot: str | None = None, architectureRef: str | None = None, language: str = "python"
) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        documentsRoot: 仕様側の走査範囲。未指定なら architectureRef が受け持つコンテキストから決まる
        srcRoot: usecase実装クラスの配置ルートディレクトリ（明示指定時は--architectureRefより優先）
        architectureRef: srcRoot未指定時に参照するarchitecture documentのdocumentId（例: architecture-waffle）
        language: 実装言語（python/java/typescript/javascript）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    resolved = _resolve_src_root(srcRoot, architectureRef, "usecase")
    if isinstance(resolved, dict):
        return resolved
    scope = _resolve_documents_root(documentsRoot, architectureRef)
    if isinstance(scope, dict):
        return scope

    naming = _resolve_naming(architectureRef)
    if isinstance(naming, dict) and "error" in naming:
        return naming
    # 1つのファイルで探すか、配置ディレクトリで探すかは architecture の宣言が決める
    unit = resolve_search_unit(_docs(), architectureRef, "usecase")
    return _dict(CheckUsecaseClassDrift(_docs(), _class_extractor()).run(scope, resolved, naming, language, unit))

@mcp.tool(description="aggregate specの集約ルート名と実装クラス名が一致しているかを検証（uc-check-aggregate-class-drift）。srcRoot省略時はarchitectureRefが指すarchitecture documentから動的解決する。")
def check_aggregate_class_drift(
    documentsRoot: str = None, srcRoot: str | None = None, architectureRef: str | None = None, language: str = "python"
) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        documentsRoot: 仕様側の走査範囲。未指定なら architectureRef が受け持つコンテキストから決まる
        srcRoot: 集約Entityクラスの配置ルートディレクトリ（明示指定時は--architectureRefより優先）
        architectureRef: srcRoot未指定時に参照するarchitecture documentのdocumentId（例: architecture-waffle）
        language: 実装言語（python/java/typescript/javascript）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    resolved = _resolve_src_root(srcRoot, architectureRef, "aggregate")
    if isinstance(resolved, dict):
        return resolved
    scope = _resolve_documents_root(documentsRoot, architectureRef)
    if isinstance(scope, dict):
        return scope

    naming = _resolve_naming(architectureRef)
    if isinstance(naming, dict) and "error" in naming:
        return naming
    # 値オブジェクトをどこまで探すかは architecture の宣言が決める
    value_object_root = resolve_directory_scoped_root(_docs(), architectureRef, "value-object")
    # 集約ルート自身の探し方も同じ宣言から決める
    unit = resolve_search_unit(_docs(), architectureRef, "aggregate")
    return _dict(CheckAggregateClassDrift(_docs(), _class_extractor()).run(
        scope, resolved, naming, language, value_object_root, unit))

@mcp.tool(description="宣言した層の依存の向きが実装でも守られているかを検証（uc-check-layer-drift）。architectureRefが宣言する層・置き場所・依存してよい先だけを基準に使う。")
def check_layer_drift(architectureRef: str) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        architectureRef: 層・置き場所・依存してよい先を宣言するarchitecture documentのdocumentId（例: architecture-waffle）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(CheckLayerDrift(_docs(), TreeSitterImportExtractor()).run(architectureRef))

@mcp.tool(description="業務サービスのgroupと実装ファイルが一致しているかを検証（uc-check-domain-service-drift）。srcRoot省略時はarchitectureRefが指すarchitecture documentから動的解決する。")
def check_domain_service_drift(documentsRoot: str = None, srcRoot: str | None = None, architectureRef: str | None = None) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        documentsRoot: 仕様側の走査範囲。未指定なら architectureRef が受け持つコンテキストから決まる
        srcRoot: 業務サービス実装ファイルの配置ルートディレクトリ（明示指定時は--architectureRefより優先）
        architectureRef: srcRoot未指定時に参照するarchitecture documentのdocumentId（例: architecture-waffle）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    resolved = _resolve_src_root(srcRoot, architectureRef, "domain-service")
    if isinstance(resolved, dict):
        return resolved
    scope = _resolve_documents_root(documentsRoot, architectureRef)
    if isinstance(scope, dict):
        return scope

    naming = _resolve_naming(architectureRef)
    if isinstance(naming, dict) and "error" in naming:
        return naming
    return _dict(CheckDomainServiceDrift(_docs()).run(scope, resolved, naming))

@mcp.tool(description="usecase specが宣言するoperation名と実装のoperation分岐が一致しているかを検証（uc-check-operation-drift）。srcRoot省略時はarchitectureRefが指すarchitecture documentから動的解決する。")
def check_operation_drift(documentsRoot: str = None, srcRoot: str | None = None, architectureRef: str | None = None) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        documentsRoot: 仕様側の走査範囲。未指定なら architectureRef が受け持つコンテキストから決まる
        srcRoot: usecase実装クラスの配置ルートディレクトリ（明示指定時は--architectureRefより優先）
        architectureRef: srcRoot未指定時に参照するarchitecture documentのdocumentId（例: architecture-waffle）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    resolved = _resolve_src_root(srcRoot, architectureRef, "usecase")
    if isinstance(resolved, dict):
        return resolved
    scope = _resolve_documents_root(documentsRoot, architectureRef)
    if isinstance(scope, dict):
        return scope

    naming = _resolve_naming(architectureRef)
    if isinstance(naming, dict) and "error" in naming:
        return naming
    return _dict(CheckOperationDrift(_docs()).run(scope, resolved, naming))

@mcp.tool(description="対象コードベースの公開要素のdocstringを構造化抽出（uc-scan-source-code）。")
def scan_source_code(path: str, kind: str) -> dict | list:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        path: 対象コードベース(ディレクトリ)のパス
        kind: DocstringSchemaのkind（現状はgoogleのみ対応）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(ScanSourceCode(_docs(), PythonAstSourceScanner()).run(path, kind))

@mcp.tool(description="対象コードベースのdocstringが規約どおりか既存lintツールで検証（uc-lint-docstring）。")
def lint_docstring(path: str, standardRef: str) -> dict | list:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        path: 確かめる対象のコードベースの置き場所
        standardRef: どの構文で判定するかを宣言している規約のdocumentの置き場所

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    scan_engine = ScanSourceCode(_docs(), PythonAstSourceScanner())
    return _dict(LintDocstring(scan_engine, PydoclintLinter()).run(path, standardRef))

@mcp.tool(description="プリセットからtech-stack/architecture/coding-standard/test-standardの4documentを一括生成（uc-init-coding-preset）。")
def init_coding_preset(preset: str, product: str) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        preset: プリセット名（例: python-hexagonal）
        product: プロダクト名（documentIdのサフィックスになる。例: waffle）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(InitCodingPreset(_docs(), PackageCodingPresetRepository()).run(preset, product))

@mcp.tool(description="実践で確かめた規約の指定部分を、次の出発点となるプリセットへ反映（uc-update-coding-preset）。丸ごとの写しは行わないため、戻す部分の指定は省略できない。dryRunを真にすると書き換えずに何が変わるかだけを返す。")
def update_coding_preset(preset: str, fromDocumentId: str, blocks: list[str], dryRun: bool = False) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        preset: 反映先のプリセット名（例: python-hexagonal）
        fromDocumentId: 出どころとなる規約のdocumentId（例: architecture-waffle）
        blocks: 戻す部分をカンマ区切りで（例: rules,layers,layout.granularity）。ブロックの中の欄まで指定できる。丸ごとの写しは行わないため省略できない
        dryRun: 書き換えずに、何が変わるかだけを返す

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(UpdateCodingPreset(_docs(), PackageCodingPresetRepository()).run(
        preset, fromDocumentId, blocks, dryRun))

@mcp.tool(description="実体パスがdocument.json（原本）からの投影かどうかを判定（uc-check-path-is-projection）。")
def check_path_is_projection(resolvedPath: str) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        resolvedPath: 判定対象の実体パス（symlink解決済み）

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(CheckPathIsProjection(_schemas()).run(resolvedPath))

@mcp.tool(description="配列fillの前に対象pathへのqueryが先行しているかを判定（uc-check-query-precedes-array-fill）。")
def check_query_precedes_array_fill(targetPath: str, hasArrayValue: bool, queriedPaths: list[str]) -> dict:
    """受け取った引数をユースケースへ渡し、結果を辞書で返す。

    Args:
        targetPath: fill対象のdocument.jsonパス
        hasArrayValue: 値に配列を含むか
        queriedPaths: 同一セッション内で既にqueryされたpathのJSON配列。例: ["a.json"]

    Returns:
        その操作の結果。

    Raises:
        なし。失敗は結果の中で表す。
    """
    return _dict(CheckQueryPrecedesArrayFill().run(targetPath, hasArrayValue, queriedPaths))


def main() -> None:
    """MCPサーバを標準入出力で起動する。

    合成ルートの一部（起動と結線のみ）。業務ロジックはここに書かない。
    """
    mcp.run()


if __name__ == "__main__":
    main()
