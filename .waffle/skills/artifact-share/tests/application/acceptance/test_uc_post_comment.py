"""コメントを残す操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

この操作は業務のLambdaを通らない。閲覧画面が記録を組み立てて保管へ直接書き、
閲覧ゲートが鍵の形・種類・大きさ・上書きの宣言を検査する。つまり実装は
「層を持たない」と宣言した2つの出荷物にまたがる。

だからここで確かめるのは、出荷する2つが定めどおりであること。閲覧ゲートを
実際に走らせる検証は infra/cloudfront-function/tests/viewer-token-gate.test.mjs
にあり、tests/adapters/inbound/contract/test_deployed_gate.py が配る形に対して
それを回している。

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-post-comment
"""
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[3]
VIEWER = (SKILL / "references" / "templates" / "share-wrapper.html").read_text(
    encoding="utf-8")
GATE = (SKILL / "infra" / "cloudfront-function" / "viewer-token-gate.js").read_text(
    encoding="utf-8")


def _post_body() -> str:
    """コメントを組み立てて送るところだけを取り出す。"""
    start = VIEWER.index("function post(event)")
    return VIEWER[start:VIEWER.index("function", start + 10)]


def test_名乗るだけでコメントを残せる():
    """
    Scenario: 名乗るだけでコメントを残せる
    Given 閲覧者はあらかじめ登録されていない
    When 名乗りと本文を与えてコメントを残す
    Then コメントが1件残る
    And そのコメントは共有アーティファクトAに結び付いている
    """
    post = _post_body()

    # 名乗りは求めるが、登録は求めない
    assert "お名前を入れてください。" in post
    assert "signIn" not in post and "authorization" not in post
    # 1件が1つの記録として、その共有アーティファクトの下に置かれる
    assert "'comments/' + ARTIFACT_ID + '/'" in post


def test_判定を添えられる():
    """
    Scenario: 判定を添えられる
    When この方向でよいという判定を添えてコメントを残す
    Then その判定とともにコメントが残る
    And 後から読んだ人が、合意が示されたことを読み取れる
    """
    post = _post_body()

    assert "input[name=dec]:checked" in post
    assert "decision: checked ? checked.value" in post
    # 読む側も判定を取り出して描く
    assert re.search(r"decision:\s*String\(rec\.decision", VIEWER)


def test_判定が無ければただの意見として扱う():
    """
    Scenario: 判定が無ければただの意見として扱う
    When 判定を添えずにコメントを残す
    Then ただの意見として残る
    """
    assert "checked ? checked.value : 'comment'" in _post_body()


def test_本文は文字として示される():
    """
    Scenario: 本文は文字として示される
    When 組み立ての指示に見える文字列を本文に含めてコメントを残す
    Then 他の閲覧者にはその文字列がそのまま文字として見える
    And 指示として実行されることはない

    誰でも投稿でき、投稿は上書きできず残る。ここが崩れると消せない仕掛けが残る。
    """
    assert re.findall(r"\.innerHTML\s*=", VIEWER) == []
    assert ".textContent" in VIEWER


def test_同じ共有アーティファクトのコメントへ返信できる():
    """
    Scenario: 同じ共有アーティファクトのコメントへ返信できる
    Given 共有アーティファクトAにコメントが1件ある
    When そのコメントを返信先に指して新しいコメントを残す
    Then 返信として結び付いて残る
    """
    post = _post_body()

    assert "parentId: replyTarget ? replyTarget.__id : null" in post


def test_別の共有アーティファクトのコメントへは返信できない():
    """
    Scenario: 別の共有アーティファクトのコメントへは返信できない
    Given 共有アーティファクトBにコメントが1件ある
    When 共有アーティファクトAへのコメントとして、共有アーティファクトBのコメントを返信先に指す
    Then INVALID_PARENT として拒まれる

    返信先は、いま開いている共有アーティファクトの並びからしか選べない。
    そして書き込む鍵はその共有アーティファクトの下に閉じており、閲覧ゲートも
    鍵の形を検査する。別のものへ結び付ける経路が構造として無い。
    """
    assert "'comments/' + ARTIFACT_ID + '/'" in _post_body()
    assert re.search(r"\^/comments/'\s*\+\s*artifactId", GATE)


def test_停止している共有アーティファクトには残せない():
    """
    Scenario: 停止している共有アーティファクトには残せない
    Given 共有アーティファクトAが公開停止されている
    When コメントを残そうとする
    Then ARTIFACT_NOT_VIEWABLE として拒まれる
    """
    # 書き込みも、開くのと同じ関所を通る（先に鍵の在り処を確かめる）
    assert "const isCommentPut = method === 'PUT'" in GATE
    put_gate = GATE[GATE.index("const isCommentPut"):]
    assert "readKey('token:' + artifactId)" in put_gate
    assert "DISABLED" in put_gate


def test_大きすぎる本文は拒む():
    """
    Scenario: 大きすぎる本文は拒む
    When 受け入れられる大きさを超える本文でコメントを残そうとする
    Then BODY_TOO_LARGE として拒まれる
    And 拒まれた理由が閲覧者に伝わる
    """
    assert re.search(r"len > 16384", GATE)
    # 拒まれたことは閲覧者へ伝わる
    assert "showError" in _post_body() or "showError" in VIEWER
