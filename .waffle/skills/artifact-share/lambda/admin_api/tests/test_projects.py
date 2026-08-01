"""プロジェクトの作成と、見せ方を変える操作を確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-create-project / uc-control-project-access
引き継ぎ: handoff-project-scope

個人と共有の別は、閲覧の可否ではなく書き換えの可否である。したがって
閲覧の関門はこの別を知らず、判定はすべてここに閉じる。
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import manage  # noqa: E402
import projects  # noqa: E402

from test_manage import FakeKeyStore, FakeStore  # noqa: E402

X = manage.Caller("publisher-x")
Y = manage.Caller("publisher-y")
ADMIN = manage.Caller("admin-1", is_admin=True)


def setup():
    return manage.Deps(
        store=FakeStore(), keys=FakeKeyStore(),
        project_page="<html data-project=\"{{プロジェクトID}}\"></html>",
        now=lambda: 1_700_000_000, viewer_domain="viewer.example.net",
    )


def index_of(deps, project_id):
    return json.loads(deps.store.get(f"projects/{project_id}.json"))


def listing_of(deps, project_id):
    return json.loads(deps.store.get(f"proj/{project_id}/index.json"))


# ── 作る ────────────────────────────────────────────────

def test_作ると共有URLと閲覧トークンが返る():
    deps = setup()
    r = projects.create(deps, X, "検索基盤リニューアル", "PERSONAL")

    assert r["url"] == f"https://viewer.example.net/proj/{r['projectId']}/"
    assert r["token"]
    assert r["tokenShownOnce"] is True
    assert r["event"] == "ProjectCreated"


def test_作った人が持ち主になり共有の別が残る():
    deps = setup()
    r = projects.create(deps, X, "検索基盤リニューアル", "SHARED")

    index = index_of(deps, r["projectId"])
    assert index["owner"] == X.id
    assert index["scope"] == "SHARED"
    assert index["status"] == "active"
    assert index["memberArtifactIds"] == []


def test_作った直後は何も入っていない():
    deps = setup()
    r = projects.create(deps, X, "空のまとめ", "PERSONAL")
    assert listing_of(deps, r["projectId"])["artifacts"] == []


def test_一覧ページの雛形と中身が置かれる():
    """雛形はどのプロジェクトでも同じもの、中身はこのプロジェクトのもの"""
    deps = setup()
    r = projects.create(deps, X, "検索基盤リニューアル", "PERSONAL")

    page = deps.store.get(f"proj/{r['projectId']}/index.html")
    assert "{{プロジェクトID}}" not in page
    assert r["projectId"] in page
    assert listing_of(deps, r["projectId"])["name"] == "検索基盤リニューアル"


def test_表示名が空なら作らない():
    deps = setup()
    with pytest.raises(projects.ProjectError) as x:
        projects.create(deps, X, "   ", "PERSONAL")
    assert x.value.code == "NAME_REQUIRED"
    assert deps.keys.keys == {}          # 閲覧トークンは発行されない


def test_想定外の共有の別では作らない():
    deps = setup()
    with pytest.raises(projects.ProjectError) as x:
        projects.create(deps, X, "まとめ", "EVERYONE")
    assert x.value.code == "SCOPE_REQUIRED"


def test_閲覧トークンは記録から取り出せない():
    deps = setup()
    r = projects.create(deps, X, "まとめ", "PERSONAL")

    record = deps.keys.get(f"proj:{r['projectId']}")
    value, expires, generation = record.split("|")
    assert value != r["token"]           # そのままは残さない
    assert generation == "1"
    assert "token" not in index_of(deps, r["projectId"])


# ── 見せ方を変える ──────────────────────────────────────

def owned(deps, scope="PERSONAL"):
    return projects.create(deps, X, "検索基盤リニューアル", scope)


def test_再発行すると世代が上がりURLは変わらない():
    deps = setup()
    r = owned(deps)
    before = deps.keys.get(f"proj:{r['projectId']}")

    again = projects.reissue_token(deps, X, r["projectId"])

    after = deps.keys.get(f"proj:{r['projectId']}")
    assert before.split("|")[2] == "1"
    assert after.split("|")[2] == "2"
    assert again["url"] == r["url"]
    assert again["token"] != r["token"]


def test_公開停止すると開けなくなるが中身は残る():
    deps = setup()
    r = owned(deps)
    projects.suspend(deps, X, r["projectId"])

    assert deps.keys.get(f"proj:{r['projectId']}") == "DISABLED"
    assert index_of(deps, r["projectId"])["status"] == "disabled"
    assert deps.store.get(f"proj/{r['projectId']}/index.json")


def test_再開すると閲覧トークンが必ず新しくなる():
    deps = setup()
    r = owned(deps)
    projects.suspend(deps, X, r["projectId"])

    again = projects.resume(deps, X, r["projectId"])

    assert again["token"] != r["token"]
    assert deps.keys.get(f"proj:{r['projectId']}").split("|")[2] == "2"
    assert index_of(deps, r["projectId"])["status"] == "active"


def test_止まっていないものは再開できない():
    deps = setup()
    r = owned(deps)
    with pytest.raises(projects.ProjectError) as x:
        projects.resume(deps, X, r["projectId"])
    assert x.value.code == "NOT_SUSPENDED"


def test_管理者は自分が作ったものでなくても扱える():
    """持ち主が抜けたあとに、誰も止められないプロジェクトが残らないこと"""
    deps = setup()
    r = owned(deps)
    projects.suspend(deps, ADMIN, r["projectId"])
    assert index_of(deps, r["projectId"])["status"] == "disabled"


def test_共有でも持ち主以外は見せ方を変えられない():
    """出し入れができることと、見せ方を変えられることは別

    誰でも止められると、他の人が渡した相手まで巻き込んで見えなくなる。
    """
    deps = setup()
    r = owned(deps, scope="SHARED")

    for call in (lambda: projects.suspend(deps, Y, r["projectId"]),
                 lambda: projects.reissue_token(deps, Y, r["projectId"])):
        with pytest.raises(projects.ProjectError) as x:
            call()
        assert x.value.code == "PROJECT_NOT_FOUND"

    assert index_of(deps, r["projectId"])["status"] == "active"


def test_無いプロジェクトと他人のものを同じ拒み方にする():
    """そこに何かがあること自体を読み取らせない"""
    deps = setup()
    r = owned(deps)

    with pytest.raises(projects.ProjectError) as a:
        projects.suspend(deps, Y, r["projectId"])
    with pytest.raises(projects.ProjectError) as b:
        projects.suspend(deps, Y, "no-such-project")
    assert a.value.code == b.value.code == "PROJECT_NOT_FOUND"


# ── 一覧 ────────────────────────────────────────────────

def test_一覧には自分のものと共有のものが並ぶ():
    deps = setup()
    mine = projects.create(deps, X, "自分の", "PERSONAL")
    shared = projects.create(deps, Y, "みんなの", "SHARED")
    others = projects.create(deps, Y, "他人の", "PERSONAL")

    ids = {p["projectId"] for p in projects.list_projects(deps, X)}
    assert mine["projectId"] in ids
    assert shared["projectId"] in ids        # 共有なら自分のものを入れられる
    assert others["projectId"] not in ids


def test_管理者の一覧には全部が並ぶ():
    deps = setup()
    projects.create(deps, X, "自分の", "PERSONAL")
    projects.create(deps, Y, "他人の", "PERSONAL")
    assert len(projects.list_projects(deps, ADMIN)) == 2


def test_一覧に閲覧トークンは含まれない():
    deps = setup()
    owned(deps)
    for row in projects.list_projects(deps, X):
        assert "token" not in row
