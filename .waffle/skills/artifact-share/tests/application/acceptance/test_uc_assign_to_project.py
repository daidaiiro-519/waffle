"""共有アーティファクトをまとめへ出し入れする操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。仕様の文言が変われば、ここが古いままであることに
気づける。

対象の仕様: uc-assign-to-project
"""
import pytest

from manage_setup import (
    HTML, ME, OTHER, SOMEONE_ELSE, meta_of, project, with_project,
)
from adapters.outbound.kvs_view_gate import MEMBERSHIP_SEPARATOR
from application.usecases.create_project import CreateProject
from domain.entities.shared_artifact import MAX_PROJECTS
from application.usecases.assign_artifact_to_project import AssignArtifactToProject
from application.usecases.control_project_access import ControlProjectAccess
from application.usecases.replace_artifact_content import ReplaceArtifactContent
from application.usecases.suspend_artifact import SuspendArtifact
from shared.errors import ManageError
from usecase_builder import build


def _assign(deps, caller, artifact_id, project_id, operation="assign"):
    return build(deps, AssignArtifactToProject).run(
        operation, caller, artifact_id, project_id)


def test_加えるとプロジェクト閲覧トークンで開ける():
    """
    Scenario: 加えるとプロジェクト閲覧トークンで開ける
    When 共有アーティファクトAをPへ加える
    Then Pの閲覧トークンで共有アーティファクトAを開ける
    And 共有アーティファクトA自身の閲覧トークンも引き続き使える
    """
    deps, r, pid = with_project("PERSONAL")
    own_token = deps.keys.written[f"token:{r.artifact_id}"]

    _assign(deps, ME, r.artifact_id, pid)

    assert deps.keys.written[f"pp:{r.artifact_id}"] == pid
    assert meta_of(deps, r.artifact_id)["projects"] == [pid]
    assert deps.keys.written[f"token:{r.artifact_id}"] == own_token


def test_外しても共有アーティファクトは生きている():
    """
    Scenario: 外しても共有アーティファクトは生きている
    Given 共有アーティファクトAがPに入っている
    When 共有アーティファクトAをPから外す
    Then Pの閲覧トークンでは共有アーティファクトAを開けない
    And 共有アーティファクトA自身の閲覧トークンでは開ける
    """
    deps, r, pid = with_project("PERSONAL")
    _assign(deps, ME, r.artifact_id, pid)

    _assign(deps, ME, r.artifact_id, pid, operation="unassign")

    assert deps.keys.written[f"pp:{r.artifact_id}"] == ""
    assert meta_of(deps, r.artifact_id)["projects"] == []
    assert deps.keys.written[f"token:{r.artifact_id}"] != "DISABLED"
    assert deps.store.get(f"p/{r.artifact_id}/content.html")


def test_複数の単位に同時に入れる():
    """
    Scenario: 複数の単位に同時に入れる
    Given プロジェクトQも存在する
    When 共有アーティファクトAをPとQの両方へ加える
    Then Pの閲覧トークンでも、Qの閲覧トークンでも共有アーティファクトAを開ける
    """
    deps, r, p = with_project("PERSONAL")
    q = project(deps, "PERSONAL", name="Q")

    _assign(deps, ME, r.artifact_id, p)
    _assign(deps, ME, r.artifact_id, q)

    assert sorted(meta_of(deps, r.artifact_id)["projects"]) == sorted([p, q])
    belongs = deps.keys.written[f"pp:{r.artifact_id}"].split(MEMBERSHIP_SEPARATOR)
    assert set(belongs) == {p, q}


def test_中身に書いた値では所属できない():
    """
    Scenario: 中身に書いた値では所属できない
    Given 共有アーティファクトBはPに入っていない
    When 共有アーティファクトBの中身にPを指す分類の目印を書いて差し替える
    Then 共有アーティファクトBはPに入らない
    And Pの閲覧トークンで共有アーティファクトBを開けない
    """
    deps, r, pid = with_project("PERSONAL")
    tagged = HTML.replace("</head>", f'<meta name="tags" content="{pid}"></head>')

    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, tagged)

    meta = meta_of(deps, r.artifact_id)
    assert meta["tags"] == [pid]      # 目印としては控える
    assert meta["projects"] == []     # 所属は変わらない
    with pytest.raises(KeyError):
        deps.keys.written[f"pp:{r.artifact_id}"]


def test_停止している共有アーティファクトは加えても開けない():
    """
    Scenario: 停止している共有アーティファクトは加えても開けない
    Given 共有アーティファクトCが公開停止されている
    When 共有アーティファクトCをPへ加える
    Then 所属自体は成立する
    And Pの閲覧トークンでも共有アーティファクトCは開けない
    """
    deps, r, pid = with_project("PERSONAL")
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    _assign(deps, ME, r.artifact_id, pid)

    assert meta_of(deps, r.artifact_id)["projects"] == [pid]
    assert deps.keys.written[f"token:{r.artifact_id}"] == "DISABLED"


def test_停止している単位へは加えられない():
    """
    Scenario: 停止している単位へは加えられない
    Given プロジェクトPが公開停止されている
    When 共有アーティファクトAをPへ加えようとする
    Then PROJECT_SUSPENDED として拒まれる
    """
    deps, r, pid = with_project("SHARED")
    build(deps, ControlProjectAccess).run("suspend", ME, pid)

    with pytest.raises(ManageError) as x:
        _assign(deps, ME, r.artifact_id, pid)

    assert x.value.code == "PROJECT_SUSPENDED"


def test_共有なら他の人も自分のものを入れられる():
    """
    Scenario: 共有なら他の人も自分のものを入れられる
    Given 投稿者Xが共有としてプロジェクトPを作っている
    And 投稿者Yが共有アーティファクトBを公開している
    When YがBをPへ加える
    Then Pの閲覧トークンでBを開ける

    持ち主が『誰でも入れてよい』と決めた前提が働く。
    """
    deps, r, pid = with_project("SHARED", owner=OTHER)

    _assign(deps, ME, r.artifact_id, pid)

    assert deps.keys.written[f"pp:{r.artifact_id}"] == pid
    assert pid in meta_of(deps, r.artifact_id)["projects"]


def test_個人のプロジェクトへは持ち主しか入れられない():
    """
    Scenario: 個人のプロジェクトへは持ち主しか入れられない
    Given 投稿者Xが個人としてプロジェクトPを作っている
    When 投稿者Yが自分の共有アーティファクトをPへ加えようとする
    Then PROJECT_NOT_FOUND として拒まれる
    And Pに入っているものは変わらない

    渡した相手に何が見えるかを、持ち主が把握し続けられるようにする。
    """
    deps, r, pid = with_project("PERSONAL", owner=OTHER)

    with pytest.raises(ManageError) as x:
        _assign(deps, ME, r.artifact_id, pid)

    assert x.value.code == "PROJECT_NOT_FOUND"
    assert meta_of(deps, r.artifact_id)["projects"] == []


def test_他人の共有アーティファクトは出し入れできない():
    """
    Scenario: 他人の共有アーティファクトは出し入れできない
    Given 共有のプロジェクトPがある
    And 共有アーティファクトAの投稿者はXである
    When 投稿者YがAをPへ加えようとする
    Then ARTIFACT_NOT_FOUND として拒まれる
    """
    deps, r, pid = with_project("SHARED")

    with pytest.raises(ManageError) as x:
        _assign(deps, SOMEONE_ELSE, r.artifact_id, pid)

    assert x.value.code == "ARTIFACT_NOT_FOUND"


def test_上限を超えてプロジェクトへ加えられない():
    """
    Scenario: 上限を超えてプロジェクトへ加えられない
      Given 共有アーティファクトAが上限の数だけプロジェクトに入っている
      When Aをもう1つのプロジェクトへ加えようとする
      Then TOO_MANY_PROJECTS として拒まれる

    閲覧の面は先頭から決まった数しか見ない。書き手が黙って超えると、
    投稿者には成功が返り、閲覧者だけが開けない状態になる。
    """
    deps, r, _ = with_project("SHARED")
    ids = []
    for i in range(MAX_PROJECTS + 1):
        p = build(deps, CreateProject).run(ME, f"まとめ{i}", "SHARED")
        ids.append(p.project_id)

    for pid in ids[:MAX_PROJECTS]:
        _assign(deps, ME, r.artifact_id, pid)

    with pytest.raises(ManageError) as x:
        _assign(deps, ME, r.artifact_id, ids[-1])

    assert x.value.code == "TOO_MANY_PROJECTS"
    assert len(meta_of(deps, r.artifact_id)["projects"]) == MAX_PROJECTS
