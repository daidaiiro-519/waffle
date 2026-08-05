"""投稿者がコメントを読み、中身とコメントを取り出す操作を確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-read-comments / uc-export-artifact
引き継ぎ: handoff-read-export

閲覧者は閲覧トークンで開いた画面から読み書きし、投稿者は本人確認を通った
画面から読む。指しているものは同じコメントだが、通ってよい条件が違う。
"""

import main
import json
from dataclasses import asdict
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from usecase_builder import build  # noqa: E402
from application.usecases.export_artifact import ExportArtifact  # noqa: E402
from application.usecases.publish_artifact import PublishArtifact  # noqa: E402
from application.usecases.read_comments import ReadComments  # noqa: E402
from application.usecases.replace_artifact_content import ReplaceArtifactContent  # noqa: E402
from application.usecases.suspend_artifact import SuspendArtifact  # noqa: E402

from application.ports import Caller  # noqa: E402
from shared.errors import ManageError  # noqa: E402


from test_manage import HTML, FakeKeyStore, FakeStore  # noqa: E402

ME = Caller("publisher-1")
SOMEONE_ELSE = Caller("publisher-2")
ADMIN = Caller("admin-1", is_admin=True)


def setup():
    """公開済みのものが1件ある状態を作る。"""
    store, keys = FakeStore(), FakeKeyStore()
    c = main.Connections(
        store=store, keys=keys, identify=lambda _t: ME.id,
        wrapper_template="<html>{{アーティファクトID}}</html>",
        now=lambda: 1_700_000_000, viewer_domain="viewer.example.net")
    r = build(c, PublishArtifact).run({"html": HTML, "authorization": "Bearer x"})
    deps = main.Connections(store=store, keys=keys, now=lambda: 1_700_000_100,
                       viewer_domain="viewer.example.net")
    return deps, r.artifact_id


def post(deps, artifact_id, at, author, body, decision="comment", parent=None):
    """閲覧者が書き込んだ1件。閲覧画面が書くのと同じ形。"""
    deps.store.put(
        f"comments/{artifact_id}/{at}-abcd1234.json",
        json.dumps({"kind": "comment", "author": author, "decision": decision,
                    "body": body, "parentId": parent,
                    "postedAt": f"2026-07-{at % 30 + 1:02d}T10:00:00Z"}, ensure_ascii=False),
        "application/json")


# ── 読む ────────────────────────────────────────────────

def test_寄せられた順に読める():
    deps, aid = setup()
    post(deps, aid, 1700000001, "田中", "これで良いと思います", "approve")
    post(deps, aid, 1700000003, "山田", "ここが分かりません")
    post(deps, aid, 1700000002, "佐藤", "1点直してほしい", "revise")

    got = build(deps, ReadComments).run(ME, aid)

    assert [c["author"] for c in got.comments] == ["田中", "佐藤", "山田"]
    assert got.comments[0]["decision"] == "approve"
    assert got.comments[0]["body"] == "これで良いと思います"


def test_保存されている形のまま返る():
    """表示用に整えるのは画面側。ここで別の呼び名へ置き換えない"""
    deps, aid = setup()
    post(deps, aid, 1700000001, "田中", "本文")

    c = build(deps, ReadComments).run(ME, aid).comments[0]
    assert set(c) >= {"kind", "author", "decision", "body", "parentId", "postedAt"}


def test_返信がどれへの返信かが分かる():
    deps, aid = setup()
    post(deps, aid, 1700000001, "山田", "質問です")
    post(deps, aid, 1700000002, "投稿者", "回答です", parent="1700000001-abcd1234")

    got = build(deps, ReadComments).run(ME, aid)
    assert got.comments[1]["parentId"] == "1700000001-abcd1234"


def test_差し替えの区切りが並びに現れる():
    """差し替えの区切りも、反応と同じ並びに1件として載る"""
    deps, aid = setup()
    post(deps, aid, 1700000001, "佐藤", "直してほしい", "revise")
    build(deps, ReplaceArtifactContent).run(ME, aid, HTML.replace("本文", "直した"))
    post(deps, aid, 1700000200, "佐藤", "直りました", "approve")

    kinds = [c["kind"] for c in build(deps, ReadComments).run(ME, aid).comments]
    assert kinds == ["comment", "divider", "comment"]


def test_他人のものは読めない():
    """寄せられた指摘には、渡した相手しか知らない内容が含まれうる"""
    deps, aid = setup()
    with pytest.raises(ManageError) as x:
        build(deps, ReadComments).run(SOMEONE_ELSE, aid)
    assert x.value.code == "ARTIFACT_NOT_FOUND"


def test_管理者は他人のものも読める():
    deps, aid = setup()
    post(deps, aid, 1700000001, "田中", "本文")
    assert len(build(deps, ReadComments).run(ADMIN, aid).comments) == 1


def test_公開が止まっていても読める():
    deps, aid = setup()
    post(deps, aid, 1700000001, "田中", "本文")
    build(deps, SuspendArtifact).run(ME, aid)
    assert len(build(deps, ReadComments).run(ME, aid).comments) == 1


def test_読めない記録があっても残りが返る():
    """1件の不具合で、その共有アーティファクトの反応がすべて見えなくなるのを避ける"""
    deps, aid = setup()
    post(deps, aid, 1700000001, "田中", "読める")
    deps.store.put(f"comments/{aid}/1700000002-broken.json", "{壊れている", "application/json")
    post(deps, aid, 1700000003, "佐藤", "これも読める")

    got = build(deps, ReadComments).run(ME, aid)

    assert [c["author"] for c in got.comments] == ["田中", "佐藤"]
    # 黙って落とすと、投稿者が「これで全部だ」と思い込む
    assert got.unreadable == 1


def test_読んでも何も変わらない():
    deps, aid = setup()
    post(deps, aid, 1700000001, "田中", "本文")
    before = dict(deps.store.objects)

    build(deps, ReadComments).run(ME, aid)
    build(deps, ReadComments).run(ME, aid)

    assert deps.store.objects == before


# ── 取り出す ────────────────────────────────────────────

def test_中身とコメントがまとめて返る():
    deps, aid = setup()
    post(deps, aid, 1700000001, "田中", "本文")

    got = build(deps, ExportArtifact).run(ME, aid)

    assert got.content == HTML
    assert got.name == "検索基盤の選定"
    assert len(got.comments) == 1


def test_取り出しても何も変わらない():
    """読むだけの操作。控えを取るたびに渡した相手へ影響が及んではならない"""
    deps, aid = setup()
    post(deps, aid, 1700000001, "田中", "本文")
    store_before = dict(deps.store.objects)
    keys_before = dict(deps.keys.keys)

    first = build(deps, ExportArtifact).run(ME, aid)
    second = build(deps, ExportArtifact).run(ME, aid)

    assert first == second
    assert deps.store.objects == store_before
    assert deps.keys.keys == keys_before


def test_公開が止まっていても取り出せる():
    """止めてからでは取り出せないと、迷ったときに止められなくなる"""
    deps, aid = setup()
    build(deps, SuspendArtifact).run(ME, aid)
    assert build(deps, ExportArtifact).run(ME, aid).content == HTML


def test_取り出したものに閲覧トークンは含まれない():
    """渡り歩いても、それだけで開ける状態にならないようにする"""
    deps, aid = setup()
    got = json.dumps(asdict(build(deps, ExportArtifact).run(ME, aid)), ensure_ascii=False)
    assert "token" not in got


def test_他人のものは取り出せない():
    deps, aid = setup()
    with pytest.raises(ManageError) as x:
        build(deps, ExportArtifact).run(SOMEONE_ELSE, aid)
    assert x.value.code == "ARTIFACT_NOT_FOUND"
