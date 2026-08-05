"""引き継ぎの操作が守る約束を確かめる。

対象の仕様: uc-transfer-artifact（操作保証）
"""
import json
from transfer_setup import ADMIN, Y, setup
from application.usecases.transfer_artifact import TransferArtifact
from usecase_builder import build


def test_コメントは引き継ぎをまたいで残る():
    """
    Scenario: コメントは引き継ぎをまたいで残る
    Given 共有アーティファクトAにコメントが2件付いている
    When 管理者がAの投稿者をYへ移す
    Then Aのコメントは2件のまま残っている
    And 区切りの記録は増えていない
    """
    deps, r = setup()
    for at, author in ((1_700_000_010, "田中"), (1_700_000_020, "佐藤")):
        deps.store.put(f"comments/{r.artifact_id}/{at}-abcd1234.json",
                       json.dumps({"kind": "comment", "author": author,
                                   "decision": "comment", "body": "意見",
                                   "parentId": None,
                                   "postedAt": "2026-07-01T10:00:00Z"},
                                  ensure_ascii=False), "application/json")

    build(deps, TransferArtifact).run(ADMIN, r.artifact_id, Y.id)

    entries = [json.loads(deps.store.get(k))
               for k in deps.store.list(f"comments/{r.artifact_id}/")]
    assert [e["kind"] for e in entries] == ["comment", "comment"]
