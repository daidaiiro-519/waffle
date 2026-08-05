"""見せる相手をまとめて外す操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。仕様の文言が変われば、ここが古いままであることに
気づける。

対象の仕様: uc-revoke-all-view-tokens
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from usecase_builder import build  # noqa: E402
from view_token_setup import AID, ME, NOW, PID, issue, setup  # noqa: E402
from application.usecases.revoke_all_view_tokens import RevokeAllViewTokens  # noqa: E402
from domain import view_token  # noqa: E402
from domain.view_subject import ViewSubject  # noqa: E402


def test_すべての閲覧トークンが一度に使えなくなる():
    """
    Scenario: すべての閲覧トークンが一度に使えなくなる
    Given 閲覧トークンが3本ある共有アーティファクト
    When まとめて外すことを求める
    Then 3本のいずれでも開けない
    """
    deps = setup()
    issue(deps, "1人目")
    issue(deps, "2人目")
    issue(deps, "3人目")

    got = build(deps, RevokeAllViewTokens).run(ME, ViewSubject.artifact(AID))

    assert got.revoked == 3
    assert view_token.usable(deps.artifacts.find(AID).view_tokens, NOW) == ()
    assert deps.gate._keys.written["token:" + AID] == ""


def test_まとめて外しても公開は止まらない():
    """
    Scenario: まとめて外しても公開は止まらない
    Given 閲覧トークンが2本ある共有アーティファクト
    When まとめて外すことを求める
    Then 対象の公開は止まっていない
    And 新しい閲覧トークンを発行すれば再び見せられる
    """
    deps = setup()
    issue(deps, "1人目")
    issue(deps, "2人目")

    build(deps, RevokeAllViewTokens).run(ME, ViewSubject.artifact(AID))

    assert deps.artifacts.find(AID).status.is_published()
    again = issue(deps, "改めて")
    assert again.token
    assert deps.gate._keys.written["token:" + AID] != ""


def test_まとめの側の閲覧トークンからは引き続き開ける():
    """
    Scenario: まとめの側の閲覧トークンからは引き続き開ける
    Given 共有アーティファクトAがプロジェクトPに入っている
    When Aの閲覧トークンをまとめて外す
    Then Pの閲覧トークンでAを開ける
    """
    deps = setup()
    issue(deps, "まとめ", subject=ViewSubject.project(PID))
    issue(deps, "個別")

    build(deps, RevokeAllViewTokens).run(ME, ViewSubject.artifact(AID))

    assert deps.gate._keys.written["proj:" + PID] != ""


def test_1本も無い状態でまとめて外しても変わらない():
    """
    Scenario: 1本も無い状態でまとめて外しても変わらない
    Given 有効な閲覧トークンが1本も無い共有アーティファクト
    When まとめて外すことを求める
    Then 成功し、対象の公開は止まっていない
    """
    deps = setup()

    got = build(deps, RevokeAllViewTokens).run(ME, ViewSubject.artifact(AID))

    assert got.revoked == 0
    assert deps.artifacts.find(AID).status.is_published()
