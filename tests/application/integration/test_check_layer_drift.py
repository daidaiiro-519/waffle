"""uc-check-layer-drift の操作保証テスト（ネイティブpytest）。

規約を特定し取得する解決プロセス自体の契約を、実物のリポジトリに対して確かめる。
"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_import_extractor import TreeSitterImportExtractor
from waffle.application.usecases.check_layer_drift import CheckLayerDrift
from waffle.shared.result import Err


def _engine() -> CheckLayerDrift:
    return CheckLayerDrift(FsDocumentRepository(), TreeSitterImportExtractor())


def test_unknown_architecture_ref_is_not_found():
    """
    Scenario: 見つからない規約はARCHITECTURE_REF_NOT_FOUND
    When 存在しない規約を指定して層の差分を確かめる
    Then ARCHITECTURE_REF_NOT_FOUNDエラーが返る
    """
    result = _engine().run("architecture-存在しない規約")
    assert isinstance(result, Err), result
    assert "ARCHITECTURE_REF_NOT_FOUND" in result.details


def test_architecture_without_placement_is_unresolved(tmp_path, monkeypatch):
    """
    Scenario: 置き場所を決められない規約はARCHITECTURE_REF_UNRESOLVED
    When 層の置き場所を決めるのに足りる宣言を持たない規約を指定して層の差分を確かめる
    Then ARCHITECTURE_REF_UNRESOLVEDエラーが返る
    """
    class _WithoutPlacement(FsDocumentRepository):
        def load(self, path: str) -> dict:
            document = super().load(path)
            if document.get("documentId") == "architecture-waffle":
                document["content"]["layout"] = {}
            return document

    result = CheckLayerDrift(_WithoutPlacement(), TreeSitterImportExtractor()).run(
        "architecture-waffle")
    assert isinstance(result, Err), result
    assert "ARCHITECTURE_REF_UNRESOLVED" in result.details
