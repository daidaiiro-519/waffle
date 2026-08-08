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


class UnsupportedRootDispatchShapeError(Exception):
    """add_kind_branchの対象となるルート直下のkind分岐が、既知の形状（if/then/else形式・
    allOf形式）に適合しない、またはif/then/else形式でありながらelseの暗黙kind値を
    一意に逆算できないときに送出する。"""


class UnsupportedRenderTargetShapeError(Exception):
    """set_kind_render_targetの対象schemaがx-render-target自体を持たない、または
    pathVars・path・deployのいずれかがkind別dict形式でないときに送出する。"""


def add_block(
    schema: dict, block_name: str, block_def: dict, content_def_name: str, prop_name: str, required: bool = False
) -> dict:
    """$defsに新規ブロックを追加し、対応するContent defにプロパティ参照を追加する（冪等）。

    Args:
        schema: 編集対象のschema。書き換えず、新しいdictを返す。
        block_name: $defsへ追加するブロック定義の名前。
        block_def: そのブロックの定義そのもの。
        content_def_name: 参照を追加する先のContent defの名前。
        prop_name: Content def上でそのブロックを指すプロパティ名。
        required: 対象Content defのrequired配列にもprop_nameを追加するか。
            公開済みkindに対して行うと後方互換違反になりうるので、
            呼び出し側がcheck_backward_compatibleで確認する。

    Returns:
        ブロックを追加した新しいschema。既に存在すれば元のschemaをそのまま。

    Raises:
        なし。
    """
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
    一貫してリネームする（冪等）。

    Args:
        schema: 編集対象のschema。
        old_short_name: リネーム元の短縮名（Block接尾辞を除いたもの）。
        new_short_name: リネーム先の短縮名。

    Returns:
        リネーム後の新しいschema。旧ブロックが既に無く新ブロックが既にあれば、
        完了済みとみなして元のschemaをそのまま。

    Raises:
        BlockNotFoundError: リネーム元・リネーム先のいずれも$defsに存在しない。
    """
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


def set_field(schema: dict, def_name: str | None, field_path: str, value) -> dict:
    """$defs[def_name]内のドットパス(field_path)が指す値をvalueに書き換える（冪等・対象外は不変）。
    ブロックの内容変更（x-render・title・enum等）を、add_block/rename_blockが対象としない
    既存ブロックのフィールド単位で行うための汎用操作。パス中の数字は配列インデックスとして辿る
    （x-render配列内のcolumns等、リストを含む構造への部分編集に対応する）。def_nameにNoneを
    渡すと$defsではなくschemaのルート直下を対象にする（$idやproperties.schemaRef.const等、
    $defsの外側にあるフィールドの書き換えに対応する）。

    Args:
        schema: 編集対象のschema。
        def_name: 対象の$defsエントリ名。Noneならschemaのルート直下を対象にする。
        field_path: 書き換える値までのドットパス。数字は配列の位置として辿る。
        value: 書き込む値。

    Returns:
        書き換え後の新しいschema。既に同じ値なら元のschemaをそのまま。

    Raises:
        BlockNotFoundError: def_nameが$defsに存在しない。
    """
    if def_name is not None and def_name not in schema["$defs"]:
        raise BlockNotFoundError(f"{def_name} が $defs に存在しない")
    new_schema = json.loads(dump(schema))
    cur = new_schema if def_name is None else new_schema["$defs"][def_name]
    parts = field_path.split(".")
    for part in parts[:-1]:
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    last = int(parts[-1]) if isinstance(cur, list) else parts[-1]
    current = cur[last] if isinstance(cur, list) else cur.get(last)
    if current == value:
        return schema
    cur[last] = value
    return new_schema


def remove_field(schema: dict, def_name: str | None, field_path: str) -> dict:
    """$defs[def_name]内のドットパス(field_path)が指すフィールドを、キーごと取り除く（冪等）。

    set_fieldにNoneを渡してもキーは残りnullが書かれるだけで、誤って足したフィールドを
    元に戻せない。スキーマにとって「値がnull」と「そのフィールドが無い」は別の状態であり、
    前者は契約に無いキーが残り続けることを意味する。def_nameにNoneを渡すと$defsではなく
    schemaのルート直下を対象にする（set_fieldと同じ扱い）。

    Args:
        schema: 編集対象のschema。
        def_name: 対象の$defsエントリ名。Noneならschemaのルート直下を対象にする。
        field_path: 取り除くフィールドまでのドットパス。

    Returns:
        取り除いた後の新しいschema。そのフィールドが既に無ければ元のschemaをそのまま。

    Raises:
        BlockNotFoundError: def_nameが$defsに存在しない。
    """
    if def_name is not None and def_name not in schema["$defs"]:
        raise BlockNotFoundError(f"{def_name} が $defs に存在しない")
    new_schema = json.loads(dump(schema))
    cur = new_schema if def_name is None else new_schema["$defs"][def_name]
    parts = field_path.split(".")
    for part in parts[:-1]:
        key = int(part) if isinstance(cur, list) else part
        if not isinstance(cur, list) and key not in cur:
            return schema
        cur = cur[key]
    last = int(parts[-1]) if isinstance(cur, list) else parts[-1]
    if isinstance(cur, list):
        if last >= len(cur):
            return schema
    elif last not in cur:
        return schema
    del cur[last]
    return new_schema


def create_version(base_schema: dict, edits: list[dict]) -> dict:
    """base_schemaを複製し、edits（defName/fieldPath/valueの列）をset_fieldと同じ経路で順に
    適用した新しいschemaを返す。新版はまだどのDocumentも参照していない未公開の状態のため、
    check_backward_compatibleの対象にしない（呼び出し元はこの結果に対して互換性チェックを
    行わない）。

    Args:
        base_schema: 複製元のschema。
        edits: defName / fieldPath / value を持つ編集の列。順に適用する。

    Returns:
        編集を適用した新しいschema。

    Raises:
        BlockNotFoundError: 編集が指すdefNameが$defsに存在しない。
    """
    schema = json.loads(dump(base_schema))
    for edit in edits:
        schema = set_field(schema, edit.get("defName"), edit["fieldPath"], edit["value"])
    return schema


def remove_block(schema: dict, content_def_name: str, prop_name: str) -> dict:
    """$defs[content_def_name]のpropertiesからprop_nameへの参照を外す（冪等）。
    $defs内のブロック定義自体は削除しない（他のcontent defから参照され続けている
    可能性があるため）。requiredに指定されているプロパティの除去は
    check_backward_compatibleが後方互換違反として検出する（呼び出し側が確認する）。

    Args:
        schema: 編集対象のschema。
        content_def_name: 参照を外す先のContent defの名前。
        prop_name: 外すプロパティ名。

    Returns:
        参照を外した新しいschema。既に無ければ元のschemaをそのまま。

    Raises:
        BlockNotFoundError: content_def_nameが$defsに存在しない。
    """
    if content_def_name not in schema["$defs"]:
        raise BlockNotFoundError(f"{content_def_name} が $defs に存在しない")
    if prop_name not in schema["$defs"][content_def_name].get("properties", {}):
        return schema
    new_schema = json.loads(dump(schema))
    del new_schema["$defs"][content_def_name]["properties"][prop_name]
    return new_schema


def add_def(schema: dict, def_name: str, def_body: dict) -> dict:
    """$defsに、既存content defへの紐付けを持たない独立した新規エントリを追加する（冪等）。
    新しいkindのcontent def（例: RouterContent）をゼロから作るときに使う。
    紐付け（ルート直下のkind分岐への組み込み）はadd_kind_branchが別途担う。

    Args:
        schema: 編集対象のschema。
        def_name: 追加する$defsエントリの名前。
        def_body: そのエントリの定義そのもの。

    Returns:
        追加後の新しいschema。既に同名のエントリがあれば元のschemaをそのまま。

    Raises:
        なし。
    """
    if def_name in schema["$defs"]:
        return schema
    new_schema = json.loads(dump(schema))
    new_schema["$defs"][def_name] = def_body
    return new_schema


def _branch_kind_value(branch: dict, discriminator_field: str) -> str | None:
    if not isinstance(branch, dict):
        return None
    return branch.get("if", {}).get("properties", {}).get(discriminator_field, {}).get("const")


def _branch_content_ref(branch: dict) -> str | None:
    if not isinstance(branch, dict):
        return None
    return branch.get("then", {}).get("properties", {}).get("content", {}).get("$ref")


def _make_branch(discriminator_field: str, kind_value: str, content_def_name: str) -> dict:
    return {
        "if": {"properties": {discriminator_field: {"const": kind_value}}, "required": [discriminator_field]},
        "then": {"properties": {"content": {"$ref": f"#/$defs/{content_def_name}"}}},
    }


def add_kind_branch(schema: dict, discriminator_field: str, kind_value: str, content_def_name: str) -> dict:
    """discriminatorフィールドのenumに新しいkind値を追加し、ルート直下のkind分岐に
    新しいブランチを追加する（冪等）。既存がif/then/else形式（2値限定の二分岐）の場合は、
    elseブランチが暗黙に表していたkind値をenumから逆算した上でallOf形式（N分岐）に
    正規化してから新ブランチを追加する（enumがkind値の唯一の情報源になるよう、
    暗黙のelseを残さない）。

    Args:
        schema: 編集対象のschema。
        discriminator_field: kindを表すフィールド名。
        kind_value: 追加するkindの値。
        content_def_name: そのkindが指すContent defの名前。

    Returns:
        分岐を追加した新しいschema。既に同じkindがあれば元のschemaをそのまま。

    Raises:
        UnsupportedRootDispatchShapeError: ルート直下のkind分岐が、
            if/then/else形式でもallOf形式でもない未知の形をしている。
    """
    new_content_ref = f"#/$defs/{content_def_name}"

    if "allOf" in schema:
        branches = schema["allOf"]
        if not isinstance(branches, list) or not all(_branch_kind_value(b, discriminator_field) for b in branches):
            raise UnsupportedRootDispatchShapeError("allOfの各要素がkind分岐（if/then）の形状に適合しない")
        existing = {_branch_kind_value(b, discriminator_field): _branch_content_ref(b) for b in branches}
        enum = schema["properties"][discriminator_field]["enum"]
        if existing.get(kind_value) == new_content_ref and kind_value in enum:
            return schema
        new_schema = json.loads(dump(schema))
        if kind_value not in existing:
            new_schema["allOf"].append(_make_branch(discriminator_field, kind_value, content_def_name))
        if kind_value not in new_schema["properties"][discriminator_field]["enum"]:
            new_schema["properties"][discriminator_field]["enum"].append(kind_value)
        return new_schema

    if "if" in schema and "then" in schema and "else" in schema:
        enum = schema["properties"][discriminator_field]["enum"]
        if len(enum) != 2:
            raise UnsupportedRootDispatchShapeError(
                "if/then/else形式だがenumが2値ではない（elseの暗黙kind値を一意に逆算できない）"
            )
        if_kind_value = _branch_kind_value(schema, discriminator_field)
        if if_kind_value not in enum:
            raise UnsupportedRootDispatchShapeError("if分岐のconstがenumに含まれない")
        else_candidates = [v for v in enum if v != if_kind_value]
        if len(else_candidates) != 1:
            raise UnsupportedRootDispatchShapeError("elseの暗黙kind値を一意に逆算できない")
        else_kind_value = else_candidates[0]
        if_content_ref = _branch_content_ref(schema)
        else_content_ref = schema["else"]["properties"]["content"]["$ref"]

        if kind_value == if_kind_value and if_content_ref == new_content_ref:
            return schema
        if kind_value == else_kind_value and else_content_ref == new_content_ref:
            return schema

        new_schema = json.loads(dump(schema))
        del new_schema["if"]
        del new_schema["then"]
        del new_schema["else"]
        new_schema["allOf"] = [
            _make_branch(discriminator_field, if_kind_value, if_content_ref.removeprefix("#/$defs/")),
            {
                "if": {"properties": {discriminator_field: {"const": else_kind_value}}, "required": [discriminator_field]},
                "then": {"properties": {"content": {"$ref": else_content_ref}}},
            },
        ]
        if kind_value not in (if_kind_value, else_kind_value):
            new_schema["allOf"].append(_make_branch(discriminator_field, kind_value, content_def_name))
            new_schema["properties"][discriminator_field]["enum"].append(kind_value)
        return new_schema

    raise UnsupportedRootDispatchShapeError("ルート直下の分岐がif/then/else形式でもallOf形式でもない")


def set_kind_render_target(schema: dict, kind_value: str, path_vars: dict, path: str, deploy: list) -> dict:
    """x-render-target.pathVars/path/deploy（いずれもkind別dict形式）に、新しいkind値の
    エントリを追加する（冪等）。add_kind_branchが担うルート直下のkind分岐（content参照）とは
    別に、render/deploy先を決めるx-render-target側にもkind別のエントリが必要なため。

    Args:
        schema: 編集対象のschema。
        kind_value: エントリを追加するkindの値。
        path_vars: そのkindの描画に使うパス変数。
        path: そのkindの描画先。
        deploy: そのkindの配置先の一覧。

    Returns:
        エントリを追加した新しいschema。既に同じ内容なら元のschemaをそのまま。

    Raises:
        UnsupportedRenderTargetShapeError: x-render-target自体が無い、または
            pathVars/path/deployがkind別のdict形式になっていない。
    """
    target = schema.get("x-render-target")
    if not isinstance(target, dict):
        raise UnsupportedRenderTargetShapeError("x-render-targetが存在しない")
    for key in ("pathVars", "path", "deploy"):
        if key in target and not isinstance(target[key], dict):
            raise UnsupportedRenderTargetShapeError(f"x-render-target.{key}がkind別dict形式ではない")

    current_path_vars = target.get("pathVars", {}).get(kind_value)
    current_path = target.get("path", {}).get(kind_value)
    current_deploy = target.get("deploy", {}).get(kind_value)
    if current_path_vars == path_vars and current_path == path and current_deploy == deploy:
        return schema

    new_schema = json.loads(dump(schema))
    new_target = new_schema["x-render-target"]
    new_target.setdefault("pathVars", {})[kind_value] = path_vars
    new_target.setdefault("path", {})[kind_value] = path
    new_target.setdefault("deploy", {})[kind_value] = deploy
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

    Args:
        old_schema: 変更前のschema。
        new_schema: 変更後のschema。

    Returns:
        後方互換を壊す変更の説明の一覧。壊すものが無ければ空配列。

    Raises:
        なし。
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
    """agg-schemaが定める整形でschemaを文字列にする。

    Args:
        schema: 文字列にするschema。

    Returns:
        2スペース字下げ・非ASCIIをそのまま・末尾に改行を持つJSON文字列。

    Raises:
        なし。
    """
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
