"""まとめの顔ぶれと中身を確かめ、自分のものをどこへ入れるかを決める。

一覧で候補を絞り、中身を見て入れ先を決めるのは1つの場面なので、分けずに置く。
入れるには、いま何が入っているかが見えている必要がある。

中身は公開が止まっていても見られる。止めたものを再開するか外すかを決めるのに
中身が要るため。閲覧トークンはどちらにも含めない。

対象の仕様: uc-browse-projects
"""
from __future__ import annotations

from dataclasses import dataclass

from application.ports import Caller
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.viewer_site import ViewerSitePort
from application.project_access import read_index
from domain.project import PERSONAL, SHARED
from shared.errors import ProjectError



@dataclass(frozen=True)
class ProjectRow:
    """一覧の1行。入っているものの件数だけを添え、中身は詳しく見るときに読む。"""

    project_id: str
    name: str
    project_key: str
    scope: str
    status: str
    owner: str
    is_mine: bool
    artifact_count: int
    updated_at: int


@dataclass(frozen=True)
class ProjectSummary:
    """1つのまとめの概要。閲覧トークンそのものの値は持たない。"""

    project_id: str
    name: str
    project_key: str
    scope: str
    status: str
    owner: str
    is_mine: bool
    url: str


@dataclass(frozen=True)
class MemberRow:
    """まとめに入っている共有アーティファクト1件。"""

    artifact_id: str
    name: str
    doc_type: str
    status: str
    uploaded_by: str
    is_mine: bool
    updated_at: int


@dataclass(frozen=True)
class Projects:
    """出し入れできるまとめの一覧。"""

    projects: tuple[ProjectRow, ...]
    unreadable: int


@dataclass(frozen=True)
class ProjectDetail:
    """1つのまとめと、いま入っているもの。"""

    project: ProjectSummary
    artifacts: tuple[MemberRow, ...]

def _list_projects(projects: ProjectRepository, caller: Caller) -> Projects:
    """出し入れできるプロジェクトを並べる。閲覧トークンは含めない。

    自分が持ち主のものと、共有のものが並ぶ。管理者には全部が並ぶ。
    共有のものを並べるのは、そこへ自分のものを入れられるため。

    読めない記録は飛ばして残りを返し、飛ばした件数を添える。黙って
    落とすと、作ったはずのプロジェクトが消えたように見える。
    """
    found, unreadable = projects.all()
    rows = []
    for index in found:
        mine = index.owner.value == caller.id
        if not (caller.is_admin or mine or index.scope.is_shared()):
            continue
        rows.append(ProjectRow(
            project_id=index.project_id.value,
            name=index.display_name,
            project_key=index.project_key.value,
            scope=index.scope.value,
            status=index.status.value,
            owner=index.owner.value,
            is_mine=mine,
            artifact_count=len(projects.members_of(index.project_id.value)),
            updated_at=index.updated_at,
        ))
    return Projects(
        projects=tuple(sorted(rows, key=lambda r: r.updated_at, reverse=True)),
        unreadable=unreadable)


def _detail(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, caller: Caller, project_id: str) -> ProjectDetail:
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
    if not index.accepts_membership_from(caller.id, caller.is_admin):
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")

    rows = []
    for artifact_id in projects.members_of(index.project_id.value):
        meta = artifacts.find(artifact_id)
        if meta is None:
            continue
        rows.append(MemberRow(
            artifact_id=artifact_id,
            name=meta.display_name,
            doc_type=meta.descriptor.doc_type,
            status=meta.status.value,
            uploaded_by=meta.published_by.value,
            is_mine=meta.published_by.value == caller.id,
            updated_at=meta.updated_at,
        ))
    rows.sort(key=lambda r: r.updated_at, reverse=True)

    return ProjectDetail(
        project=ProjectSummary(
            project_id=index.project_id.value,
            name=index.display_name,
            project_key=index.project_key.value,
            scope=index.scope.value,
            status=index.status.value,
            owner=index.owner.value,
            is_mine=index.owner.value == caller.id,
            url=viewer.project_url(project_id),
        ),
        artifacts=tuple(rows),
    )


class BrowseProjects:
    """まとめの顔ぶれと中身を確かめ、自分のものをどこへ入れるかを決める。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._viewer = viewer

    def run(self, operation: str, caller: Caller, project_id: str = "") -> Projects | ProjectDetail:
        """このユースケースの唯一の入口。"""
        if operation == "list":
            return _list_projects(self._projects, caller)
        if operation == "detail":
            return _detail(self._artifacts, self._projects, self._viewer, caller, project_id)
        raise ValueError(f"知らない操作です: {operation}")
