"""uc-patch-schema のguaranteeScenarios(operationGuaranteesと対)に対応する統合テスト。

add_block/rename_blockのべき等性と、整形契約に従う既存箇所が書き込み後も不変であることを、
実adapter(FsDocumentRepository/PackageSchemaRepository)経由で検証する。
"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.jsonschema_validator import JsonSchemaValidator
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.patch_schema import PatchSchema
from waffle.shared.result import Ok

_FIXTURE_DIR = Path("src/waffle/domain/model/TestPatchSchemaIntegrationFixture")
_FIXTURE_PATH = _FIXTURE_DIR / "v1.json"
_SCHEMA_REF = "TestPatchSchemaIntegrationFixture/v1"


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


def test_add_blockの複数回実行はべき等である():
    """
    Given 同一のadd_block操作
    When 2回連続で実行する
    Then 2回目の実行結果は1回目と完全に同一である
    """
    params = {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock",
        "blockDef": {
            "type": "object",
            "required": ["blockType", "note"],
            "properties": {"blockType": {"type": "string", "const": "Note"}, "note": {"type": "string"}},
        },
        "contentDefName": "SomeContent",
        "propName": "note",
    }
    _engine().run("add_block", params)
    after_first = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("add_block", params)
    assert isinstance(result, Ok), result
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == after_first


def test_rename_blockの複数回実行はべき等である():
    """
    Given 同一のrename_block操作
    When 2回連続で実行する
    Then 2回目の実行結果は1回目と完全に同一である
    """
    params = {"schemaRef": _SCHEMA_REF, "oldName": "Title", "newName": "Heading"}
    _engine().run("rename_block", params)
    after_first = _FIXTURE_PATH.read_text(encoding="utf-8")
    result = _engine().run("rename_block", params)
    assert isinstance(result, Ok), result
    assert _FIXTURE_PATH.read_text(encoding="utf-8") == after_first


def test_整形契約に従う既存箇所は書き込み後も不変である():
    """
    Given 整形契約に従った既存のschemaファイル
    When patchを実行する
    Then 変更対象以外の既存の行はバイト単位で不変である
    """
    before_lines = set(_FIXTURE_PATH.read_text(encoding="utf-8").splitlines())
    _engine().run("add_block", {
        "schemaRef": _SCHEMA_REF,
        "blockName": "NoteBlock",
        "blockDef": {
            "type": "object",
            "required": ["blockType", "note"],
            "properties": {"blockType": {"type": "string", "const": "Note"}, "note": {"type": "string"}},
        },
        "contentDefName": "SomeContent",
        "propName": "note",
    })
    after_lines = set(_FIXTURE_PATH.read_text(encoding="utf-8").splitlines())
    assert before_lines <= after_lines
