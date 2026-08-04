"""まとめて見てもらう範囲を、加える・外すで調整する。

加えられるのは自分が公開したものだけ。入れ先は、共有なら誰でも、個人なら持ち主
だけ。この2つの判定を両方通ったときにだけ成立する。

外しても、その共有アーティファクト自体とそれ自身の閲覧トークンは失われない。

対象の仕様: uc-assign-to-project
"""
from __future__ import annotations

from application.artifact_access import require_manageable
from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from application.project_access import require_writable
from application.viewer_listing import sync_project
from domain.publication import MAX_PROJECTS_PER_ARTIFACT, within_project_limit
from shared.errors import ManageError


def _write_meta(artifacts: SharedArtifactRepository, clock: Clock, meta: dict) -> None:
    meta["updatedAt"] = clock()
    artifacts.save(meta)


def _require_within_limit(project_ids: list[str]) -> None:
    """上限を超えていないかを、書き始める前に確かめる。"""
    if not within_project_limit(project_ids):
        raise ManageError(
            "TOO_MANY_PROJECTS",
            f"1つのアーティファクトが入れるプロジェクトは{MAX_PROJECTS_PER_ARTIFACT}件までです。"
            "どれかから外してから加えてください。")


def _write_membership(gate: ViewGatePort, artifact_id: str, project_ids: list[str]) -> None:
    """所属を、閲覧ゲートが読める形へ書き出す。

    上限を超えるものは書かずに拒む。黙って書くと、超えた分は閲覧ゲートから
    見えないまま所属したことになり、投稿者には成功が返って閲覧者だけが
    開けない。原因の分からない不具合になるため、ここで止める。
    """
    _require_within_limit(project_ids)     # 最後の守り。ここへ来る前に弾かれているはず
    gate.set_membership(artifact_id, project_ids)


def assign(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, artifact_id: str, project_id: str) -> dict:
    """プロジェクトへ加える。人の明示的な操作でのみ成立する。

    加えられるのは自分が公開したものだけ。入れ先は、共有なら誰でも、
    個人なら持ち主だけ。この2つの判定を両方通ったときにだけ成立する。
    """
    meta = require_manageable(artifacts, caller, artifact_id)
    if meta.get("uploadedBy") != caller.id and not caller.is_admin:
        # 他人のものを、勝手に誰かの見せる範囲へ入れられない
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。")

    index = require_writable(projects, caller, project_id)

    belongs = list(meta.get("projects") or [])
    if project_id not in belongs:               # 重ねて加えても二重にならない
        belongs.append(project_id)
    # 書き始める前に確かめる。索引を書いてから拒むと、索引と閲覧ゲート用の
    # 記録が食い違ったまま残る
    _require_within_limit(belongs)

    meta["projects"] = belongs
    _write_meta(artifacts, clock, meta)
    _write_membership(gate, artifact_id, belongs)
    sync_project(artifacts, projects, viewer, clock, index, artifact_id, member=True)

    return {"artifactId": artifact_id, "projects": belongs}


def unassign(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, artifact_id: str, project_id: str) -> dict:
    """プロジェクトから外す。共有アーティファクト自体は個別の閲覧トークンで開けるまま残る。"""
    meta = require_manageable(artifacts, caller, artifact_id)
    if meta.get("uploadedBy") != caller.id and not caller.is_admin:
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。")

    index = require_writable(projects, caller, project_id)

    belongs = [p for p in (meta.get("projects") or []) if p != project_id]
    meta["projects"] = belongs
    _write_meta(artifacts, clock, meta)
    _write_membership(gate, artifact_id, belongs)
    sync_project(artifacts, projects, viewer, clock, index, artifact_id, member=False)

    return {"artifactId": artifact_id, "projects": belongs}
