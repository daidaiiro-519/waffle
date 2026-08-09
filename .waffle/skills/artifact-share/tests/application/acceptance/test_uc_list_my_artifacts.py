"""自分が公開したものを見渡す操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-list-my-artifacts
"""
import json

from manage_setup import (
    ADMIN, HTML, ME, NOW, SOMEONE_ELSE, meta_of, publish_other, setup,
)
from application.usecases.issue_view_token import IssueViewToken
from application.usecases.list_my_artifacts import ListMyArtifacts
from application.usecases.replace_artifact_content import ReplaceArtifactContent
from application.usecases.suspend_artifact import SuspendArtifact
from domain.value_objects.view_subject import ViewSubject
from usecase_builder import build


def _rows(deps, caller=ME):
    return build(deps, ListMyArtifacts).run(caller).artifacts


def _comment(deps, artifact_id, at, author):
    deps.store.put(
        f"comments/{artifact_id}/{at}-abcd1234.json",
        json.dumps({"kind": "comment", "author": author, "decision": "comment",
                    "body": "意見", "parentId": None,
                    "postedAt": "2026-07-01T10:00:00Z"}, ensure_ascii=False),
        "application/json")


def test_自分が公開したものだけが並ぶ():
    """
    Scenario: 自分が公開したものだけが並ぶ
    Given 投稿者XがAを公開している
    And 投稿者YがBを公開している
    When 投稿者Xが見渡しを求める
    Then A だけが返る
    And B は含まれない
    """
    deps, mine = setup()
    other = publish_other(deps, SOMEONE_ELSE)

    ids = [row.artifact_id for row in _rows(deps)]

    assert ids == [mine.artifact_id]
    assert other.artifact_id not in ids


def test_管理者には全員のものが並ぶ():
    """
    Scenario: 管理者には全員のものが並ぶ
    Given 投稿者XがAを公開している
    And 投稿者YがBを公開している
    When 管理者が見渡しを求める
    Then A と B の両方が返る
    And それぞれを公開した人が分かる
    """
    deps, mine = setup()
    other = publish_other(deps, SOMEONE_ELSE)

    rows = _rows(deps, ADMIN)

    by_id = {row.artifact_id: row for row in rows}
    assert {mine.artifact_id, other.artifact_id} <= set(by_id)
    assert by_id[mine.artifact_id].uploaded_by == ME.id
    assert by_id[other.artifact_id].uploaded_by == SOMEONE_ELSE.id


def test_新しく直したものが先頭に来る():
    """
    Scenario: 新しく直したものが先頭に来る
    Given 投稿者XがAを公開し、その後 B を公開している
    And その後 A の中身を差し替えている
    When 投稿者Xが見渡しを求める
    Then A が B より先に並ぶ
    """
    deps, a = setup()
    b = publish_other(deps, ME)
    deps.now = lambda: NOW + 1_000
    build(deps, ReplaceArtifactContent).run(ME, a.artifact_id, HTML.replace("本文", "直した"))

    ids = [row.artifact_id for row in _rows(deps)]

    assert ids.index(a.artifact_id) < ids.index(b.artifact_id)


def test_閲覧トークンは一覧に現れない():
    """
    Scenario: 閲覧トークンは一覧に現れない
    Given 投稿者XがAを公開し、閲覧トークンを受け取っている
    When 投稿者Xが見渡しを求める
    Then 返った一覧のどこにも、その閲覧トークンの値は現れない
    """
    deps, r = setup()

    rows = _rows(deps)

    assert r.token not in repr(rows)
    for row in rows:
        assert not hasattr(row, "token")


def test_寄せられた反応の件数が添う():
    """
    Scenario: 寄せられた反応の件数が添う
    Given 投稿者XがAを公開している
    And A に反応が2件寄せられている
    When 投稿者Xが見渡しを求める
    Then A の行に反応が2件と添う
    """
    deps, r = setup()
    _comment(deps, r.artifact_id, 1_700_000_010, "田中")
    _comment(deps, r.artifact_id, 1_700_000_020, "佐藤")

    assert _rows(deps)[0].comments == 2


def test_いま見せている配布先の数が添う():
    """
    Scenario: いま見せている配布先の数が添う
    Given 投稿者XがAを公開している
    And A に有効な閲覧トークンが2本あり、そのほかに期限を過ぎたものが1本ある
    When 投稿者Xが見渡しを求める
    Then A の行に配布先が2件と添う
    """
    deps, r = setup()
    subject = ViewSubject.artifact(r.artifact_id)
    build(deps, IssueViewToken).run(ME, subject, "経理チーム", None)   # 有効な2本目
    build(deps, IssueViewToken).run(ME, subject, "短い期限", 1)        # すぐ切れる

    deps.now = lambda: NOW + 2 * 24 * 60 * 60

    assert _rows(deps)[0].distributions == 2


def test_読めない記録があっても残りは返る():
    """
    Scenario: 読めない記録があっても残りは返る
    Given 投稿者XがAとBを公開している
    And A の記録が読めない状態になっている
    When 投稿者Xが見渡しを求める
    Then B が返る
    And 読めなかった件数が1と伝わる

    1件の不具合で一覧が空になるのを避ける。ただし黙っては落とさない——落とすと、
    投稿者が「公開したはずのものが消えた」と気づけない。
    """
    deps, a = setup()
    b = publish_other(deps, ME)
    deps.store.put(f"meta/{a.artifact_id}.json", "{壊れている", "application/json")

    got = build(deps, ListMyArtifacts).run(ME)

    assert [row.artifact_id for row in got.artifacts] == [b.artifact_id]
    assert got.unreadable == 1


def test_公開を止めているものも並ぶ():
    """
    Scenario: 公開を止めているものも並ぶ
    Given 投稿者XがAを公開し、その後公開を止めている
    When 投稿者Xが見渡しを求める
    Then A が並び、止まっていることが分かる
    """
    deps, r = setup()
    assert _rows(deps)[0].status == "PUBLISHED"

    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    rows = _rows(deps)
    assert [row.artifact_id for row in rows] == [r.artifact_id]
    assert rows[0].status == "SUSPENDED"


def test_差し替えの区切りはコメントの件数に数えない():
    """
    Scenario: 差し替えの区切りはコメントの件数に数えない
      Given 共有アーティファクトAに2件のコメントがあり、一度差し替えられている
      When 投稿者Xが見渡しを求める
      Then 添えられる反応の件数は2である

    区切りは印であって、誰かの反応ではない。
    """
    deps, r = setup()
    _comment(deps, r.artifact_id, 1_700_000_010, "田中")
    _comment(deps, r.artifact_id, 1_700_000_020, "佐藤")

    build(deps, ReplaceArtifactContent).run(
        ME, r.artifact_id, HTML.replace("本文", "直した"))

    assert _rows(deps)[0].comments == 2
