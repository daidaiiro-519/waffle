"""stack_resolution（architectureRef から同じスタックの規約を引く）のテスト。

仕様のシナリオには対応しない、規約由来のテスト。
検査がファイル名を組み立てるための規則は、コードではなくそのスタックの
coding-standard が持つ。ここではその引き当てを確かめる。
"""
from waffle.application.services.stack_resolution import resolve_naming
from waffle.shared.result import Err, Ok

_ARCHITECTURE = {"documentId": "architecture-demo", "codingKind": "architecture",
                 "stack": "demo-stack", "content": {}}
_CODING_STANDARD = {"documentId": "coding-standard-demo", "codingKind": "coding-standard",
                    "stack": "demo-stack",
                    "content": {"naming": {"fileNameDerivedFrom": "type",
                                           "fileNameTransform": "identity",
                                           "fileNameSuffix": ".java"}}}
_OTHER_STACK = {"documentId": "coding-standard-other", "codingKind": "coding-standard",
                "stack": "other-stack",
                "content": {"naming": {"fileNameSuffix": ".py"}}}

CODING = ".waffle/documents/coding/"


class _FakeDocs:
    """coding ディレクトリの走査と読込だけを持つ DocumentRepository の偽実装。"""

    def __init__(self, documents: dict[str, dict]) -> None:
        self._documents = documents

    def list_files(self, directory: str, pattern: str) -> list[str]:
        return sorted(p for p in self._documents if p.startswith(directory))

    def load(self, path: str) -> dict:
        if path not in self._documents:
            raise FileNotFoundError(path)
        return self._documents[path]


def _docs(*documents):
    return _FakeDocs({CODING + d["documentId"] + "." + "json": d for d in documents})


def test_resolves_naming_of_the_same_stack():
    """architectureRef と同じ stack を持つ coding-standard の naming を返す。"""
    result = resolve_naming(_docs(_ARCHITECTURE, _CODING_STANDARD, _OTHER_STACK),
                            "architecture-demo")
    assert isinstance(result, Ok)
    assert result.value["fileNameSuffix"] == ".java"


def test_unknown_architecture_ref_returns_not_found():
    """architecture文書が無ければ ARCHITECTURE_REF_NOT_FOUND を返す。"""
    result = resolve_naming(_docs(_CODING_STANDARD), "architecture-demo")
    assert isinstance(result, Err)
    assert result.details[0] == "ARCHITECTURE_REF_NOT_FOUND"


def test_missing_coding_standard_returns_not_found():
    """同じ stack の coding-standard が無ければ CODING_STANDARD_NOT_FOUND を返す。

    黙って既定の表記へ倒すと、宣言の無いスタックで誤った名前を探し続ける。
    """
    result = resolve_naming(_docs(_ARCHITECTURE, _OTHER_STACK), "architecture-demo")
    assert isinstance(result, Err)
    assert result.details[0] == "CODING_STANDARD_NOT_FOUND"
