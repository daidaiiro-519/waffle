"""agg-schema（Schema集約）のinvariantScenariosに対応するネイティブテスト。

集約の不変条件はいずれもport（DocumentRepository/SchemaRepository）を必要としない
純粋な検証（実schemaロード・実Validator呼び出し）で完結するため、全件をdomain層に置く。

test-standardの命名規約(test_{documentId}.py)に従い、以前
test_schema_invariants.py/test_schema_status.py/test_part_renderer.py(x-render/lint分)
に散らばっていたagg-schema由来のテストをここに集約した。

x-migration語彙(MigrationMetaSchema)・移行方向の不変条件は、実際の運用規模では
過剰なため撤去した(詳細はdocs/brainstorm/brainstorm-schema-versioning-migration.md
に撤回の経緯として追記済み)。
"""
import json
from importlib import resources

import pytest

from waffle.adapters.outbound.jsonschema_validator import JsonSchemaValidator
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from tests.fakes import base_schema, new_block
from waffle.domain.services import schema_patch

_IN_SCOPE_SCHEMAS = ["SkillSchema/v1", "AgentSchema/v2", "TemplateSchema/v1", "CodingSchema/v2", "DomainSpecSchema/v5", "PresentationSpecSchema/v1", "PlatformSpec/v1"]
_PACKAGES = ["waffle.domain.model", "waffle.domain.value_objects", "waffle.application.dto"]


def _load_raw_text(schema_ref: str) -> str:
    *dirs, name = schema_ref.split("/")
    for package in _PACKAGES:
        ref = resources.files(package)
        for d in dirs:
            ref = ref / d
        try:
            return (ref / f"{name}.json").read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
    raise FileNotFoundError(schema_ref)


# --- 値フィールドに oneOf を持てない ---

def _contains_oneof_or_anyof(node) -> bool:
    if isinstance(node, dict):
        if "oneOf" in node or "anyOf" in node:
            return True
        return any(_contains_oneof_or_anyof(v) for v in node.values())
    if isinstance(node, list):
        return any(_contains_oneof_or_anyof(v) for v in node)
    return False


@pytest.mark.parametrize("schema_ref", _IN_SCOPE_SCHEMAS)
def test_value_field_cannot_have_one_of(schema_ref):
    """
    Scenario: 値フィールドに oneOf を持てない
    Given 値フィールドに oneOf を含む Schema
    When scaffoldability を検証する
    Then scaffold 不能として拒否される
    """
    schema = PackageSchemaRepository().load(schema_ref)
    assert not _contains_oneof_or_anyof(schema["$defs"]), f"{schema_ref} の $defs に oneOf/anyOf が含まれている"


# --- x-render は閉じた語彙にのみ従う ---

def _lint_render(parts):
    meta = PackageSchemaRepository().load("RenderMetaSchema/v1")
    schema = {"$defs": meta["$defs"], "type": "array", "items": {"$ref": "#/$defs/RenderPart"}}
    return JsonSchemaValidator().validate(parts, schema)


@pytest.mark.parametrize("schema_ref", _IN_SCOPE_SCHEMAS)
def test_x_render_follows_closed_vocabulary(schema_ref):
    """
    Scenario: x-render は閉じた語彙にのみ従う
      Given 未知の部品種別、または必須属性が欠けた x-render 宣言を持つ Schema
      When x-render の適合を検証する
      Then 不適合として拒否される

    (実証: 全 in-scope schema の全 block の x-render が RenderMetaSchema に適合する)
    """
    schema = PackageSchemaRepository().load(schema_ref)
    for name, bdef in schema["$defs"].items():
        if "x-render" in bdef:
            assert _lint_render(bdef["x-render"]) == [], f"{schema_ref}:{name} の x-render が不適合"


# --- 公開済みの版は後方互換を壊さない ---
# (port不要・純粋なValidator呼び出しで検証できる不変条件)

# --- Schemaファイルの物理整形は一意に定まる形と完全一致する ---

@pytest.mark.parametrize("schema_ref", _IN_SCOPE_SCHEMAS)
def test_schema_file_formatting_is_canonical(schema_ref):
    """
    Scenario: Schemaファイルの物理整形は一意に定まる形と完全一致する
      Given 独自の整形（コンパクト配列・キー長揃え等）が施されたSchemaファイル
      When 契約が定める形（2段の字下げ・非ASCII文字はそのまま・末尾に改行）と比較する
      Then バイト単位で一致しない場合は不適合として検出される

    (整形ルールを一意に固定することで、部分編集・ブロック追加・リネーム等の機械的な
    差分適用が、既存の無関係な箇所を一切変更せずに行えるようにする)
    """
    original = _load_raw_text(schema_ref)
    reserialized = json.dumps(json.loads(original), indent=2, ensure_ascii=False) + "\n"
    assert original == reserialized, f"{schema_ref} が json.dumps(indent=2, ensure_ascii=False) の出力と一致しない"


def test_published_version_keeps_backward_compatibility():
    """
    Scenario: 一度作った版は後方互換を壊さない
      Given 既にDocumentが参照している既存のSchema版
      When 既存ブロックに必須フィールドを追加しようとする
      Then 後方互換を壊す変更として拒否される

    (実証: 旧バージョンの既存Documentに、新schemaが要求する必須フィールドが
    欠けている場合、実際のJsonSchemaValidatorで不適合と判定されることを確認する)
    """
    old_document = {"name": "既存データ"}
    new_schema_with_required_field = {
        "required": ["name", "newRequiredField"],
        "properties": {"name": {"type": "string"}, "newRequiredField": {"type": "string"}},
    }
    errors = JsonSchemaValidator().validate(old_document, new_schema_with_required_field)
    assert errors, "後方互換を壊す変更（必須フィールド追加）が誤って適合と判定された"


def test_adding_required_to_published_kind_breaks_compatibility():
    """
    Scenario: requiredへの追加は後方互換違反として検出される
    Given 既にある版のschemaと、あるContent defのrequired配列に新規エントリを追加した変更後schema
    When 後方互換チェックを実行する
    Then 違反として検出される
    """
    old_schema = base_schema()
    new_schema = schema_patch.add_block(old_schema, "NoteBlock", new_block(), "SomeContent", "note", required=True)
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations, "required配列への追加が検出されなかった"


def test_adding_optional_property_keeps_compatibility():
    """
    Scenario: optionalプロパティの追加は後方互換違反にならない
    Given 既にある版のschemaと、requiredに含めずに新規プロパティのみ追加した変更後schema
    When 後方互換チェックを実行する
    Then 違反として検出されない
    """
    old_schema = base_schema()
    new_schema = schema_patch.add_block(old_schema, "NoteBlock", new_block(), "SomeContent", "note")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations == []


def test_removing_required_property_breaks_compatibility():
    """
    Scenario: requiredなプロパティの除去は後方互換違反として検出される
    Given requiredに指定されているプロパティをremove_blockで除去した変更後schema
    When 後方互換チェックを実行する
    Then 違反として検出される
    """
    old_schema = base_schema()
    new_schema = schema_patch.remove_block(old_schema, "SomeContent", "title")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations, "必須プロパティのremove_blockが検出されなかった"


def test_removing_optional_property_keeps_compatibility():
    """
    Scenario: requiredでないプロパティの除去は後方互換違反にならない
    Given requiredに含まれないプロパティをremove_blockで除去した変更後schema
    When 後方互換チェックを実行する
    Then 違反として検出されない
    """
    old_schema = schema_patch.add_block(base_schema(), "NoteBlock", new_block(), "SomeContent", "note", required=False)
    new_schema = schema_patch.remove_block(old_schema, "SomeContent", "note")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations == []


def test_renaming_required_property_breaks_compatibility():
    """
    Scenario: requiredなプロパティの改名は後方互換違反として検出される
    Given 公開済みkindのContent defでrequiredに指定されているブロックのリネーム
    When 後方互換チェックを実行する
    Then 違反として検出される（旧プロパティ名を持つ既存instanceが新schemaのrequiredを満たせなくなるため）
    """
    old_schema = base_schema()
    new_schema = schema_patch.rename_block(old_schema, "Title", "Heading")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations, "requiredプロパティのリネームが検出されなかった"


def test_renaming_optional_property_keeps_compatibility():
    """
    Scenario: requiredでないプロパティの改名は後方互換違反にならない
    Given 公開済みkindのContent defでrequiredに指定されていないブロックのリネーム
    When 後方互換チェックを実行する
    Then 違反として検出されない
    """
    old_schema = base_schema()
    old_schema = schema_patch.add_block(old_schema, "NoteBlock", new_block(), "SomeContent", "note")
    new_schema = schema_patch.rename_block(old_schema, "Note", "Memo")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations == []


def test_changing_field_type_breaks_compatibility():
    """
    Scenario: 既存フィールドの型変更は後方互換違反として検出される
    Given 公開済みkindの既存フィールドの型(type)を書き換える変更
    When 後方互換チェックを実行する
    Then 違反として検出される（旧型の値を持つ既存instanceが新schemaの型制約を満たせなくなるため）
    """
    old_schema = base_schema()
    new_schema = schema_patch.set_field(old_schema, "TitleBlock", "properties.title.type", "number")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations, "既存フィールドの型変更が検出されなかった"


def test_set_field_without_type_change_keeps_compatibility():
    """
    Scenario: 型を変えない書き換えは後方互換違反にならない
    Given 型(type)以外のフィールドを書き換えるset_field
    When 後方互換チェックを実行する
    Then 違反として検出されない
    """
    old_schema = base_schema()
    new_schema = schema_patch.set_field(old_schema, "TitleBlock", "properties.title.description", "タイトル文字列")
    violations = schema_patch.check_backward_compatible(old_schema, new_schema)
    assert violations == []


def test_dump_matches_json_dumps_indent2():
    """
    Scenario: 契約整形は契約が定める形と完全一致する
    Given 任意の整形が施されたschema
    When 契約整形を適用する
    Then 出力は契約が定める形（2段の字下げ・非ASCII文字はそのまま・末尾に改行）と完全一致する
    """
    schema = base_schema()
    assert schema_patch.dump(schema) == json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
