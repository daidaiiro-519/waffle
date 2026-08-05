"""見せる相手を1つ増やす操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。仕様の文言が変われば、ここが古いままであることに
気づける。

対象の仕様: uc-issue-view-token
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

from view_token_setup import AID, NOW, PID, issue, setup  # noqa: E402
from application.view_token_access import ViewTokenError  # noqa: E402
from domain import view_token  # noqa: E402
from domain.view_subject import ViewSubject  # noqa: E402


def test_発行しても既存の閲覧トークンは使えたまま残る():
    """
    Scenario: 発行しても既存の閲覧トークンは使えたまま残る
    Given 閲覧トークンが1本ある共有アーティファクト
    When 新しい閲覧トークンを発行する
    Then 新しい閲覧トークンで開ける
    And それまでの閲覧トークンでも開ける
    """
    deps = setup()
    first = issue(deps, "1人目")

    second = issue(deps, "2人目")

    names = [t.name for t in
             view_token.usable(deps.artifacts.find(AID).view_tokens, NOW)]
    assert names == ["1人目", "2人目"]
    assert first.token and second.token
    # 閲覧の面へも2本が渡っている（区切りが1つ＝2本）
    assert deps.gate._keys.written["token:" + AID].count(";") == 1


def test_期限を指定しないと1週間になる():
    """
    Scenario: 期限を指定しないと1週間になる
    Given 公開されている共有アーティファクト
    When 期限を指定せずに閲覧トークンを発行する
    Then その閲覧トークンの期限は発行から1週間後である
    """
    deps = setup()

    r = issue(deps, "レビュー班")

    assert r.expires_at == NOW + view_token.WEEK


def test_1ヶ月を超える期限は拒まれる():
    """
    Scenario: 1ヶ月を超える期限は拒まれる
    Given 公開されている共有アーティファクト
    When 発行から1ヶ月を超える期限を指定して発行を求める
    Then EXPIRY_TOO_FAR として拒まれる
    """
    deps = setup()

    with pytest.raises(ViewTokenError) as x:
        issue(deps, "ずっと", ttl=view_token.MONTH + 1)

    assert x.value.code == "EXPIRY_TOO_FAR"
    assert deps.artifacts.find(AID).view_tokens == ()


def test_プロジェクトには期限を設けない指定ができる():
    """
    Scenario: プロジェクトには期限を設けない指定ができる
    Given 公開されているプロジェクト
    When 期限を設けない指定で閲覧トークンを発行する
    Then 発行できる
    """
    deps = setup()

    r = issue(deps, "常設", ttl=0, subject=ViewSubject.project(PID))

    assert r.expires_at == view_token.NO_EXPIRY


def test_上限に達していると発行できない():
    """
    Scenario: 上限に達していると発行できない
    Given 有効な閲覧トークンが上限に達している共有アーティファクト
    When 新しい閲覧トークンを発行しようとする
    Then TOKEN_LIMIT_REACHED として拒まれる
    """
    deps = setup()
    for i in range(view_token.MAX_ACTIVE):
        issue(deps, f"相手{i}")

    with pytest.raises(ViewTokenError) as x:
        issue(deps, "もう1人")

    assert x.value.code == "TOKEN_LIMIT_REACHED"
    assert len(deps.artifacts.find(AID).view_tokens) == view_token.MAX_ACTIVE


def test_同じ名前では発行できない():
    """
    Scenario: 同じ名前では発行できない
    Given 「デザインチーム」という名前の有効な閲覧トークンがある対象
    When 同じ名前で発行を求める
    Then DUPLICATE_TOKEN_NAME として拒まれる
    """
    deps = setup()
    issue(deps, "デザインチーム")

    with pytest.raises(ViewTokenError) as x:
        issue(deps, "デザインチーム")

    assert x.value.code == "DUPLICATE_TOKEN_NAME"


def test_期限を過ぎた閲覧トークンは発行のときに取り除かれる():
    """
    Scenario: 期限を過ぎた閲覧トークンは発行のときに取り除かれる
    Given 期限を過ぎた閲覧トークンがある対象
    When 新しい閲覧トークンを発行する
    Then 期限を過ぎた閲覧トークンの記録は残っていない
    """
    deps = setup()
    for i in range(view_token.MAX_ACTIVE):
        issue(deps, f"相手{i}", ttl=view_token.WEEK)

    later = NOW + view_token.WEEK + 1
    r = issue(deps, "新しい相手", at=later)

    assert r.token
    assert [t.name for t in deps.artifacts.find(AID).view_tokens] == ["新しい相手"]

