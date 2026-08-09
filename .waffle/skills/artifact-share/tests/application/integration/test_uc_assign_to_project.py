"""出し入れの操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

同じものを重ねて加えても、二重に入ることも拒まれることもない。人が同じ操作を
繰り返しても壊れないことが、この操作を安心して使える前提になる。

対象の仕様: uc-assign-to-project（操作保証）
"""
from manage_setup import ME, meta_of, with_project
from application.usecases.assign_artifact_to_project import AssignArtifactToProject
from usecase_builder import build


def test_重ねて加えても一度分と同じ():
    """
    Scenario: 重ねて加えても一度分と同じ
    Given 共有アーティファクトAがPに入っている
    When 共有アーティファクトAをPへもう一度加える
    Then 共有アーティファクトAは1件としてだけ入っている
    And 拒まれることもない
    """
    deps, r, pid = with_project("PERSONAL")
    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    assert meta_of(deps, r.artifact_id)["projects"] == [pid]
    assert deps.keys.written[f"pp:{r.artifact_id}"] == pid
