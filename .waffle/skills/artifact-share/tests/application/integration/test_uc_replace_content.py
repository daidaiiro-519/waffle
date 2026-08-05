"""入れ替えの操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

途中で倒れても、元の中身が生きていること。直すたびに失われるなら、
指摘を受けて直すという往復そのものが成り立たない。

対象の仕様: uc-replace-content（操作保証）
"""
import json

import pytest

from manage_setup import HTML, ME, setup
from application.usecases.replace_artifact_content import ReplaceArtifactContent
from application.usecases.suspend_artifact import SuspendArtifact
from shared.errors import ManageError
from usecase_builder import build


def test_失敗しても元の中身が生きている():
    """
    Scenario: 失敗しても元の中身が生きている
    Given 入れ替えの途中で拒まれる条件が成立している
    When 中身を入れ替えようとする
    Then 元の中身がそのまま見られる
    And コメントも失われていない
    """
    deps, r = setup()
    deps.store.put(f"comments/{r.artifact_id}/1700000010-abcd1234.json",
                   json.dumps({"kind": "comment", "author": "田中",
                               "decision": "comment", "body": "意見",
                               "parentId": None,
                               "postedAt": "2026-07-01T10:00:00Z"},
                              ensure_ascii=False), "application/json")
    before = deps.store.get(f"p/{r.artifact_id}/content.html")
    build(deps, SuspendArtifact).run(ME, r.artifact_id)   # 拒まれる条件を作る

    with pytest.raises(ManageError):
        build(deps, ReplaceArtifactContent).run(
            ME, r.artifact_id, HTML.replace("本文", "直した"))

    assert deps.store.get(f"p/{r.artifact_id}/content.html") == before
    assert len(deps.store.list(f"comments/{r.artifact_id}/")) == 1
