"""uc-check-query-precedes-array-fill の操作保証テスト。

同じ判断が、Pythonから直接呼んでもCLIから呼んでも同じ答えを返すことを確かめる。
この判断はフックからCLI経由で使われ、テストからは直接使われる。片方だけを
確かめていると、受け口の翻訳がずれたときに気づけない。
"""
import json
import subprocess
import sys
from pathlib import Path

from waffle.application.usecases.check_query_precedes_array_fill import (
    CheckQueryPrecedesArrayFill,
)
from waffle.shared.result import Ok

_ROOT = Path(__file__).resolve().parents[3]


def _via_cli(*args: str) -> dict:
    result = subprocess.run(
        [str(Path(sys.executable).parent / "waffle"), *args],
        cwd=_ROOT, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_直接呼び出しとCLI呼び出しで同じ判定結果になる():
    """
    Scenario: 直接呼び出しとCLI呼び出しで同じ判定結果になる
    Given targetPathが"X.json"であり、hasArrayValueがtrueであり、queriedPathsに"X.json"が含まれていない
    When Pythonから直接CheckQueryPrecedesArrayFillを呼び出す
    Then 拒否判定が返る
    When 同じ入力をCLI経由（waffle check-query-precedes-array-fill）で呼び出す
    Then 同じ拒否判定が返る
    """
    direct = CheckQueryPrecedesArrayFill().run("X.json", True, [])
    assert isinstance(direct, Ok)
    assert direct.value["allowed"] is False

    via_cli = _via_cli("check-query-precedes-array-fill",
                       "--targetPath", "X.json", "--hasArrayValue")

    assert via_cli == direct.value
