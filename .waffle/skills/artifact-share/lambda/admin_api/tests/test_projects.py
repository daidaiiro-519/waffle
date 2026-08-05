"""プロジェクトの作成と、見せ方を変える操作を確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-create-project / uc-control-project-access
引き継ぎ: handoff-project-scope

個人と共有の別は、閲覧の可否ではなく書き換えの可否である。したがって
閲覧ゲートはこの別を知らず、判定はすべてここに閉じる。
"""

import main
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from usecase_builder import build  # noqa: E402
from application.usecases.assign_artifact_to_project import AssignArtifactToProject  # noqa: E402
from application.usecases.browse_projects import BrowseProjects  # noqa: E402
from application.usecases.control_project_access import ControlProjectAccess  # noqa: E402
from application.usecases.create_project import CreateProject  # noqa: E402

from application.ports import Caller  # noqa: E402
from domain.publication import PERSONAL, SHARED  # noqa: E402
from shared.errors import ProjectError  # noqa: E402


from test_manage import FakeKeyStore, FakeStore  # noqa: E402

X = Caller("publisher-x")
Y = Caller("publisher-y")
ADMIN = Caller("admin-1", is_admin=True)


def setup():
    return main.Connections(
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
    r = build(deps, CreateProject).run(X, "検索基盤リニューアル", "PERSONAL")

    assert r["url"] == f"https://viewer.example.net/proj/{r['projectId']}/"
    assert r["token"]
    assert r["tokenShownOnce"] is True
    

def test_作った人が持ち主になり共有の別が残る():
    deps = setup()
    r = build(deps, CreateProject).run(X, "検索基盤リニューアル", "SHARED")

    index = index_of(deps, r["projectId"])
    assert index["owner"] == X.id
    assert index["scope"] == "SHARED"
    assert index["status"] == "active"      # 保管の綴り。業務では PUBLISHED
    assert index["memberArtifactIds"] == []


def test_作った直後は何も入っていない():
    deps = setup()
    r = build(deps, CreateProject).run(X, "空のまとめ", "PERSONAL")
    assert listing_of(deps, r["projectId"])["artifacts"] == []


def test_一覧ページの雛形と中身が置かれる():
    """雛形はどのプロジェクトでも同じもの、中身はこのプロジェクトのもの"""
    deps = setup()
    r = build(deps, CreateProject).run(X, "検索基盤リニューアル", "PERSONAL")

    page = deps.store.get(f"proj/{r['projectId']}/index.html")
    assert "{{プロジェクトID}}" not in page
    assert r["projectId"] in page
    assert listing_of(deps, r["projectId"])["name"] == "検索基盤リニューアル"


def test_表示名が空なら作らない():
    deps = setup()
    with pytest.raises(ProjectError) as x:
        build(deps, CreateProject).run(X, "   ", "PERSONAL")
    assert x.value.code == "NAME_REQUIRED"
    assert deps.keys.keys == {}          # 閲覧トークンは発行されない


def test_想定外の共有の別では作らない():
    deps = setup()
    with pytest.raises(ProjectError) as x:
        build(deps, CreateProject).run(X, "まとめ", "EVERYONE")
    assert x.value.code == "SCOPE_REQUIRED"


def test_閲覧トークンは記録から取り出せない():
    deps = setup()
    r = build(deps, CreateProject).run(X, "まとめ", "PERSONAL")

    record = deps.keys.get(f"proj:{r['projectId']}")
    value, expires = record.split("|")
    assert value != r["token"]           # そのままは残さない
    assert "token" not in index_of(deps, r["projectId"])


# ── 見せ方を変える ──────────────────────────────────────

def owned(deps, scope="PERSONAL"):
    return build(deps, CreateProject).run(X, "検索基盤リニューアル", scope)


def test_作ると最初の1本が渡される():
    deps = setup()
    r = owned(deps)

    tokens = index_of(deps, r["projectId"])["viewTokens"]
    assert len(tokens) == 1
    assert r["token"] not in str(tokens)

def test_公開停止すると開けなくなるが中身は残る():
    deps = setup()
    r = owned(deps)
    build(deps, ControlProjectAccess).run("suspend", X, r["projectId"])

    assert deps.keys.get(f"proj:{r['projectId']}") == "DISABLED"
    assert index_of(deps, r["projectId"])["status"] == "disabled"
    assert deps.store.get(f"proj/{r['projectId']}/index.json")


def test_再開すると止める前の閲覧トークンがそのまま使える():
    deps = setup()
    r = owned(deps)
    before = deps.keys.get(f"proj:{r['projectId']}")
    build(deps, ControlProjectAccess).run("suspend", X, r["projectId"])

    build(deps, ControlProjectAccess).run("resume", X, r["projectId"])

    assert deps.keys.get(f"proj:{r['projectId']}") == before
    assert index_of(deps, r["projectId"])["status"] == "active"


def test_止まっていないものは再開できない():
    deps = setup()
    r = owned(deps)
    with pytest.raises(ProjectError) as x:
        build(deps, ControlProjectAccess).run("resume", X, r["projectId"])
    assert x.value.code == "NOT_SUSPENDED"


def test_管理者は自分が作ったものでなくても扱える():
    """持ち主が抜けたあとに、誰も止められないプロジェクトが残らないこと"""
    deps = setup()
    r = owned(deps)
    build(deps, ControlProjectAccess).run("suspend", ADMIN, r["projectId"])
    assert index_of(deps, r["projectId"])["status"] == "disabled"


def test_共有でも持ち主以外は見せ方を変えられない():
    """出し入れができることと、見せ方を変えられることは別

    誰でも止められると、他の人が渡した相手まで巻き込んで見えなくなる。
    """
    deps = setup()
    r = owned(deps, scope="SHARED")

    with pytest.raises(ProjectError) as x:
        build(deps, ControlProjectAccess).run("suspend", Y, r["projectId"])
    assert x.value.code == "PROJECT_NOT_FOUND"

    assert index_of(deps, r["projectId"])["status"] == "active"


def test_無いプロジェクトと他人のものを同じ拒み方にする():
    """そこに何かがあること自体を読み取らせない"""
    deps = setup()
    r = owned(deps)

    with pytest.raises(ProjectError) as a:
        build(deps, ControlProjectAccess).run("suspend", Y, r["projectId"])
    with pytest.raises(ProjectError) as b:
        build(deps, ControlProjectAccess).run("suspend", Y, "no-such-project")
    assert a.value.code == b.value.code == "PROJECT_NOT_FOUND"


# ── 一覧 ────────────────────────────────────────────────

def test_一覧には自分のものと共有のものが並ぶ():
    deps = setup()
    mine = build(deps, CreateProject).run(X, "自分の", "PERSONAL")
    shared = build(deps, CreateProject).run(Y, "みんなの", "SHARED")
    others = build(deps, CreateProject).run(Y, "他人の", "PERSONAL")

    ids = {p["projectId"] for p in build(deps, BrowseProjects).run("list", X)["projects"]}
    assert mine["projectId"] in ids
    assert shared["projectId"] in ids        # 共有なら自分のものを入れられる
    assert others["projectId"] not in ids


def test_管理者の一覧には全部が並ぶ():
    deps = setup()
    build(deps, CreateProject).run(X, "自分の", "PERSONAL")
    build(deps, CreateProject).run(Y, "他人の", "PERSONAL")
    assert len(build(deps, BrowseProjects).run("list", ADMIN)["projects"]) == 2


def test_一覧に閲覧トークンは含まれない():
    deps = setup()
    owned(deps)
    for row in build(deps, BrowseProjects).run("list", X)["projects"]:
        assert "token" not in row


# ── 中身を見る ──────────────────────────────────────────

def artifact(deps, artifact_id, name, owner=X, status="active"):
    deps.store.put(f"meta/{artifact_id}.json", json.dumps({
        "artifactId": artifact_id, "name": name, "status": status,
        "docType": "DecisionRecord", "description": "", "tags": [],
        "uploadedBy": owner.id, "projects": [], "updatedAt": 1,
    }), "application/json")


def test_中身に入っているものが名前つきで返る():
    """一覧の件数だけでは、何が入っているかを画面に出せない"""
    deps = setup()
    r = owned(deps)
    artifact(deps, "aaaaaaaa", "検索基盤の選定")
    manage_assign(deps, X, "aaaaaaaa", r["projectId"])

    got = build(deps, BrowseProjects).run("detail", X, r["projectId"])

    assert got["project"]["name"] == "検索基盤リニューアル"
    assert [a["artifactId"] for a in got["artifacts"]] == ["aaaaaaaa"]
    assert got["artifacts"][0]["name"] == "検索基盤の選定"


def test_中身に閲覧トークンは含まれない():
    deps = setup()
    r = owned(deps)
    got = build(deps, BrowseProjects).run("detail", X, r["projectId"])
    assert "token" not in got["project"]


def test_共有なら持ち主でなくても中身を見られる():
    """そこへ自分のものを入れるには、いま何が入っているかが見えている必要がある"""
    deps = setup()
    r = owned(deps, scope="SHARED")
    assert build(deps, BrowseProjects).run("detail", Y, r["projectId"])["project"]["projectId"] == r["projectId"]


def test_個人なら持ち主以外は中身を見られない():
    deps = setup()
    r = owned(deps)
    with pytest.raises(ProjectError) as x:
        build(deps, BrowseProjects).run("detail", Y, r["projectId"])
    assert x.value.code == "PROJECT_NOT_FOUND"


def test_公開が止まっていても持ち主は中身を見られる():
    """止めたものを再開するか外すかを決めるのに、中身が見えている必要がある"""
    deps = setup()
    r = owned(deps)
    build(deps, ControlProjectAccess).run("suspend", X, r["projectId"])
    assert build(deps, BrowseProjects).run("detail", X, r["projectId"])["project"]["status"] == "SUSPENDED"


def manage_assign(deps, caller, artifact_id, project_id):
    return build(deps, AssignArtifactToProject).run("assign", caller, artifact_id, project_id)


def test_読めない記録があっても残りが並ぶ():
    """一覧が黙って短くなると、作ったはずのプロジェクトが消えたように見える"""
    deps = setup()
    build(deps, CreateProject).run(X, "設計レビュー", PERSONAL, "")
    deps.store.put("projects/broken.json", "{壊れている", "application/json")

    got = build(deps, BrowseProjects).run("list", X)

    assert len(got["projects"]) == 1
    assert got["unreadable"] == 1
