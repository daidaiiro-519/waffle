"""source_root_resolution（architecture文書から概念の実装配置を解決する）のテスト。

仕様のシナリオには対応しない、規約由来のテスト。CLIとMCPの両方が同じ解決を
使うため、判断はapplication層に置き、アダプターはResultを各プロトコルの形へ
translateするだけにする。
"""
from waffle.application.services.source_root_resolution import resolve_src_root
from waffle.shared.result import Err, Ok

_ARCHITECTURE = {
    "content": {
        "layout": {"sourceRoot": "src/{package}"},
        "conceptPlacement": {"items": [
            {"concept": "usecase",
             "placements": [{"role": "single", "path": "application/usecases"}]},
        ]},
    }
}


class _FakeDocs:
    """architecture文書だけを知るDocumentRepositoryの偽実装。"""

    def __init__(self, documents: dict[str, dict]) -> None:
        self._documents = documents

    def load(self, path: str) -> dict:
        if path not in self._documents:
            raise FileNotFoundError(path)
        return self._documents[path]


def _docs(found: bool = True):
    return _FakeDocs({".waffle/documents/coding/architecture-waffle.json": _ARCHITECTURE} if found else {})


def test_explicit_src_root_takes_precedence():
    """srcRootが明示されていれば、architectureRefを見ずにそのまま返す。"""
    result = resolve_src_root(_docs(), "src/custom", "architecture-waffle", "usecase")
    assert isinstance(result, Ok)
    assert result.value == "src/custom"


def test_missing_both_params_returns_missing_param():
    """srcRootもarchitectureRefも無ければMISSING_PARAMを返す。"""
    result = resolve_src_root(_docs(), None, None, "usecase")
    assert isinstance(result, Err)
    assert result.details[0] == "MISSING_PARAM"


def test_unknown_architecture_ref_returns_not_found():
    """architecture文書が見つからなければARCHITECTURE_REF_NOT_FOUNDを返す。"""
    result = resolve_src_root(_docs(found=False), None, "architecture-waffle", "usecase")
    assert isinstance(result, Err)
    assert result.details[0] == "ARCHITECTURE_REF_NOT_FOUND"


def test_resolves_from_architecture_document():
    """architecture文書のsourceRootとconceptPlacementから配置を解決する。"""
    result = resolve_src_root(_docs(), None, "architecture-waffle", "usecase")
    assert isinstance(result, Ok)
    assert result.value == "src/waffle/application/usecases"


def test_unresolvable_concept_returns_unresolved():
    """conceptPlacementに該当concept が無ければARCHITECTURE_REF_UNRESOLVEDを返す。"""
    result = resolve_src_root(_docs(), None, "architecture-waffle", "no-such-concept")
    assert isinstance(result, Err)
    assert result.details[0] == "ARCHITECTURE_REF_UNRESOLVED"
