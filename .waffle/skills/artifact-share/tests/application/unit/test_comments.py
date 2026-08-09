"""投稿者がコメントを読み、中身とコメントを取り出す操作を確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-read-comments / uc-export-artifact
引き継ぎ: handoff-read-export

閲覧者は閲覧トークンで開いた画面から読み書きし、投稿者は本人確認を通った
画面から読む。指しているものは同じコメントだが、通ってよい条件が違う。
"""

import main
import json


from usecase_builder import build  # noqa: E402
from application.usecases.publish_artifact import PublishArtifact  # noqa: E402
from application.usecases.read_comments import ReadComments  # noqa: E402

from application.ports import Caller  # noqa: E402


from fakes import FakeKeyStore, FakeStore  # noqa: E402
from manage_setup import ADMIN, HTML, ME  # noqa: E402
SOMEONE_ELSE = Caller("publisher-2")

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



def test_業務の語彙で返り欠けが無い():
    """外の綴りへ直すのは受け口の仕事。ここが返すのは業務の語彙。

    判定だけは保管も画面も decision と呼び、業務は判定と呼ぶ。既に書かれた
    記録の欄名を変えられないための食い違いで、対応は受け口が宣言する。
    """
    deps, aid = setup()
    post(deps, aid, 1700000001, "田中", "本文")

    c = build(deps, ReadComments).run(ME, aid).comments[0]

    assert (c.kind, c.author, c.body) == ("comment", "田中", "本文")
    assert c.verdict == "comment"      # 添えなければ、ただの意見
    assert c.parent_id is None
    assert c.posted_at
    assert c.id == "1700000001-abcd1234"


# ── 取り出す ────────────────────────────────────────────

