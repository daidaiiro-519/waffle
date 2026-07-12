"""schemaのcontent定義から、x-prompt-writeを持つ値フィールドのpath一覧（fillTemplate）を
機械的に走査するドメインサービス。ScaffoldDocument（値埋め込みの土台）とCheckSchemaVersionDrift
（documentが現行schemaの宣言する項目に追従しているかの確認）の両方が使う純ロジック。
"""
from __future__ import annotations


def resolve_ref(schema: dict, ref: str):
    node = schema
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def _matches(if_clause: dict, discriminator: dict) -> bool:
    for key, cond in if_clause.get("properties", {}).items():
        if "const" in cond and discriminator.get(key) != cond["const"]:
            return False
    return True


def content_def(schema: dict, discriminator: dict) -> dict:
    if "if" in schema:
        branch = schema.get("then", {}) if _matches(schema["if"], discriminator) else schema.get("else", {})
        ref = branch.get("properties", {}).get("content", {}).get("$ref")
        if ref:
            return resolve_ref(schema, ref)
    for entry in schema.get("allOf", []):
        if "if" in entry and _matches(entry["if"], discriminator):
            ref = entry.get("then", {}).get("properties", {}).get("content", {}).get("$ref")
            if ref:
                return resolve_ref(schema, ref)
    return schema.get("properties", {}).get("content", {})


def _merge_allof(schema: dict, d: dict) -> dict:
    if "allOf" not in d:
        return d
    merged: dict = {"properties": {}}
    for part in d["allOf"]:
        if "$ref" in part:
            part = resolve_ref(schema, part["$ref"])
        merged["properties"].update(part.get("properties", {}))
    merged["properties"].update(d.get("properties", {}))
    return merged


def build_fill_template(schema: dict, content: dict) -> list:
    entries: list = []
    _walk_fill(schema, content, "content", entries, is_required=True)
    return entries


def build_top_level_fill_template(schema: dict, protected: set) -> list:
    """content の外側にある値フィールド（subdomainRef/skillRef 等）の fillTemplate を走査する。

    documentId・discriminator キー（agentKind/skillKind/specKind/templateKind 等）は、
    それ自体がdocumentの識別子・構造分岐を決める値であり、作成後の書き換えは別のdocumentへの
    変質を意味するため、protected として明示的に除外する。
    """
    entries: list = []
    required = set(schema.get("required", []))
    for key, prop in schema.get("properties", {}).items():
        if key == "content" or key in protected:
            continue
        _walk_fill(schema, prop, key, entries, is_required=key in required)
    return entries


def build_const_paths(schema: dict, content: dict) -> dict:
    """constを持つ値フィールドのpath→現行schemaが宣言するconst値の対応を機械的に走査する。
    fillのconst再同期（値が現行schemaの宣言値と完全一致する場合のみの書き込み許可）が使う。"""
    paths: dict = {}
    _walk_const(schema, content, "content", paths)
    return paths


def build_top_level_const_paths(schema: dict, protected: set) -> dict:
    paths: dict = {}
    for key, prop in schema.get("properties", {}).items():
        if key == "content" or key in protected:
            continue
        _walk_const(schema, prop, key, paths)
    return paths


def _walk_const(schema, d, path, paths):
    if "$ref" in d:
        return _walk_const(schema, resolve_ref(schema, d["$ref"]), path, paths)
    if d.get("type") == "object":
        for k, v in d.get("properties", {}).items():
            _walk_const(schema, v, f"{path}.{k}", paths)
        return
    if "const" in d:
        paths[path] = d["const"]


def _walk_fill(schema, d, path, entries, is_required):
    if "$ref" in d:
        return _walk_fill(schema, resolve_ref(schema, d["$ref"]), path, entries, is_required)
    t = d.get("type")
    if t == "object":
        required_keys = set(d.get("required", []))
        for k, v in d.get("properties", {}).items():
            _walk_fill(schema, v, f"{path}.{k}", entries, is_required and k in required_keys)
        return
    if "const" in d or "x-prompt-write" not in d:
        return
    entry = {"path": path, "type": t or "any", "prompt": d["x-prompt-write"], "required": is_required}
    if "enum" in d:
        entry["enum"] = d["enum"]
    if t == "array":
        item = d.get("items", {})
        if "$ref" in item:
            item = resolve_ref(schema, item["$ref"])
        item = _merge_allof(schema, item)
        element = {
            ik: iv["x-prompt-write"]
            for ik, iv in item.get("properties", {}).items()
            if "x-prompt-write" in iv and "const" not in iv
        }
        if element:
            entry["element"] = element
    entries.append(entry)
