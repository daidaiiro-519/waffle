"""uc-check-domain-service-drift の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_domain_service_drift import CheckDomainServiceDrift
from waffle.shared.result import Ok


def _engine() -> CheckDomainServiceDrift:
    return CheckDomainServiceDrift(FsDocumentRepository())


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _bc_doc(services: list[dict]) -> dict:
    return {
        "documentId": "bc-a",
        "specKind": "bounded-context",
        "content": {"domainServices": {"blockType": "DomainServices", "title": "ドメインサービス", "items": services}},
    }


def test_全業務サービスのgroupと実装ファイルが一致するとき差分なしと判定する(tmp_path):
    """
    Given 全業務サービスのgroupが、対応する実装ファイルと一致するspecツリー
    When ドリフト検査を実行する
    Then missing_implementation_fileが空配列で返る
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "bc-a.json", _bc_doc([{"name": "サービスA", "responsibility": "x", "serviceName": "ServiceA", "group": "GroupA"}]))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "group_a.py").write_text("def service_a():\n    pass\n", encoding="utf-8")

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value == {"missing_implementation_file": []}


def test_実装ファイルが存在しない業務サービスを検出する(tmp_path):
    """
    Given groupから導出したファイルパスに対応する実装ファイルが実在しない業務サービス宣言
    When ドリフト検査を実行する
    Then missing_implementation_fileにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "bc-a.json", _bc_doc([{"name": "サービスA", "responsibility": "x", "serviceName": "ServiceA", "group": "GroupA"}]))
    src_root.mkdir(parents=True, exist_ok=True)

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["missing_implementation_file"] == [
        {"documentId": "bc-a", "group": "GroupA", "expectedPath": str(src_root / "group_a.py")}
    ]


def test_同じgroupを共有する複数サービスは1回のファイル確認にまとめられる(tmp_path):
    """
    Given 同じgroupを宣言する2件以上の業務サービス（対応する実装ファイルは実在しない）
    When ドリフト検査を実行する
    Then missing_implementation_fileには重複を除いた1件だけが含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "bc-a.json", _bc_doc([
        {"name": "サービスA", "responsibility": "x", "serviceName": "ServiceA", "group": "SharedGroup"},
        {"name": "サービスB", "responsibility": "y", "serviceName": "ServiceB", "group": "SharedGroup"},
    ]))
    src_root.mkdir(parents=True, exist_ok=True)

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["missing_implementation_file"] == [
        {"documentId": "bc-a", "group": "SharedGroup", "expectedPath": str(src_root / "shared_group.py")}
    ]
