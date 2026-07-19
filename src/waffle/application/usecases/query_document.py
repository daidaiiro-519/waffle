"""query document — document.json / 通常ファイルへのセマンティック・クエリ。

6 のセマンティック操作（scan/get_meta/index_scan/find_all/resolve_ref/query_path）で、
AI がファイルを直接読まずに必要な意味単位だけを取得する。構造アクセスは全て Python が担い、
常に `{ prompt, value }` を返す（prompt=value の読み方の指針）。ブロック単位の操作は対象
block の x-prompt-query を schema から動的算出し、メタ/集約系操作（get_meta/scan/index_scan/
find_all）は動的に導出できないため操作の性質に基づく固定文言を使う（値を返すすべての操作で
読み方の指針を省略しない）。ディレクトリ横断のindex集約（index_scan_documents）は
uc-query-document-collection側が担う。schemaRef を持たないファイルは raw フォールバック。
全エラーは Result.Err（details[0]=エラーコード）で構造化し、例外を AI に素通りさせない。

query_path は、かつて存在した get_block/get_field/get_items/get_item_field/get_items_slice/
filter_items/filter_exists/filter_pattern/get_by_id/get_nested_items/get_children の10操作
（いずれも「1ブロックの内側を起点に値を取り出す」という同じ責務のバリエーション）を1つの
JMESPath 式操作へ統合したもの（ddd-advisor: これらは実装都合の語彙でありユビキタス言語では
ないため統合が妥当）。統合後はこの10操作自体をspec・実装の両方から削除済み。式は常に
「1ブロックの内側を起点とした相対式」（tech-lead-advisor: 「値を返す全操作に
prompt が付く」という絶対制約と整合させるため、doc全体や複数blockTypeを跨ぐ評価はしない）。
"""
from __future__ import annotations

import re

import jmespath
import jmespath.exceptions
import jmespath.functions

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.schema_repository import SchemaRepository
from waffle.application.services.document_loading import load_document, load_schema
from waffle.domain.services import path_template
from waffle.domain.services.document_index import build_block_index
from waffle.domain.services.schema_discriminator import discriminator_key
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result

# 各 operation の必須パラメータ（path を除く）
_REQUIRED: dict[str, list[str]] = {
    "scan": [],
    "get_meta": [],
    "index_scan": [],
    "find_all": ["fieldName"],
    "resolve_ref": ["field", "targetSchemaRef"],
    "query_path": ["expression"],
}

_META_FIELDS = ("documentId", "documentType", "schemaRef", "skillKind", "codingKind", "status", "tags")

# schemaのx-prompt-queryから動的に引けない operation（メタ/集約系）向けの固定prompt。
# promptは「値が有るときだけ付随する情報」ではなく「取得した意味単位をどう解釈すべきかの指針」を
# 全operationに共通して渡すためのものであり、動的に導出できない場合も操作の性質に基づく
# 固定的な説明文を与える（値を持たないから省略してよい、という扱いはしない）。
_PROMPT_SCAN = "未パースの生テキストです。構造化されたアクセスにはindex_scanまたはquery_path等を使ってください。"
_PROMPT_GET_META = "documentId等のDocument識別用メタ情報です。ドメイン内容の解釈には使いません。"
_PROMPT_FIND_ALL = "全階層を横断して集約した値の配列です。どのブロック・階層に属していたかという文脈は失われています。文脈が必要な場合はquery_path等で個別に取得してください。"
_PROMPT_INDEX_SCAN = "各ブロックの索引です。各要素のprompt（value[key].prompt）に、そのブロック自体の読み方の指針が入っています。"
_PROMPT_RESOLVE_REF = "参照先Documentのpathです。中身は取得されていません。必要ならこのpathに対してquery_path等を別途実行してください。"

class QueryDocument:
    def __init__(self, documents: DocumentRepository, schemas: SchemaRepository) -> None:
        self._documents = documents
        self._schemas = schemas

    def run(self, operation: str, path: str, params: dict | None = None) -> Result[dict]:
        params = params or {}
        if operation not in _REQUIRED:
            return _err("INVALID_OPERATION", f"未知の operation: {operation}")
        missing = [p for p in _REQUIRED[operation] if params.get(p) in (None, "")]
        if missing:
            return _err("MISSING_PARAM", f"{operation} には {', '.join(missing)} が必要です")

        # G6: パストラバーサル拒否（全 operation・読み取り対象を制限）
        if not is_confined(path):
            return _err("INVALID_PATH", f"パストラバーサルは許可されません: {path}")

        # Group 1: ファイル/ディレクトリ単位（schema 不要なものを先に処理）
        if operation == "scan":
            try:
                return Ok({"prompt": _PROMPT_SCAN, "value": self._documents.read_text(path)})
            except FileNotFoundError:
                return _err("INVALID_PATH", f"ファイルが見つかりません: {path}")
        # それ以外は document を読む
        loaded = load_document(self._documents, path)
        if isinstance(loaded, Err):
            return loaded
        doc = loaded.value

        # schemaRef を持たない通常ファイル → raw フォールバック
        if not isinstance(doc, dict) or "schemaRef" not in doc:
            return Ok({"type": "raw", "content": self._documents.read_text(path)})

        schema_result = load_schema(self._schemas, doc["schemaRef"])
        if isinstance(schema_result, Err):
            return schema_result
        return self._dispatch(operation, doc, schema_result.value, params, path)

    # --- ディスパッチ ---

    def _dispatch(self, operation: str, doc: dict, schema: dict, params: dict, path: str) -> Result[dict]:
        if operation == "get_meta":
            return Ok({"prompt": _PROMPT_GET_META, "value": {k: doc[k] for k in _META_FIELDS if k in doc}})
        if operation == "index_scan":
            return Ok({"prompt": _PROMPT_INDEX_SCAN, "value": build_block_index(doc, schema)})
        if operation == "find_all":
            return Ok({"prompt": _PROMPT_FIND_ALL, "value": _find_all(doc, params["fieldName"])})
        if operation == "resolve_ref":
            return self._resolve_ref(doc, schema, path, params)
        if operation == "query_path":
            return self._query_path(doc, schema, params)
        return _err("INVALID_OPERATION", f"未知の operation: {operation}")  # pragma: no cover — _REQUIRED で網羅済み

    def _resolve_ref(self, doc: dict, schema: dict, document_path: str, params: dict) -> Result[dict]:
        field = params["field"]
        if field not in doc:
            return _err("NOT_FOUND", f"field が見つかりません: {field}")

        target_schema_result = load_schema(self._schemas, params["targetSchemaRef"])
        if isinstance(target_schema_result, Err):
            return target_schema_result
        target_schema = target_schema_result.value

        path_vars = {"documentId": doc["documentId"]}
        x_source = schema.get("x-source-target")
        if isinstance(x_source, dict):
            own_key = discriminator_key(schema)
            own_template = x_source.get(doc.get(own_key)) if own_key else None
            if own_template:
                recovered = path_template.reverse_parse(own_template, document_path)
                if recovered:
                    path_vars.update(recovered)
        path_vars["documentId"] = doc[field]

        target_x_source = target_schema.get("x-source-target") or ""
        if isinstance(target_x_source, dict):
            target_discriminator = params.get("targetDiscriminator") or {}
            target_key = discriminator_key(target_schema)
            template = target_x_source.get(target_discriminator.get(target_key)) if target_key else None
        else:
            template = target_x_source
        if not template:
            return _err("MISSING_TEMPLATE_VAR", "参照先のpathテンプレートを特定できません（targetDiscriminatorを確認してください）")

        try:
            resolved_path = path_template.resolve(template, **path_vars)
        except KeyError as e:
            return _err("MISSING_TEMPLATE_VAR", f"テンプレート変数を解決できません: {e}")
        return Ok({"prompt": _PROMPT_RESOLVE_REF, "value": {"path": resolved_path}})

    def _query_path(self, doc: dict, schema: dict, params: dict) -> Result[dict]:
        """query_path — 1ブロックの内側を起点とした相対式で JMESPath 評価する（絶対制約:
        doc全体や複数blockTypeを跨ぐ評価はしない。blockKey省略時はcontent配下の全ブロックへ
        同じ相対式を個別評価し、ヒットしたブロックだけを集める）。"""
        compiled_result = _compile_jmespath(params["expression"])
        if isinstance(compiled_result, Err):
            return compiled_result
        compiled = compiled_result.value

        block_key = params.get("blockKey")
        if block_key:
            block = doc.get("content", {}).get(block_key)
            if not isinstance(block, dict):
                return _err("NOT_FOUND", f"block が見つかりません: {block_key}")
            evaluated = _evaluate(compiled, block)
            if isinstance(evaluated, Err):
                return evaluated
            return Ok({
                "documentId": doc["documentId"],
                "prompt": _block_prompt(schema, block),
                "value": evaluated.value,
            })

        results_result = _query_path_all_blocks(doc.get("content", {}), compiled, schema)
        if isinstance(results_result, Err):
            return results_result
        return Ok({"documentId": doc["documentId"], "results": results_result.value})

class _WaffleFunctions(jmespath.functions.Functions):
    """query_path が式内から呼べる Waffle 固有のカスタム関数（filter_pattern相当の正規表現絞り込み）。"""

    @jmespath.functions.signature({"types": ["string"]}, {"types": ["string"]})
    def _func_regex_match(self, text, pattern):
        return re.search(pattern, text) is not None


_JMESPATH_OPTIONS = jmespath.Options(custom_functions=_WaffleFunctions())

# --- 純ヘルパ ---

def _err(code: str, message: str) -> Err:
    return Err(message, [code])

def _compile_jmespath(expression: str) -> Result:
    """expression をコンパイルする。構文エラーは jmespath の生例外ではなく
    Waffle独自のエラーコード（INVALID_JMESPATH_EXPRESSION）へ変換する。"""
    try:
        return Ok(jmespath.compile(expression))
    except jmespath.exceptions.ParseError as e:
        return _err("INVALID_JMESPATH_EXPRESSION", f"JMESPath式が不正です: {expression!r} ({e})")

def _evaluate(compiled, root) -> Result:
    """コンパイル済み式を root（1ブロックの内側）に対して評価する。評価時エラー
    （regex_matchへの不正な正規表現渡し等）も Waffle独自のエラーへ変換する。"""
    try:
        return Ok(compiled.search(root, options=_JMESPATH_OPTIONS))
    except jmespath.exceptions.JMESPathError as e:
        return _err("INVALID_JMESPATH_EXPRESSION", f"JMESPath式の評価に失敗しました: {e}")
    except re.error as e:
        return _err("INVALID_JMESPATH_EXPRESSION", f"正規表現が不正です: {e}")

def _query_path_all_blocks(content: dict, compiled, schema: dict) -> Result:
    """content配下の全blockKeyそれぞれへ同じ相対式を個別評価し、ヒットした
    （評価結果が空でない）ブロックだけを集める。式の構文自体は_compile_jmespathで
    事前にコンパイル済みのためここでは評価時エラーのみが起こりうる。あるブロックの
    形が式に合わず評価時型エラー（JMESPathTypeError等）になっても、そのブロックを
    ヒットなしとして黙ってスキップし、他のブロックの評価・クエリ全体は継続する
    （blockKeyを明示指定した単一ブロック評価とは異なり、ハードエラーにはしない）。"""
    results: list[dict] = []
    for key, block in content.items():
        if not isinstance(block, dict):
            continue
        evaluated = _evaluate(compiled, block)
        if isinstance(evaluated, Err):
            continue
        value = evaluated.value
        if value:
            results.append({"blockKey": key, "prompt": _block_prompt(schema, block), "value": value})
    return Ok(results)

def _block_prompt(schema: dict, block: dict):
    bdef = schema.get("$defs", {}).get(f"{block.get('blockType')}Block", {})
    return bdef.get("x-prompt-query")

def _find_all(node, field: str) -> list:
    """node 配下を再帰走査し field の値を全て集める（全階層検索）。"""
    out: list = []
    if isinstance(node, dict):
        if field in node:
            out.append(node[field])
        for v in node.values():
            out.extend(_find_all(v, field))
    elif isinstance(node, list):
        for v in node:
            out.extend(_find_all(v, field))
    return out
