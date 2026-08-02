"""schema_patch（Schema定義ファイルへの構造化編集）のネイティブテスト。

uc-patch-schemaの受け入れ基準・操作保証に対応する。純粋なdict操作のみで
port(DocumentRepository/SchemaRepository)を必要としないため、全件をdomain層に置く。
"""
import json

from waffle.domain.services import schema_patch


def _base_schema() -> dict:
    return {
        "$defs": {
            "SomeContent": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"$ref": "#/$defs/TitleBlock"},
                },
            },
            "TitleBlock": {
                "type": "object",
                "required": ["blockType", "title"],
                "properties": {
                    "blockType": {"type": "string", "const": "Title"},
                    "title": {"type": "string"},
                },
            },
        }
    }


def _new_block() -> dict:
    return {
        "type": "object",
        "required": ["blockType", "note"],
        "properties": {
            "blockType": {"type": "string", "const": "Note"},
            "note": {"type": "string"},
        },
    }


# --- add_block ---

def test_add_blockはdefsとcontent_defのプロパティ参照を追加する():
    """
    Given ブロック名・ブロック定義・紐付け先のContent def名・プロパティ名
    When add_blockを実行する
    Then $defsに新規ブロックが追加され、対応するContent defにプロパティ参照が追加される
    """
    schema = _base_schema()
    result = schema_patch.add_block(schema, "NoteBlock", _new_block(), "SomeContent", "note")
    assert "NoteBlock" in result["$defs"]
    assert result["$defs"]["SomeContent"]["properties"]["note"] == {"$ref": "#/$defs/NoteBlock"}


def test_add_blockは既存の他のブロックを変更しない():
    """
    Given 既存のブロックを含むschema
    When 新規ブロックをadd_blockする
    Then 既存のブロックの内容は変わらない
    """
    schema = _base_schema()
    before_title_block = json.loads(json.dumps(schema["$defs"]["TitleBlock"]))
    result = schema_patch.add_block(schema, "NoteBlock", _new_block(), "SomeContent", "note")
    assert result["$defs"]["TitleBlock"] == before_title_block


def test_add_blockは既に存在するブロックに対して冪等である():
    """
    Given 既に追加済みのブロック名を含むadd_block操作
    When add_blockを再実行する
    Then 対象は無変更のまま成功する
    """
    schema = _base_schema()
    once = schema_patch.add_block(schema, "NoteBlock", _new_block(), "SomeContent", "note")
    twice = schema_patch.add_block(once, "NoteBlock", _new_block(), "SomeContent", "note")
    assert schema_patch.dump(once) == schema_patch.dump(twice)


# --- rename_block ---

def test_rename_blockはdefsキー_const_プロパティキー_ref参照を一貫してリネームする():
    """
    Given 旧短縮名・新短縮名
    When rename_blockを実行する
    Then $defsキー名・blockType const・プロパティキー名・required配列内エントリ・
    $ref参照文字列がすべて新短縮名に一貫してリネームされる
    """
    schema = _base_schema()
    result = schema_patch.rename_block(schema, "Title", "Heading")
    assert "HeadingBlock" in result["$defs"]
    assert "TitleBlock" not in result["$defs"]
    assert result["$defs"]["HeadingBlock"]["properties"]["blockType"]["const"] == "Heading"
    assert "heading" in result["$defs"]["SomeContent"]["properties"]
    assert result["$defs"]["SomeContent"]["properties"]["heading"] == {"$ref": "#/$defs/HeadingBlock"}
    assert "heading" in result["$defs"]["SomeContent"]["required"]
    assert "title" not in result["$defs"]["SomeContent"]["properties"]
    assert "title" not in result["$defs"]["SomeContent"]["required"]


def test_rename_blockは無関係な箇所にある同名の文字列値を変更しない():
    """
    Given リネーム対象の短縮名と偶然同じ文字列値を、無関係なブロックの無関係なフィールドに持つschema
    When rename_blockを実行する
    Then その無関係な文字列値は変更されない（識別子としての一致だけを対象にする）
    """
    schema = _base_schema()
    schema["$defs"]["NoteBlock"] = {
        "type": "object",
        "required": ["blockType", "note"],
        "properties": {
            "blockType": {"type": "string", "const": "Note"},
            "note": {"type": "string", "default": "Title"},
        },
    }
    result = schema_patch.rename_block(schema, "Title", "Heading")
    assert result["$defs"]["NoteBlock"]["properties"]["note"]["default"] == "Title"


def test_rename_blockは既にリネーム済みの状態に対して冪等である():
    """
    Given リネーム元が既に存在せずリネーム先が既に存在する状態
    When 同じrename_block操作を再実行する
    Then 対象は無変更のまま成功する
    """
    schema = _base_schema()
    once = schema_patch.rename_block(schema, "Title", "Heading")
    twice = schema_patch.rename_block(once, "Title", "Heading")
    assert schema_patch.dump(once) == schema_patch.dump(twice)


def test_rename_blockはリネーム元も先も存在しなければ拒否する():
    """
    Given リネーム元・リネーム先のいずれも存在しないschema
    When rename_blockを実行する
    Then BLOCK_NOT_FOUNDに相当する例外が送出される
    """
    schema = _base_schema()
    try:
        schema_patch.rename_block(schema, "NoSuchBlock", "AlsoNoSuchBlock")
        assert False, "例外が送出されなかった"
    except schema_patch.BlockNotFoundError:
        pass


# --- set_field ---

def test_set_fieldは指定したdefの指定したドットパスの値を書き換える():
    """
    Given def名・ドットパス・新しい値
    When set_fieldを実行する
    Then そのdef内の指定パスの値だけが書き換わる
    """
    schema = _base_schema()
    result = schema_patch.set_field(schema, "TitleBlock", "properties.title.type", "number")
    assert result["$defs"]["TitleBlock"]["properties"]["title"]["type"] == "number"


def test_set_fieldは対象外のdefを変更しない():
    """
    Given 複数のdefを含むschema
    When 1つのdefにset_fieldする
    Then 他のdefの内容は変わらない
    """
    schema = _base_schema()
    before_content = json.loads(json.dumps(schema["$defs"]["SomeContent"]))
    result = schema_patch.set_field(schema, "TitleBlock", "properties.title.type", "number")
    assert result["$defs"]["SomeContent"] == before_content


def test_set_fieldは同じ値への書き込みに対して冪等である():
    """
    Given 既に目的の値になっているフィールド
    When 同じ値でset_fieldを再実行する
    Then 出力は変更前と完全に同一である
    """
    schema = _base_schema()
    once = schema_patch.set_field(schema, "TitleBlock", "properties.title.type", "number")
    twice = schema_patch.set_field(once, "TitleBlock", "properties.title.type", "number")
    assert schema_patch.dump(once) == schema_patch.dump(twice)


def test_set_fieldはドットパス中の数字を配列インデックスとして辿る():
    """
    Given x-render配列を含むdefと、数字を含むドットパス（例: x-render.0.columns.1.bullet）
    When set_fieldを実行する
    Then 配列の該当インデックスの値だけが書き換わる
    """
    schema = _base_schema()
    schema["$defs"]["TitleBlock"]["x-render"] = [
        {"as": "table", "columns": [{"field": "code"}, {"field": "condition"}]}
    ]
    result = schema_patch.set_field(schema, "TitleBlock", "x-render.0.columns.1.bullet", True)
    assert result["$defs"]["TitleBlock"]["x-render"][0]["columns"][1]["bullet"] is True
    assert result["$defs"]["TitleBlock"]["x-render"][0]["columns"][0] == {"field": "code"}


def test_set_fieldはdefNameがNoneのときschemaのルート直下を書き換える():
    """
    Given defNameにNone、ルート直下のドットパス（例: properties.schemaRef.const）
    When set_fieldを実行する
    Then $defsではなくschemaのルート直下の値が書き換わる
    """
    schema = _base_schema()
    schema["properties"] = {"schemaRef": {"const": "Foo/v1"}}
    result = schema_patch.set_field(schema, None, "properties.schemaRef.const", "Foo/v2")
    assert result["properties"]["schemaRef"]["const"] == "Foo/v2"
    assert result["$defs"] == schema["$defs"]


def test_set_fieldは存在しないdefを拒否する():
    """
    Given schemaの$defsに存在しないdef名
    When set_fieldを実行する
    Then BLOCK_NOT_FOUNDに相当する例外が送出される
    """
    schema = _base_schema()
    try:
        schema_patch.set_field(schema, "NoSuchBlock", "properties.title.type", "number")
        assert False, "例外が送出されなかった"
    except schema_patch.BlockNotFoundError:
        pass


# --- create_version ---

def test_create_versionはeditsを順に適用した新しいschemaを返す():
    """
    Given 既存schemaと複数のフィールド編集(edits)
    When create_versionを実行する
    Then 各editが順に適用された新しいschemaが返る
    """
    schema = _base_schema()
    edits = [
        {"defName": "TitleBlock", "fieldPath": "properties.title.type", "value": "array"},
        {"defName": "SomeContent", "fieldPath": "properties.title.description", "value": "タイトル"},
    ]
    result = schema_patch.create_version(schema, edits)
    assert result["$defs"]["TitleBlock"]["properties"]["title"]["type"] == "array"
    assert result["$defs"]["SomeContent"]["properties"]["title"]["description"] == "タイトル"


def test_create_versionは元のschemaを変更しない():
    """
    Given 既存schema
    When create_versionを実行する
    Then 引数として渡した元のschemaは変更されない
    """
    schema = _base_schema()
    before = json.loads(json.dumps(schema))
    schema_patch.create_version(schema, [{"defName": "TitleBlock", "fieldPath": "properties.title.type", "value": "array"}])
    assert schema == before


# --- remove_block ---

def test_remove_blockはcontent_defのプロパティ参照を外す():
    """
    Given optionalなプロパティ参照を持つcontent def
    When remove_blockを実行する
    Then そのプロパティ参照がcontent defから外れる
    """
    schema = schema_patch.add_block(_base_schema(), "NoteBlock", _new_block(), "SomeContent", "note", required=False)
    result = schema_patch.remove_block(schema, "SomeContent", "note")
    assert "note" not in result["$defs"]["SomeContent"]["properties"]


def test_remove_blockはブロック定義自体を削除しない():
    """
    Given optionalなプロパティ参照を持つcontent def
    When remove_blockを実行する
    Then $defs内のブロック定義自体は残る（他のcontent defから参照されうるため）
    """
    schema = schema_patch.add_block(_base_schema(), "NoteBlock", _new_block(), "SomeContent", "note", required=False)
    result = schema_patch.remove_block(schema, "SomeContent", "note")
    assert "NoteBlock" in result["$defs"]


def test_remove_blockは対象外のdefを変更しない():
    """
    Given 複数のdefを含むschema
    When 1つのcontent defからremove_blockする
    Then 他のdefの内容は変わらない
    """
    schema = schema_patch.add_block(_base_schema(), "NoteBlock", _new_block(), "SomeContent", "note", required=False)
    before_title_block = json.loads(json.dumps(schema["$defs"]["TitleBlock"]))
    result = schema_patch.remove_block(schema, "SomeContent", "note")
    assert result["$defs"]["TitleBlock"] == before_title_block


def test_remove_blockは既に存在しないプロパティに対して冪等である():
    """
    Given 既に存在しないプロパティ名
    When remove_blockを実行する
    Then 出力は変更前と完全に同一である
    """
    schema = _base_schema()
    result = schema_patch.remove_block(schema, "SomeContent", "no_such_prop")
    assert schema_patch.dump(result) == schema_patch.dump(schema)


def test_remove_blockは存在しないcontent_defを拒否する():
    """
    Given schemaの$defsに存在しないcontent def名
    When remove_blockを実行する
    Then BLOCK_NOT_FOUNDに相当する例外が送出される
    """
    schema = _base_schema()
    try:
        schema_patch.remove_block(schema, "NoSuchContent", "title")
        assert False, "例外が送出されなかった"
    except schema_patch.BlockNotFoundError:
        pass


# --- add_def ---

def _kind_dispatch_schema() -> dict:
    """if/then/else形式（2値）のkind分岐を持つschema。SkillSchemaのskillKind分岐を模す。"""
    schema = _base_schema()
    schema["properties"] = {
        "skillKind": {"type": "string", "enum": ["advisor", "custom"]},
    }
    schema["$defs"]["AdvisorContent"] = {"type": "object", "properties": {}}
    schema["$defs"]["CustomContent"] = {"type": "object", "properties": {}}
    schema["if"] = {"properties": {"skillKind": {"const": "advisor"}}, "required": ["skillKind"]}
    schema["then"] = {"properties": {"content": {"$ref": "#/$defs/AdvisorContent"}}}
    schema["else"] = {"properties": {"content": {"$ref": "#/$defs/CustomContent"}}}
    return schema


def test_add_defはdefsに独立した新規エントリを追加する():
    """
    Given def名・def定義
    When add_defを実行する
    Then $defsに新規エントリが追加される（既存content defへの紐付けは行わない）
    """
    schema = _base_schema()
    result = schema_patch.add_def(schema, "RouterContent", {"type": "object", "properties": {}})
    assert result["$defs"]["RouterContent"] == {"type": "object", "properties": {}}


def test_add_defは既存の他のdefを変更しない():
    """
    Given 既存のdefを含むschema
    When 新規defをadd_defする
    Then 既存のdefの内容は変わらない
    """
    schema = _base_schema()
    before_some_content = json.loads(json.dumps(schema["$defs"]["SomeContent"]))
    result = schema_patch.add_def(schema, "RouterContent", {"type": "object", "properties": {}})
    assert result["$defs"]["SomeContent"] == before_some_content


def test_add_defは既に存在するdefに対して冪等である():
    """
    Given 既に追加済みのdef名を含むadd_def操作
    When add_defを再実行する
    Then 対象は無変更のまま成功する
    """
    schema = _base_schema()
    once = schema_patch.add_def(schema, "RouterContent", {"type": "object", "properties": {}})
    twice = schema_patch.add_def(once, "RouterContent", {"type": "object", "properties": {}})
    assert schema_patch.dump(once) == schema_patch.dump(twice)


# --- add_kind_branch ---

def test_add_kind_branchはif_then_else形式をallOf形式に正規化し新ブランチを追加する():
    """
    Given if/then/else形式（enumが既存kind値を2つのみ持つ）のルート分岐
    When add_kind_branchを実行する
    Then discriminatorフィールドのenumに新しいkind値が追加され、
    ルート直下の分岐はallOf形式に正規化された上で新しいブランチを含む
    """
    schema = _kind_dispatch_schema()
    schema["$defs"]["RouterContent"] = {"type": "object", "properties": {}}
    result = schema_patch.add_kind_branch(schema, "skillKind", "router", "RouterContent")

    assert "if" not in result
    assert "then" not in result
    assert "else" not in result
    assert result["properties"]["skillKind"]["enum"] == ["advisor", "custom", "router"]

    branches = {b["if"]["properties"]["skillKind"]["const"]: b["then"]["properties"]["content"]["$ref"] for b in result["allOf"]}
    assert branches == {
        "advisor": "#/$defs/AdvisorContent",
        "custom": "#/$defs/CustomContent",
        "router": "#/$defs/RouterContent",
    }


def test_add_kind_branchは既にallOf形式の分岐に新ブランチを追加する():
    """
    Given 既にallOf形式のルート分岐
    When add_kind_branchを実行する
    Then discriminatorフィールドのenumに新しいkind値が追加され、allOf配列に新しいブランチが追加される
    """
    schema = _kind_dispatch_schema()
    schema["$defs"]["RouterContent"] = {"type": "object", "properties": {}}
    schema = schema_patch.add_kind_branch(schema, "skillKind", "router", "RouterContent")
    schema["$defs"]["FourthContent"] = {"type": "object", "properties": {}}

    result = schema_patch.add_kind_branch(schema, "skillKind", "fourth", "FourthContent")

    assert result["properties"]["skillKind"]["enum"] == ["advisor", "custom", "router", "fourth"]
    branches = {b["if"]["properties"]["skillKind"]["const"]: b["then"]["properties"]["content"]["$ref"] for b in result["allOf"]}
    assert branches["fourth"] == "#/$defs/FourthContent"
    assert len(result["allOf"]) == 4


def test_add_kind_branchは対象外の箇所を変更しない():
    """
    Given 既存のブロックを含むschema
    When add_kind_branchを実行する
    Then 既存のブロック($defs内の無関係なエントリ)は変わらない
    """
    schema = _kind_dispatch_schema()
    schema["$defs"]["RouterContent"] = {"type": "object", "properties": {}}
    before_title_block = json.loads(json.dumps(schema["$defs"]["TitleBlock"]))
    result = schema_patch.add_kind_branch(schema, "skillKind", "router", "RouterContent")
    assert result["$defs"]["TitleBlock"] == before_title_block


def test_add_kind_branchは既に存在するkind値_content_def紐付けに対して冪等である():
    """
    Given 既にenumとルート分岐の両方に存在するkind値・content def紐付け
    When add_kind_branchを再実行する
    Then 対象は無変更のまま成功する
    """
    schema = _kind_dispatch_schema()
    schema["$defs"]["RouterContent"] = {"type": "object", "properties": {}}
    once = schema_patch.add_kind_branch(schema, "skillKind", "router", "RouterContent")
    twice = schema_patch.add_kind_branch(once, "skillKind", "router", "RouterContent")
    assert schema_patch.dump(once) == schema_patch.dump(twice)


def test_add_kind_branchは既存2値のif_then_else形式に対して冪等である():
    """
    Given if/then/elseの既存2値(advisor/custom)そのものを対象にした add_kind_branch
    When advisor（if分岐が表すkind値）を対象に add_kind_branchを実行する
    Then 対象は無変更のまま成功する（既にif/then/elseが表現している）
    """
    schema = _kind_dispatch_schema()
    result = schema_patch.add_kind_branch(schema, "skillKind", "advisor", "AdvisorContent")
    assert schema_patch.dump(result) == schema_patch.dump(schema)


def test_add_kind_branchはif_then_elseでもallOfでもない形状を拒否する():
    """
    Given ルート直下にif/then/elseもallOfも持たないschema
    When add_kind_branchを実行する
    Then UnsupportedRootDispatchShapeErrorが送出される
    """
    schema = _base_schema()
    schema["properties"] = {"skillKind": {"type": "string", "enum": ["advisor", "custom"]}}
    try:
        schema_patch.add_kind_branch(schema, "skillKind", "router", "RouterContent")
        assert False, "例外が送出されなかった"
    except schema_patch.UnsupportedRootDispatchShapeError:
        pass


def test_add_kind_branchはif_then_elseでenumが3値以上の不整合な状態を拒否する():
    """
    Given if/then/else形式でありながらenumが既に3値以上を持つ（elseの暗黙値を一意に逆算できない）schema
    When add_kind_branchを実行する
    Then UnsupportedRootDispatchShapeErrorが送出される
    """
    schema = _kind_dispatch_schema()
    schema["properties"]["skillKind"]["enum"] = ["advisor", "custom", "extra"]
    try:
        schema_patch.add_kind_branch(schema, "skillKind", "router", "RouterContent")
        assert False, "例外が送出されなかった"
    except schema_patch.UnsupportedRootDispatchShapeError:
        pass


# --- set_kind_render_target ---

def _kind_keyed_render_target_schema() -> dict:
    return {
        "$defs": {},
        "x-render-target": {
            "formats": ["md"],
            "pathVars": {"judgment": {"skillRef": "doc.skillRef"}},
            "path": {"judgment": ".waffle/templates/{documentId}.md"},
            "deploy": {"judgment": [".claude/skills/{skillRef}/references/{documentId}.md"]},
        },
    }


def test_set_kind_render_targetはpathVars_path_deployのkind別dictに新しいエントリを追加する():
    """
    Given kind値・pathVars・path・deploy、およびpathVars/path/deployがkind別dict形式のschema
    When set_kind_render_targetを実行する
    Then x-render-target.pathVars/path/deployそれぞれに、そのkind値のエントリが追加される
    """
    schema = _kind_keyed_render_target_schema()
    result = schema_patch.set_kind_render_target(
        schema,
        "investigation-report",
        {"skillRef": "doc.skillRef"},
        ".waffle/templates/{documentId}.md",
        [".claude/skills/{skillRef}/references/{documentId}.md"],
    )
    target = result["x-render-target"]
    assert target["pathVars"]["investigation-report"] == {"skillRef": "doc.skillRef"}
    assert target["path"]["investigation-report"] == ".waffle/templates/{documentId}.md"
    assert target["deploy"]["investigation-report"] == [".claude/skills/{skillRef}/references/{documentId}.md"]


def test_set_kind_render_targetは既存の他のkindのエントリを変更しない():
    """
    Given 既存kindのエントリを含むschema
    When 新しいkindをset_kind_render_targetする
    Then 既存kind（judgment）のエントリは変わらない
    """
    schema = _kind_keyed_render_target_schema()
    result = schema_patch.set_kind_render_target(
        schema,
        "investigation-report",
        {"skillRef": "doc.skillRef"},
        ".waffle/templates/{documentId}.md",
        [".claude/skills/{skillRef}/references/{documentId}.md"],
    )
    target = result["x-render-target"]
    assert target["pathVars"]["judgment"] == {"skillRef": "doc.skillRef"}
    assert target["path"]["judgment"] == ".waffle/templates/{documentId}.md"
    assert target["deploy"]["judgment"] == [".claude/skills/{skillRef}/references/{documentId}.md"]


def test_set_kind_render_targetは既に一致するエントリに対して冪等である():
    """
    Given 既にpathVars・path・deployの全てで指定した値と一致するkind値のエントリ
    When set_kind_render_targetを再実行する
    Then 対象は無変更のまま成功する
    """
    schema = _kind_keyed_render_target_schema()
    once = schema_patch.set_kind_render_target(
        schema,
        "investigation-report",
        {"skillRef": "doc.skillRef"},
        ".waffle/templates/{documentId}.md",
        [".claude/skills/{skillRef}/references/{documentId}.md"],
    )
    twice = schema_patch.set_kind_render_target(
        once,
        "investigation-report",
        {"skillRef": "doc.skillRef"},
        ".waffle/templates/{documentId}.md",
        [".claude/skills/{skillRef}/references/{documentId}.md"],
    )
    assert schema_patch.dump(once) == schema_patch.dump(twice)


def test_set_kind_render_targetはx_render_targetが無いschemaを拒否する():
    """
    Given x-render-target自体を持たないschema
    When set_kind_render_targetを実行する
    Then UnsupportedRenderTargetShapeErrorが送出される
    """
    schema = {"$defs": {}}
    try:
        schema_patch.set_kind_render_target(schema, "investigation-report", {}, "path", ["deploy"])
        assert False, "例外が送出されなかった"
    except schema_patch.UnsupportedRenderTargetShapeError:
        pass


def test_set_kind_render_targetはpath_がフラット形式のschemaを拒否する():
    """
    Given x-render-target.pathがkind別dictでなくフラットな文字列であるschema
    When set_kind_render_targetを実行する
    Then UnsupportedRenderTargetShapeErrorが送出される
    """
    schema = {
        "$defs": {},
        "x-render-target": {"formats": ["md"], "path": ".waffle/skills/{documentId}/SKILL.md"},
    }
    try:
        schema_patch.set_kind_render_target(schema, "investigation-report", {}, "path", ["deploy"])
        assert False, "例外が送出されなかった"
    except schema_patch.UnsupportedRenderTargetShapeError:
        pass


# --- check_backward_compatible ---

def test_公開済みkindのrequiredへの追加は後方互換違反として検出される():
    """
    Given 公開済みkindのContent defのrequired配列に新規エントリを追加する変更
    When 後方互換チェックを実行する
    Then 違反として検出される
    """
    old_schema = _base_schema()
    new_schema = schema_patch.add_block(old_schema, "NoteBlock", _new_block(), "SomeContent", "note", required=True)
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations, "required配列への追加が検出されなかった"


def test_optionalプロパティの追加は後方互換違反にならない():
    """
    Given requiredに含めずに新規プロパティのみ追加した変更後schema
    When 後方互換チェックを実行する
    Then 違反として検出されない
    """
    old_schema = _base_schema()
    new_schema = schema_patch.add_block(old_schema, "NoteBlock", _new_block(), "SomeContent", "note")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations == []


def test_必須プロパティのremove_blockは後方互換違反として検出される():
    """
    Given requiredに指定されているプロパティをremove_blockで除去した変更後schema
    When 後方互換チェックを実行する
    Then 違反として検出される
    """
    old_schema = _base_schema()
    new_schema = schema_patch.remove_block(old_schema, "SomeContent", "title")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations, "必須プロパティのremove_blockが検出されなかった"


def test_必須でないプロパティのremove_blockは後方互換違反にならない():
    """
    Given requiredに含まれないプロパティをremove_blockで除去した変更後schema
    When 後方互換チェックを実行する
    Then 違反として検出されない
    """
    old_schema = schema_patch.add_block(_base_schema(), "NoteBlock", _new_block(), "SomeContent", "note", required=False)
    new_schema = schema_patch.remove_block(old_schema, "SomeContent", "note")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations == []


def test_必須プロパティのリネームは後方互換違反として検出される():
    """
    Given 公開済みkindのContent defでrequiredに指定されているブロックのリネーム
    When 後方互換チェックを実行する
    Then 違反として検出される（旧プロパティ名を持つ既存instanceが新schemaのrequiredを満たせなくなるため）
    """
    old_schema = _base_schema()
    new_schema = schema_patch.rename_block(old_schema, "Title", "Heading")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations, "requiredプロパティのリネームが検出されなかった"


def test_必須でないプロパティのリネームは後方互換違反にならない():
    """
    Given 公開済みkindのContent defでrequiredに指定されていないブロックのリネーム
    When 後方互換チェックを実行する
    Then 違反として検出されない
    """
    old_schema = _base_schema()
    old_schema = schema_patch.add_block(old_schema, "NoteBlock", _new_block(), "SomeContent", "note")
    new_schema = schema_patch.rename_block(old_schema, "Note", "Memo")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations == []


def test_既存フィールドの型変更は後方互換違反として検出される():
    """
    Given 公開済みkindの既存フィールドの型(type)を書き換える変更
    When 後方互換チェックを実行する
    Then 違反として検出される（旧型の値を持つ既存instanceが新schemaの型制約を満たせなくなるため）
    """
    old_schema = _base_schema()
    new_schema = schema_patch.set_field(old_schema, "TitleBlock", "properties.title.type", "number")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations, "既存フィールドの型変更が検出されなかった"


def test_型を変更しないset_fieldは後方互換違反にならない():
    """
    Given 型(type)以外のフィールドを書き換えるset_field
    When 後方互換チェックを実行する
    Then 違反として検出されない
    """
    old_schema = _base_schema()
    new_schema = schema_patch.set_field(old_schema, "TitleBlock", "properties.title.description", "タイトル文字列")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations == []


# --- dump（契約整形） ---

def test_dumpはjson_dumps_indent2_ensure_ascii_falseと完全一致する():
    """
    Given 任意のschema(dict)
    When dumpを適用する
    Then 出力はjson.dumps(schema, indent=2, ensure_ascii=False)+改行と完全一致する
    """
    schema = _base_schema()
    assert schema_patch.dump(schema) == json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
