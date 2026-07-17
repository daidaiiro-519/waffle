"""query document collection — 複数document.jsonを横断するセマンティック・クエリ。

uc-query-documentの16操作＋resolve_refが「単一document・単一block・単一配列フィールド」に
閉じた点操作であるのに対し、ここはディレクトリ配下の複数documentを横断する2操作
（grep_documents/filter_documents）を担う。都度フルスキャンであり、永続インデックス・
ミラーDBは持たない（正典はdocument.json＝git管理のプレーンJSONのまま、という設計合意）。
"""
from __future__ import annotations

import re

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.schema_repository import SchemaRepository
from waffle.shared.path_confinement import is_within_project_root
from waffle.shared.result import Err, Ok, Result

_REQUIRED: dict[str, list[str]] = {
    "grep_documents": ["pattern"],
    "filter_documents": ["key", "value"],
}

_META_FIELDS = ("documentId", "documentType", "schemaRef", "skillKind", "codingKind", "status", "tags")

_PROMPT_GREP = "対象ディレクトリ配下でpatternに一致した値を、Documentのpath単位で集めたものです。一致ゼロは正常系です。"
_PROMPT_FILTER = "対象ディレクトリ配下でkey/valueに一致したDocumentのpathとmeta（またはfields指定分）を集めたものです。一致ゼロは正常系です。"

class QueryDocumentCollection:
    def __init__(self, documents: DocumentRepository, schemas: SchemaRepository) -> None:
        self._documents = documents
        self._schemas = schemas

    def run(self, operation: str, directory: str, params: dict | None = None) -> Result[dict]:
        params = params or {}
        if operation not in _REQUIRED:
            return _err("INVALID_OPERATION", f"未知の operation: {operation}")
        missing = [p for p in _REQUIRED[operation] if params.get(p) in (None, "")]
        if missing:
            return _err("MISSING_PARAM", f"{operation} には {', '.join(missing)} が必要です")
        if not is_within_project_root(directory):
            return _err("INVALID_PATH", f"プロジェクトルート外は走査できません: {directory}")

        try:
            paths = self._documents.list_json(directory)
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {directory}")

        if operation == "grep_documents":
            return self._grep_documents(paths, params)
        if operation == "filter_documents":
            return self._filter_documents(paths, params)
        return _err("INVALID_OPERATION", f"未知の operation: {operation}")  # pragma: no cover — _REQUIRED で網羅済み

    def _grep_documents(self, paths: list[str], params: dict) -> Result[dict]:
        try:
            rx = re.compile(params["pattern"])
        except re.error as e:
            return _err("INVALID_PATTERN", f"正規表現が不正です: {e}")
        field = params.get("field")

        out: dict[str, list[dict]] = {}
        for p in paths:
            doc = self._documents.load(p)
            if not isinstance(doc, dict) or "schemaRef" not in doc:
                continue
            hits = list(_grep_content(doc.get("content", {}), rx, field))
            if hits:
                out[p] = hits
        return Ok({"prompt": _PROMPT_GREP, "value": out})

    def _filter_documents(self, paths: list[str], params: dict) -> Result[dict]:
        key, want = params["key"], params["value"]
        fields = params.get("fields")

        out: dict[str, dict] = {}
        for p in paths:
            doc = self._documents.load(p)
            if not isinstance(doc, dict) or "schemaRef" not in doc:
                continue
            if not _matches(doc.get(key), want):
                continue
            meta = {k: doc[k] for k in fields} if fields else {k: doc[k] for k in _META_FIELDS if k in doc}
            out[p] = meta
        return Ok({"prompt": _PROMPT_FILTER, "value": out})

# --- 純ヘルパ ---

def _err(code: str, message: str) -> Err:
    return Err(message, [code])

def _matches(actual, want) -> bool:
    if isinstance(actual, list):
        return want in actual
    return actual == want

def _grep_content(node, rx: re.Pattern, field: str | None, block_key: str | None = None) -> list[dict]:
    """content配下を再帰走査し、patternに一致する文字列値を{blockKey, field, value}で列挙する。"""
    hits: list[dict] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str):
                if (field is None or k == field) and rx.search(v):
                    hits.append({"blockKey": block_key, "field": k, "value": v})
            else:
                hits.extend(_grep_content(v, rx, field, block_key if block_key is not None else k))
    elif isinstance(node, list):
        for v in node:
            hits.extend(_grep_content(v, rx, field, block_key))
    return hits
