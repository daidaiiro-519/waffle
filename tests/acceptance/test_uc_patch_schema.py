"""uc-patch-schema の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.jsonschema_validator import JsonSchemaValidator
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.patch_schema import PatchSchema
from waffle.shared.result import Err, Ok

_FIXTURE_DIR = Path("src/waffle/domain/model/TestPatchSchemaFixture")
_FIXTURE_PATH = _FIXTURE_DIR / "v1.json"
_SCHEMA_REF = "TestPatchSchemaFixture/v1"
_FIXTURE_V2_PATH = _FIXTURE_DIR / "v2.json"


def _base_schema() -> dict:
    return {
        "$defs": {
            "SomeContent": {
                "type": "object",
                "required": ["title"],
                "properties": {"title": {"$ref": "#/$defs/TitleBlock"}},
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


def _note_block_def() -> dict:
    return {
        "type": "object",
        "required": ["blockType", "note"],
        "properties": {"blockType": {"type": "string", "const": "Note"}, "note": {"type": "string"}},
    }


def _write_fixture(schema: dict) -> None:
    _FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    _FIXTURE_PATH.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _engine() -> PatchSchema:
    return PatchSchema(FsDocumentRepository(), PackageSchemaRepository(), JsonSchemaValidator())


def setup_function():
    _write_fixture(_base_schema())


def teardown_function():
    _FIXTURE_PATH.unlink(missing_ok=True)
    _FIXTURE_V2_PATH.unlink(missing_ok=True)
    if _FIXTURE_DIR.exists() and not any(_FIXTURE_DIR.iterdir()):
        _FIXTURE_DIR.rmdir()


def test_新規ブロックを追加する():
    """
    Given ブロック名・ブロック定義・紐付け先・プロパティ名
    When add_blockを実行する
    Then Schemaに新規ブロックが追加され、指定した紐付け先から参照できるようになる
    """
    result = _engine().run("add_block", {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock",
        "blockDef": _note_block_def(),
        "contentDefName": "SomeContent",
        "propName": "note",
    })
    assert isinstance(result, Ok), result
    written = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "NoteBlock" in written["$defs"]
    assert written["$defs"]["SomeContent"]["properties"]["note"] == {"$ref": "#/$defs/NoteBlock"}


def test_対象外の箇所は一切変更されない():
    """
    Given 整形契約に従った既存のschemaファイル
    When add_blockまたはrename_blockを実行する
    Then 変更に関係のない既存の行は1バイトも変わらない
    """
    before_title_block = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))["$defs"]["TitleBlock"]
    _engine().run("add_block", {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock",
        "blockDef": _note_block_def(),
        "contentDefName": "SomeContent",
        "propName": "note",
    })
    after_title_block = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))["$defs"]["TitleBlock"]
    assert after_title_block == before_title_block

    before_title_block = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))["$defs"]["TitleBlock"]
    _engine().run("rename_block", {"schemaRef": _SCHEMA_REF, "oldName": "Note", "newName": "Memo"})
    after_title_block = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))["$defs"]["TitleBlock"]
    assert after_title_block == before_title_block


def test_既に存在するブロックの追加は無変更で成功する():
    """
    Given 既に追加済みのブロック名を含むadd_block操作
    When add_blockを再実行する
    Then 対象は無変更のまま成功する
    """
    params = {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock",
        "blockDef": _note_block_def(),
        "contentDefName": "SomeContent",
        "propName": "note",
    }
    first = _engine().run("add_block", params)
    assert isinstance(first, Ok) and first.value["changed"] is True
    after_first = _FIXTURE_PATH.read_text(encoding="utf-8")

    second = _engine().run("add_block", params)
    assert isinstance(second, Ok) and second.value["changed"] is False
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == after_first


def test_識別子を複数箇所にわたってリネームする():
    """
    Given 旧短縮名・新短縮名（必須ではないブロック）
    When rename_blockを実行する
    Then Schema内でその識別子を参照する全ての箇所が新短縮名に一貫してリネームされる
    """
    _engine().run("add_block", {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock",
        "blockDef": _note_block_def(),
        "contentDefName": "SomeContent",
        "propName": "note",
    })
    result = _engine().run("rename_block", {"schemaRef": _SCHEMA_REF, "oldName": "Note", "newName": "Memo"})
    assert isinstance(result, Ok), result
    written = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "MemoBlock" in written["$defs"]
    assert "NoteBlock" not in written["$defs"]
    assert written["$defs"]["MemoBlock"]["properties"]["blockType"]["const"] == "Memo"
    assert "memo" in written["$defs"]["SomeContent"]["properties"]


def test_必須プロパティのリネームはBACKWARD_INCOMPATIBLEとして拒否される():
    """
    Given 公開済みkindのrequiredに指定されているブロックのリネーム
    When rename_blockを実行する
    Then BACKWARD_INCOMPATIBLEエラーが返り書き込まれない
    """
    before = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("rename_block", {"schemaRef": _SCHEMA_REF, "oldName": "Title", "newName": "Heading"})
    assert isinstance(result, Err), result
    assert result.details[0] == "BACKWARD_INCOMPATIBLE"
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == before


def test_既にリネーム済みの状態への再リネームは無変更で成功する():
    """
    Given リネーム元が既に存在せずリネーム先が既に存在する状態
    When 同じrename_block操作を再実行する
    Then 対象は無変更のまま成功する
    """
    _engine().run("add_block", {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock",
        "blockDef": _note_block_def(),
        "contentDefName": "SomeContent",
        "propName": "note",
    })
    params = {"schemaRef": _SCHEMA_REF, "oldName": "Note", "newName": "Memo"}
    first = _engine().run("rename_block", params)
    assert isinstance(first, Ok) and first.value["changed"] is True
    after_first = _FIXTURE_PATH.read_text(encoding="utf-8")

    second = _engine().run("rename_block", params)
    assert isinstance(second, Ok) and second.value["changed"] is False
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == after_first


def test_既存ブロックの1フィールドだけを書き換える():
    """
    Given ブロック名・書き換える項目・新しい値
    When set_fieldを実行する
    Then そのブロックの指定した項目だけが新しい値に置き換わる
    """
    result = _engine().run("set_field", {
        "schemaRef": _SCHEMA_REF,
        "defName": "TitleBlock",
        "fieldPath": "properties.title.description",
        "value": "タイトル文字列",
    })
    assert isinstance(result, Ok), result
    written = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert written["$defs"]["TitleBlock"]["properties"]["title"]["description"] == "タイトル文字列"
    assert written["$defs"]["SomeContent"] == _base_schema()["$defs"]["SomeContent"]


def test_set_fieldはdefNameにnullを渡すとschemaのルート直下を書き換える():
    """
    Given defNameにnull・ルート直下のドットパス・新しい値
    When set_fieldを実行する
    Then $defsではなくschemaのルート直下の値が書き換わる
    """
    schema = _base_schema()
    schema["properties"] = {}
    _write_fixture(schema)

    result = _engine().run("set_field", {
        "schemaRef": _SCHEMA_REF,
        "defName": None,
        "fieldPath": "properties.newTopLevelField",
        "value": {"type": "string"},
    })
    assert isinstance(result, Ok), result
    written = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert written["properties"]["newTopLevelField"] == {"type": "string"}


def test_既存フィールドの型変更はBACKWARD_INCOMPATIBLEとして拒否される():
    """
    Given 公開済みkindの既存フィールドの型(type)を書き換える変更
    When set_fieldを実行する
    Then BACKWARD_INCOMPATIBLEエラーが返り書き込まれない
    """
    before = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("set_field", {
        "schemaRef": _SCHEMA_REF,
        "defName": "TitleBlock",
        "fieldPath": "properties.title.type",
        "value": "number",
    })
    assert isinstance(result, Err), result
    assert result.details[0] == "BACKWARD_INCOMPATIBLE"
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == before


def test_set_fieldの同じ値への再実行は無変更で成功する():
    """
    Given 既に目的の値になっている項目
    When 同じ値でset_fieldを再実行する
    Then 対象は無変更のまま成功する
    """
    params = {
        "schemaRef": _SCHEMA_REF,
        "defName": "TitleBlock",
        "fieldPath": "properties.title.description",
        "value": "タイトル文字列",
    }
    first = _engine().run("set_field", params)
    assert isinstance(first, Ok) and first.value["changed"] is True
    after_first = _FIXTURE_PATH.read_text(encoding="utf-8")

    second = _engine().run("set_field", params)
    assert isinstance(second, Ok) and second.value["changed"] is False
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == after_first


def test_存在しないブロックへのset_fieldはBLOCK_NOT_FOUND():
    """
    Given Schemaに存在しないブロック名
    When set_fieldを実行する
    Then BLOCK_NOT_FOUNDエラーが返り書き込まれない
    """
    before = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("set_field", {
        "schemaRef": _SCHEMA_REF,
        "defName": "NoSuchBlock",
        "fieldPath": "properties.title.type",
        "value": "number",
    })
    assert isinstance(result, Err), result
    assert result.details[0] == "BLOCK_NOT_FOUND"
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == before


def test_content_defからプロパティ参照を外す():
    """
    Given 必須ではないプロパティを持つcontent def名・プロパティ名
    When remove_blockを実行する
    Then そのcontent defからプロパティ参照が外れ、$defs内のブロック定義自体は変更されない
    """
    add = _engine().run("add_block", {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock", "blockDef": _note_block_def(),
        "contentDefName": "SomeContent", "propName": "note",
    })
    assert isinstance(add, Ok), add

    result = _engine().run("remove_block", {
        "schemaRef": _SCHEMA_REF,
        "contentDefName": "SomeContent", "propName": "note",
    })
    assert isinstance(result, Ok), result
    written = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "note" not in written["$defs"]["SomeContent"]["properties"]
    assert "NoteBlock" in written["$defs"]


def test_既に存在しないプロパティのremove_blockは無変更で成功する():
    """
    Given 既に除去済みのプロパティ名を含むremove_block操作
    When remove_blockを再実行する
    Then 対象は無変更のまま成功する
    """
    params = {"schemaRef": _SCHEMA_REF, "contentDefName": "SomeContent", "propName": "no_such_prop"}
    result = _engine().run("remove_block", params)
    assert isinstance(result, Ok) and result.value["changed"] is False


def test_必須プロパティのremove_blockはBACKWARD_INCOMPATIBLEとして拒否される():
    """
    Given 公開済みkindのrequiredに指定されているプロパティ
    When remove_blockを実行する
    Then BACKWARD_INCOMPATIBLEエラーが返り書き込まれない
    """
    before = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("remove_block", {
        "schemaRef": _SCHEMA_REF,
        "contentDefName": "SomeContent", "propName": "title",
    })
    assert isinstance(result, Err), result
    assert result.details[0] == "BACKWARD_INCOMPATIBLE"
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == before


def test_既存Documentを壊す変更はBACKWARD_INCOMPATIBLEとして拒否される():
    """
    Given 既存Documentを壊しうる後方互換性のない変更
    When patchを実行する
    Then BACKWARD_INCOMPATIBLEエラーが返り書き込まれない
    """
    before = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("add_block", {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock",
        "blockDef": _note_block_def(),
        "contentDefName": "SomeContent",
        "propName": "note",
        "required": True,
    })
    assert isinstance(result, Err), result
    assert result.details[0] == "BACKWARD_INCOMPATIBLE"
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == before


def test_構文的に不正な結果はINVALID_SCHEMA_STRUCTUREとして拒否される():
    """
    Given 適用するとJSON Schemaとして構文的に不正になる変更
    When patchを実行する
    Then INVALID_SCHEMA_STRUCTUREエラーが返り書き込まれない
    """
    before = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("add_block", {
        "schemaRef": _SCHEMA_REF,
        "blockName": "BrokenBlock",
        "blockDef": {"type": "not-a-real-json-schema-type"},
        "contentDefName": "SomeContent",
        "propName": "broken",
    })
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_SCHEMA_STRUCTURE"
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == before


class _BrokenWriteDocumentRepository:
    """write_text時に必ずOSErrorを送出するfake（Port障害時の振る舞いを検証する）。"""

    def write_text(self, path: str, text: str) -> None:
        raise OSError("disk full")


def test_書き込み失敗はWRITE_ERRORを返す():
    """
    Given 書き込み時にOSErrorを送出するDocumentRepository
    When add_blockを実行する
    Then WRITE_ERRORエラーが返る
    """
    engine = PatchSchema(_BrokenWriteDocumentRepository(), PackageSchemaRepository(), JsonSchemaValidator())
    result = engine.run("add_block", {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock",
        "blockDef": _note_block_def(),
        "contentDefName": "SomeContent",
        "propName": "note",
    })
    assert isinstance(result, Err), result
    assert result.details[0] == "WRITE_ERROR"


def test_解決できないschemaRefはINVALID_SCHEMA_REF():
    """
    Given 解決できないschemaRef
    When patchを実行する
    Then INVALID_SCHEMA_REFエラーが返る
    """
    result = _engine().run("add_block", {"schemaRef": "NoSuchSchema/v1"})
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_SCHEMA_REF"


def test_未知のoperationはINVALID_OPERATION():
    """
    Given add_block/rename_block/set_field/remove_block/add_def/add_kind_branch/create_version/set_kind_render_target以外のoperation
    When patchを実行する
    Then INVALID_OPERATIONエラーが返る
    """
    result = _engine().run("bogus", {"schemaRef": _SCHEMA_REF})
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_OPERATION"


def _kind_dispatch_fixture() -> dict:
    schema = _base_schema()
    schema["properties"] = {"skillKind": {"type": "string", "enum": ["advisor", "custom"]}}
    schema["$defs"]["AdvisorContent"] = {"type": "object", "properties": {}}
    schema["$defs"]["CustomContent"] = {"type": "object", "properties": {}}
    schema["if"] = {"properties": {"skillKind": {"const": "advisor"}}, "required": ["skillKind"]}
    schema["then"] = {"properties": {"content": {"$ref": "#/$defs/AdvisorContent"}}}
    schema["else"] = {"properties": {"content": {"$ref": "#/$defs/CustomContent"}}}
    return schema


def test_既存content_defへの紐付けを持たない新規defを追加する():
    """
    Given def名・def定義
    When add_defを実行する
    Then $defsに新規エントリが追加され、既存のcontent defには一切変更が加わらない
    """
    result = _engine().run("add_def", {
        "schemaRef": _SCHEMA_REF,
        "defName": "RouterContent",
        "defDef": {"type": "object", "properties": {}},
    })
    assert isinstance(result, Ok), result
    written = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert written["$defs"]["RouterContent"] == {"type": "object", "properties": {}}
    assert written["$defs"]["SomeContent"] == _base_schema()["$defs"]["SomeContent"]


def test_既に存在するdefの追加は無変更で成功する():
    """
    Given 既に追加済みのdef名を含むadd_def操作
    When add_defを再実行する
    Then 対象は無変更のまま成功する
    """
    params = {
        "schemaRef": _SCHEMA_REF,
        "defName": "RouterContent",
        "defDef": {"type": "object", "properties": {}},
    }
    first = _engine().run("add_def", params)
    assert isinstance(first, Ok) and first.value["changed"] is True
    after_first = _FIXTURE_PATH.read_text(encoding="utf-8")

    second = _engine().run("add_def", params)
    assert isinstance(second, Ok) and second.value["changed"] is False
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == after_first


def test_2値のif_then_else形式に新しいkindブランチを追加する():
    """
    Given if/then/else形式（enumが既存kind値を2つのみ持つ）のルート分岐、discriminatorフィールド名、新しいkind値、紐付け先content def名
    When add_kind_branchを実行する
    Then discriminatorフィールドのenumに新しいkind値が追加され、ルート直下の分岐はallOf形式に正規化された上で新しいブランチを含む
    """
    _write_fixture(_kind_dispatch_fixture())
    _engine().run("add_def", {
        "schemaRef": _SCHEMA_REF,
        "defName": "RouterContent",
        "defDef": {"type": "object", "properties": {}},
    })

    result = _engine().run("add_kind_branch", {
        "schemaRef": _SCHEMA_REF,
        "discriminatorField": "skillKind",
        "kindValue": "router",
        "contentDefName": "RouterContent",
    })
    assert isinstance(result, Ok), result
    written = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "if" not in written and "then" not in written and "else" not in written
    assert written["properties"]["skillKind"]["enum"] == ["advisor", "custom", "router"]
    branches = {b["if"]["properties"]["skillKind"]["const"]: b["then"]["properties"]["content"]["$ref"] for b in written["allOf"]}
    assert branches == {
        "advisor": "#/$defs/AdvisorContent",
        "custom": "#/$defs/CustomContent",
        "router": "#/$defs/RouterContent",
    }


def test_allOf形式の分岐に新しいkindブランチを追加する():
    """
    Given 既にallOf形式のルート分岐、discriminatorフィールド名、新しいkind値、紐付け先content def名
    When add_kind_branchを実行する
    Then discriminatorフィールドのenumに新しいkind値が追加され、allOf配列に新しいブランチが追加される
    """
    _write_fixture(_kind_dispatch_fixture())
    _engine().run("add_def", {
        "schemaRef": _SCHEMA_REF,
        "defName": "RouterContent",
        "defDef": {"type": "object", "properties": {}},
    })
    _engine().run("add_kind_branch", {
        "schemaRef": _SCHEMA_REF,
        "discriminatorField": "skillKind",
        "kindValue": "router",
        "contentDefName": "RouterContent",
    })
    _engine().run("add_def", {
        "schemaRef": _SCHEMA_REF,
        "defName": "FourthContent",
        "defDef": {"type": "object", "properties": {}},
    })

    result = _engine().run("add_kind_branch", {
        "schemaRef": _SCHEMA_REF,
        "discriminatorField": "skillKind",
        "kindValue": "fourth",
        "contentDefName": "FourthContent",
    })
    assert isinstance(result, Ok), result
    written = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert written["properties"]["skillKind"]["enum"] == ["advisor", "custom", "router", "fourth"]
    branches = {b["if"]["properties"]["skillKind"]["const"]: b["then"]["properties"]["content"]["$ref"] for b in written["allOf"]}
    assert branches["fourth"] == "#/$defs/FourthContent"
    assert len(written["allOf"]) == 4


def test_既に存在するkindブランチの追加は無変更で成功する():
    """
    Given 既にenumとルート分岐の両方に存在するkind値・content def紐付け
    When add_kind_branchを再実行する
    Then 対象は無変更のまま成功する
    """
    _write_fixture(_kind_dispatch_fixture())
    _engine().run("add_def", {
        "schemaRef": _SCHEMA_REF,
        "defName": "RouterContent",
        "defDef": {"type": "object", "properties": {}},
    })
    params = {
        "schemaRef": _SCHEMA_REF,
        "discriminatorField": "skillKind",
        "kindValue": "router",
        "contentDefName": "RouterContent",
    }
    first = _engine().run("add_kind_branch", params)
    assert isinstance(first, Ok) and first.value["changed"] is True
    after_first = _FIXTURE_PATH.read_text(encoding="utf-8")

    second = _engine().run("add_kind_branch", params)
    assert isinstance(second, Ok) and second.value["changed"] is False
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == after_first


def test_未知の形状のルート分岐へのadd_kind_branchはUNSUPPORTED_ROOT_DISPATCH_SHAPE():
    """
    Given if/then/else形式でもallOf形式でもないルート分岐、またはif/then/else形式でありながらenumが3つ以上のkind値を持つ状態
    When add_kind_branchを実行する
    Then UNSUPPORTED_ROOT_DISPATCH_SHAPEエラーが返り書き込まれない
    """
    before = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("add_kind_branch", {
        "schemaRef": _SCHEMA_REF,
        "discriminatorField": "skillKind",
        "kindValue": "router",
        "contentDefName": "RouterContent",
    })
    assert isinstance(result, Err), result
    assert result.details[0] == "UNSUPPORTED_ROOT_DISPATCH_SHAPE"
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == before


def test_create_versionは既存版を複製しeditsを適用した新しい版ファイルを作る():
    """
    Given 複製元のfromSchemaRefと、複製先のschemaRef（新版）・edits
    When create_versionを実行する
    Then fromSchemaRefの内容を複製しeditsを適用した新しい版ファイルがschemaRefへ書き込まれ、fromSchemaRef自体は変更されない
    """
    before = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("create_version", {
        "schemaRef": f"{_SCHEMA_REF.rsplit('/', 1)[0]}/v2",
        "fromSchemaRef": _SCHEMA_REF,
        "edits": [{"defName": "TitleBlock", "fieldPath": "properties.title.type", "value": "array"}],
    })
    assert isinstance(result, Ok), result
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == before
    written = json.loads(_FIXTURE_V2_PATH.read_text(encoding="utf-8"))
    assert written["$defs"]["TitleBlock"]["properties"]["title"]["type"] == "array"


def test_create_versionは既存フィールドの型を変えてもBACKWARD_INCOMPATIBLEにならない():
    """
    Given 既存フィールドの型を変更するedits（通常のset_fieldなら拒否される変更）
    When create_versionを実行する
    Then BACKWARD_INCOMPATIBLEエラーにならず新版が作られる
    """
    result = _engine().run("create_version", {
        "schemaRef": f"{_SCHEMA_REF.rsplit('/', 1)[0]}/v2",
        "fromSchemaRef": _SCHEMA_REF,
        "edits": [{"defName": "TitleBlock", "fieldPath": "properties.title.type", "value": "array"}],
    })
    assert isinstance(result, Ok), result


def test_create_versionは既に存在する版ファイルを上書きしない():
    """
    Given schemaRef（新版）が指す版ファイルが既に存在する状態
    When create_versionを実行する
    Then VERSION_ALREADY_EXISTSエラーが返り、既存の版ファイルは変更されない
    """
    _FIXTURE_V2_PATH.write_text(json.dumps(_base_schema(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    before = _FIXTURE_V2_PATH.read_text(encoding="utf-8")
    result = _engine().run("create_version", {
        "schemaRef": f"{_SCHEMA_REF.rsplit('/', 1)[0]}/v2",
        "fromSchemaRef": _SCHEMA_REF,
        "edits": [{"defName": "TitleBlock", "fieldPath": "properties.title.type", "value": "array"}],
    })
    assert isinstance(result, Err), result
    assert result.details[0] == "VERSION_ALREADY_EXISTS"
    assert _FIXTURE_V2_PATH.read_text(encoding="utf-8") == before


def _kind_keyed_render_target_fixture() -> dict:
    schema = _base_schema()
    schema["x-render-target"] = {
        "formats": ["md"],
        "pathVars": {"judgment": {"skillRef": "doc.skillRef"}},
        "path": {"judgment": ".waffle/templates/{documentId}.md"},
        "deploy": {"judgment": [".claude/skills/{skillRef}/references/{documentId}.md"]},
    }
    return schema


def test_x_render_targetのkind別dictに新しいkind値のエントリを追加する():
    """
    Given kind値・pathVars・path・deploy、およびpathVars/path/deployがkind別dict形式のschema
    When set_kind_render_targetを実行する
    Then x-render-target.pathVars/path/deployそれぞれに、そのkind値のエントリが追加される
    """
    _write_fixture(_kind_keyed_render_target_fixture())
    result = _engine().run("set_kind_render_target", {
        "schemaRef": _SCHEMA_REF,
        "kindValue": "investigation-report",
        "pathVars": {"skillRef": "doc.skillRef"},
        "path": ".waffle/templates/{documentId}.md",
        "deploy": [".claude/skills/{skillRef}/references/{documentId}.md"],
    })
    assert isinstance(result, Ok), result
    written = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    target = written["x-render-target"]
    assert target["pathVars"]["investigation-report"] == {"skillRef": "doc.skillRef"}
    assert target["path"]["investigation-report"] == ".waffle/templates/{documentId}.md"
    assert target["deploy"]["investigation-report"] == [".claude/skills/{skillRef}/references/{documentId}.md"]
    assert target["pathVars"]["judgment"] == {"skillRef": "doc.skillRef"}


def test_既に存在するkind別render_targetエントリの追加は無変更で成功する():
    """
    Given 既にpathVars・path・deployの全てで指定した値と一致するkind値のエントリ
    When set_kind_render_targetを再実行する
    Then 対象は無変更のまま成功する
    """
    _write_fixture(_kind_keyed_render_target_fixture())
    params = {
        "schemaRef": _SCHEMA_REF,
        "kindValue": "investigation-report",
        "pathVars": {"skillRef": "doc.skillRef"},
        "path": ".waffle/templates/{documentId}.md",
        "deploy": [".claude/skills/{skillRef}/references/{documentId}.md"],
    }
    first = _engine().run("set_kind_render_target", params)
    assert isinstance(first, Ok) and first.value["changed"] is True
    after_first = _FIXTURE_PATH.read_text(encoding="utf-8")

    second = _engine().run("set_kind_render_target", params)
    assert isinstance(second, Ok) and second.value["changed"] is False
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == after_first


def test_x_render_targetがkind別dict形式でないschemaへのset_kind_render_targetはUNSUPPORTED_RENDER_TARGET_SHAPE():
    """
    Given x-render-target自体を持たない、またはpathVars・path・deployのいずれかがフラット形式（kind別dictでない）のschema
    When set_kind_render_targetを実行する
    Then UNSUPPORTED_RENDER_TARGET_SHAPEエラーが返り書き込まれない
    """
    before = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("set_kind_render_target", {
        "schemaRef": _SCHEMA_REF,
        "kindValue": "investigation-report",
        "pathVars": {"skillRef": "doc.skillRef"},
        "path": ".waffle/templates/{documentId}.md",
        "deploy": [".claude/skills/{skillRef}/references/{documentId}.md"],
    })
    assert isinstance(result, Err), result
    assert result.details[0] == "UNSUPPORTED_RENDER_TARGET_SHAPE"
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == before
