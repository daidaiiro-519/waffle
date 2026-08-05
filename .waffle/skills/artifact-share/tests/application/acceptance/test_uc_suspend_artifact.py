"""見せるのを止める操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-suspend-artifact
"""
import json

import pytest

from manage_setup import ADMIN, ME, SOMEONE_ELSE, meta_of, setup, with_project
from application.usecases.assign_artifact_to_project import AssignArtifactToProject
from application.usecases.export_artifact import ExportArtifact
from application.usecases.suspend_artifact import SuspendArtifact
from shared.errors import ManageError
from usecase_builder import build


def _comment(deps, artifact_id, at, author, body):
    deps.store.put(
        f"comments/{artifact_id}/{at}-abcd1234.json",
        json.dumps({"kind": "comment", "author": author, "decision": "comment",
                    "body": body, "parentId": None,
                    "postedAt": "2026-07-01T10:00:00Z"}, ensure_ascii=False),
        "application/json")


def test_止めると開けなくなる():
    """
    Scenario: 止めると開けなくなる
    When 共有アーティファクトAの公開を止める
    Then 共有アーティファクトAの閲覧トークンで開けない
    """
    deps, r = setup()

    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    assert deps.keys.get(f"token:{r.artifact_id}") == "DISABLED"
    assert meta_of(deps, r.artifact_id)["status"] == "disabled"


def test_プロジェクト閲覧トークンでも開けない():
    """
    Scenario: プロジェクト閲覧トークンでも開けない
    Given 共有アーティファクトAがプロジェクトPに入っている
    When 共有アーティファクトAの公開を止める
    Then Pの閲覧トークンでも共有アーティファクトAを開けない

    止めるのは配布先を選ばず全ての経路を閉じたいときの手立てなので、
    まとめ経由の経路も残さない。
    """
    deps, r, pid = with_project("PERSONAL")
    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    assert deps.keys.get(f"token:{r.artifact_id}") == "DISABLED"


def test_中身もコメントも残る():
    """
    Scenario: 中身もコメントも残る
    When 共有アーティファクトAの公開を止める
    Then 中身は残っている
    And コメントもすべて残っている
    And 手元へ取り出せる
    """
    deps, r = setup()
    for at, author in ((1, "田中"), (2, "佐藤")):
        _comment(deps, r.artifact_id, at, author, "意見")

    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    assert deps.store.get(f"p/{r.artifact_id}/content.html")
    assert len(deps.store.list(f"comments/{r.artifact_id}/")) == 2
    exported = build(deps, ExportArtifact).run(ME, r.artifact_id)
    assert exported.artifact_id == r.artifact_id


def test_既に止まっているものは止められない():
    """
    Scenario: 既に止まっているものは止められない
    Given 共有アーティファクトAが既に停止している
    When もう一度停止しようとする
    Then NOT_PUBLISHED として拒まれる
    """
    deps, r = setup()
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    with pytest.raises(ManageError) as x:
        build(deps, SuspendArtifact).run(ME, r.artifact_id)

    assert x.value.code == "NOT_PUBLISHED"


def test_他人のものは見つからないものとして拒む():
    """
    Scenario: 他人のものは見つからないものとして拒む
    Given 共有アーティファクトAの投稿者がXである
    When 管理者でない投稿者YがAの公開停止を求める
    Then ARTIFACT_NOT_FOUND として拒まれる
    And Aの状態は変わっていない
    """
    deps, r = setup()

    with pytest.raises(ManageError) as x:
        build(deps, SuspendArtifact).run(SOMEONE_ELSE, r.artifact_id)

    assert x.value.code == "ARTIFACT_NOT_FOUND"
    assert meta_of(deps, r.artifact_id)["status"] == "active"


def test_管理者は自分のものでなくても扱える():
    """
    Scenario: 管理者は自分のものでなくても扱える
    Given 共有アーティファクトAの投稿者がXである
    When 管理者がAの公開停止を求める
    Then Aは開けない状態になる
    """
    deps, r = setup()

    build(deps, SuspendArtifact).run(ADMIN, r.artifact_id)

    assert meta_of(deps, r.artifact_id)["status"] == "disabled"
    assert deps.keys.get(f"token:{r.artifact_id}") == "DISABLED"
