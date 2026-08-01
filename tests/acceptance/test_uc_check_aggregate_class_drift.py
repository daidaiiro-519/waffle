"""uc-check-aggregate-class-drift の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_class_extractor import TreeSitterClassExtractor
from waffle.application.usecases.check_aggregate_class_drift import CheckAggregateClassDrift
from waffle.shared.result import Ok


def _engine() -> CheckAggregateClassDrift:
    return CheckAggregateClassDrift(FsDocumentRepository(), TreeSitterClassExtractor())


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _aggregate_doc(
    root_name: str,
    attributes: list[str] | None = None,
    value_objects: list[str] | None = None,
    value_object_attributes: dict[str, list[str]] | None = None,
) -> dict:
    def _vo_item(name: str) -> dict:
        item = {"name": name}
        if value_object_attributes and name in value_object_attributes:
            item["attributes"] = [{"name": a, "type": "string"} for a in value_object_attributes[name]]
        return item

    return {
        "documentId": "agg-a",
        "specKind": "aggregate",
        "content": {
            "aggregateRoot": {"blockType": "AggregateRoot", "title": "集約ルート", "name": root_name},
            "entities": {
                "blockType": "Entities", "title": "エンティティ",
                "items": [{"name": root_name, "isRoot": True, "attributes": [{"name": a} for a in (attributes or [])]}],
            },
            "valueObjects": {
                "blockType": "ValueObjects", "title": "値オブジェクト",
                "items": [_vo_item(v) for v in (value_objects or [])],
            },
        },
    }


def test_全aggregateの集約ルート名と実装クラスが一致するとき差分なしと判定する(tmp_path):
    """
    Scenario: 全aggregateの集約ルート名と実装クラスが一致するとき差分なしと判定する
    Given 全aggregateの集約ルート名・属性集合・値オブジェクトが、対応する実装ファイル内の同名クラス・同一フィールド集合と一致するspecツリー
    When クラス名ドリフト検査を実行する
    Then missing_implementation_file・class_name_mismatch・attribute_mismatch・missing_value_object全てが空配列で返る
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "aggregate" / "agg-a.json", _aggregate_doc("Schema", ["schemaId", "version"], ["SchemaId"]))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "schema.py").write_text(
        "class SchemaId:\n    value: str\n\n\nclass Schema:\n    schema_id: str\n    version: str\n", encoding="utf-8"
    )

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value == {
        "missing_implementation_file": [], "class_name_mismatch": [],
        "attribute_mismatch": [], "missing_value_object": [], "value_object_attribute_mismatch": [],
    }


def test_宣言された値オブジェクトが実装に存在しないとき検出する(tmp_path):
    """
    Scenario: 宣言された値オブジェクトが実装に存在しないとき検出する
    Given 集約ルートクラスは一致するが、ValueObjectsが宣言する値オブジェクトのクラス定義が実装ファイル内に無いaggregate document
    When クラス名ドリフト検査を実行する
    Then missing_value_objectにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "aggregate" / "agg-a.json", _aggregate_doc("Schema", ["schemaId"], ["SchemaId", "Version"]))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "schema.py").write_text(
        "class SchemaId:\n    value: str\n\n\nclass Schema:\n    schema_id: str\n", encoding="utf-8"
    )

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["missing_value_object"] == [
        {"documentId": "agg-a", "aggregateRootName": "Schema", "valueObjectName": "Version", "expectedPath": str(src_root / "schema.py")}
    ]


def test_属性が空でもクラス名だけ一致すれば通っていた盲点をattribute_mismatchで検出する(tmp_path):
    """
    Scenario: 属性が空でもクラス名だけ一致すれば通っていた盲点をattribute_mismatchで検出する
    Given 集約ルート名と一致するクラスは存在するが、Entitiesが宣言する属性を1つも持たない実装
    When クラス名ドリフト検査を実行する
    Then attribute_mismatchにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "aggregate" / "agg-a.json", _aggregate_doc("Schema", ["schemaId", "version", "kindProfiles"]))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "schema.py").write_text("class Schema:\n    pass\n", encoding="utf-8")

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["attribute_mismatch"] == [
        {
            "documentId": "agg-a",
            "aggregateRootName": "Schema",
            "expectedPath": str(src_root / "schema.py"),
            "declaredAttributes": ["schema_id", "version", "kind_profiles"],
            "foundFields": [],
        }
    ]


def test_実装ファイルが存在しないaggregateを検出する(tmp_path):
    """
    Scenario: 実装ファイルが存在しないaggregateを検出する
    Given 集約ルート名から導出したファイルパスに対応する実装ファイルが実在しないaggregate document
    When クラス名ドリフト検査を実行する
    Then missing_implementation_fileにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "aggregate" / "agg-a.json", _aggregate_doc("Schema"))
    src_root.mkdir(parents=True, exist_ok=True)

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["missing_implementation_file"] == [
        {"documentId": "agg-a", "aggregateRootName": "Schema", "expectedPath": str(src_root / "schema.py")}
    ]


def test_クラス名が一致しないaggregateを検出する(tmp_path):
    """
    Scenario: クラス名が一致しないaggregateを検出する
    Given 実装ファイルは実在するが、集約ルート名と一致するクラス定義を持たないaggregate document
    When クラス名ドリフト検査を実行する
    Then class_name_mismatchにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "aggregate" / "agg-a.json", _aggregate_doc("Schema"))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "schema.py").write_text("class SomethingElse:\n    pass\n", encoding="utf-8")

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["class_name_mismatch"] == [
        {
            "documentId": "agg-a",
            "aggregateRootName": "Schema",
            "expectedPath": str(src_root / "schema.py"),
            "foundClasses": ["SomethingElse"],
        }
    ]


def test_値オブジェクトのクラス名だけ一致し属性が空でも通っていた盲点をvalue_object_attribute_mismatchで検出する(tmp_path):
    """
    Scenario: 値オブジェクトのクラス名だけ一致し属性が空でも通っていた盲点をvalue_object_attribute_mismatchで検出する
    Given valueObjects宣言がattributesを持ち、値オブジェクトのクラス自体は存在するが属性を1つも持たない実装
    When クラス名ドリフト検査を実行する
    Then value_object_attribute_mismatchにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(
        docs_root / "aggregate" / "agg-a.json",
        _aggregate_doc("Schema", ["schemaId"], ["SchemaId"], value_object_attributes={"SchemaId": ["value"]}),
    )
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "schema.py").write_text(
        "class SchemaId:\n    pass\n\n\nclass Schema:\n    schema_id: str\n", encoding="utf-8"
    )

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["value_object_attribute_mismatch"] == [
        {
            "documentId": "agg-a",
            "aggregateRootName": "Schema",
            "valueObjectName": "SchemaId",
            "expectedPath": str(src_root / "schema.py"),
            "declaredAttributes": ["value"],
            "foundFields": [],
        }
    ]


def test_値オブジェクトがattributesを宣言していなければ属性対応は対象外にする(tmp_path):
    """
    Scenario: 値オブジェクトがattributesを宣言していなければ属性対応は対象外にする
    Given valueObjects宣言がattributesを持たない値オブジェクト
    When クラス名ドリフト検査を実行する
    Then value_object_attribute_mismatchにその組は含まれない
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "aggregate" / "agg-a.json", _aggregate_doc("Schema", ["schemaId"], ["SchemaId"]))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "schema.py").write_text(
        "class SchemaId:\n    pass\n\n\nclass Schema:\n    schema_id: str\n", encoding="utf-8"
    )

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["value_object_attribute_mismatch"] == []
