"""手入れできる共有アーティファクトを見渡し、次に何を直すかを決める。

投稿者には自分が公開したものだけ、管理者には全員のものが並ぶ。誰が公開したかを
添えるのは、管理者が引き継ぎ先を決めるのに要るため。

読めない記録は飛ばして残りを返し、飛ばした件数を添える。黙って落とさないのは、
投稿者が「公開したはずのものが消えた」と気づけないため。

対象の仕様: uc-list-my-artifacts
"""
from __future__ import annotations

from dataclasses import dataclass

from application.ports import Caller, Clock
from application.ports.comment_repository import CommentRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from domain import view_token



@dataclass(frozen=True)
class ArtifactRow:
    """一覧の1行。閲覧トークンそのものの値は持たない。"""

    artifact_id: str
    name: str
    status: str
    doc_type: str
    description: str
    tags: tuple[str, ...]
    projects: tuple[str, ...]
    uploaded_by: str
    updated_at: int
    comments: int
    distributions: int


@dataclass(frozen=True)
class MyArtifacts:
    """見渡した結果。読めなかった件数を添えるのは、黙って落とさないため。"""

    artifacts: tuple[ArtifactRow, ...]
    unreadable: int

def _list_artifacts(artifacts: SharedArtifactRepository, comments: CommentRepository, clock: Clock, caller: Caller) -> MyArtifacts:
    """扱えるものを新しい順に並べる。トークンは含めない。

    投稿者には自分が公開したものだけ、管理者には全員のものが並ぶ。
    誰が公開したかを添えるのは、管理者が引き継ぎ先を決めるのに要るため。

    読めない記録は飛ばして残りを返し、飛ばした件数を添える。1件の不具合で
    一覧がすべて空になるのを避ける。黙って落とさないのは、投稿者が
    「公開したはずのものが消えた」と気づけないため（コメントの読み出しと
    同じ扱い）。
    """
    now = clock()
    found, unreadable = artifacts.all()
    rows = []
    for artifact in found:
        if not artifact.manageable_by(caller.id, caller.is_admin):
            continue
        rows.append(ArtifactRow(
            artifact_id=artifact.artifact_id.value,
            name=artifact.display_name,
            status=artifact.status.value,
            doc_type=artifact.descriptor.doc_type,
            description=artifact.descriptor.description,
            tags=artifact.descriptor.labels,
            projects=artifact.projects,
            uploaded_by=artifact.published_by.value,
            updated_at=artifact.updated_at,
            comments=comments.count_of(artifact.artifact_id.value),
            # 数えるのは有効なものだけ。期限を過ぎたものは、もう誰にも開けない
            distributions=len(view_token.usable(artifact.view_tokens, now)),
        ))
    return MyArtifacts(
        artifacts=tuple(sorted(rows, key=lambda r: r.updated_at, reverse=True)),
        unreadable=unreadable)


class ListMyArtifacts:
    """手入れできる共有アーティファクトを見渡し、次に何を直すかを決める。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, comments: CommentRepository,
                 clock: Clock) -> None:
        self._artifacts = artifacts
        self._comments = comments
        self._clock = clock

    def run(self, caller: Caller) -> MyArtifacts:
        """このユースケースの唯一の入口。"""
        return _list_artifacts(self._artifacts, self._comments, self._clock, caller)
