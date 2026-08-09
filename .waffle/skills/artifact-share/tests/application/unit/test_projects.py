"""プロジェクトの作成と、見せ方を変える操作を確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-create-project / uc-control-project-access
引き継ぎ: handoff-project-scope

個人と共有の別は、閲覧の可否ではなく書き換えの可否である。したがって
閲覧ゲートはこの別を知らず、判定はすべてここに閉じる。
"""


import pytest

from project_setup import (  # noqa: E402
    X, Y, index_of, listing_of, owned, setup,
)
from usecase_builder import build  # noqa: E402
from application.usecases.control_project_access import ControlProjectAccess  # noqa: E402
from application.usecases.create_project import CreateProject  # noqa: E402

from shared.errors import ProjectError  # noqa: E402





def test_一覧ページの雛形と中身が置かれる():
    """雛形はどのプロジェクトでも同じもの、中身はこのプロジェクトのもの"""
    deps = setup()
    r = build(deps, CreateProject).run(X, "検索基盤リニューアル", "PERSONAL")

    page = deps.store.get(f"proj/{r.project_id}/index.html")
    assert "{{プロジェクトID}}" not in page
    assert r.project_id in page
    assert listing_of(deps, r.project_id)["name"] == "検索基盤リニューアル"


# ── 見せ方を変える ──────────────────────────────────────

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



# ── 中身を見る ──────────────────────────────────────────

