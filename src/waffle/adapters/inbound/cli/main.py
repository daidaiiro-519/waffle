"""waffle CLI — inbound(driving) adapter。

各 engine(application use case) に outbound adapter を結線し、CLI 引数を params に成型して呼ぶ。
Result[dict] を JSON で標準出力に出す（Ok→value をそのまま / Err→{error, message}・exit!=0）。
これが engine Skill の InvocationSpec が指す実体（`waffle <op> ...`）。
"""
from __future__ import annotations

import json
import os

os.environ.setdefault("PYTHON_COLORS", "0")

import typer

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
from waffle.application.usecases.check_path_is_projection import CheckPathIsProjection
from waffle.application.usecases.check_query_precedes_array_fill import CheckQueryPrecedesArrayFill
from waffle.application.usecases.check_verification_gate import CheckVerificationGate
from waffle.application.usecases.check_aggregate_class_drift import CheckAggregateClassDrift
from waffle.application.usecases.check_domain_service_drift import CheckDomainServiceDrift
from waffle.application.usecases.lint_docstring import LintDocstring
from waffle.application.usecases.patch_schema import PatchSchema
from waffle.application.usecases.query_document import QueryDocument
from waffle.application.usecases.query_document_collection import QueryDocumentCollection
from waffle.application.usecases.render_blank_template import RenderBlankTemplate
from waffle.application.usecases.render_document import RenderDocument
from waffle.application.usecases.render_handoff_template import RenderHandoffTemplate
from waffle.application.usecases.scaffold_document import ScaffoldDocument
from waffle.application.usecases.scan_source_code import ScanSourceCode
from waffle.application.usecases.validate_document import ValidateDocument
from waffle.shared.result import Ok, Result

app = typer.Typer(
    add_completion=False,
    help="waffle CLI — query / render / validate / scaffold",
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)

def _emit(result: Result) -> None:
    if isinstance(result, Ok):
        typer.echo(json.dumps(result.value, ensure_ascii=False))
        return
    code = result.details[0] if result.details else "ERROR"
    typer.echo(json.dumps({"error": code, "message": result.message}, ensure_ascii=False))
    raise typer.Exit(1)

def _docs() -> FsDocumentRepository:
    return FsDocumentRepository()

def _schemas() -> PackageSchemaRepository:
    return PackageSchemaRepository()

def _class_extractor() -> TreeSitterClassExtractor:
    return TreeSitterClassExtractor()

@app.command()
def query(
    operation: str = typer.Option(..., "--operation"),
    path: str = typer.Option(..., "--path"),
    block_key: str = typer.Option(None, "--blockKey", "--block-key"),
    array_field: str = typer.Option(None, "--arrayField", "--array-field"),
    field: str = typer.Option(None, "--field"),
    id_field: str = typer.Option(None, "--idField", "--id-field"),
    id_value: str = typer.Option(None, "--idValue", "--id-value"),
    key: str = typer.Option(None, "--key"),
    value: str = typer.Option(None, "--value"),
    pattern: str = typer.Option(None, "--pattern"),
    start: int = typer.Option(None, "--start"),
    end: int = typer.Option(None, "--end"),
    field_name: str = typer.Option(None, "--fieldName", "--field-name"),
    nested_field: str = typer.Option(None, "--nestedField", "--nested-field"),
    target_schema_ref: str = typer.Option(None, "--targetSchemaRef", "--target-schema-ref"),
    target_discriminator: str = typer.Option(
        None, "--targetDiscriminator", "--target-discriminator",
        help="key=value 形式（例: specKind=subdomain）",
    ),
) -> None:
    """document.json へのセマンティック・クエリ（uc-query-document）。"""
    raw = {
        "blockKey": block_key, "arrayField": array_field, "field": field,
        "idField": id_field, "idValue": id_value, "key": key, "value": value,
        "pattern": pattern, "start": start, "end": end,
        "fieldName": field_name, "nestedField": nested_field,
        "targetSchemaRef": target_schema_ref,
    }
    params = {k: v for k, v in raw.items() if v is not None}
    if target_discriminator:
        k, _, v = target_discriminator.partition("=")
        params["targetDiscriminator"] = {k: v}
    _emit(QueryDocument(_docs(), _schemas()).run(operation, path, params))

@app.command("query-collection")
def query_collection(
    operation: str = typer.Option(..., "--operation"),
    path: str = typer.Option(..., "--path", help="対象ディレクトリ"),
    pattern: str = typer.Option(None, "--pattern"),
    field: str = typer.Option(None, "--field"),
    key: str = typer.Option(None, "--key"),
    value: str = typer.Option(None, "--value"),
    fields: str = typer.Option(None, "--fields", help="カンマ区切りのフィールド名一覧"),
) -> None:
    """複数document.jsonを横断するセマンティック・クエリ（uc-query-document-collection）。"""
    raw = {"pattern": pattern, "field": field, "key": key, "value": value}
    params = {k: v for k, v in raw.items() if v is not None}
    if fields:
        params["fields"] = [f.strip() for f in fields.split(",") if f.strip()]
    _emit(QueryDocumentCollection(_docs(), _schemas()).run(operation, path, params))

@app.command()
def render(
    path: str = typer.Option(..., "--path"),
    no_deploy: bool = typer.Option(False, "--no-deploy"),
) -> None:
    """document.json を成果物にレンダリングして deploy（uc-render-document）。"""
    _emit(RenderDocument(_docs(), _schemas()).run(path, deploy=not no_deploy))

@app.command("render-handoff-template")
def render_handoff_template(
    path: str = typer.Option(..., "--path"),
    output_path: str = typer.Option(..., "--outputPath", "--output-path"),
) -> None:
    """HandoffのDocument.jsonを固定HTMLテンプレートへ描画する（uc-render-handoff-template）。"""
    _emit(RenderHandoffTemplate(_docs()).run(path, output_path))

@app.command("render-blank-template")
def render_blank_template(
    schema_ref: str = typer.Option(..., "--schemaRef", "--schema-ref"),
    discriminator: str = typer.Option(None, "--discriminator", help="key=value 形式（例: codingKind=coding-standard）"),
) -> None:
    """schemaRefが宣言する値フィールドをx-prompt-write本文のプレースホルダーとして描画する（uc-render-blank-template）。"""
    params = {}
    if discriminator:
        k, _, v = discriminator.partition("=")
        params = {k: v}
    _emit(RenderBlankTemplate(_docs(), _schemas()).run(schema_ref, params))

@app.command()
def validate(path: str = typer.Option(..., "--path")) -> None:
    """document を schema 適合検証（uc-validate-document）。"""
    _emit(ValidateDocument(_docs(), _schemas(), JsonSchemaValidator()).run(path))

@app.command()
def scaffold(
    operation: str = typer.Option(..., "--operation"),
    schema_ref: str = typer.Option(None, "--schemaRef", "--schema-ref"),
    document_id: str = typer.Option(None, "--documentId", "--document-id"),
    discriminator: str = typer.Option(None, "--discriminator", help="key=value 形式（例: skillKind=engine）"),
    context_ref: str = typer.Option(None, "--contextRef", "--context-ref", help="所属する bounded-context の documentId（ネストしたx-source-targetが要求する場合）"),
    subdomain_ref: str = typer.Option(None, "--subdomainRef", "--subdomain-ref", help="usecase が属する subdomain の documentId"),
    path: str = typer.Option(None, "--path", help="fill / clear_field 対象の documentPath"),
    values: str = typer.Option(None, "--values", help="fill する値の JSON オブジェクト"),
    field_path: str = typer.Option(None, "--fieldPath", "--field-path", help="clear_field で削除する値フィールドのドットパス"),
) -> None:
    """document.json の骨格生成 / 値書き込み / フィールド削除 / schemaRef移行（uc-scaffold-document）。operation: create / fill / clear_field / migrate_schema。"""
    if operation == "create":
        params: dict = {"schemaRef": schema_ref, "documentId": document_id}
        if discriminator:
            k, _, v = discriminator.partition("=")
            params["discriminator"] = {k: v}
        if context_ref:
            params["contextRef"] = context_ref
        if subdomain_ref:
            params["subdomainRef"] = subdomain_ref
    elif operation == "fill":
        params = {"documentPath": path, "values": json.loads(values) if values else {}}
    elif operation == "clear_field":
        params = {"documentPath": path, "path": field_path}
    elif operation == "migrate_schema":
        params = {"documentPath": path, "schemaRef": schema_ref}
    else:
        params = {}
    _emit(ScaffoldDocument(_docs(), _schemas()).run(operation, params))

@app.command("patch-schema")
def patch_schema(
    operation: str = typer.Option(..., "--operation", help="add_block / rename_block / set_field / remove_block / add_def / add_kind_branch / create_version"),
    schema_ref: str = typer.Option(..., "--schemaRef", "--schema-ref"),
    params: str = typer.Option(None, "--params", help="operation固有パラメータのJSONオブジェクト"),
) -> None:
    """Schema定義ファイル自体への構造化編集（uc-patch-schema）。"""
    p = json.loads(params) if params else {}
    p["schemaRef"] = schema_ref
    _emit(PatchSchema(_docs(), _schemas(), JsonSchemaValidator()).run(operation, p))

@app.command("check-spec-integrity")
def check_spec_integrity(
    path: str = typer.Option(..., "--path", help="bounded-context の bc.json のパス"),
    documents_root: str = typer.Option(".waffle/documents", "--documentsRoot", "--documents-root", help="Document集約の実インスタンス群を走査する対象ディレクトリ"),
) -> None:
    """bc.jsonのmembers宣言とディスク上の実ファイルの参照整合性を検証（uc-check-spec-integrity）。"""
    _emit(CheckSpecIntegrity(_docs()).run(path, documents_root))

@app.command("check-scenario-drift")
def check_scenario_drift(
    spec_path: str = typer.Option(..., "--specPath", "--spec-path", help="spec.json のパス"),
    test_path: str = typer.Option(..., "--testPath", "--test-path", help="対応するテストファイル(.py)のパス"),
) -> None:
    """specのシナリオとテストコードの対応関係を検証（uc-check-scenario-drift）。"""
    _emit(CheckScenarioDrift(_docs()).run(spec_path, test_path))

@app.command("check-verification-gate")
def check_verification_gate(
    spec_path: str = typer.Option(..., "--specPath", "--spec-path", help="spec.json のパス"),
    test_path: str = typer.Option(..., "--testPath", "--test-path", help="対応するテストファイル(.py)のパス"),
    test_results_path: str = typer.Option(
        ..., "--testResultsPath", "--test-results-path",
        help='テスト実行結果({"passed": [...], "failed": [...]})のパス',
    ),
) -> None:
    """実装完了→検証フェーズへ進んでよいかを判定（uc-check-verification-gate）。"""
    _emit(CheckVerificationGate(_docs()).run(spec_path, test_path, test_results_path))

@app.command("check-query-precedes-array-fill")
def check_query_precedes_array_fill(
    target_path: str = typer.Option(..., "--targetPath", "--target-path", help="fill対象のdocument.jsonパス"),
    has_array_value: bool = typer.Option(..., "--hasArrayValue", "--has-array-value", help="値に配列を含むか"),
    queried_paths: str = typer.Option(
        "[]", "--queriedPaths", "--queried-paths",
        help="同一セッション内で既にqueryされたpathのJSON配列。例: [\"a.json\"]",
    ),
) -> None:
    """配列fillの前にqueryが先行しているかを判定（uc-check-query-precedes-array-fill）。"""
    _emit(CheckQueryPrecedesArrayFill().run(target_path, has_array_value, json.loads(queried_paths)))

@app.command("check-path-is-projection")
def check_path_is_projection(
    resolved_path: str = typer.Option(..., "--resolvedPath", "--resolved-path", help="判定対象の実体パス（symlink解決済み）"),
) -> None:
    """実体パスがdocument.jsonからの投影かどうかを判定（uc-check-path-is-projection）。"""
    _emit(CheckPathIsProjection(_docs()).run(resolved_path))

@app.command("check-schema-version-drift")
def check_schema_version_drift(
    documents_root: str = typer.Option(".waffle/documents", "--documentsRoot", "--documents-root", help="Document集約の実インスタンス群を走査する対象ディレクトリ"),
) -> None:
    """DocumentのschemaRefが実在し最新であるかを検証（uc-check-schema-version-drift）。"""
    _emit(CheckSchemaVersionDrift(_docs(), _schemas()).run(documents_root))

@app.command("check-usecase-class-drift")
def check_usecase_class_drift(
    documents_root: str = typer.Option(".waffle/documents", "--documentsRoot", "--documents-root", help="Document集約の実インスタンス群を走査する対象ディレクトリ"),
    src_root: str = typer.Option("src/waffle/application/usecases", "--srcRoot", "--src-root", help="usecase実装クラスの配置ルートディレクトリ"),
    language: str = typer.Option("python", "--language", help="実装言語（python/java/typescript/javascript）"),
) -> None:
    """usecase specの操作名と実装クラス名が一致しているかを検証（uc-check-usecase-class-drift）。"""
    _emit(CheckUsecaseClassDrift(_docs(), _class_extractor()).run(documents_root, src_root, language))

@app.command("check-aggregate-class-drift")
def check_aggregate_class_drift(
    documents_root: str = typer.Option(".waffle/documents", "--documentsRoot", "--documents-root", help="Document集約の実インスタンス群を走査する対象ディレクトリ"),
    src_root: str = typer.Option("src/waffle/domain/entities", "--srcRoot", "--src-root", help="集約Entityクラスの配置ルートディレクトリ"),
    language: str = typer.Option("python", "--language", help="実装言語（python/java/typescript/javascript）"),
) -> None:
    """aggregate specの集約ルート名と実装クラス名が一致しているかを検証（uc-check-aggregate-class-drift）。"""
    _emit(CheckAggregateClassDrift(_docs(), _class_extractor()).run(documents_root, src_root, language))

@app.command("check-domain-service-drift")
def check_domain_service_drift(
    documents_root: str = typer.Option(".waffle/documents", "--documentsRoot", "--documents-root", help="Document集約の実インスタンス群を走査する対象ディレクトリ"),
    src_root: str = typer.Option("src/waffle/domain/services", "--srcRoot", "--src-root", help="業務サービス実装ファイルの配置ルートディレクトリ"),
) -> None:
    """業務サービスのgroupと実装ファイルが一致しているかを検証（uc-check-domain-service-drift）。"""
    _emit(CheckDomainServiceDrift(_docs()).run(documents_root, src_root))

@app.command("check-operation-drift")
def check_operation_drift(
    documents_root: str = typer.Option(".waffle/documents", "--documentsRoot", "--documents-root", help="Document集約の実インスタンス群を走査する対象ディレクトリ"),
    src_root: str = typer.Option("src/waffle/application/usecases", "--srcRoot", "--src-root", help="usecase実装クラスの配置ルートディレクトリ"),
) -> None:
    """usecase specが宣言するoperation名と実装のoperation分岐が一致しているかを検証（uc-check-operation-drift）。"""
    _emit(CheckOperationDrift(_docs()).run(documents_root, src_root))

@app.command("scan-source-code")
def scan_source_code(
    path: str = typer.Option(..., "--path", help="対象コードベース(ディレクトリ)のパス"),
    kind: str = typer.Option(..., "--kind", help="DocstringSchemaのkind（現状はgoogleのみ対応）"),
) -> None:
    """対象コードベースの公開要素のdocstringを構造化抽出（uc-scan-source-code）。"""
    _emit(ScanSourceCode(_docs(), PythonAstSourceScanner()).run(path, kind))

@app.command("lint-docstring")
def lint_docstring(
    path: str = typer.Option(..., "--path", help="対象コードベース(ディレクトリ)のパス"),
    kind: str = typer.Option(..., "--kind", help="DocstringSchemaのkind（現状はgoogleのみ対応）"),
) -> None:
    """対象コードベースのdocstringが規約どおりか既存lintツールで検証（uc-lint-docstring）。"""
    scan_engine = ScanSourceCode(_docs(), PythonAstSourceScanner())
    _emit(LintDocstring(scan_engine, PydoclintLinter()).run(path, kind))

@app.command()
def serve() -> None:
    """MCP サーバを起動（query_document / render_document / … を MCP ツールとして公開）。"""
    from waffle.adapters.inbound.mcp.main import mcp

    mcp.run()

if __name__ == "__main__":
    app()
