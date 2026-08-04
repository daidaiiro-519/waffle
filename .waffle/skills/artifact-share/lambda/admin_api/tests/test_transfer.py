"""引き継ぎと、管理者が扱える範囲を、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-transfer-artifact、および uc-suspend-artifact /
uc-resume-artifact / uc-reissue-view-token / uc-replace-content の
「誰が扱えるか」の受け入れ基準。
"""

import main
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import manage  # noqa: E402
from application.usecases import publish_artifact  # noqa: E402

from test_publishers import FakeDirectory  # noqa: E402
from test_manage import HTML, FakeKeyStore, FakeStore  # noqa: E402

X = manage.Caller("publisher-x")
Y = manage.Caller("publisher-y")
ADMIN = manage.Caller("admin-1", is_admin=True)


def setup():
    """XがAを公開しており、Yも招かれている状態を作る。"""
    store, keys = FakeStore(), FakeKeyStore()
    c = main.Connections(
        store=store, keys=keys, identify=lambda _t: X.id,
        wrapper_template="<html>{{アーティファクトID}}</html>",
        now=lambda: 1_700_000_000, viewer_domain="viewer.example.net")
    result = publish_artifact.publish(c.artifacts, c.viewer, c.gate, c.identify, c.now, {"html": HTML, "authorization": "Bearer x"})
    deps = main.Connections(
        store=store, keys=keys,
        directory=FakeDirectory({
            X.id: {"email": "x@example.com", "status": "active"},
            Y.id: {"email": "y@example.com", "status": "active"},
            ADMIN.id: {"email": "a@example.com", "status": "active"},
        }),
        now=lambda: 1_700_000_100, viewer_domain="viewer.example.net",
    )
    return deps, result


def meta_of(deps, artifact_id):
    return json.loads(deps.store.get(f"meta/{artifact_id}.json"))


# ── 管理者が扱える範囲 ──────────────────────────────────

def test_管理者は他人のものも一覧できる():
    deps, r = setup()
    ids = [row["artifactId"] for row in manage.list_artifacts(deps.artifacts, deps.comments, ADMIN)["artifacts"]]
    assert ids == [r["artifactId"]]


def test_一覧には誰が公開したかが分かる():
    """管理者が全員のものを見るとき、持ち主が読めないと引き継ぎ先を決められない"""
    deps, r = setup()
    assert manage.list_artifacts(deps.artifacts, deps.comments, ADMIN)["artifacts"][0]["uploadedBy"] == X.id


def test_管理者は他人のものを公開停止_再開できる():
    deps, r = setup()
    aid = r["artifactId"]

    manage.suspend(deps.artifacts, deps.gate, deps.now, ADMIN, aid)
    assert meta_of(deps, aid)["status"] == "disabled"

    manage.resume(deps.artifacts, deps.viewer, deps.gate, deps.now, ADMIN, aid)
    assert meta_of(deps, aid)["status"] == "active"

    assert deps.keys.get(f"token:{aid}") != "DISABLED"


def test_管理者でも他人の中身は差し替えられない():
    """集まったコメントが何に対する反応かを、投稿者の知らないうちに変えない"""
    deps, r = setup()
    before = deps.store.get(f"p/{r['artifactId']}/content.html")

    with pytest.raises(manage.ManageError) as x:
        manage.replace_content(deps.artifacts, deps.projects, deps.comments, deps.viewer, deps.now, ADMIN, r["artifactId"], HTML.replace("本文", "別"))

    assert x.value.code == "NOT_THE_PUBLISHER"
    assert deps.store.get(f"p/{r['artifactId']}/content.html") == before


def test_第三者には見つからないものとして拒む():
    """拒否と不在を区別させないことで、そこに何かがあること自体を伝えない"""
    deps, r = setup()
    with pytest.raises(manage.ManageError) as x:
        manage.suspend(deps.artifacts, deps.gate, deps.now, Y, r["artifactId"])
    assert x.value.code == "ARTIFACT_NOT_FOUND"


# ── 引き継ぎ ────────────────────────────────────────────

def test_移した先が手入れできるようになる():
    deps, r = setup()
    result = manage.transfer(deps.artifacts, deps.directory, deps.now, ADMIN, r["artifactId"], Y.id)

    assert result["event"] == "ArtifactTransferred"
    assert meta_of(deps, r["artifactId"])["uploadedBy"] == Y.id
    manage.suspend(deps.artifacts, deps.gate, deps.now, Y, r["artifactId"])          # Yが扱える


def test_移す前の人は扱えなくなる():
    """引き継ぎは移動であって複製ではない"""
    deps, r = setup()
    manage.transfer(deps.artifacts, deps.directory, deps.now, ADMIN, r["artifactId"], Y.id)

    with pytest.raises(manage.ManageError) as x:
        manage.suspend(deps.artifacts, deps.gate, deps.now, X, r["artifactId"])
    assert x.value.code == "ARTIFACT_NOT_FOUND"


def test_閲覧者から見て何も変わらない():
    deps, r = setup()
    token_before = deps.keys.get(f"token:{r['artifactId']}")
    content_before = deps.store.get(f"p/{r['artifactId']}/content.html")

    manage.transfer(deps.artifacts, deps.directory, deps.now, ADMIN, r["artifactId"], Y.id)

    assert deps.keys.get(f"token:{r['artifactId']}") == token_before
    assert deps.store.get(f"p/{r['artifactId']}/content.html") == content_before
    assert meta_of(deps, r["artifactId"])["status"] == "active"


def test_引き継いでもコメントの並びに区切りは増えない():
    deps, r = setup()
    manage.transfer(deps.artifacts, deps.directory, deps.now, ADMIN, r["artifactId"], Y.id)
    assert deps.store.list(f"comments/{r['artifactId']}/") == []


def test_管理者でない者は移せない():
    deps, r = setup()
    with pytest.raises(manage.ManageError) as x:
        manage.transfer(deps.artifacts, deps.directory, deps.now, X, r["artifactId"], Y.id)
    assert x.value.code == "NOT_ADMINISTRATOR"
    assert meta_of(deps, r["artifactId"])["uploadedBy"] == X.id


def test_招かれていない人へは移せない():
    """移した先が公開できる人でなければ、その場で手入れできない状態に戻る"""
    deps, r = setup()
    with pytest.raises(manage.ManageError) as x:
        manage.transfer(deps.artifacts, deps.directory, deps.now, ADMIN, r["artifactId"], "no-such-person")
    assert x.value.code == "PUBLISHER_NOT_FOUND"
    assert meta_of(deps, r["artifactId"])["uploadedBy"] == X.id


def test_公開停止されているものも移せる():
    """止まっているものこそ引き継ぎ先が要る"""
    deps, r = setup()
    manage.suspend(deps.artifacts, deps.gate, deps.now, X, r["artifactId"])

    manage.transfer(deps.artifacts, deps.directory, deps.now, ADMIN, r["artifactId"], Y.id)

    assert meta_of(deps, r["artifactId"])["uploadedBy"] == Y.id
    assert meta_of(deps, r["artifactId"])["status"] == "disabled"   # 止まったまま
