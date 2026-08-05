"""再び見せられるようにする操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-resume-artifact
"""
import json

import pytest

from manage_setup import ADMIN, ME, SOMEONE_ELSE, meta_of, setup
from application.usecases.issue_view_token import IssueViewToken
from application.usecases.resume_artifact import ResumeArtifact
from application.usecases.revoke_view_token import RevokeViewToken
from application.usecases.suspend_artifact import SuspendArtifact
from domain import view_token
from domain.view_subject import ViewSubject
from shared.errors import ManageError
from usecase_builder import build


def _comment(deps, artifact_id, at, author, body):
    deps.store.put(
        f"comments/{artifact_id}/{at}-abcd1234.json",
        json.dumps({"kind": "comment", "author": author, "decision": "comment",
                    "body": body, "parentId": None,
                    "postedAt": "2026-07-01T10:00:00Z"}, ensure_ascii=False),
        "application/json")


def test_再開しても止める前の閲覧トークンで開ける():
    """
    Scenario: 再開しても止める前の閲覧トークンで開ける
    Given 公開を止めた共有アーティファクトと、期限内で無効にされていない閲覧トークン
    When 公開を再開する
    Then その閲覧トークンで開ける
    """
    deps, r = setup()
    before = deps.keys.get(f"token:{r.artifact_id}")
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    build(deps, ResumeArtifact).run(ME, r.artifact_id)

    assert deps.keys.get(f"token:{r.artifact_id}") == before
    assert meta_of(deps, r.artifact_id)["status"] == "active"


def test_止める前に無効にした閲覧トークンは再開しても戻らない():
    """
    Scenario: 止める前に無効にした閲覧トークンは再開しても戻らない
    Given 公開を止める前に無効にした閲覧トークン
    When 公開を再開する
    Then その閲覧トークンでは開けない
    """
    deps, r = setup()
    subject = ViewSubject.artifact(r.artifact_id)
    extra = build(deps, IssueViewToken).run(ME, subject, "レビュー班", None)
    build(deps, RevokeViewToken).run(ME, subject, extra.token_id)
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    build(deps, ResumeArtifact).run(ME, r.artifact_id)

    # 記録には残るが、開ける対象からは外れる（閲覧の面へ渡るのは1本だけ）
    grants = deps.keys.get(f"token:{r.artifact_id}")
    assert grants.count(";") == 0
    assert extra.token not in grants


def test_止めている間に期限が切れた閲覧トークンは再開しても使えない():
    """
    Scenario: 止めている間に期限が切れた閲覧トークンは再開しても使えない
    Given 公開を止めている間に期限が切れた閲覧トークン
    When 公開を再開する
    Then その閲覧トークンでは開けない
    """
    deps, r = setup()
    subject = ViewSubject.artifact(r.artifact_id)
    build(deps, IssueViewToken).run(ME, subject, "短い相手", view_token.WEEK)
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    later = deps.now() + view_token.WEEK + 1
    deps.now = lambda: later
    build(deps, ResumeArtifact).run(ME, r.artifact_id)

    # 期限を過ぎたものは、記録に残っていても開ける対象にならない
    grants = deps.keys.get(f"token:{r.artifact_id}")
    assert grants != "DISABLED"
    assert grants.count(";") == 0


def test_共有URLと中身とコメントは戻る():
    """
    Scenario: 共有URLと中身とコメントは戻る
    When 共有アーティファクトAの公開を再開する
    Then 共有URLは停止前と同じである
    And 中身も停止前と同じである
    And コメントもすべて残っている
    """
    deps, r = setup()
    _comment(deps, r.artifact_id, 1, "田中", "意見")
    content_before = deps.store.get(f"p/{r.artifact_id}/content.html")
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    resumed = build(deps, ResumeArtifact).run(ME, r.artifact_id)

    assert resumed.url == r.url
    assert deps.store.get(f"p/{r.artifact_id}/content.html") == content_before
    assert len(deps.store.list(f"comments/{r.artifact_id}/")) == 1


def test_止まっていないものは再開できない():
    """
    Scenario: 止まっていないものは再開できない
    Given 共有アーティファクトBが公開されている
    When 共有アーティファクトBを再開しようとする
    Then NOT_SUSPENDED として拒まれる
    And 閲覧トークンは変わらない
    """
    deps, r = setup()
    before = deps.keys.get(f"token:{r.artifact_id}")

    with pytest.raises(ManageError) as x:
        build(deps, ResumeArtifact).run(ME, r.artifact_id)

    assert x.value.code == "NOT_SUSPENDED"
    assert deps.keys.get(f"token:{r.artifact_id}") == before


def test_他人のものは見つからないものとして拒む():
    """
    Scenario: 他人のものは見つからないものとして拒む
    Given 共有アーティファクトAの投稿者がXである
    When 管理者でない投稿者YがAの再公開を求める
    Then ARTIFACT_NOT_FOUND として拒まれる
    And Aの状態は変わっていない
    """
    deps, r = setup()
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    with pytest.raises(ManageError) as x:
        build(deps, ResumeArtifact).run(SOMEONE_ELSE, r.artifact_id)

    assert x.value.code == "ARTIFACT_NOT_FOUND"
    assert meta_of(deps, r.artifact_id)["status"] == "disabled"


def test_管理者は自分のものでなくても扱える():
    """
    Scenario: 管理者は自分のものでなくても扱える
    Given 共有アーティファクトAの投稿者がXである
    When 管理者がAの再公開を求める
    Then Aは開ける状態に戻る
    And 止める前の閲覧トークンのうち、期限内で無効にされていないものはそのまま使える
    """
    deps, r = setup()
    before = deps.keys.get(f"token:{r.artifact_id}")
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    build(deps, ResumeArtifact).run(ADMIN, r.artifact_id)

    assert meta_of(deps, r.artifact_id)["status"] == "active"
    assert deps.keys.get(f"token:{r.artifact_id}") == before
