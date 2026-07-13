"""scaffold document — document.json の骨格生成（create）と値書き込み（fill）。

Harness 原則: AI は「値」だけを生成し、document.json の構造は engine が組む。
- create: schema を機械走査して skeleton（自分の schema で valid・status=enum 先頭）と
  fillTemplate（値フィールドの path × x-prompt-write）を生成し、x-source-target に書く。
- fill: AI が生成した values を、宣言済み値フィールドにのみ機械的に書き込む（構造保護）。
  値の型/enum 適合検証は uc-validate-document の責務（疎結合）。
"""
from __future__ import annotations

import json

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.schema_repository import SchemaRepository
from waffle.application.services.document_loading import load_document, load_schema, require_schema_ref
from waffle.domain.services import path_template
from waffle.domain.services.fill_template import build_const_paths as _build_const_paths
from waffle.domain.services.fill_template import build_fill_template as _build_fill_template
from waffle.domain.services.fill_template import build_skeleton as _build_skeleton
from waffle.domain.services.fill_template import build_top_level_const_paths as _build_top_level_const_paths
from waffle.domain.services.fill_template import build_top_level_fill_template as _build_top_level_fill_template
from waffle.domain.services.fill_template import content_def as _content_def
from waffle.domain.services.fill_template import discriminator_candidates as _discriminator_candidates
from waffle.domain.services.schema_discriminator import discriminator_key as _discriminator_key
from waffle.shared.result import Err, Ok, Result

def _err(code: str, message: str) -> Err:
    return Err(message, [code])

class ScaffoldDocument:
    def __init__(self, documents: DocumentRepository, schemas: SchemaRepository) -> None:
        self._documents = documents
        self._schemas = schemas

    def run(self, operation: str, params: dict | None = None) -> Result[dict]:
        params = params or {}
        if operation == "create":
            return self._create(params)
        if operation == "fill":
            return self._fill(params)
        if operation == "clear_field":
            return self._clear_field(params)
        return _err("INVALID_OPERATION", f"未知の operation: {operation}")

    def _create(self, params: dict) -> Result[dict]:
        schema_ref = params.get("schemaRef")
        document_id = params.get("documentId")
        if not schema_ref or not document_id:
            return _err("MISSING_PARAM", "create には schemaRef, documentId が必要です")
        schema_result = load_schema(self._schemas, schema_ref)
        if isinstance(schema_result, Err):
            return schema_result
        schema = schema_result.value

        disc_key = _discriminator_key(schema)
        discriminator = params.get("discriminator") or {}
        if disc_key:
            candidates = _discriminator_candidates(schema, disc_key)
            if disc_key not in discriminator:
                return _err("MISSING_DISCRIMINATOR", f"{disc_key} の指定が必要です（候補: {', '.join(candidates)}）")
            if discriminator[disc_key] not in candidates:
                return _err(
                    "INVALID_DISCRIMINATOR",
                    f"{disc_key}='{discriminator[disc_key]}' は不正な値です（候補: {', '.join(candidates)}）",
                )

        path_vars = {"documentId": document_id, **{k: v for k, v in params.items() if isinstance(v, str)}}
        content_def = _content_def(schema, discriminator)
        skeleton = _build_skeleton(schema, document_id, disc_key, discriminator, content_def, path_vars)
        protected = {"documentId"} | ({disc_key} if disc_key else set())
        fill_template = _build_top_level_fill_template(schema, protected) + _build_fill_template(schema, content_def)

        x_source = schema.get("x-source-target") or ""
        template = x_source.get(discriminator.get(disc_key)) if isinstance(x_source, dict) else x_source
        path = path_template.resolve(template, **path_vars) if template else ""
        if path:
            existing = self._existing_document(path)
            if existing is not None:
                # べき等性: 既にdocument.jsonがある場合は、fillで埋めた既存のvaluesを保護し
                # 骨格で上書きしない（構造は保存時に既に保証済み）。
                skeleton = existing
            else:
                self._documents.save(path, skeleton)
        return Ok({"skeleton": skeleton, "fillTemplate": fill_template, "path": path})

    def _existing_document(self, path: str) -> dict | None:
        try:
            return self._documents.load(path)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _fill(self, params: dict) -> Result[dict]:
        document_path = params.get("documentPath")
        values = params.get("values")
        if not document_path or values is None:
            return _err("MISSING_PARAM", "fill には documentPath, values が必要です")
        loaded = load_document(self._documents, document_path)
        if isinstance(loaded, Err):
            return loaded
        doc = loaded.value

        schema_ref_result = require_schema_ref(doc)
        if isinstance(schema_ref_result, Err):
            return schema_ref_result
        schema_ref = schema_ref_result.value

        schema_result = load_schema(self._schemas, schema_ref)
        if isinstance(schema_result, Err):
            return schema_result
        schema = schema_result.value

        disc_key = _discriminator_key(schema)
        discriminator = {disc_key: doc.get(disc_key)} if disc_key else {}
        content_def = _content_def(schema, discriminator)
        protected = {"documentId"} | ({disc_key} if disc_key else set())
        allowed = {e["path"] for e in _build_top_level_fill_template(schema, protected)}
        allowed |= {e["path"] for e in _build_fill_template(schema, content_def)}
        const_paths = _build_top_level_const_paths(schema, protected) | _build_const_paths(schema, content_def)

        written: list[str] = []
        skipped: list[str] = []
        for path, value in values.items():
            # const再同期: schema版更新でconst値自体が変わった既存documentを、現行schemaの
            # 宣言値と完全一致する値でのみ書き込み許可する（任意の値への上書きは引き続き拒否）
            is_const_resync = path in const_paths and const_paths[path] == value
            if (path in allowed or is_const_resync) and _set_path(doc, path, value):
                written.append(path)
            else:
                skipped.append(path)  # 未知 / const（現行値と不一致）/ discriminator / 構造改変は拒否
        self._documents.save(document_path, doc)
        return Ok({"documentPath": document_path, "written": written, "skipped": skipped})

    def _clear_field(self, params: dict) -> Result[dict]:
        document_path = params.get("documentPath")
        path = params.get("path")
        if not document_path or not path:
            return _err("MISSING_PARAM", "clear_field には documentPath, path が必要です")
        loaded = load_document(self._documents, document_path)
        if isinstance(loaded, Err):
            return loaded
        doc = loaded.value

        schema_ref_result = require_schema_ref(doc)
        if isinstance(schema_ref_result, Err):
            return schema_ref_result
        schema_ref = schema_ref_result.value

        schema_result = load_schema(self._schemas, schema_ref)
        if isinstance(schema_result, Err):
            return schema_result
        schema = schema_result.value

        disc_key = _discriminator_key(schema)
        discriminator = {disc_key: doc.get(disc_key)} if disc_key else {}
        content_def = _content_def(schema, discriminator)

        if _is_required_path(schema, content_def, path):
            return _err("REQUIRED_FIELD", f"必須フィールドは削除できません: {path}")

        cleared = _clear_path(doc, path)
        if cleared:
            self._documents.save(document_path, doc)
        return Ok({"documentPath": document_path, "cleared": cleared})

# --- schema 走査ヘルパ（純ロジック・機械的） ---

def _set_path(doc: dict, path: str, value) -> bool:
    """path上の中間キーが無ければ新設しながら値を設定する（呼び出し元がpathを既に
    allowed/const_pathsで検証済みのため、ここでの新設は現行schemaが宣言する経路に限られる。
    schema版更新で新設された任意ブロックへ、旧版のまま追従していない既存Documentも書き込めるようにする）。"""
    parts = path.split(".")
    cur = doc
    for p in parts[:-1]:
        if not isinstance(cur, dict):
            return False
        cur = cur.setdefault(p, {})
    if not isinstance(cur, dict):
        return False
    cur[parts[-1]] = value
    return True

def _is_required_path(schema: dict, content_def: dict, path: str) -> bool:
    """pathの直下フィールドが、その階層のschema required配列に含まれるか判定する
    （トップレベルはschema自身、content配下はcontent_defのrequiredを見る）。"""
    parts = path.split(".")
    if parts[0] == "content" and len(parts) >= 2:
        return parts[1] in content_def.get("required", [])
    return parts[0] in schema.get("required", [])

def _clear_path(doc: dict, path: str) -> bool:
    """path上のキーが実在すれば削除する（冪等：存在しなければ何もせずFalseを返す）。"""
    parts = path.split(".")
    cur = doc
    for p in parts[:-1]:
        if not isinstance(cur, dict) or p not in cur:
            return False
        cur = cur[p]
    if not isinstance(cur, dict) or parts[-1] not in cur:
        return False
    del cur[parts[-1]]
    return True
