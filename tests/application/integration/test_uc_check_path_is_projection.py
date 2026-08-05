"""uc-check-path-is-projection の操作保証テスト。

同じ判断が、Pythonから直接呼んでもCLIから呼んでも同じ答えを返すことを確かめる。
この判断はフックからCLI経由で使われ、テストからは直接使われる。片方だけを
確かめていると、受け口の翻訳がずれたときに気づけない。
"""
import json
import subprocess
import sys
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_path_is_projection import CheckPathIsProjection
from waffle.shared.result import Ok

_ROOT = Path(__file__).resolve().parents[3]
_PATH = ".waffle/skills/ddd-advisor/SKILL.md"


def _via_cli(*args: str) -> dict:
    result = subprocess.run(
        [str(Path(sys.executable).parent / "waffle"), *args],
        cwd=_ROOT, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_直接呼び出しとCLI呼び出しで同じ判定結果になる():
    """
    Scenario: 直接呼び出しとCLI呼び出しで同じ判定結果になる
    Given 実体パスが".waffle/skills/ddd-advisor/SKILL.md"である
    When Pythonから直接CheckPathIsProjectionを呼び出す
    Then isProjection=trueが返る
    When 同じ入力をCLI経由（waffle check-path-is-projection）で呼び出す
    Then 同じ判定結果が返る
    """
    direct = CheckPathIsProjection(FsDocumentRepository()).run(_PATH)
    assert isinstance(direct, Ok)
    assert direct.value["isProjection"] is True

    via_cli = _via_cli("check-path-is-projection", "--resolvedPath", _PATH)

    assert via_cli == direct.value
