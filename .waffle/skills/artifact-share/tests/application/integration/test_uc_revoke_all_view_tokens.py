"""見せる相手をまとめて外す操作が、対象を特定し権限を確かめる契約を守っているかを確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くWhen/Thenは仕様の文言を一字一句
そのまま写したもの。ここで確かめるのは、この操作そのものの結果ではなく、
操作へ入る前段の解決プロセスが返す答え。

対象の仕様: uc-revoke-all-view-tokens（操作保証）
"""

import pytest

from usecase_builder import build
from view_token_setup import ADMIN, AID, OTHER, issue, setup
from application.usecases.revoke_all_view_tokens import RevokeAllViewTokens
from application.view_token_access import ViewTokenError
from domain.view_subject import ViewSubject


def test_権限の無い者にはTARGET_NOT_FOUND():
    """
    Scenario: 権限の無い者にはTARGET_NOT_FOUND
    When 対象の投稿者でも管理者でもない者がこの操作を求める
    Then TARGET_NOT_FOUNDエラーが返る
    """
    deps = setup()

    with pytest.raises(ViewTokenError) as x:
        build(deps, RevokeAllViewTokens).run(OTHER, ViewSubject.artifact(AID))

    assert x.value.code == "TARGET_NOT_FOUND"


def test_管理者は他人の対象でも操作できる():
    """
    Scenario: 管理者は他人の対象でも操作できる
    When 対象の投稿者ではない管理者がこの操作を求める
    Then 拒まれずに操作できる
    """
    deps = setup(owner="publisher-2")

    got = build(deps, RevokeAllViewTokens).run(ADMIN, ViewSubject.artifact(AID))

    assert got.revoked == 0
