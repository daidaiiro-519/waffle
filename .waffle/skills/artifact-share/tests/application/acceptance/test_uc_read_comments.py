"""寄せられたコメントを読む操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-read-comments
"""
import json

import pytest

from manage_setup import HTML, ME, SOMEONE_ELSE, setup
from application.usecases.read_comments import ReadComments
from application.usecases.replace_artifact_content import ReplaceArtifactContent
from application.usecases.suspend_artifact import SuspendArtifact
from shared.errors import ManageError
from usecase_builder import build


def _post(deps, artifact_id, at, author, body, decision="comment", parent=None):
    """閲覧者が書き込んだ1件。閲覧画面が書くのと同じ形。"""
    deps.store.put(
        f"comments/{artifact_id}/{at}-abcd1234.json",
        json.dumps({"kind": "comment", "author": author, "decision": decision,
                    "body": body, "parentId": parent,
                    "postedAt": f"2026-07-{at % 28 + 1:02d}T10:00:00Z"},
                   ensure_ascii=False),
        "application/json")


def _read(deps, caller, artifact_id):
    return build(deps, ReadComments).run(caller, artifact_id).comments


def test_寄せられた順に読める():
    """
    Scenario: 寄せられた順に読める
    Given Aに3件のコメントが順に寄せられている
    When Xが読み出しを求める
    Then 3件が古いものから順に返る
    And それぞれに、誰が・いつ・何を言い・どういう判定だったかが含まれている
    """
    deps, r = setup()
    _post(deps, r.artifact_id, 1_700_000_010, "田中", "これで良いと思います", "approve")
    _post(deps, r.artifact_id, 1_700_000_020, "佐藤", "ここが気になります")
    _post(deps, r.artifact_id, 1_700_000_030, "山田", "直してほしい", "request")

    got = _read(deps, ME, r.artifact_id)

    assert [c.author for c in got] == ["田中", "佐藤", "山田"]
    assert got[0].verdict == "approve"
    assert got[0].body == "これで良いと思います"
    assert got[0].posted_at


def test_返信がどれへの返信か分かる():
    """
    Scenario: 返信がどれへの返信か分かる
    Given あるコメントへの返信が寄せられている
    When Xが読み出しを求める
    Then その返信が、どのコメントへの返信かが分かる形で返る
    """
    deps, r = setup()
    _post(deps, r.artifact_id, 1_700_000_010, "田中", "ここが気になります")
    _post(deps, r.artifact_id, 1_700_000_020, "投稿者", "直しました",
          parent="1700000010-abcd1234")

    got = _read(deps, ME, r.artifact_id)

    assert got[1].parent_id == "1700000010-abcd1234"


def test_差し替えの区切りが並びに現れる():
    """
    Scenario: 差し替えの区切りが並びに現れる
    Given Aが一度差し替えられており、その前後にコメントがある
    When Xが読み出しを求める
    Then 差し替えの区切りが、その時点の位置に現れる
    """
    deps, r = setup()
    _post(deps, r.artifact_id, 1_700_000_010, "田中", "差し替え前の指摘")
    build(deps, ReplaceArtifactContent).run(
        ME, r.artifact_id, HTML.replace("本文", "直した"))
    _post(deps, r.artifact_id, 1_700_000_200, "佐藤", "差し替え後の指摘")

    kinds = [c.kind for c in _read(deps, ME, r.artifact_id)]

    assert kinds == ["comment", "divider", "comment"]


def test_他人のものは読めない():
    """
    Scenario: 他人のものは読めない
    Given Aの投稿者はXである
    When 管理者でない投稿者YがAのコメントを読もうとする
    Then ARTIFACT_NOT_FOUND として拒まれる
    """
    deps, r = setup()
    _post(deps, r.artifact_id, 1_700_000_010, "田中", "意見")

    with pytest.raises(ManageError) as x:
        build(deps, ReadComments).run(SOMEONE_ELSE, r.artifact_id)

    assert x.value.code == "ARTIFACT_NOT_FOUND"


def test_公開が止まっていても読める():
    """
    Scenario: 公開が止まっていても読める
    Given Aが公開停止されている
    When Xが読み出しを求める
    Then それまでに寄せられたコメントが返る

    止めるかどうかを決めた後も、何を言われたかは読めている必要がある。
    """
    deps, r = setup()
    _post(deps, r.artifact_id, 1_700_000_010, "田中", "意見")
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    got = _read(deps, ME, r.artifact_id)

    assert [c.author for c in got] == ["田中"]


def test_読んでも何も変わらない():
    """
    Scenario: 読んでも何も変わらない
    Given Aに3件のコメントがある
    When 続けて2回読み出しを求める
    Then 2回とも同じ3件が返る
    And コメントは何も変わっていない
    """
    deps, r = setup()
    for at, author in ((1_700_000_010, "田中"), (1_700_000_020, "佐藤"),
                       (1_700_000_030, "山田")):
        _post(deps, r.artifact_id, at, author, "意見")
    objects_before = json.dumps(deps.store.objects, ensure_ascii=False, sort_keys=True)

    first = _read(deps, ME, r.artifact_id)
    second = _read(deps, ME, r.artifact_id)

    assert len(first) == 3
    assert second == first
    assert json.dumps(deps.store.objects, ensure_ascii=False,
                      sort_keys=True) == objects_before
