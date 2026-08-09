"""取り出しの操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

読むだけの操作なので、何度求めても同じものが返り、保管は動かない。

対象の仕様: uc-export-artifact（操作保証）
"""
import json

from manage_setup import ME, setup
from application.usecases.export_artifact import ExportArtifact
from usecase_builder import build


def test_何度取り出しても同じものが返る():
    """
    Scenario: 何度取り出しても同じものが返る
    Given Aが公開されている
    When 続けて2回取り出しを求める
    Then 2回とも同じ中身とコメントが返る
    And 保管されているものは何も変わっていない
    """
    deps, r = setup()
    deps.store.put(f"comments/{r.artifact_id}/1700000010-abcd1234.json",
                   json.dumps({"kind": "comment", "author": "田中",
                               "decision": "comment", "body": "意見",
                               "parentId": None,
                               "postedAt": "2026-07-01T10:00:00Z"},
                              ensure_ascii=False), "application/json")
    objects_before = json.dumps(deps.store.objects, ensure_ascii=False, sort_keys=True)
    keys_before = dict(deps.keys.written)

    first = build(deps, ExportArtifact).run(ME, r.artifact_id)
    second = build(deps, ExportArtifact).run(ME, r.artifact_id)

    assert second == first
    assert json.dumps(deps.store.objects, ensure_ascii=False,
                      sort_keys=True) == objects_before
    assert deps.keys.written == keys_before
