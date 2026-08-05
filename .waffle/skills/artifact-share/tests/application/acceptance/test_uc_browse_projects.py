"""まとめを見て回る操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。仕様の文言が変われば、ここが古いままであることに
気づける。

対象の仕様: uc-browse-projects
"""
import pytest

from project_setup import ADMIN, X, Y, artifact, assign, owned, setup
from application.usecases.browse_projects import BrowseProjects
from application.usecases.control_project_access import ControlProjectAccess
from shared.errors import ProjectError
from usecase_builder import build


def _list(deps, caller):
    return build(deps, BrowseProjects).run("list", caller)


def _detail(deps, caller, project_id):
    return build(deps, BrowseProjects).run("detail", caller, project_id)


def test_持ち主のものと共有のものが並ぶ():
    """
    Scenario: 持ち主のものと共有のものが並ぶ
    Given 投稿者Xが個人のプロジェクトPを作っている
    And 投稿者Yが共有のプロジェクトQを作っている
    When 投稿者Xが一覧を求める
    Then P と Q が並ぶ
    """
    deps = setup()
    p = owned(deps, caller=X, name="P", scope="PERSONAL")
    q = owned(deps, caller=Y, name="Q", scope="SHARED")

    ids = {row.project_id for row in _list(deps, X).projects}

    assert {p.project_id, q.project_id} <= ids


def test_他人の個人のプロジェクトは並ばない():
    """
    Scenario: 他人の個人のプロジェクトは並ばない
    Given 投稿者Yが個人のプロジェクトRを作っている
    When 投稿者Xが一覧を求める
    Then R は含まれない
    """
    deps = setup()
    r = owned(deps, caller=Y, name="R", scope="PERSONAL")

    ids = {row.project_id for row in _list(deps, X).projects}

    assert r.project_id not in ids


def test_管理者にはすべてが並ぶ():
    """
    Scenario: 管理者にはすべてが並ぶ
    Given 投稿者Yが個人のプロジェクトRを作っている
    When 管理者が一覧を求める
    Then R が含まれる
    """
    deps = setup()
    r = owned(deps, caller=Y, name="R", scope="PERSONAL")

    ids = {row.project_id for row in _list(deps, ADMIN).projects}

    assert r.project_id in ids


def test_中身が名前つきで返る():
    """
    Scenario: 中身が名前つきで返る
    Given プロジェクトPに共有アーティファクトAが入っている
    When 投稿者XがPの中身を求める
    Then A の表示名と状態が返る
    """
    deps = setup()
    p = owned(deps, caller=X, name="P")
    artifact(deps, "aaaaaaaa", "検索基盤の選定")
    assign(deps, X, "aaaaaaaa", p.project_id)

    got = _detail(deps, X, p.project_id)

    assert [a.artifact_id for a in got.artifacts] == ["aaaaaaaa"]
    assert got.artifacts[0].name == "検索基盤の選定"
    assert got.artifacts[0].status


def test_自分のものかどうかが分かる():
    """
    Scenario: 自分のものかどうかが分かる
    Given 共有のプロジェクトQに、投稿者XのAと投稿者YのBが入っている
    When 投稿者XがQの中身を求める
    Then A は自分のもの、B はそうでないと分かる
    """
    deps = setup()
    q = owned(deps, caller=X, name="Q", scope="SHARED")
    artifact(deps, "aaaaaaaa", "Xのもの", owner=X)
    artifact(deps, "bbbbbbbb", "Yのもの", owner=Y)
    assign(deps, X, "aaaaaaaa", q.project_id)
    assign(deps, Y, "bbbbbbbb", q.project_id)

    got = _detail(deps, X, q.project_id)

    mine = {a.artifact_id: a.is_mine for a in got.artifacts}
    assert mine == {"aaaaaaaa": True, "bbbbbbbb": False}


def test_止まっていても中身は見られる():
    """
    Scenario: 止まっていても中身は見られる
    Given プロジェクトPの公開が止まっている
    When 投稿者XがPの中身を求める
    Then 入っているものの一覧が返る

    止めたものを再開するか外すかを決めるのに、中身が見えている必要がある。
    """
    deps = setup()
    p = owned(deps, caller=X, name="P")
    artifact(deps, "aaaaaaaa", "検索基盤の選定")
    assign(deps, X, "aaaaaaaa", p.project_id)
    build(deps, ControlProjectAccess).run("suspend", X, p.project_id)

    got = _detail(deps, X, p.project_id)

    assert got.project.status == "SUSPENDED"
    assert [a.artifact_id for a in got.artifacts] == ["aaaaaaaa"]


def test_見れないプロジェクトは存在しない扱いになる():
    """
    Scenario: 見れないプロジェクトは存在しない扱いになる
    Given 投稿者Yが個人のプロジェクトRを作っている
    When 投稿者XがRの中身を求める
    Then 見つからないとして拒まれる
    And 存在しない識別子を指したときと同じ答えになる

    そこに何かがあること自体を読み取らせない。
    """
    deps = setup()
    r = owned(deps, caller=Y, name="R", scope="PERSONAL")

    with pytest.raises(ProjectError) as hidden:
        _detail(deps, X, r.project_id)
    with pytest.raises(ProjectError) as absent:
        _detail(deps, X, "no-such-project")

    assert hidden.value.code == absent.value.code == "PROJECT_NOT_FOUND"
    assert str(hidden.value) == str(absent.value)


def test_読めない記録があっても残りは返る():
    """
    Scenario: 読めない記録があっても残りは返る
    Given 投稿者XがプロジェクトPとQを作っている
    And P の記録が読めない状態になっている
    When 投稿者Xが一覧を求める
    Then Q が返る
    And 読めなかった件数が1と伝わる

    一覧が黙って短くなると、作ったはずのプロジェクトが消えたように見える。
    """
    deps = setup()
    p = owned(deps, caller=X, name="P")
    q = owned(deps, caller=X, name="Q")
    deps.store.put(f"projects/{p.project_id}.json", "{壊れている", "application/json")

    got = _list(deps, X)

    assert [row.project_id for row in got.projects] == [q.project_id]
    assert got.unreadable == 1


def test_閲覧トークンはどちらにも現れない():
    """
    Scenario: 閲覧トークンはどちらにも現れない
    Given 投稿者XがプロジェクトPを作り、閲覧トークンを受け取っている
    When 投稿者Xが一覧と P の中身を求める
    Then どちらの答えにも、その閲覧トークンの値は現れない
    """
    deps = setup()
    p = owned(deps, caller=X, name="P")

    listed = _list(deps, X)
    detail = _detail(deps, X, p.project_id)

    assert p.token not in repr(listed)
    assert p.token not in repr(detail)
    for row in listed.projects:
        assert not hasattr(row, "token")
    assert not hasattr(detail.project, "token")
