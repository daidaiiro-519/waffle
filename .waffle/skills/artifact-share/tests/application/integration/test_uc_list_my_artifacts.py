"""見渡しの操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

見るだけの操作なので、何度求めても同じ一覧が返り、公開の状態も閲覧トークンも動かない。

対象の仕様: uc-list-my-artifacts（操作保証）
"""
from manage_setup import ME, meta_of, setup
from application.usecases.list_my_artifacts import ListMyArtifacts
from usecase_builder import build


def test_何度見渡しても何も変わらない():
    """
    Scenario: 何度見渡しても何も変わらない
    Given 投稿者Xが見渡しを求めている
    When 同じ見渡しをもう一度求める
    Then 同じ一覧が返る
    And A の公開の状態も閲覧トークンも変わっていない
    """
    deps, r = setup()
    first = build(deps, ListMyArtifacts).run(ME)
    status_before = meta_of(deps, r.artifact_id)["status"]
    keys_before = dict(deps.keys.keys)

    second = build(deps, ListMyArtifacts).run(ME)

    assert second == first
    assert meta_of(deps, r.artifact_id)["status"] == status_before
    assert deps.keys.keys == keys_before
