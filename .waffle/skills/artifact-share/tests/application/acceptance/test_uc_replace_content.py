"""中身を丸ごと入れ替える操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-replace-content
"""
import json

import pytest

from manage_setup import ADMIN, HTML, ME, setup
from application.usecases.replace_artifact_content import ReplaceArtifactContent
from application.usecases.suspend_artifact import SuspendArtifact
from shared.errors import ManageError
from usecase_builder import build

# 入れ替え前の断片が残らないことを見るため、共通の語を持たない中身にする
REVISED = HTML.replace("本文", "すっかり別の記述")


def _comment(deps, artifact_id, at, author, body):
    deps.store.put(
        f"comments/{artifact_id}/{at}-abcd1234.json",
        json.dumps({"kind": "comment", "author": author, "decision": "comment",
                    "body": body, "parentId": None,
                    "postedAt": "2026-07-01T10:00:00Z"}, ensure_ascii=False),
        "application/json")


def _entries(deps, artifact_id):
    return [json.loads(deps.store.get(k))
            for k in deps.store.list(f"comments/{artifact_id}/")]


def test_共有URLと閲覧トークンを保ったまま入れ替わる():
    """
    Scenario: 共有URLと閲覧トークンを保ったまま入れ替わる
    When 新しい文書で中身を入れ替える
    Then 中身は新しいものと一致する
    And 共有URLは変わらない
    And 閲覧トークンも変わらない
    """
    deps, r = setup()
    token_before = deps.keys.get(f"token:{r.artifact_id}")

    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, REVISED)

    assert deps.store.get(f"p/{r.artifact_id}/content.html") == REVISED
    assert deps.store.get(f"p/{r.artifact_id}/index.html")  # 同じ居場所に在り続ける
    assert deps.keys.get(f"token:{r.artifact_id}") == token_before


def test_コメントが残り区切りが現れる():
    """
    Scenario: コメントが残り、区切りが現れる
    When 新しい文書で中身を入れ替える
    Then 3件のコメントはいずれも残っている
    And 入れ替えの時点が区切りとしてコメントの並びに現れる
    And 区切りより前の3件は入れ替え前への指摘だと読み取れる
    """
    deps, r = setup()
    for at, author in ((1_700_000_010, "田中"), (1_700_000_020, "佐藤"),
                       (1_700_000_030, "山田")):
        _comment(deps, r.artifact_id, at, author, "意見")

    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, REVISED)

    kinds = [e["kind"] for e in _entries(deps, r.artifact_id)]
    assert kinds.count("comment") == 3
    assert kinds.count("divider") == 1
    assert kinds.index("divider") == 3   # 区切りは3件のあとに来る


def test_止まっているものは入れ替えられない():
    """
    Scenario: 止まっているものは入れ替えられない
    Given 共有アーティファクトAの公開が止まっている
    When 中身を入れ替えようとする
    Then NOT_PUBLISHED として拒まれる
    And 中身は変わらない
    """
    deps, r = setup()
    before = deps.store.get(f"p/{r.artifact_id}/content.html")
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    with pytest.raises(ManageError) as x:
        build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, REVISED)

    assert x.value.code == "NOT_PUBLISHED"
    assert deps.store.get(f"p/{r.artifact_id}/content.html") == before


def test_部分的な書き換えは起きない():
    """
    Scenario: 部分的な書き換えは起きない
    When 新しい文書で中身を入れ替える
    Then 入れ替え前の中身の一部が残ることはない
    """
    deps, r = setup()

    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, REVISED)

    after = deps.store.get(f"p/{r.artifact_id}/content.html")
    assert after == REVISED
    assert "本文" not in after   # 入れ替え前の断片が混じらない


def test_管理者でも他人の中身は差し替えられない():
    """
    Scenario: 管理者でも他人の中身は差し替えられない
    Given 共有アーティファクトAの投稿者がXである
    When 管理者がAの中身を差し替えようとする
    Then NOT_THE_PUBLISHER として拒まれる
    And Aの中身とコメントは変わっていない

    集まったコメントが何に対するものかを、投稿者の知らないうちに変えないため。
    """
    deps, r = setup()
    _comment(deps, r.artifact_id, 1_700_000_010, "田中", "意見")
    before = deps.store.get(f"p/{r.artifact_id}/content.html")

    with pytest.raises(ManageError) as x:
        build(deps, ReplaceArtifactContent).run(ADMIN, r.artifact_id, REVISED)

    assert x.value.code == "NOT_THE_PUBLISHER"
    assert deps.store.get(f"p/{r.artifact_id}/content.html") == before
    assert len(_entries(deps, r.artifact_id)) == 1


def test_空の中身には差し替えられない():
    """
    Scenario: 空の中身には差し替えられない
      Given 共有アーティファクトAが公開されている
      When 空の中身で差し替えようとする
      Then EMPTY_CONTENT として拒まれる
      And それまでの中身は変わらない
    """
    deps, r = setup()

    with pytest.raises(ManageError) as x:
        build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, "   ")

    assert x.value.code == "EMPTY_CONTENT"
    assert deps.store.get(f"p/{r.artifact_id}/content.html") == HTML
