"""uc-check-layer-drift の受け入れテスト（ネイティブpytest）。"""
import json

from waffle.application.usecases.check_layer_drift import CheckLayerDrift
from waffle.shared.result import Err, Ok

from tests.fakes import FakeSchemaRepository  # noqa: F401  (契約の同居を明示するため)

_ARCH = "architecture-probe"
_STACK = "probe"
_SRC = "src/probe"

_LAYERS = [
    {"layer": "shared", "path": "shared", "mayDependOn": []},
    {"layer": "domain", "path": "domain", "mayDependOn": ["shared"]},
    {"layer": "application", "path": "application", "mayDependOn": ["domain", "shared"]},
    {"layer": "inbound adapter", "path": "adapters/inbound",
     "mayDependOn": ["application", "shared"]},
]


def _architecture(layers=None, composition_roots=None, source_root=_SRC) -> dict:
    return {
        "documentId": _ARCH, "stack": _STACK, "codingKind": "architecture",
        "content": {
            "layers": {"items": layers if layers is not None else _LAYERS},
            "layout": {"sourceRoot": source_root,
                       "compositionRootPaths": composition_roots or []},
        },
    }


def _tech_stack() -> dict:
    return {
        "documentId": "tech-stack-probe", "stack": _STACK, "codingKind": "tech-stack",
        "content": {"runtime": {"languages": [
            {"language": "python", "extensions": [".py"]},
        ]}},
    }


class _FakeDocuments:
    """規約文書と、置き場所ごとのソースを持つ偽のリポジトリ。"""

    def __init__(self, sources: dict, architecture: dict | None = None):
        self._sources = sources
        self._coding = [architecture or _architecture(), _tech_stack()]

    def list_files(self, directory: str, pattern: str) -> list[str]:
        if directory == ".waffle/documents/coding":
            return [f".waffle/documents/coding/{d['documentId']}.json" for d in self._coding]
        found = [p for p in self._sources if p.startswith(directory.rstrip("/") + "/")]
        if not found and directory != ".waffle/documents/coding":
            raise FileNotFoundError(directory)
        return found

    def load(self, path: str) -> dict:
        for document in self._coding:
            if path.endswith(f"/{document['documentId']}." + "json"):
                return document
        raise FileNotFoundError(path)

    def read_text(self, path: str) -> str:
        if path not in self._sources:
            raise FileNotFoundError(path)
        return self._sources[path]

    def save(self, path, document): raise AssertionError("確認だけを行う")
    def write_text(self, path, text): raise AssertionError("確認だけを行う")
    def link(self, canonical, path): raise AssertionError("確認だけを行う")
    def list_json(self, directory): return []
    def list_dirs(self, directory): return []


class _FakeImports:
    def imports(self, source: str, language: str) -> list[str]:
        return [line.split()[1] for line in source.splitlines()
                if line.startswith("import ")]


def _run(sources, architecture=None):
    return CheckLayerDrift(_FakeDocuments(sources, architecture), _FakeImports()).run(_ARCH)


def test_declared_dependencies_produce_no_drift():
    """
    Scenario: 宣言に沿った依存だけなら差分は出ない
    Given 層と依存してよい先を宣言した規約
    And その宣言に沿った依存だけを持つ実装
    When 層の差分を確かめる
    Then 違反は報告されない
    """
    result = _run({
        f"{_SRC}/shared/result.py": "",
        f"{_SRC}/domain/order.py": "import probe.shared.result\n",
        f"{_SRC}/application/publish.py": "import probe.domain.order\n",
        f"{_SRC}/adapters/inbound/cli.py": "import probe.application.publish\n",
    })
    assert isinstance(result, Ok), result
    assert result.value["violations"] == []


def test_dependency_outside_may_depend_on_is_reported():
    """
    Scenario: 依存してよい先に無い層へ依存していると違反として報告する
    Given 層と依存してよい先を宣言した規約
    And 依存してよい先に無い層を使っている実装
    When 層の差分を確かめる
    Then その実装と、使っている層が違反として報告される
    """
    result = _run({
        f"{_SRC}/shared/result.py": "",
        f"{_SRC}/domain/order.py": "import probe.application.publish\n",
        f"{_SRC}/application/publish.py": "",
    })
    assert isinstance(result, Ok), result
    assert result.value["violations"] == [{
        "path": f"{_SRC}/domain/order.py", "layer": "domain",
        "imports": "probe.application.publish", "importedLayer": "application",
    }]


def test_dependency_within_the_same_layer_is_not_a_violation():
    """
    Scenario: 同じ層の中での依存は違反にしない
    Given 依存してよい先を1つも持たない層
    And その層の中だけで完結している依存
    When 層の差分を確かめる
    Then 違反は報告されない
    """
    result = _run({
        f"{_SRC}/shared/result.py": "import probe.shared.errors\n",
        f"{_SRC}/shared/errors.py": "",
    })
    assert isinstance(result, Ok), result
    assert result.value["violations"] == []


def test_dependency_outside_the_declared_scope_is_ignored():
    """
    Scenario: 宣言の外にある部品への依存は対象にしない
    Given 層の置き場所を宣言した規約
    And その置き場所の外にある部品を使っている実装
    When 層の差分を確かめる
    Then 違反は報告されない
    """
    result = _run({
        f"{_SRC}/domain/order.py": (
            "import json\n"
            "import dataclasses\n"
            # 層と同じ名前を持つ外部ライブラリ。置き場所の下に実在しないので対象外
            "import application\n"
            "import shared.logging\n"),
        f"{_SRC}/shared/result.py": "",
        f"{_SRC}/application/publish.py": "",
    })
    assert isinstance(result, Ok), result
    assert result.value["violations"] == []


def test_composition_root_is_excluded_from_the_dependency_rules():
    """
    Scenario: 合成ルートは依存の規則から除外する
    Given 合成ルートの場所を宣言した規約
    And すべての層を使っている合成ルート
    When 層の差分を確かめる
    Then 違反は報告されない
    """
    architecture = _architecture(composition_roots=["adapters/inbound/main.py"])
    result = _run({
        f"{_SRC}/shared/result.py": "",
        f"{_SRC}/domain/order.py": "",
        f"{_SRC}/application/publish.py": "",
        f"{_SRC}/adapters/inbound/main.py": (
            "import probe.domain.order\nimport probe.shared.result\n"),
    }, architecture)
    assert isinstance(result, Ok), result
    assert result.value["violations"] == []


def test_file_belonging_to_no_layer_is_reported():
    """
    Scenario: どの層にも属さない実装は宣言漏れとして報告する
    Given 層の置き場所を宣言した規約
    And どの層の置き場所にも入らない場所に置かれた実装
    When 層の差分を確かめる
    Then その実装が宣言漏れとして報告される
    """
    layers = [{"layer": "domain", "path": "domain", "mayDependOn": []}]
    result = _run({
        f"{_SRC}/domain/order.py": "",
        # どの層の置き場所にも入らない場所（util は層として宣言されていない）
        f"{_SRC}/util/helper.py": "x = 1\n",
    }, _architecture(layers=layers))
    assert isinstance(result, Ok), result
    assert [u["path"] for u in result.value["unassigned"]] == [f"{_SRC}/util/helper.py"]


def test_missing_layer_directory_is_reported_as_not_implemented():
    """
    Scenario: 宣言した置き場所が無ければ未実装として報告する
    Given まだ実装が存在しない層を含む規約
    When 層の差分を確かめる
    Then その層が未実装として報告され、他の層の確認は続く
    """
    result = _run({
        f"{_SRC}/domain/order.py": "import probe.shared.result\n",
        f"{_SRC}/shared/result.py": "",
    })
    assert isinstance(result, Ok), result
    reported = {(m["layer"], m["path"]) for m in result.value["missing_layer_dirs"]}
    assert reported == {("application", "application"),
                        ("inbound adapter", "adapters/inbound")}
    # 他の層の確認は続いている（domain→shared は宣言どおりなので違反にならない）
    assert result.value["violations"] == []


def test_layer_path_containing_another_is_rejected_before_scanning():
    """
    Scenario: ある層の置き場所が別の層を飲み込んでいると宣言の誤りとして報告する
    Given ある層の置き場所が、別の層の置き場所を含んでいる規約
    When 層の差分を確かめる
    Then 実装を確かめる前に、宣言の誤りとして報告される
    """
    layers = [
        {"layer": "inbound adapter", "path": "", "mayDependOn": []},
        {"layer": "domain", "path": "domain", "mayDependOn": []},
        {"layer": "application", "path": "domain/inner", "mayDependOn": []},
    ]
    result = _run({f"{_SRC}/domain/order.py": "壊れた構文"}, _architecture(layers=layers))
    assert isinstance(result, Err), result
    assert "OVERLAPPING_LAYER_PATHS" in result.details
    assert "domain" in result.message


def test_missing_architecture_ref_is_rejected():
    """
    Scenario: 規約を指定しないと拒否される
    Given 規約の指定が無い
    When 層の差分を確かめる
    Then 拒否される
    """
    result = CheckLayerDrift(_FakeDocuments({}), _FakeImports()).run(None)
    assert isinstance(result, Err), result
    assert "MISSING_PARAM" in result.details


def test_empty_file_is_not_counted_as_unassigned():
    """
    Scenario: 中身の無いファイルは宣言漏れに数えない
    Given 層の置き場所を宣言した規約
    And どの層にも属さない場所にある、中身の無いファイル
    When 層の差分を確かめる
    Then 宣言漏れとして報告されない
    """
    layers = [{"layer": "domain", "path": "domain", "mayDependOn": []}]
    result = _run({
        f"{_SRC}/domain/order.py": "",
        f"{_SRC}/__init__.py": "",          # 何も宣言していない
        f"{_SRC}/util/helper.py": "x = 1\n",  # 宣言漏れ
    }, _architecture(layers=layers))
    assert isinstance(result, Ok), result
    assert [u["path"] for u in result.value["unassigned"]] == [f"{_SRC}/util/helper.py"]
