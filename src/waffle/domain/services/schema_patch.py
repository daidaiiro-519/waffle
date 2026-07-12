"""schema_patch — Schema定義ファイル自体への構造化編集(add_block/rename_block)を、
素のdict操作＋契約整形(json.dumps(indent=2, ensure_ascii=False))で行う純粋なドメインサービス。
uc-patch-schemaが使う（uc-scaffold-documentがdocument.jsonに対して持つ「AIは値だけ、
構造は機械が守る」というHarness原則を、Schema自体の編集にも適用する）。

再現性はバイト同一性の追求ではなく、agg-schemaが定める整形契約への適合で担保する
（brainstorm-cli-native-document-and-schema-editing.md参照）。
"""
from __future__ import annotations

import json
import re

import jsonpatch


class BlockNotFoundError(Exception):
    """rename_blockでリネーム元・リネーム先のいずれも存在しないときに送出する。"""


def add_block(
    schema: dict, block_name: str, block_def: dict, content_def_name: str, prop_name: str, required: bool = False
) -> dict:
    """$defsに新規ブロックを追加し、対応するContent defにプロパティ参照を追加する（冪等）。
    required=Trueの場合、対象Content defのrequired配列にもprop_nameを追加する
    （公開済みkindに対して行うと後方互換違反になりうる。呼び出し側がcheck_backward_compatibleで確認する）。"""
    if block_name in schema["$defs"]:
        return schema
    new_schema = json.loads(dump(schema))
    new_schema["$defs"][block_name] = block_def
    new_schema["$defs"][content_def_name]["properties"][prop_name] = {"$ref": f"#/$defs/{block_name}"}
    if required:
        req = new_schema["$defs"][content_def_name].setdefault("required", [])
        if prop_name not in req:
            req.append(prop_name)
    return new_schema


def rename_block(schema: dict, old_short_name: str, new_short_name: str) -> dict:
    """$defsキー名・blockType const・プロパティキー名・required配列・$ref参照文字列を
    一貫してリネームする（冪等。旧ブロックが既に無く新ブロックが既にあれば完了済みとみなす）。"""
    old_block, new_block = f"{old_short_name}Block", f"{new_short_name}Block"
    if old_block not in schema["$defs"]:
        if new_block in schema["$defs"]:
            return schema
        raise BlockNotFoundError(f"{old_block} も {new_block} も $defs に存在しない")

    old_prop = old_short_name[0].lower() + old_short_name[1:]
    new_prop = new_short_name[0].lower() + new_short_name[1:]
    old_ref = f"#/$defs/{old_block}"
    new_ref = f"#/$defs/{new_block}"

    def _walk(obj):
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                new_k = new_block if k == old_block else (new_prop if k == old_prop else k)
                if isinstance(v, str):
                    # blockType の const 値だけが短縮名そのものを識別子として持つ。
                    # それ以外の文字列値（x-prompt-write本文・default値等）は、
                    # 偶然同じ文字列であっても識別子としての参照ではないため書き換えない。
                    if k == "const" and v == old_short_name:
                        new_v = new_short_name
                    else:
                        new_v = v.replace(old_ref, new_ref)
                else:
                    new_v = _walk(v)
                out[new_k] = new_v
            return out
        if isinstance(obj, list):
            return [(new_prop if v == old_prop else _walk(v)) for v in obj]
        return obj

    return _walk(schema)


def set_field(schema: dict, def_name: str, field_path: str, value) -> dict:
    """$defs[def_name]内のドットパス(field_path)が指す値をvalueに書き換える（冪等・対象外は不変）。
    ブロックの内容変更（x-render・title・enum等）を、add_block/rename_blockが対象としない
    既存ブロックのフィールド単位で行うための汎用操作。"""
    if def_name not in schema["$defs"]:
        raise BlockNotFoundError(f"{def_name} が $defs に存在しない")
    new_schema = json.loads(dump(schema))
    cur = new_schema["$defs"][def_name]
    parts = field_path.split(".")
    for part in parts[:-1]:
        cur = cur[part]
    if cur.get(parts[-1]) == value:
        return schema
    cur[parts[-1]] = value
    return new_schema


def remove_block(schema: dict, content_def_name: str, prop_name: str) -> dict:
    """$defs[content_def_name]のpropertiesからprop_nameへの参照を外す（冪等）。
    $defs内のブロック定義自体は削除しない（他のcontent defから参照され続けている
    可能性があるため）。requiredに指定されているプロパティの除去は
    check_backward_compatibleが後方互換違反として検出する（呼び出し側が確認する）。"""
    if content_def_name not in schema["$defs"]:
        raise BlockNotFoundError(f"{content_def_name} が $defs に存在しない")
    if prop_name not in schema["$defs"][content_def_name].get("properties", {}):
        return schema
    new_schema = json.loads(dump(schema))
    del new_schema["$defs"][content_def_name]["properties"][prop_name]
    return new_schema


_REQUIRED_ENTRY = re.compile(r"/required/\d+$")
_PROPERTY_ENTRY = re.compile(r"^/\$defs/([^/]+)/properties/([^/]+)$")


def check_backward_compatible(old_schema: dict, new_schema: dict) -> list[str]:
    """既存instanceを壊しうる変更（公開済みkindのrequired配列への追加・エントリのリネーム、
    既存フィールドの型変更、必須プロパティの除去等）を検出する。違反が無ければ空配列。

    jsonpatchはrequired配列の変更を常に要素単位のadd/replace（例: /required/0）として
    表現し、配列全体を丸ごとreplaceすることはない。エントリのリネーム（rename_block）も
    要素単位のreplaceとして現れ、旧エントリ名を持つ既存instanceを壊しうる点でadd と
    同じ扱いが必要（remove単体は制約が緩む方向のため許容する）。
    """
    patch = jsonpatch.make_patch(old_schema, new_schema)
    violations: list[str] = []
    for op in list(patch):
        path = op["path"]
        if op["op"] in ("add", "replace") and _REQUIRED_ENTRY.search(path):
            violations.append(f"required配列への追加・変更は後方互換を壊す: {path}")
        if op["op"] == "replace" and path.endswith("/type"):
            violations.append(f"既存フィールドの型変更は後方互換を壊す: {path}")
        if op["op"] == "remove" and (m := _PROPERTY_ENTRY.match(path)):
            content_def_name, prop_name = m.groups()
            required = old_schema["$defs"].get(content_def_name, {}).get("required", [])
            if prop_name in required:
                violations.append(f"必須プロパティの除去は後方互換を壊す: {path}")
    return violations


def dump(schema: dict) -> str:
    """agg-schemaが定める整形契約。"""
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
