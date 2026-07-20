"""schemaのcontent定義から、x-prompt-writeを持つ値フィールドのpath一覧（fillTemplate）を
機械的に走査するドメインサービス。ScaffoldDocument（値埋め込みの土台）とCheckSchemaVersionDrift
（documentが現行schemaの宣言する項目に追従しているかの確認）の両方が使う純ロジック。
"""
from __future__ import annotations

import copy


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


def _select_prompt(value, spec_kind: str | None):
    """x-prompt-write は、フラットな文字列（discriminator非依存）か discriminatorごとの
    辞書（kind→文言）のどちらでも書ける。辞書なら該当spec_kindの文言を選ぶ（render_document.py の
    _select_template/_select_deploy と同型の規約）。"""
    if isinstance(value, dict):
        return value.get(spec_kind, "") if spec_kind else ""
    return value


def build_fill_template(schema: dict, content: dict, spec_kind: str | None = None) -> list:
    entries: list = []
    _walk_fill(schema, content, "content", entries, is_required=True, spec_kind=spec_kind)
    return entries


def build_top_level_fill_template(schema: dict, protected: set, spec_kind: str | None = None) -> list:
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
        _walk_fill(schema, prop, key, entries, is_required=key in required, spec_kind=spec_kind)
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


def discriminator_candidates(schema: dict, key: str) -> list:
    return schema.get("properties", {}).get(key, {}).get("enum", [])


def skeleton_from_def(schema: dict, d: dict):
    if "$ref" in d:
        return skeleton_from_def(schema, resolve_ref(schema, d["$ref"]))
    if "const" in d:
        return d["const"]
    if "enum" in d:
        return d["enum"][0]
    t = d.get("type")
    if t == "object":
        return {k: skeleton_from_def(schema, v) for k, v in d.get("properties", {}).items()}
    if t == "array":
        return []
    if t == "string":
        return ""
    if t in ("number", "integer"):
        return 0
    if t == "boolean":
        return False
    return None


def build_skeleton(schema, document_id, disc_key, discriminator, content_def, extra_refs) -> dict:
    props = schema.get("properties", {})
    out: dict = {}
    for name in schema.get("required", []):
        if name == "documentId":
            out[name] = document_id
        elif name == disc_key:
            out[name] = discriminator[disc_key]
        elif name == "content":
            out[name] = skeleton_from_def(schema, content_def)
        elif name in extra_refs:
            out[name] = extra_refs[name]
        else:
            out[name] = skeleton_from_def(schema, props.get(name, {}))
    if "tags" in props and "tags" not in out:
        out["tags"] = []
    for name, value in extra_refs.items():
        if name in props and name not in out and name != disc_key:
            out[name] = value
    return out


def _placeholder_value(entry: dict) -> str:
    text = entry["prompt"]
    if "enum" in entry:
        text = f"{text}（選択肢: {' / '.join(entry['enum'])}）"
    return f"{{{{{text}}}}}"


def _placeholder_object(element: dict) -> dict:
    """_build_elementが作るelementマップ(値がpromptの文字列、またはネストした
    {"element": {...}}のいずれか)から、プレースホルダーオブジェクトを再帰的に作る。"""
    out: dict = {}
    for k, v in element.items():
        if isinstance(v, dict) and "element" in v:
            out[k] = [_placeholder_object(v["element"])]
        else:
            out[k] = f"{{{{{v}}}}}"
    return out


def overlay_placeholders(skeleton: dict, entries: list) -> dict:
    """skeletonのコピーに、entries(build_fill_template等の出力)が指すpathへ
    x-prompt-write本文を{{...}}プレースホルダーとして上書きする。elementを持つ配列は
    要素1件分のプレースホルダーオブジェクトを含む配列にする。副作用なし（コピーを返す）。"""
    out = copy.deepcopy(skeleton)
    for entry in entries:
        if "element" in entry:
            # 構造化要素を持つ配列: 要素1件分のプレースホルダーオブジェクトを含む配列にする。
            value = [_placeholder_object(entry["element"])]
        elif entry.get("type") == "array":
            # 単純な配列(例: tags): プレースホルダー文字列のまま代入すると、レンダラが
            # 文字列を1文字ずつの配列として反復してしまうため、必ず配列で包む。
            value = [_placeholder_value(entry)]
        else:
            value = _placeholder_value(entry)
        _set_path(out, entry["path"], value)
    return out


def _set_path(doc: dict, path: str, value) -> None:
    parts = path.split(".")
    cur = doc
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def _is_object_schema(d: dict) -> bool:
    """objectスキーマかどうかを判定する。type:objectの明示だけでなく、allOf合成
    （_merge_allofの返り値はtypeキーを持たずpropertiesキーだけを持つ）も対象にする。"""
    return d.get("type") == "object" or "properties" in d


def _walk_fill(schema, d, path, entries, is_required, spec_kind: str | None = None):
    if "$ref" in d:
        return _walk_fill(schema, resolve_ref(schema, d["$ref"]), path, entries, is_required, spec_kind)
    t = d.get("type")
    if t == "object":
        required_keys = set(d.get("required", []))
        for k, v in d.get("properties", {}).items():
            _walk_fill(schema, v, f"{path}.{k}", entries, is_required and k in required_keys, spec_kind)
        return
    if "const" in d or "x-prompt-write" not in d:
        return
    entry = {"path": path, "type": t or "any", "prompt": _select_prompt(d["x-prompt-write"], spec_kind), "required": is_required}
    if "enum" in d:
        entry["enum"] = d["enum"]
    if t == "array":
        item = d.get("items", {})
        if "$ref" in item:
            item = resolve_ref(schema, item["$ref"])
        item = _merge_allof(schema, item)
        # itemがobject型かどうかで判定する（プロパティにx-prompt-writeが1つも無い
        # object型itemもありうるため、_build_elementの結果が空でも{}を保持する。
        # そうしないとoverlay_placeholdersが単純配列と誤認し、文字列プレースホルダーを
        # 1件だけ入れてしまい、element前提のtable/section描画がAttributeErrorになる）。
        if _is_object_schema(item):
            entry["element"] = _build_element(schema, item, spec_kind=spec_kind)
    entries.append(entry)


def _build_element(schema, item, depth: int = 0, max_depth: int = 2, spec_kind: str | None = None) -> dict:
    """配列itemのプロパティごとのprompt(x-prompt-write)を集める。プロパティ自身が
    さらに構造化された配列(例: Entities.items[].attributes)の場合、ネストしたelementとして
    表現する（{"element": {...}}の形）。ネスト構造そのものは常に保持する（配列は常に
    {"element": ...}を持つ形でなければならず、途中で平坦なprompt文字列に落としてしまうと、
    x-renderは常にlistを期待するため描画がAttributeErrorになる）。ただしプロンプト文言を
    集める再帰の深さはmax_depthで打ち切り、それ以上は空のelementにする（自己参照的な
    schema、例: AgentSchemaのSubStepのchildren、で無限再帰にならないようにするため）。"""
    element: dict = {}
    for ik, iv in item.get("properties", {}).items():
        if "$ref" in iv:
            iv = resolve_ref(schema, iv["$ref"])
        if "const" in iv:
            continue
        if iv.get("type") == "array":
            sub_item = iv.get("items", {})
            if "$ref" in sub_item:
                sub_item = resolve_ref(schema, sub_item["$ref"])
            sub_item = _merge_allof(schema, sub_item)
            if _is_object_schema(sub_item):
                nested = _build_element(schema, sub_item, depth + 1, max_depth, spec_kind) if depth < max_depth else {}
                element[ik] = {"element": nested}
                continue
        if "x-prompt-write" in iv:
            element[ik] = _select_prompt(iv["x-prompt-write"], spec_kind)
    return element
