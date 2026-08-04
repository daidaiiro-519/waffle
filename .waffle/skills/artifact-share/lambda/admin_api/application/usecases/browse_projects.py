"""まとめの顔ぶれと中身を確かめ、自分のものをどこへ入れるかを決める。

一覧で候補を絞り、中身を見て入れ先を決めるのは1つの場面なので、分けずに置く。
入れるには、いま何が入っているかが見えている必要がある。

中身は公開が止まっていても見られる。止めたものを再開するか外すかを決めるのに
中身が要るため。閲覧トークンはどちらにも含めない。

対象の仕様: uc-browse-projects
"""
from __future__ import annotations

from application.ports import Caller
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.viewer_site import ViewerSitePort
from application.project_access import read_index
from domain.publication import PERSONAL, SHARED
from shared.errors import ProjectError


def _list_projects(projects: ProjectRepository, caller: Caller) -> dict:
    """出し入れできるプロジェクトを並べる。閲覧トークンは含めない。

    自分が持ち主のものと、共有のものが並ぶ。管理者には全部が並ぶ。
    共有のものを並べるのは、そこへ自分のものを入れられるため。

    読めない記録は飛ばして残りを返し、飛ばした件数を添える。黙って
    落とすと、作ったはずのプロジェクトが消えたように見える。
    """
    found, unreadable = projects.all()
    rows = []
    for index in found:
        mine = index.get("owner") == caller.id
        if not (caller.is_admin or mine or index.get("scope") == SHARED):
            continue
        rows.append({
            "projectId": index.get("projectId", ""),
            "name": index.get("displayName", ""),
            "projectKey": index.get("projectKey", ""),
            "scope": index.get("scope", PERSONAL),
            "status": index.get("status", ""),
            "owner": index.get("owner", ""),
            "isMine": mine,
            "artifactCount": len(index.get("memberArtifactIds", [])),
            "updatedAt": index.get("updatedAt", 0),
        })
    return {"projects": sorted(rows, key=lambda r: r["updatedAt"], reverse=True),
            "unreadable": unreadable}


def _detail(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, caller: Caller, project_id: str) -> dict:
    """プロジェクトと、いま入っている共有アーティファクトを返す。

    見られるのは、そこへ自分のものを出し入れできる人（持ち主・管理者・
    共有なら招かれた投稿者）。入れるには、いま何が入っているかが
    見えている必要がある。

    公開が止まっていても見られる。止めたものを再開するか外すかを決めるのに
    中身が要るため。閲覧トークンは含めない。
    """
    index = read_index(projects, project_id)
    if not index:
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")
    if not (caller.is_admin or index.get("owner") == caller.id
            or index.get("scope") == SHARED):
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")

    rows = []
    for artifact_id in index.get("memberArtifactIds", []):
        meta = artifacts.find(artifact_id)
        if meta is None:
            continue
        rows.append({
            "artifactId": artifact_id,
            "name": meta.get("name", ""),
            "docType": meta.get("docType", ""),
            "status": meta.get("status", ""),
            "uploadedBy": meta.get("uploadedBy", ""),
            "isMine": meta.get("uploadedBy") == caller.id,
            "updatedAt": meta.get("updatedAt", 0),
        })
    rows.sort(key=lambda r: r["updatedAt"], reverse=True)

    return {
        "project": {
            "projectId": index.get("projectId", ""),
            "name": index.get("displayName", ""),
            "projectKey": index.get("projectKey", ""),
            "scope": index.get("scope", PERSONAL),
            "status": index.get("status", ""),
            "owner": index.get("owner", ""),
            "isMine": index.get("owner") == caller.id,
            "url": viewer.project_url(project_id),
        },
        "artifacts": rows,
    }


class BrowseProjects:
    """まとめの顔ぶれと中身を確かめ、自分のものをどこへ入れるかを決める。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._viewer = viewer

    def run(self, operation: str, caller: Caller, project_id: str = "") -> dict:
        """このユースケースの唯一の入口。"""
        if operation == "list":
            return _list_projects(self._projects, caller)
        if operation == "detail":
            return _detail(self._artifacts, self._projects, self._viewer, caller, project_id)
        raise ValueError(f"知らない操作です: {operation}")
