"""プロジェクトの作成と、見せ方を変える操作を確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-create-project / uc-control-project-access
引き継ぎ: handoff-project-scope

個人と共有の別は、閲覧の可否ではなく書き換えの可否である。したがって
閲覧ゲートはこの別を知らず、判定はすべてここに閉じる。
"""

import main
import json

import pytest

from usecase_builder import build  # noqa: E402
from application.usecases.assign_artifact_to_project import AssignArtifactToProject  # noqa: E402
from application.usecases.browse_projects import BrowseProjects  # noqa: E402
from application.usecases.control_project_access import ControlProjectAccess  # noqa: E402
from application.usecases.create_project import CreateProject  # noqa: E402

from application.ports import Caller  # noqa: E402
from domain.project import PERSONAL  # noqa: E402
from domain.project import SHARED  # noqa: E402
from shared.errors import ProjectError  # noqa: E402


from fakes import FakeKeyStore, FakeStore  # noqa: E402

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


def test_一覧ページの雛形と中身が置かれる():
    """雛形はどのプロジェクトでも同じもの、中身はこのプロジェクトのもの"""
    deps = setup()
    r = build(deps, CreateProject).run(X, "検索基盤リニューアル", "PERSONAL")

    page = deps.store.get(f"proj/{r.project_id}/index.html")
    assert "{{プロジェクトID}}" not in page
    assert r.project_id in page
    assert listing_of(deps, r.project_id)["name"] == "検索基盤リニューアル"


def test_想定外の共有の別では作らない():
    deps = setup()
    with pytest.raises(ProjectError) as x:
        build(deps, CreateProject).run(X, "まとめ", "EVERYONE")
    assert x.value.code == "SCOPE_REQUIRED"


# ── 見せ方を変える ──────────────────────────────────────

def owned(deps, scope="PERSONAL"):
    return build(deps, CreateProject).run(X, "検索基盤リニューアル", scope)


def test_作ると最初の1本が渡される():
    deps = setup()
    r = owned(deps)

    tokens = index_of(deps, r.project_id)["viewTokens"]
    assert len(tokens) == 1
    assert r.token not in str(tokens)


def test_無いプロジェクトと他人のものを同じ拒み方にする():
    """そこに何かがあること自体を読み取らせない"""
    deps = setup()
    r = owned(deps)

    with pytest.raises(ProjectError) as a:
        build(deps, ControlProjectAccess).run("suspend", Y, r.project_id)
    with pytest.raises(ProjectError) as b:
        build(deps, ControlProjectAccess).run("suspend", Y, "no-such-project")
    assert a.value.code == b.value.code == "PROJECT_NOT_FOUND"


# ── 一覧 ────────────────────────────────────────────────


# ── 中身を見る ──────────────────────────────────────────

def artifact(deps, artifact_id, name, owner=X, status="active"):
    deps.store.put(f"meta/{artifact_id}.json", json.dumps({
        "artifactId": artifact_id, "name": name, "status": status,
        "docType": "DecisionRecord", "description": "", "tags": [],
        "uploadedBy": owner.id, "projects": [], "updatedAt": 1,
    }), "application/json")


def manage_assign(deps, caller, artifact_id, project_id):
    return build(deps, AssignArtifactToProject).run("assign", caller, artifact_id, project_id)
