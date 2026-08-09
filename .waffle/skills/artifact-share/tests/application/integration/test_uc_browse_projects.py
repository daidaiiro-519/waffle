"""見て回る操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

見る操作は何も変えない。何度見ても同じ答えが返り、見たこと自体が公開の状態や
所属や閲覧トークンに触れない。

対象の仕様: uc-browse-projects（操作保証）
"""
from project_setup import X, artifact, assign, index_of, owned, setup
from application.usecases.browse_projects import BrowseProjects
from usecase_builder import build


def test_何度見ても何も変わらない():
    """
    Scenario: 何度見ても何も変わらない
    Given 投稿者Xが一覧と P の中身を見ている
    When 同じものをもう一度求める
    Then 同じ答えが返る
    And P の公開の状態も所属も閲覧トークンも変わっていない
    """
    deps = setup()
    p = owned(deps, caller=X, name="P")
    artifact(deps, "aaaaaaaa", "検索基盤の選定")
    assign(deps, X, "aaaaaaaa", p.project_id)

    engine = build(deps, BrowseProjects)
    first_list = engine.run("list", X)
    first_detail = engine.run("detail", X, p.project_id)
    before = index_of(deps, p.project_id)
    before_keys = dict(deps.keys.written)

    second_list = engine.run("list", X)
    second_detail = engine.run("detail", X, p.project_id)

    assert second_list == first_list
    assert second_detail == first_detail
    after = index_of(deps, p.project_id)
    assert after["status"] == before["status"]
    assert after["memberArtifactIds"] == before["memberArtifactIds"]
    assert deps.keys.written == before_keys
