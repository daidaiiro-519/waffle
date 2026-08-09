"""まとめの見せ方を変える操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。仕様の文言が変われば、ここが古いままであることに
気づける。

まとめを止めることと、その中身を止めることは別。まとめの閲覧トークンが
閉じても、中身へ個別に渡した閲覧トークンはそのまま生きている。

対象の仕様: uc-control-project-access
"""
import pytest

from project_setup import ADMIN, X, Y, artifact, assign, index_of, owned, setup
from application.usecases.control_project_access import ControlProjectAccess
from application.usecases.issue_view_token import IssueViewToken
from domain.value_objects.view_subject import ViewSubject
from shared.errors import ProjectError
from usecase_builder import build


def _control(deps, operation, caller, project_id):
    return build(deps, ControlProjectAccess).run(operation, caller, project_id)


def test_公開停止しても中身は個別の閲覧トークンで開ける():
    """
    Scenario: 公開停止しても中身は個別の閲覧トークンで開ける
    Given 共有アーティファクトAの閲覧トークンを別の相手へ渡している
    When Xがプロジェクトを公開停止する
    Then プロジェクトの閲覧トークンでは何も開けない
    And Aの閲覧トークンを持つ相手はAを開ける
    """
    deps = setup()
    p = owned(deps, caller=X)
    artifact(deps, "aaaaaaaa", "検索基盤の選定")
    assign(deps, X, "aaaaaaaa", p.project_id)
    build(deps, IssueViewToken).run(
        X, ViewSubject.artifact("aaaaaaaa"), "別の相手", None)
    for_artifact = deps.keys.written["token:aaaaaaaa"]

    _control(deps, "suspend", X, p.project_id)

    assert deps.keys.written[f"proj:{p.project_id}"] == "DISABLED"
    assert deps.keys.written["token:aaaaaaaa"] == for_artifact


def test_管理者は自分が作ったものでなくても扱える():
    """
    Scenario: 管理者は自分が作ったものでなくても扱える
    Given プロジェクトの持ち主がXである
    When 管理者が公開停止を求める
    Then 公開停止される

    持ち主が抜けたあとに、誰も止められないプロジェクトが残らないこと。
    """
    deps = setup()
    p = owned(deps, caller=X)

    _control(deps, "suspend", ADMIN, p.project_id)

    assert index_of(deps, p.project_id)["status"] == "disabled"


def test_共有でも持ち主以外は見せ方を変えられない():
    """
    Scenario: 共有でも持ち主以外は見せ方を変えられない
    Given プロジェクトが共有であり、投稿者Yが自分の共有アーティファクトを入れている
    When Yが公開停止を求める
    Then PROJECT_NOT_FOUND として拒まれる
    And プロジェクトは開ける状態のままである

    出し入れができることと、見せ方を変えられることは別。誰でも止められると、
    他の人が渡した相手まで巻き込んで見えなくなる。
    """
    deps = setup()
    p = owned(deps, caller=X, scope="SHARED")
    artifact(deps, "bbbbbbbb", "Yのもの", owner=Y)
    assign(deps, Y, "bbbbbbbb", p.project_id)

    with pytest.raises(ProjectError) as x:
        _control(deps, "suspend", Y, p.project_id)

    assert x.value.code == "PROJECT_NOT_FOUND"
    assert index_of(deps, p.project_id)["status"] == "active"


def test_止まっていないものは再開できない():
    """
    Scenario: 止まっていないものは再開できない
    Given プロジェクトが開ける状態である
    When Xが再開を求める
    Then NOT_SUSPENDED として拒まれる
    """
    deps = setup()
    p = owned(deps, caller=X)

    with pytest.raises(ProjectError) as x:
        _control(deps, "resume", X, p.project_id)

    assert x.value.code == "NOT_SUSPENDED"


def test_再び開けるようにしても止める前の閲覧トークンで開ける():
    """
    Scenario: 再び開けるようにしても止める前の閲覧トークンで開ける
    Given 開けない状態にしたプロジェクトと、期限内で無効にされていない閲覧トークン
    When 再び開ける状態に戻す
    Then その閲覧トークンで、入っている共有アーティファクトを開ける
    """
    deps = setup()
    p = owned(deps, caller=X)
    artifact(deps, "aaaaaaaa", "検索基盤の選定")
    assign(deps, X, "aaaaaaaa", p.project_id)
    before = deps.keys.written[f"proj:{p.project_id}"]
    _control(deps, "suspend", X, p.project_id)

    _control(deps, "resume", X, p.project_id)

    assert deps.keys.written[f"proj:{p.project_id}"] == before
    assert index_of(deps, p.project_id)["status"] == "active"
    assert "aaaaaaaa" in index_of(deps, p.project_id)["memberArtifactIds"]
