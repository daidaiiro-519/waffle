"""再開の操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

途中で倒れたときに、中途半端に開ける状態が生まれないこと。

対象の仕様: uc-resume-artifact（操作保証）
"""
import pytest

from manage_setup import SOMEONE_ELSE, ME, meta_of, setup
from application.usecases.resume_artifact import ResumeArtifact
from application.usecases.suspend_artifact import SuspendArtifact
from shared.errors import ManageError
from usecase_builder import build


def test_失敗しても閲覧トークンは変わらない():
    """
    Scenario: 失敗しても閲覧トークンは変わらない
    Given 再開の途中で拒まれる条件が成立している
    When 再開しようとする
    Then 共有アーティファクトAは停止したままである
    And 新しい閲覧トークンは発行されていない
    """
    deps, r = setup()
    build(deps, SuspendArtifact).run(ME, r.artifact_id)
    before = dict(deps.keys.written)

    with pytest.raises(ManageError):
        build(deps, ResumeArtifact).run(SOMEONE_ELSE, r.artifact_id)

    assert meta_of(deps, r.artifact_id)["status"] == "disabled"
    assert deps.keys.written == before
