"""公開したあとの管理操作を、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

これらの操作は、Cognitoで本人確認を通った投稿者がブラウザから呼ぶ。
手元のCLIは環境の構築だけを担い、ここには関わらない。

対象の仕様:
  uc-replace-content / uc-reissue-view-token / uc-suspend-artifact /
  uc-resume-artifact / uc-assign-to-project
"""

import json

import pytest


from manage_setup import (  # noqa: E402
    HTML, ME, meta_of, setup, with_project,
)
from usecase_builder import build  # noqa: E402
from application.usecases.assign_artifact_to_project import AssignArtifactToProject  # noqa: E402
from application.usecases.create_project import CreateProject  # noqa: E402
from application.usecases.list_my_artifacts import ListMyArtifacts  # noqa: E402
from application.usecases.replace_artifact_content import ReplaceArtifactContent  # noqa: E402

from application.ports import Caller  # noqa: E402
from domain.entities.shared_artifact import (
    MAX_PROJECTS  # noqa: E402  # 旧 MAX_PROJECTS_PER_ARTIFACT,
)
from shared.errors import ManageError  # noqa: E402




SOMEONE_ELSE = Caller("publisher-2")




# ── 閲覧トークン ────────────────────────────────────────

def test_公開すると最初の1本が渡される():
    """相手ごとに増やせるが、公開した時点で1本は渡されている"""
    deps, r = setup()

    tokens = meta_of(deps, r.artifact_id)["viewTokens"]
    assert len(tokens) == 1
    assert r.token
    assert r.token not in str(tokens)


# ── プロジェクトへの出し入れ ────────────────────────────


def test_無いプロジェクトへは加えられない():
    deps, r = setup()
    with pytest.raises(ManageError) as x:
        build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, "nope")
    assert x.value.code == "PROJECT_NOT_FOUND"


# ── 共有と個人で出し入れの可否が変わる ──────────────────

OTHER = Caller("publisher-9")


def test_自分のプロジェクトへは個人でも入れられる():
    deps, r, pid = with_project("PERSONAL")
    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)
    assert pid in meta_of(deps, r.artifact_id)["projects"]


def test_出し入れするとプロジェクトの索引と一覧が揃う():
    """所属は索引と閲覧ゲート用の投影の2か所に持つ。片方だけを書く経路を作らない"""
    deps, r, pid = with_project("SHARED")

    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)
    index = json.loads(deps.store.get(f"projects/{pid}.json"))
    listing = json.loads(deps.store.get(f"proj/{pid}/index.json"))
    assert index["memberArtifactIds"] == [r.artifact_id]
    assert [a["artifactId"] for a in listing["artifacts"]] == [r.artifact_id]

    build(deps, AssignArtifactToProject).run("unassign", ME, r.artifact_id, pid)
    index = json.loads(deps.store.get(f"projects/{pid}.json"))
    listing = json.loads(deps.store.get(f"proj/{pid}/index.json"))
    assert index["memberArtifactIds"] == []
    assert listing["artifacts"] == []
    assert deps.keys.get(f"pp:{r.artifact_id}") == ""


def test_差し替えると入っている全プロジェクトの一覧が書き直される():
    """一覧は種別と要約を含む。差し替えで変わったものが閲覧者へ届くようにする

    表示名は差し替えでは変わらない（公開したときのまま）。変わるのは
    中身から読み直す種別・要約・分類の目印である。
    """
    deps, r, pid = with_project("SHARED")
    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    revised = HTML.replace("</head>", '<meta name="description" content="改訂した理由"></head>')
    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, revised)

    listing = json.loads(deps.store.get(f"proj/{pid}/index.json"))
    assert listing["artifacts"][0]["description"] == "改訂した理由"


