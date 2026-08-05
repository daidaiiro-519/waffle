"""コメントを読む操作が守る約束を確かめる。

対象の仕様: uc-read-comments（操作保証）
"""
import json

from manage_setup import ME, setup
from application.usecases.read_comments import ReadComments
from usecase_builder import build


def test_閲覧トークンを控えていなくても読める():
    """
    Scenario: 閲覧トークンを控えていなくても読める
    Given Xは公開時に示された閲覧トークンを控えていない
    When XがAのコメントを読もうとする
    Then 読める
    And 閲覧トークンの入力は求められない

    投稿者であることは名簿で分かる。閲覧トークンは渡す相手のための鍵であって、
    自分のものを見るための鍵ではない。
    """
    deps, r = setup()
    deps.store.put(f"comments/{r.artifact_id}/1700000010-abcd1234.json",
                   json.dumps({"kind": "comment", "author": "田中",
                               "decision": "comment", "body": "意見",
                               "parentId": None,
                               "postedAt": "2026-07-01T10:00:00Z"},
                              ensure_ascii=False), "application/json")

    # 閲覧トークンを一切渡さずに読む
    got = build(deps, ReadComments).run(ME, r.artifact_id)

    assert [c["author"] for c in got.comments] == ["田中"]
