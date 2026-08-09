"""反応の並びの欄が、4つの実行環境で同じ綴りであることを確かめる。

実行:  python3 -m pytest tests/ -v

この並びは閲覧画面が書き、業務のLambdaが区切りを書き、閲覧ゲートが検査し、
閲覧画面と管理画面が読む。綴りの取り決めは infra/contract/comment-entries.json
が正で、ここで規則を書き直さない——書き直すと同じ規則の写しが増えるだけで、
突き合わせにならない。

業務の語彙と保管の綴りが食い違う欄が1つある（判定＝decision）。その対応が
確かめられる形で存在することが、同義語の乱立を防ぐ唯一の手立てなので、
対応そのものをここで確かめる。

対象の仕様: agg-comment / uc-read-comments（欄の綴りの取り決め）
"""
import json
from pathlib import Path

from conftest import SKILL

from adapters.inbound.admin_api import _outward
from adapters.outbound.stored_comment_repository import (
    DIVIDER_SUFFIX, StoredCommentRepository,
)
from application.usecases.read_comments import CommentEntry, Comments
from fakes import FakeStore

CONTRACT = json.loads(
    (SKILL / "infra" / "contract" / "comment-entries.json").read_text(encoding="utf-8"))
VIEWER = (SKILL / "references" / "templates" / "share-wrapper.html").read_text(
    encoding="utf-8")

A = "aaaaaaaa"


def _spellings() -> set[str]:
    return {f["綴り"] for f in CONTRACT["欄"]}


def test_契約が挙げる欄を閲覧画面が組み立てている():
    """書く側。ここが欠けると、読む側が揃っていても値が入らない。"""
    post = VIEWER[VIEWER.index("function post(event)"):]
    payload = post[post.index("JSON.stringify({"):]

    for spelling in _spellings():
        assert f"{spelling}:" in payload, spelling


def test_契約が挙げる欄を応答が同じ綴りで返す():
    """読む側。管理画面はこの綴りで読むので、受け口が戻す形が正でなければならない。"""
    got = _outward(Comments(artifact_id=A, unreadable=0, comments=(
        CommentEntry(id="1700000010-abcd1234", kind="comment", author="田中",
                     body="本文", posted_at="2026-08-09", verdict="approve"),)))

    assert _spellings() <= set(got["comments"][0])


def test_判定は保管の綴りで出入りし業務の語彙は内側だけにある():
    """唯一、綴りが食い違う欄。対応が保たれていることを両方向で確かめる。

    保管の綴りを変えられないのは、コメントが追記しかされず書き直す経路を
    持たないため。だから対応が壊れていないことを、ここで押さえる。
    """
    stored = next(f for f in CONTRACT["欄"] if "判定" in f["業務の語彙"])
    assert stored["綴り"] == "decision"

    store = FakeStore()
    store.put(f"comments/{A}/1700000010-abcd1234.json",
              json.dumps({"kind": "comment", "author": "田中", "body": "意見",
                          stored["綴り"]: "approve"}, ensure_ascii=False),
              "application/json")

    # 入り: 保管の綴り → 業務の語彙
    comment = StoredCommentRepository(store).list_of(A)[0][0]
    assert comment.verdict.value == "approve"
    assert comment.verdict.is_approval()

    # 出: 業務の語彙 → 外の綴り。同じ値が同じ意味で戻る
    entry = _outward(CommentEntry(id="x", kind="comment", author="田中",
                                  body="意見", posted_at="", verdict="approve"))
    assert entry[stored["綴り"]] == "approve"


def test_契約が挙げる判定の値を画面と業務が同じだけ持つ():
    """値が増えたのに片方だけが知っている、を防ぐ。"""
    from domain.value_objects.comment import APPROVED, JUST_AN_OPINION, NEEDS_REVISION

    declared = {v["綴り"] for v in CONTRACT["判定の値"]}

    assert declared == {JUST_AN_OPINION, APPROVED, NEEDS_REVISION}
    for value in declared:
        assert f"'{value}'" in VIEWER or f'"{value}"' in VIEWER, value


def test_区切りの目印は契約が定めたもの():
    """鍵の末尾で種別を決める。本文の中の値では決めない。"""
    assert DIVIDER_SUFFIX == CONTRACT["形式"]["区切りの目印"]

    store = FakeStore()
    StoredCommentRepository(store).add_replacement_divider(A, 1_700_000_100)

    divider = StoredCommentRepository(store).list_of(A)[0][0]
    assert divider.is_divider()
    assert divider.author.value == ""      # 区切りには名乗りが無い
    assert divider.verdict.value == "comment"
