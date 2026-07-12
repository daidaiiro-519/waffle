"""uc-check-aggregate-class-drift の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_aggregate_class_drift import CheckAggregateClassDrift
from waffle.shared.result import Ok


def _engine() -> CheckAggregateClassDrift:
    return CheckAggregateClassDrift(FsDocumentRepository())


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _aggregate_doc(root_name: str, attributes: list[str] | None = None, value_objects: list[str] | None = None) -> dict:
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
                "items": [{"name": v} for v in (value_objects or [])],
            },
        },
    }


def test_全aggregateの集約ルート名と実装クラスが一致するとき差分なしと判定する(tmp_path):
    """
    Given 全aggregateの集約ルート名・値オブジェクトが、対応する実装ファイル内の同名クラスと一致するspecツリー
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
        "attribute_mismatch": [], "missing_value_object": [],
    }


def test_宣言された値オブジェクトが実装に存在しないとき検出する(tmp_path):
    """
    Given 集約ルートクラスは一致するが、valueObjectsが宣言する値オブジェクトのクラスが実装ファイル内に無い
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
    Given 集約ルート名と一致するクラスは存在するが、中身が空(属性を1つも持たない)実装
    When クラス名ドリフト検査を実行する
    Then attribute_mismatchにその組が含まれる（クラス名の一致だけでは合格にしない）
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
