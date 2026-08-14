"""自分が渡したものにどんな反応が来たかを知る。

寄せられた順に返し、差し替えの区切りも同じ並びに含める。分けて返すと、どの指摘が
差し替え前のものかを画面側が組み立て直すことになる。

読めない記録は飛ばして残りを返し、飛ばした件数を添える。黙って落とさないのは、
投稿者が「これで全部だ」と思い込むため。

集約そのものは境界の外へ渡さない。外へ出すのは、画面が必要とする値だけを持つ
専用の型にする。判定の欄だけは、外の綴りが業務の語彙と違うので型の側で宣言する
——保管も画面も decision と呼び、業務は判定と呼ぶ。

対象の仕様: uc-read-comments
"""
from __future__ import annotations

from dataclasses import dataclass, field

from application.artifact_access import require_manageable
from application.ports import Caller
from application.ports.comment_repository import CommentRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from domain.entities.comment import Comment


@dataclass(frozen=True)
class CommentEntry:
    """並びに載る1件。閲覧者のコメントか、差し替えの区切り。

    判定の外向きの綴りをここで宣言するのは、保管に既に decision として書かれた
    記録があり、その綴りを変えられないため。業務の側は判定と呼び続ける。
    """

    id: str
    kind: str
    author: str
    body: str
    posted_at: str
    verdict: str = field(default="comment", metadata={"json": "decision"})
    parent_id: str | None = None


@dataclass(frozen=True)
class Comments:
    """寄せられた反応。差し替えの区切りも同じ並びに含む。"""

    artifact_id: str
    comments: tuple[CommentEntry, ...]
    unreadable: int


def _entry_of(comment: Comment) -> CommentEntry:
    """集約1件を、外が読む形へ写す。"""
    return CommentEntry(
        id=comment.comment_id.value,
        kind=comment.kind.value,
        author=comment.author.value,
        body=comment.body.text,
        posted_at=comment.posted_at,
        verdict=comment.verdict.value,
        parent_id=comment.parent_id.value if comment.parent_id else None,
    )


def _read(artifacts: SharedArtifactRepository, comments: CommentRepository, caller: Caller, artifact_id: str) -> Comments:
    """寄せられたコメントを、古いものから順に返す。

    差し替えの区切りも同じ並びに含める。分けて返すと、どの指摘が差し替え
    前のものかを画面側が組み立て直すことになる。

    読めない記録は飛ばして残りを返し、飛ばした件数を添える。1件の不具合で
    その共有アーティファクトの反応がすべて見えなくなるのを避ける。黙って
    落とさないのは、投稿者が「これで全部だ」と思い込むため。
    """
    # 扱える範囲の判定は既にあるものを通す。拒み方（見つからないものとして
    # 扱う）も自動的に揃う
    require_manageable(artifacts, caller, artifact_id)

    rows, unreadable = comments.list_of(artifact_id)

    return Comments(artifact_id=artifact_id,
                    comments=tuple(_entry_of(c) for c in rows),
                    unreadable=unreadable)


class ReadComments:
    """自分が渡したものにどんな反応が来たかを知る。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, comments: CommentRepository) -> None:
        self._artifacts = artifacts
        self._comments = comments

    def run(self, caller: Caller, artifact_id: str) -> Comments:
        """このユースケースの唯一の入口。"""
        return _read(self._artifacts, self._comments, caller, artifact_id)
