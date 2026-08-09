"""見せる相手を1つ外す操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。仕様の文言が変われば、ここが古いままであることに
気づける。

対象の仕様: uc-revoke-view-token
"""

import pytest

from usecase_builder import build
from view_token_setup import AID, ME, NOW, issue, setup
from application.usecases.revoke_view_token import RevokeViewToken
from application.view_token_access import ViewTokenError
from domain.value_objects import view_token
from domain.value_objects.view_subject import ViewSubject


def test_指定した閲覧トークンだけが使えなくなる():
    """
    Scenario: 指定した閲覧トークンだけが使えなくなる
    Given 閲覧トークンが3本ある対象
    When そのうち1本を無効にする
    Then その閲覧トークンでは開けない
    And 残る2本ではどちらも開ける
    """
    deps = setup()
    a = issue(deps, "1人目")
    issue(deps, "2人目")
    issue(deps, "3人目")

    build(deps, RevokeViewToken).run(ME, ViewSubject.artifact(AID), a.token_id)

    left = view_token.usable(deps.artifacts.find(AID).view_tokens, NOW)
    assert [t.name for t in left] == ["2人目", "3人目"]
    # 閲覧の面へも残った2本だけが渡っている（区切りが1つ＝2本）
    assert deps.gate._keys.written["token:" + AID].count(";") == 1


def test_無効にしても公開は止まらない():
    """
    Scenario: 無効にしても公開は止まらない
    Given 閲覧トークンが2本ある共有アーティファクト
    When 1本を無効にする
    Then 対象の公開は止まっていない
    """
    deps = setup()
    a = issue(deps, "1人目")
    issue(deps, "2人目")

    build(deps, RevokeViewToken).run(ME, ViewSubject.artifact(AID), a.token_id)

    assert deps.artifacts.find(AID).status.is_published()
    assert deps.gate._keys.written["token:" + AID] != "DISABLED"


def test_すべて無効にしても公開は止まらない():
    """
    Scenario: すべて無効にしても公開は止まらない
    Given 閲覧トークンが2本ある共有アーティファクト
    When 2本とも無効にする
    Then どの閲覧トークンでも開けない
    And 対象の公開は止まっていない
    """
    deps = setup()
    a = issue(deps, "1人目")
    b = issue(deps, "2人目")
    subject = ViewSubject.artifact(AID)

    build(deps, RevokeViewToken).run(ME, subject, a.token_id)
    build(deps, RevokeViewToken).run(ME, subject, b.token_id)

    assert view_token.usable(deps.artifacts.find(AID).view_tokens, NOW) == ()
    assert deps.artifacts.find(AID).status.is_published()
    assert deps.gate._keys.written["token:" + AID] == ""


def test_既に無効な閲覧トークンをもう一度無効にしても変わらない():
    """
    Scenario: 既に無効な閲覧トークンをもう一度無効にしても変わらない
    Given 既に無効にした閲覧トークン
    When もう一度その閲覧トークンを無効にする
    Then 成功し、他の閲覧トークンも変わっていない
    """
    deps = setup()
    a = issue(deps, "1人目")
    issue(deps, "2人目")
    subject = ViewSubject.artifact(AID)
    build(deps, RevokeViewToken).run(ME, subject, a.token_id)

    got = build(deps, RevokeViewToken).run(ME, subject, a.token_id)

    assert got.revoked is True
    left = view_token.usable(deps.artifacts.find(AID).view_tokens, NOW)
    assert [t.name for t in left] == ["2人目"]


def test_存在しない閲覧トークンの無効化は拒まれる():
    """
    Scenario: 存在しない閲覧トークンの無効化は拒まれる
    Given 公開されている対象
    When その対象に存在しない閲覧トークンを指定して無効化を求める
    Then TOKEN_NOT_FOUND として拒まれる
    """
    deps = setup()

    with pytest.raises(ViewTokenError) as x:
        build(deps, RevokeViewToken).run(ME, ViewSubject.artifact(AID), "nope")

    assert x.value.code == "TOKEN_NOT_FOUND"
