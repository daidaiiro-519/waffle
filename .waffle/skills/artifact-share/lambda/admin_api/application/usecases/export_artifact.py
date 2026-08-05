"""この環境が無くなっても、渡したものと返ってきたものが手元に残る状態にする。

中身と、それまでに寄せられた反応をまとめて返す。読むだけの操作で、公開状態も
閲覧トークンも反応も変えない。公開を止める操作と切り離してあるのは、止めるか
どうかを決める前に中身を確かめたい場面があるため。

閲覧トークンは含めない。取り出したものが渡り歩いても、それだけで開ける状態に
ならないようにする。

対象の仕様: uc-export-artifact
"""
from __future__ import annotations

from dataclasses import dataclass

from application.artifact_access import require_manageable
from application.ports import Caller
from application.ports.comment_repository import CommentRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.viewer_site import ViewerSitePort
from application.usecases.read_comments import ReadComments



@dataclass(frozen=True)
class ExportedArtifact:
    """取り出した中身と、それまでに寄せられた反応。

    閲覧トークンは含めない。取り出したものが渡り歩いても、それだけで開ける
    状態にならないようにする。
    """

    artifact_id: str
    name: str
    doc_type: str
    document_id: str
    description: str
    tags: tuple[str, ...]
    status: str
    published_at: int
    updated_at: int
    content: str
    comments: tuple[dict, ...]
    unreadable: int

def _export(artifacts: SharedArtifactRepository, comments: CommentRepository, viewer: ViewerSitePort, caller: Caller, artifact_id: str) -> ExportedArtifact:
    """中身と、それまでに寄せられたコメントをまとめて返す。

    読むだけの操作で、公開状態も閲覧トークンもコメントも変えない。公開を
    止める操作と切り離してあるのは、止めるかどうかを決める前に中身を
    確かめたい場面があるため。

    1つのファイルにまとめるのは画面側が行う。ここで保管へ書くと、取り出しが
    読むだけの操作でなくなる。

    閲覧トークンは含めない。取り出したものが渡り歩いても、それだけで開ける
    状態にならないようにする。
    """
    artifact = require_manageable(artifacts, caller, artifact_id)

    content = viewer.read_artifact_content(artifact_id)

    found = ReadComments(artifacts, comments).run(caller, artifact_id)

    return ExportedArtifact(
        artifact_id=artifact_id,
        name=artifact.display_name,
        doc_type=artifact.descriptor.doc_type,
        document_id=artifact.descriptor.document_id,
        description=artifact.descriptor.description,
        tags=artifact.descriptor.labels,
        status=artifact.status.value,
        published_at=artifact.published_at,
        updated_at=artifact.updated_at,
        content=content,
        comments=found.comments,
        unreadable=found.unreadable,
    )


class ExportArtifact:
    """この環境が無くなっても、渡したものと返ってきたものが手元に残る状態にする。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, comments: CommentRepository, viewer: ViewerSitePort) -> None:
        self._artifacts = artifacts
        self._comments = comments
        self._viewer = viewer

    def run(self, caller: Caller, artifact_id: str) -> ExportedArtifact:
        """このユースケースの唯一の入口。"""
        return _export(self._artifacts, self._comments, self._viewer, caller, artifact_id)
