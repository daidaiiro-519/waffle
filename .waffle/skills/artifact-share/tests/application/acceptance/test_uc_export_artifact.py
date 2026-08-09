"""中身とコメントを手元へ取り出す操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-export-artifact
"""
import json
from dataclasses import asdict

import pytest

from manage_setup import HTML, ME, SOMEONE_ELSE, meta_of, setup
from application.usecases.export_artifact import ExportArtifact
from application.usecases.replace_artifact_content import ReplaceArtifactContent
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


def _three_comments(deps, artifact_id):
    for at, author in ((1_700_000_010, "田中"), (1_700_000_020, "佐藤"),
                       (1_700_000_030, "山田")):
        _comment(deps, artifact_id, at, author, f"{author}の意見")


def test_中身とコメントがまとめて手元に来る():
    """
    Scenario: 中身とコメントがまとめて手元に来る
    Given Aにコメントが3件寄せられている
    When Xが取り出しを求める
    Then 公開した中身がそのまま返る
    And コメント3件が、誰がいつ何を言ったかが分かる形で添えられている
    """
    deps, r = setup()
    _three_comments(deps, r.artifact_id)

    got = build(deps, ExportArtifact).run(ME, r.artifact_id)

    assert got.content == HTML
    assert got.name == "検索基盤の選定"
    assert len(got.comments) == 3
    for comment in got.comments:
        assert comment.author
        assert comment.body
        assert comment.posted_at


def test_差し替えの区切りも一緒に来る():
    """
    Scenario: 差し替えの区切りも一緒に来る
    Given Aが一度差し替えられており、その前後にコメントがある
    When Xが取り出しを求める
    Then 差し替えの区切りがコメントと同じ並びに現れる
    """
    deps, r = setup()
    _comment(deps, r.artifact_id, 1_700_000_010, "田中", "差し替え前の指摘")
    build(deps, ReplaceArtifactContent).run(
        ME, r.artifact_id, HTML.replace("本文", "直した"))
    _comment(deps, r.artifact_id, 1_700_000_200, "佐藤", "差し替え後の指摘")

    got = build(deps, ExportArtifact).run(ME, r.artifact_id)

    kinds = [c.kind for c in got.comments]
    assert kinds == ["comment", "divider", "comment"]


def test_取り出しても何も変わらない():
    """
    Scenario: 取り出しても何も変わらない
    Given 閲覧者がAの閲覧トークンを持っている
    When Xが取り出しを求める
    Then Aは公開されたままである
    And 閲覧者はそれまでの閲覧トークンでAを開ける
    And Aのコメントは3件のまま残っている
    """
    deps, r = setup()
    _three_comments(deps, r.artifact_id)
    token_before = deps.keys.written[f"token:{r.artifact_id}"]

    build(deps, ExportArtifact).run(ME, r.artifact_id)

    assert meta_of(deps, r.artifact_id)["status"] == "active"
    assert deps.keys.written[f"token:{r.artifact_id}"] == token_before
    assert len(deps.store.list(f"comments/{r.artifact_id}/")) == 3


def test_公開が止まっていても取り出せる():
    """
    Scenario: 公開が止まっていても取り出せる
    Given Aが公開停止されている
    When Xが取り出しを求める
    Then 中身とコメントが返る
    """
    deps, r = setup()
    _three_comments(deps, r.artifact_id)
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    got = build(deps, ExportArtifact).run(ME, r.artifact_id)

    assert got.content == HTML
    assert len(got.comments) == 3


def test_他人のものは取り出せない():
    """
    Scenario: 他人のものは取り出せない
    Given Aの投稿者はXである
    When 管理者でない投稿者YがAの取り出しを求める
    Then ARTIFACT_NOT_FOUND として拒まれる
    """
    deps, r = setup()

    with pytest.raises(ManageError) as x:
        build(deps, ExportArtifact).run(SOMEONE_ELSE, r.artifact_id)

    assert x.value.code == "ARTIFACT_NOT_FOUND"


def test_閲覧トークンは含まれない():
    """
    Scenario: 閲覧トークンは含まれない
    Given Aの閲覧トークンが発行されている
    When Xが取り出しを求める
    Then 返ったものに閲覧トークンは含まれない

    取り出したものが渡り歩いても、それだけで開ける状態にならないようにする。
    """
    deps, r = setup()

    got = build(deps, ExportArtifact).run(ME, r.artifact_id)

    got = json.dumps(asdict(got), ensure_ascii=False)
    assert r.token not in got
    assert "token" not in got      # 値だけでなく欄の名前も見る
    assert not hasattr(got, "view_tokens")
