"""まとめを作る操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

ここで確かめるのは1回の作成の結果ではなく、作成という操作が全体として
守る約束。渡した閲覧トークンは、そのとき示された以外に手立てが無い。

対象の仕様: uc-create-project（操作保証）
"""
from project_setup import index_of, listing_of, owned, setup


def test_閲覧トークンは後から取り出せない():
    """
    Scenario: 閲覧トークンは後から取り出せない
    Given プロジェクトの閲覧トークンが示されている
    When 一覧や記録からその閲覧トークンを取り出そうとする
    Then 閲覧トークンは得られない
    And 新しく発行する以外に手立てが無い
    """
    deps = setup()

    r = owned(deps)

    record = deps.keys.written[f"proj:{r.project_id}"]
    value, expires = record.split("|")
    assert value != r.token          # そのままは残さない
    assert r.token not in record     # 部分としても残さない
    assert int(expires) > 0          # 期限は必ず付く
    assert r.token not in str(index_of(deps, r.project_id))
    assert r.token not in str(listing_of(deps, r.project_id))
