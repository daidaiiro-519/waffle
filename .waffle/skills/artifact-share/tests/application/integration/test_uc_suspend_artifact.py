"""止める操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

止めるのは見せるのをやめることであって、失うことではない。止めた後でも
手元へ取り出せることが、安心して止められる前提になる。

対象の仕様: uc-suspend-artifact（操作保証）
"""
import json

from manage_setup import ME, setup
from application.usecases.export_artifact import ExportArtifact
from application.usecases.suspend_artifact import SuspendArtifact
from usecase_builder import build


def _comment(deps, artifact_id, at, author, body):
    deps.store.put(
        f"comments/{artifact_id}/{at}-abcd1234.json",
        json.dumps({"kind": "comment", "author": author, "decision": "comment",
                    "body": body, "parentId": None,
                    "postedAt": "2026-07-01T10:00:00Z"}, ensure_ascii=False),
        "application/json")


def test_止めた後も取り出せる():
    """
    Scenario: 止めた後も取り出せる
    Given 共有アーティファクトAが公開停止されている
    When 中身とコメントを手元へ取り出す
    Then 停止前と同じものが得られる
    """
    deps, r = setup()
    _comment(deps, r.artifact_id, 1, "田中", "意見")
    before = build(deps, ExportArtifact).run(ME, r.artifact_id)
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    after = build(deps, ExportArtifact).run(ME, r.artifact_id)

    assert after.content == before.content
    assert after.comments == before.comments
    assert after.artifact_id == before.artifact_id
