"""指摘を受けて直したものを、同じ相手に同じ共有URLで見てもらう。

中身だけを丸ごと差し替える。共有URLも閲覧トークンも変えないので、渡した相手は
何もしなくてよい。差し替えたことは、反応と同じ並びに1件の印として残す。

対象の仕様: uc-replace-content
"""
from __future__ import annotations

from application.artifact_access import require_manageable
from application.ports import Caller, Clock
from application.artifact_access import NOT_FOUND
from application.ports.comment_repository import CommentRepository
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.viewer_site import ViewerSitePort
from application.viewer_listing import refresh_listings
from domain.html_inspection import inspect_html
from domain.publication import is_published
from shared.errors import ManageError


def _write_meta(artifacts: SharedArtifactRepository, clock: Clock, meta: dict) -> None:
    meta["updatedAt"] = clock()
    artifacts.save(meta)


def _require_published(meta: dict) -> None:
    if not is_published(meta):
        raise ManageError("NOT_PUBLISHED", "公開が止まっています。先に再公開してください。")


def replace_content(artifacts: SharedArtifactRepository, projects: ProjectRepository, comments: CommentRepository, viewer: ViewerSitePort, clock: Clock, caller: Caller, artifact_id: str, html: str) -> dict:
    """中身だけを入れ替える。URL・トークン・これまでの反応は保つ。

    入れ替えた時点を区切りとして反応の並びに残す。これより前の指摘が
    入れ替え前のものだと読み取れるようにするため。
    """
    meta = require_manageable(artifacts, caller, artifact_id)
    if meta.get("uploadedBy") != caller.id:
        # 管理者であっても他人の中身には手を出せない。集まったコメントが
        # 何に対する反応かを、投稿者の知らないうちに変えないため。
        # ここで「見つからない」と返さないのは、管理者は一覧でその存在を
        # 既に知っており、嘘になるから
        raise ManageError("NOT_THE_PUBLISHER",
                          "中身を差し替えられるのは、公開した本人だけです。")
    _require_published(meta)

    if not html or not html.strip():
        raise ManageError("EMPTY_CONTENT", "中身が空です。")

    found = inspect_html(html)
    now = clock()

    viewer.replace_artifact_content(artifact_id, html)

    # 差し替えの区切り。反応と同じ並びに載る1件の印として残す
    comments.add_replacement_divider(artifact_id, now)

    if found["detected"]:
        meta.update({
            "docType": found["docType"],
            "documentId": found["documentId"],
            "description": found["description"],
            "tags": found["tags"],
        })
    meta["externalRefs"] = found["externalRefs"]
    _write_meta(artifacts, clock, meta)
    refresh_listings(artifacts, projects, viewer, meta)

    return {"artifactId": artifact_id, "url": viewer.artifact_url(artifact_id),
            "externalRefs": found["externalRefs"]}
