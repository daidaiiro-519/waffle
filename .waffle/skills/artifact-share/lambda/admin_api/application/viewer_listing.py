"""プロジェクトの見え方を、閲覧の面へ書き直す。

一覧は共有アーティファクトの表示名を含むため、所属が変わったときだけでなく
表示名が変わったときにも書き直す必要がある。この「いつ書き直すか」の判断は
複数の操作にまたがるので、1か所に置く。

所属は2か所に持つ。人へ見せるための正は索引で、閲覧の面が判じるための投影は
別に置く。投影だけを見て一覧を組み立てないのは、表示名を持たないため。
"""
from __future__ import annotations

from application.ports import Clock
from application.project_access import read_index
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from domain.publication import is_published


def write_listing(artifacts: SharedArtifactRepository, viewer: ViewerSitePort, index: dict) -> None:
    """閲覧者が見る一覧の中身を書き出す。

    雛形（index.html）はどのプロジェクトでも同じものを置き、この中身
    （index.json）だけがプロジェクトごとに変わる。雛形を直したときは
    全プロジェクトへ置き直す（CLIの反映の手順が担う）。

    共有アーティファクトの表示名を含むため、所属が変わったときだけでなく
    表示名が変わったときにも書き直す必要がある。
    """
    rows = []
    for artifact_id in index.get("memberArtifactIds", []):
        meta = artifacts.find(artifact_id)
        if meta is None:
            continue
        if not is_published(meta):
            continue          # 止まっているものは並べない（開けないため）
        rows.append({
            "artifactId": artifact_id,
            "name": meta.get("name", ""),
            "docType": meta.get("docType", ""),
            "description": meta.get("description", ""),
            "updatedAt": meta.get("updatedAt", 0),
        })
    rows.sort(key=lambda r: r["updatedAt"], reverse=True)

    viewer.place_project_listing(index["projectId"], index.get("displayName", ""), rows)


def place_project_page(viewer: ViewerSitePort, project_id: str) -> None:
    """一覧ページを置く。中身は別に置く一覧から読む。"""
    viewer.place_project(project_id)


def sync_project(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, clock: Clock, index: dict, artifact_id: str, member: bool) -> None:
    """プロジェクトの索引と、閲覧者が見る一覧を揃える。

    所属は索引（人へ見せるための正）と、閲覧ゲートが判じるための投影の
    2か所に持つ。片方だけを書く経路を作らないため、出し入れのたびに
    ここを通す。
    """
    ids = [a for a in index.get("memberArtifactIds", []) if a != artifact_id]
    if member:
        ids.append(artifact_id)
    index["memberArtifactIds"] = ids
    index["updatedAt"] = clock()
    projects.save(index)
    write_listing(artifacts, viewer, index)


def refresh_listings(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, meta: dict) -> None:
    """このアーティファクトが入っている全プロジェクトの一覧を書き直す。

    一覧は表示名を含むため、差し替えで名前が変わったときに書き直さないと、
    閲覧者へ古い名前が見え続ける。
    """
    for project_id in meta.get("projects") or []:
        index = read_index(projects, project_id)
        if index:
            write_listing(artifacts, viewer, index)
