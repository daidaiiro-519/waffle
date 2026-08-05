"""まとめて見てもらう範囲を、加える・外すで調整する。

加えられるのは自分が公開したものだけ。入れ先は、共有なら誰でも、個人なら持ち主
だけ。この2つの判定を両方通ったときにだけ成立する。

外しても、その共有アーティファクト自体とそれ自身の閲覧トークンは失われない。

対象の仕様: uc-assign-to-project
"""
from __future__ import annotations

from dataclasses import dataclass

from application.artifact_access import require_manageable
from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from application.project_access import require_writable
from application.viewer_listing import sync_project
from domain.shared_artifact import MAX_PROJECTS
from shared.errors import ManageError



@dataclass(frozen=True)
class ArtifactMembership:
    """出し入れした結果。いまどのプロジェクトに入っているかを返す。"""

    artifact_id: str
    projects: tuple[str, ...]

def _reject_over_limit() -> None:
    """上限を超えることを断る。判定は集約が持ち、ここは伝え方だけを決める。"""
    raise ManageError(
        "TOO_MANY_PROJECTS",
        f"1つのアーティファクトが入れるプロジェクトは{MAX_PROJECTS}件までです。"
        "どれかから外してから加えてください。")


def _write_membership(gate: ViewGatePort, artifact_id: str, project_ids: list[str]) -> None:
    """所属を、閲覧ゲートが読める形へ書き出す。

    上限を超えるものは書かずに拒む。黙って書くと、超えた分は閲覧ゲートから
    見えないまま所属したことになり、投稿者には成功が返って閲覧者だけが
    開けない。原因の分からない不具合になるため、ここで止める。
    """
    if len(project_ids) > MAX_PROJECTS:   # 最後の守り。ここへ来る前に弾かれているはず
        _reject_over_limit()
    gate.set_membership(artifact_id, project_ids)


def _assign(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, artifact_id: str, project_id: str) -> ArtifactMembership:
    """プロジェクトへ加える。人の明示的な操作でのみ成立する。

    加えられるのは自分が公開したものだけ。入れ先は、共有なら誰でも、
    個人なら持ち主だけ。この2つの判定を両方通ったときにだけ成立する。
    """
    artifact = require_manageable(artifacts, caller, artifact_id)
    if artifact.published_by.value != caller.id and not caller.is_admin:
        # 他人のものを、勝手に誰かの見せる範囲へ入れられない
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。")

    index = require_writable(projects, caller, project_id)

    # 書き始める前に確かめる。記録を書いてから拒むと、記録と閲覧ゲート用の
    # 投影が食い違ったまま残る
    if not artifact.can_join(project_id):
        _reject_over_limit()

    joined = artifact.joined(project_id, clock())   # 重ねて加えても二重にならない
    belongs = list(joined.projects)
    artifacts.save(joined)
    _write_membership(gate, artifact_id, belongs)
    sync_project(artifacts, projects, viewer, clock, index, artifact_id, member=True)

    return ArtifactMembership(artifact_id=artifact_id, projects=tuple(belongs))


def _unassign(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, artifact_id: str, project_id: str) -> ArtifactMembership:
    """プロジェクトから外す。共有アーティファクト自体は個別の閲覧トークンで開けるまま残る。"""
    artifact = require_manageable(artifacts, caller, artifact_id)
    if artifact.published_by.value != caller.id and not caller.is_admin:
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。")

    index = require_writable(projects, caller, project_id)

    left = artifact.left(project_id, clock())
    belongs = list(left.projects)
    artifacts.save(left)
    _write_membership(gate, artifact_id, belongs)
    sync_project(artifacts, projects, viewer, clock, index, artifact_id, member=False)

    return ArtifactMembership(artifact_id=artifact_id, projects=tuple(belongs))


class AssignArtifactToProject:
    """まとめて見てもらう範囲を、加える・外すで調整する。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._viewer = viewer
        self._gate = gate
        self._clock = clock

    def run(self, operation: str, caller: Caller, artifact_id: str, project_id: str) -> ArtifactMembership:
        """このユースケースの唯一の入口。"""
        if operation == "assign":
            return _assign(self._artifacts, self._projects, self._viewer, self._gate, self._clock, caller, artifact_id, project_id)
        if operation == "unassign":
            return _unassign(self._artifacts, self._projects, self._viewer, self._gate, self._clock, caller, artifact_id, project_id)
        raise ValueError(f"知らない操作です: {operation}")
