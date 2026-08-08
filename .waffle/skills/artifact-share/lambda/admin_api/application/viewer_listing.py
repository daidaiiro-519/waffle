"""プロジェクトの見え方を、閲覧の面へ書き直す。

一覧は共有アーティファクトの表示名を含むため、所属が変わったときだけでなく
表示名が変わったときにも書き直す必要がある。この「いつ書き直すか」の判断は
複数の操作にまたがるので、1か所に置く。

所属の正は共有アーティファクトの側にある。ここが書くのは、閲覧者へ見せるための
投影が2つ——プロジェクトの側に持つ所属の一覧と、閲覧の面が判じるための記録。
どちらも正から組み立て直せるので、失敗しても作り直せばよい。

投影だけを見て一覧を組み立てないのは、そこに表示名が無いため。
"""
from __future__ import annotations

from application.ports import Clock
from application.project_access import read_index
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort


def write_listing(artifacts: SharedArtifactRepository, projects: ProjectRepository,
                  viewer: ViewerSitePort, project) -> None:
    """閲覧者が見る一覧の中身を書き出す。

    雛形（index.html）はどのプロジェクトでも同じものを置き、この中身
    （index.json）だけがプロジェクトごとに変わる。雛形を直したときは
    全プロジェクトへ置き直す（CLIの反映の手順が担う）。

    共有アーティファクトの表示名を含むため、所属が変わったときだけでなく
    表示名が変わったときにも書き直す必要がある。

    Args:
        artifacts: 共有アーティファクトの保管。
        projects: プロジェクトの保管。
        viewer: 閲覧の面への書き出し口。
        project: 一覧を書き出すプロジェクト。

    Returns:
        なし。

    Raises:
        なし。
    """
    rows = []
    for artifact_id in projects.members_of(project.project_id.value):
        artifact = artifacts.find(artifact_id)
        if artifact is None or not artifact.status.is_published():
            continue          # 止まっているものは並べない（開けないため）
        rows.append({
            "artifactId": artifact_id,
            "name": artifact.display_name,
            "docType": artifact.descriptor.doc_type,
            "description": artifact.descriptor.description,
            "updatedAt": artifact.updated_at,
        })
    rows.sort(key=lambda r: r["updatedAt"], reverse=True)

    viewer.place_project_listing(project.project_id.value, project.display_name, rows)


def place_project_page(viewer: ViewerSitePort, project_id: str) -> None:
    """一覧ページを置く。中身は別に置く一覧から読む。

    Args:
        viewer: 閲覧の面への書き出し口。
        project_id: 一覧ページを置くプロジェクトの識別子。

    Returns:
        なし。

    Raises:
        なし。
    """
    viewer.place_project(project_id)


def sync_project(artifacts: SharedArtifactRepository, projects: ProjectRepository,
                 viewer: ViewerSitePort, clock: Clock, project, artifact_id: str,
                 member: bool) -> None:
    """所属の投影を書き直し、閲覧者向けの一覧も揃える。

    正は共有アーティファクトの側にある。ここが書くのは、閲覧者へ見せるために
    組み立て直せる投影であり、失敗しても作り直せる。

    Args:
        artifacts: 共有アーティファクトの保管。
        projects: プロジェクトの保管。
        viewer: 閲覧の面への書き出し口。
        clock: いまの時点を得る手段。
        project: 対象のプロジェクト。
        artifact_id: 出し入れした共有アーティファクトの識別子。
        member: 入れるなら真、外すなら偽。

    Returns:
        なし。

    Raises:
        なし。
    """
    ids = [a for a in projects.members_of(project.project_id.value) if a != artifact_id]
    if member:
        ids.append(artifact_id)
    projects.replace_members(project.project_id.value, ids)
    write_listing(artifacts, projects, viewer, project)


def refresh_listings(artifacts: SharedArtifactRepository, projects: ProjectRepository,
                     viewer: ViewerSitePort, artifact) -> None:
    """その共有アーティファクトが入っている全てのプロジェクトの一覧を書き直す。

    一覧は表示名を含むため、所属が変わったときだけでなく表示名が変わったときにも
    書き直す必要がある。

    Args:
        artifacts: 共有アーティファクトの保管。
        projects: プロジェクトの保管。
        viewer: 閲覧の面への書き出し口。
        artifact: 書き直すきっかけになった共有アーティファクト。

    Returns:
        なし。

    Raises:
        なし。
    """
    for project_id in artifact.projects:
        project = read_index(projects, project_id)
        if project:
            write_listing(artifacts, projects, viewer, project)
