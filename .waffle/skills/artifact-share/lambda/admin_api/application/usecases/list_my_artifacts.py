"""手入れできる共有アーティファクトを見渡し、次に何を直すかを決める。

投稿者には自分が公開したものだけ、管理者には全員のものが並ぶ。誰が公開したかを
添えるのは、管理者が引き継ぎ先を決めるのに要るため。

読めない記録は飛ばして残りを返し、飛ばした件数を添える。黙って落とさないのは、
投稿者が「公開したはずのものが消えた」と気づけないため。

対象の仕様: uc-list-my-artifacts
"""
from __future__ import annotations

from application.ports import Caller
from application.ports.comment_repository import CommentRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository


def _list_artifacts(artifacts: SharedArtifactRepository, comments: CommentRepository, caller: Caller) -> dict:
    """扱えるものを新しい順に並べる。トークンは含めない。

    投稿者には自分が公開したものだけ、管理者には全員のものが並ぶ。
    誰が公開したかを添えるのは、管理者が引き継ぎ先を決めるのに要るため。

    読めない記録は飛ばして残りを返し、飛ばした件数を添える。1件の不具合で
    一覧がすべて空になるのを避ける。黙って落とさないのは、投稿者が
    「公開したはずのものが消えた」と気づけないため（コメントの読み出しと
    同じ扱い）。
    """
    found, unreadable = artifacts.all()
    rows = []
    for artifact in found:
        if not artifact.manageable_by(caller.id, caller.is_admin):
            continue
        rows.append({
            "artifactId": artifact.artifact_id.value,
            "name": artifact.display_name,
            "status": artifact.status.value,
            "docType": artifact.descriptor.doc_type,
            "description": artifact.descriptor.description,
            "tags": list(artifact.descriptor.labels),
            "projects": list(artifact.projects),
            "uploadedBy": artifact.published_by.value,
            "updatedAt": artifact.updated_at,
            "comments": comments.count_of(artifact.artifact_id.value),
        })
    return {"artifacts": sorted(rows, key=lambda r: r["updatedAt"], reverse=True),
            "unreadable": unreadable}


class ListMyArtifacts:
    """手入れできる共有アーティファクトを見渡し、次に何を直すかを決める。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, comments: CommentRepository) -> None:
        self._artifacts = artifacts
        self._comments = comments

    def run(self, caller: Caller) -> dict:
        """このユースケースの唯一の入口。"""
        return _list_artifacts(self._artifacts, self._comments, caller)
