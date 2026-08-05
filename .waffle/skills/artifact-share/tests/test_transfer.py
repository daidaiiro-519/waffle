"""引き継ぎと、管理者が扱える範囲を、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-transfer-artifact、および uc-suspend-artifact /
uc-resume-artifact / uc-reissue-view-token / uc-replace-content の
「誰が扱えるか」の受け入れ基準。
"""

import main
import json

import pytest

from usecase_builder import build  # noqa: E402
from application.usecases.list_my_artifacts import ListMyArtifacts  # noqa: E402
from application.usecases.publish_artifact import PublishArtifact  # noqa: E402
from application.usecases.replace_artifact_content import ReplaceArtifactContent  # noqa: E402
from application.usecases.resume_artifact import ResumeArtifact  # noqa: E402
from application.usecases.suspend_artifact import SuspendArtifact  # noqa: E402
from application.usecases.transfer_artifact import TransferArtifact  # noqa: E402

from application.ports import Caller  # noqa: E402
from shared.errors import ManageError  # noqa: E402


from publisher_setup import FakeDirectory  # noqa: E402
from fakes import FakeKeyStore, FakeStore  # noqa: E402
from test_manage import HTML  # noqa: E402

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

def test_管理者は他人のものも一覧できる():
    deps, r = setup()
    ids = [row.artifact_id for row in build(deps, ListMyArtifacts).run(ADMIN).artifacts]
    assert ids == [r.artifact_id]


def test_一覧には誰が公開したかが分かる():
    """管理者が全員のものを見るとき、持ち主が読めないと引き継ぎ先を決められない"""
    deps, r = setup()
    assert build(deps, ListMyArtifacts).run(ADMIN).artifacts[0].uploaded_by == X.id


def test_管理者は他人のものを公開停止_再開できる():
    deps, r = setup()
    aid = r.artifact_id

    build(deps, SuspendArtifact).run(ADMIN, aid)
    assert meta_of(deps, aid)["status"] == "disabled"

    build(deps, ResumeArtifact).run(ADMIN, aid)
    assert meta_of(deps, aid)["status"] == "active"

    assert deps.keys.get(f"token:{aid}") != "DISABLED"


def test_管理者でも他人の中身は差し替えられない():
    """集まったコメントが何に対する反応かを、投稿者の知らないうちに変えない"""
    deps, r = setup()
    before = deps.store.get(f"p/{r.artifact_id}/content.html")

    with pytest.raises(ManageError) as x:
        build(deps, ReplaceArtifactContent).run(ADMIN, r.artifact_id, HTML.replace("本文", "別"))

    assert x.value.code == "NOT_THE_PUBLISHER"
    assert deps.store.get(f"p/{r.artifact_id}/content.html") == before


def test_第三者には見つからないものとして拒む():
    """拒否と不在を区別させないことで、そこに何かがあること自体を伝えない"""
    deps, r = setup()
    with pytest.raises(ManageError) as x:
        build(deps, SuspendArtifact).run(Y, r.artifact_id)
    assert x.value.code == "ARTIFACT_NOT_FOUND"


# ── 引き継ぎ ────────────────────────────────────────────

def test_移した先が手入れできるようになる():
    deps, r = setup()
    result = build(deps, TransferArtifact).run(ADMIN, r.artifact_id, Y.id)

    assert result.moved_to == Y.id
    assert meta_of(deps, r.artifact_id)["uploadedBy"] == Y.id
    build(deps, SuspendArtifact).run(Y, r.artifact_id)          # Yが扱える


def test_引き継いでもコメントの並びに区切りは増えない():
    deps, r = setup()
    build(deps, TransferArtifact).run(ADMIN, r.artifact_id, Y.id)
    assert deps.store.list(f"comments/{r.artifact_id}/") == []
