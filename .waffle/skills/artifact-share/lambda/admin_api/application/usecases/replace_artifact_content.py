"""指摘を受けて直したものを、同じ相手に同じ共有URLで見てもらう。

中身だけを丸ごと差し替える。共有URLも閲覧トークンも変えないので、渡した相手は
何もしなくてよい。差し替えたことは、反応と同じ並びに1件の印として残す。

対象の仕様: uc-replace-content
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from application.artifact_access import require_manageable
from domain.value_objects.artifact_content import ContentFingerprint
from domain.value_objects.shared_artifact import ArtifactDescriptor
from application.ports import Caller, Clock
from application.artifact_access import NOT_FOUND
from application.ports.comment_repository import CommentRepository
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.viewer_site import ViewerSitePort
from application.viewer_listing import refresh_listings
from domain.services.html_inspection import inspect_html
from shared.errors import ManageError



@dataclass(frozen=True)
class ReplacedArtifactContent:
    """差し替えた結果。共有URLは変わらず、外部への参照の件数を添える。"""

    artifact_id: str
    url: str
    external_refs: int

def _replace_content(artifacts: SharedArtifactRepository, projects: ProjectRepository, comments: CommentRepository, viewer: ViewerSitePort, clock: Clock, caller: Caller, artifact_id: str, html: str) -> ReplacedArtifactContent:
    """中身だけを入れ替える。URL・トークン・これまでの反応は保つ。

    入れ替えた時点を区切りとして反応の並びに残す。これより前の指摘が
    入れ替え前のものだと読み取れるようにするため。
    """
    artifact = require_manageable(artifacts, caller, artifact_id)
    if artifact.published_by.value != caller.id:
        # 管理者であっても他人の中身には手を出せない。集まったコメントが
        # 何に対する反応かを、投稿者の知らないうちに変えないため。
        # ここで「見つからない」と返さないのは、管理者は一覧でその存在を
        # 既に知っており、嘘になるから
        raise ManageError("NOT_THE_PUBLISHER",
                          "中身を差し替えられるのは、公開した本人だけです。")
    if not artifact.status.is_published():
        raise ManageError("NOT_PUBLISHED", "公開が止まっています。先に再公開してください。")

    if not html or not html.strip():
        raise ManageError("EMPTY_CONTENT", "中身が空です。")

    found = inspect_html(html)
    now = clock()

    viewer.replace_artifact_content(artifact_id, html)

    # 差し替えの区切り。反応と同じ並びに載る1件の印として残す
    comments.add_replacement_divider(artifact_id, now)

    # 読み取れたときだけ差し替える。読み取れなければ、それまでの目印を保つ
    descriptor = artifact.descriptor
    if found.detected:
        descriptor = replace(ArtifactDescriptor.of(found), title=artifact.display_name)
    updated = artifact.with_content(ContentFingerprint.of(html), descriptor,
                                    found.external_refs, now)
    artifacts.save(updated)
    refresh_listings(artifacts, projects, viewer, updated)

    return ReplacedArtifactContent(artifact_id=artifact_id,
                                   url=viewer.artifact_url(artifact_id),
                                   external_refs=found.external_refs)


class ReplaceArtifactContent:
    """指摘を受けて直したものを、同じ相手に同じ共有URLで見てもらう。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, comments: CommentRepository, viewer: ViewerSitePort, clock: Clock) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._comments = comments
        self._viewer = viewer
        self._clock = clock

    def run(self, caller: Caller, artifact_id: str, html: str) -> ReplacedArtifactContent:
        """このユースケースの唯一の入口。"""
        return _replace_content(self._artifacts, self._projects, self._comments, self._viewer, self._clock, caller, artifact_id, html)
