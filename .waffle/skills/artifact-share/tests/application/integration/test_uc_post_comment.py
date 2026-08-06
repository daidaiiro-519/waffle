"""コメントを残す操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

誰でも投稿でき、Lambdaを通らない。だから守りは書き込みそのものの形に置く——
上書きを拒む宣言と、衝突しない鍵。どちらも閲覧画面と閲覧ゲートの両方に規則が
あり、片方だけでは守れない。

対象の仕様: uc-post-comment（操作保証）
"""
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[3]
VIEWER = (SKILL / "references" / "templates" / "share-wrapper.html").read_text(
    encoding="utf-8")
GATE = (SKILL / "infra" / "cloudfront-function" / "viewer-token-gate.js").read_text(
    encoding="utf-8")


def test_残したコメントは書き換えられない():
    """
    Scenario: 残したコメントは書き換えられない
    Given 閲覧者がコメントを1件残している
    When 同じArtifactIdで別の内容を送る
    Then 元のコメントは変わらない

    送る側が上書きを拒む宣言を必ず付け、検査する側が付いていないものを通さない。
    実際に走らせる検証は viewer-token-gate.test.mjs の「条件なしの書き込みは拒む」。
    """
    assert "'if-none-match': '*'" in VIEWER
    assert "ifNoneMatch !== '*'" in GATE


def test_同時に残しても失われない():
    """
    Scenario: 同時に残しても失われない
    Given 2人の閲覧者が同じ共有アーティファクトを見ている
    When 2人がほぼ同時にコメントを残す
    Then 2件とも残っている

    1件が1つの記録で、鍵に時刻と乱数を含める。上書きを拒む宣言と合わせて、
    衝突したときは後から来た方が拒まれる——黙って消えることはない。
    """
    key_line = re.search(r"var key = 'comments/'.*", VIEWER).group(0)

    assert "Date.now()" in key_line
    assert "crypto.randomUUID()" in key_line
