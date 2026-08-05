"""まとめを1つ作る操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。仕様の文言が変われば、ここが古いままであることに
気づける。

対象の仕様: uc-create-project
"""
import inspect

import pytest

from project_setup import VIEWER_DOMAIN, X, Y, index_of, listing_of, owned, setup
from application.usecases.control_project_access import ControlProjectAccess
from application.usecases.create_project import CreateProject
from application.usecases.issue_view_token import IssueViewToken
from application.usecases.revoke_view_token import RevokeViewToken
from shared.errors import ProjectError
from usecase_builder import build


def test_作ると共有URLと閲覧トークンが返る():
    """
    Scenario: 作ると共有URLと閲覧トークンが返る
    Given 表示名と共有の別が示されている
    When プロジェクトを作る
    Then 共有URLと閲覧トークンが返る
    And 入っている共有アーティファクトは0件である
    """
    deps = setup()

    r = build(deps, CreateProject).run(X, "検索基盤リニューアル", "PERSONAL")

    assert r.url == f"https://{VIEWER_DOMAIN}/proj/{r.project_id}/"
    assert r.token
    assert r.token_shown_once is True
    assert index_of(deps, r.project_id)["memberArtifactIds"] == []
    assert listing_of(deps, r.project_id)["artifacts"] == []


def test_作った人が持ち主になる():
    """
    Scenario: 作った人が持ち主になる
    Given 投稿者Xがプロジェクトを作る
    Then Xが持ち主として記録されている
    And Xは閲覧トークンの発行・無効化と公開停止ができる
    """
    deps = setup()

    r = owned(deps, caller=X, scope="SHARED")

    index = index_of(deps, r.project_id)
    assert index["owner"] == X.id
    assert index["scope"] == "SHARED"

    subject = _project(r.project_id)
    issued = build(deps, IssueViewToken).run(X, subject, "レビュー班", None)
    assert issued.token
    assert build(deps, RevokeViewToken).run(X, subject, issued.token_id).revoked is True
    build(deps, ControlProjectAccess).run("suspend", X, r.project_id)
    assert index_of(deps, r.project_id)["status"] == "disabled"


def test_表示名が空なら作らない():
    """
    Scenario: 表示名が空なら作らない
    Given 表示名が空である
    When プロジェクトを作ろうとする
    Then NAME_REQUIRED として拒まれる
    And 閲覧トークンは発行されない
    """
    deps = setup()

    with pytest.raises(ProjectError) as x:
        build(deps, CreateProject).run(X, "   ", "PERSONAL")

    assert x.value.code == "NAME_REQUIRED"
    assert deps.keys.keys == {}


def test_招かれていない者は作れない(monkeypatch):
    """
    Scenario: 招かれていない者は作れない
    Given 操作する者が招かれた投稿者でない
    When プロジェクトを作ろうとする
    Then NOT_INVITED として拒まれる

    招かれているかを確かめるのは受け口の仕事で、業務の操作へは到達しない。
    ここでは受け口ごと通して、その手前で止まることを見る。
    """
    import main

    monkeypatch.setattr(main, "_identify", lambda _authorization: None)

    response = main.handler(
        {"headers": {"authorization": "Bearer 招かれていない"},
         "body": '{"action": "create-project", "displayName": "まとめ"}'}, None)

    assert response["statusCode"] == 403
    assert "NOT_INVITED" in response["body"]


def test_共有の別はあとから変えられない():
    """
    Scenario: 共有の別はあとから変えられない
    Given 個人として作られたプロジェクトがある
    And その閲覧トークンを相手へ渡している
    When 共有へ変えようとする
    Then 変えられない

    変える手立てそのものを持たせないことで守っている。見せ方を変える操作は
    止める・再開するしか受け取らず、共有の別を受け取る口が無い。
    """
    deps = setup()
    r = owned(deps, scope="PERSONAL")
    assert r.token  # 相手へ渡してある

    assert "scope" not in inspect.signature(ControlProjectAccess.run).parameters
    for action in ("share", "set-scope", "SHARED"):
        with pytest.raises(ValueError):
            build(deps, ControlProjectAccess).run(action, X, r.project_id)

    assert index_of(deps, r.project_id)["scope"] == "PERSONAL"


def _project(project_id):
    from domain.view_subject import ViewSubject
    return ViewSubject.project(project_id)
