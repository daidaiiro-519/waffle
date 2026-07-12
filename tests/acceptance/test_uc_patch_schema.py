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
    Given add_block/rename_block以外のoperation
    When patchを実行する
    Then INVALID_OPERATIONエラーが返る
    """
    result = _engine().run("bogus", {"schemaRef": _SCHEMA_REF})
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_OPERATION"
