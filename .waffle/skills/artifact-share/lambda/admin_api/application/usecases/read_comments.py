"""自分が渡したものにどんな反応が来たかを知る。

寄せられた順に返し、差し替えの区切りも同じ並びに含める。分けて返すと、どの指摘が
差し替え前のものかを画面側が組み立て直すことになる。

読めない記録は飛ばして残りを返し、飛ばした件数を添える。黙って落とさないのは、
投稿者が「これで全部だ」と思い込むため。

対象の仕様: uc-read-comments
"""
from __future__ import annotations

from dataclasses import dataclass

from application.artifact_access import require_manageable
from application.ports import Caller
from application.ports.comment_repository import CommentRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository



@dataclass(frozen=True)
class Comments:
    """寄せられた反応。差し替えの区切りも同じ並びに含む。

    1件ずつは保存されている形のまま返す。表示用に整えるのは画面側が行う。
    """

    artifact_id: str
    comments: tuple[dict, ...]
    unreadable: int

def _read(artifacts: SharedArtifactRepository, comments: CommentRepository, caller: Caller, artifact_id: str) -> Comments:
    """寄せられたコメントを、古いものから順に返す。

    差し替えの区切りも同じ並びに含める。分けて返すと、どの指摘が差し替え
    前のものかを画面側が組み立て直すことになる。

    読めない記録は飛ばして残りを返し、飛ばした件数を添える。1件の不具合で
    その共有アーティファクトの反応がすべて見えなくなるのを避ける。黙って
    落とさないのは、投稿者が「これで全部だ」と思い込むため。

    保存されている形のまま返す。表示用に整えるのは画面側が行う。
    """
    # 扱える範囲の判定は既にあるものを通す。拒み方（見つからないものとして
    # 扱う）も自動的に揃う
    require_manageable(artifacts, caller, artifact_id)

    rows, unreadable = comments.list_of(artifact_id)
    for record in rows:
        record.setdefault("kind", "comment")

    return Comments(artifact_id=artifact_id, comments=tuple(rows),
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
