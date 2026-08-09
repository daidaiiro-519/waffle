"""引き継ぎと、管理者が扱える範囲を、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-transfer-artifact、および uc-suspend-artifact /
uc-resume-artifact / uc-reissue-view-token / uc-replace-content の
「誰が扱えるか」の受け入れ基準。
"""

import main
import json


from usecase_builder import build  # noqa: E402
from application.usecases.list_my_artifacts import ListMyArtifacts  # noqa: E402
from application.usecases.publish_artifact import PublishArtifact  # noqa: E402
from application.usecases.transfer_artifact import TransferArtifact  # noqa: E402

from application.ports import Caller  # noqa: E402


from publisher_setup import FakeDirectory  # noqa: E402
from fakes import FakeKeyStore, FakeStore  # noqa: E402
from manage_setup import HTML  # noqa: E402

X = Caller("publisher-x")
Y = Caller("publisher-y")
ADMIN = Caller("admin-1", is_admin=True)


def setup():
    """XがAを公開しており、Yも招かれている状態を作る。"""
    store, keys = FakeStore(), FakeKeyStore()
    c = main.Connections(
        store=store, keys=keys, identify=lambda _t: X.id,
        wrapper_template="<html>{{アーティファクトID}}</html>",
        now=lambda: 1_700_000_000, viewer_domain="viewer.example.net")
    result = build(c, PublishArtifact).run({"html": HTML, "authorization": "Bearer x"})
    deps = main.Connections(
        store=store, keys=keys,
        directory=FakeDirectory({
            X.id: {"email": "x@example.com", "status": "PUBLISHED"},
            Y.id: {"email": "y@example.com", "status": "PUBLISHED"},
            ADMIN.id: {"email": "a@example.com", "status": "PUBLISHED"},
        }),
        now=lambda: 1_700_000_100, viewer_domain="viewer.example.net",
    )
    return deps, result


def meta_of(deps, artifact_id):
    return json.loads(deps.store.get(f"meta/{artifact_id}.json"))


# ── 管理者が扱える範囲 ──────────────────────────────────

def test_一覧には誰が公開したかが分かる():
    """管理者が全員のものを見るとき、持ち主が読めないと引き継ぎ先を決められない"""
    deps, r = setup()
    assert build(deps, ListMyArtifacts).run(ADMIN).artifacts[0].uploaded_by == X.id


# ── 引き継ぎ ────────────────────────────────────────────

def test_引き継いでもコメントの並びに区切りは増えない():
    deps, r = setup()
    build(deps, TransferArtifact).run(ADMIN, r.artifact_id, Y.id)
    assert deps.store.list(f"comments/{r.artifact_id}/") == []
