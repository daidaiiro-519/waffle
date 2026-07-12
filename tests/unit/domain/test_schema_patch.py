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
