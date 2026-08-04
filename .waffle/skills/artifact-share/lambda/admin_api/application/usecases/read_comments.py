"""自分が渡したものにどんな反応が来たかを知る。

寄せられた順に返し、差し替えの区切りも同じ並びに含める。分けて返すと、どの指摘が
差し替え前のものかを画面側が組み立て直すことになる。

読めない記録は飛ばして残りを返し、飛ばした件数を添える。黙って落とさないのは、
投稿者が「これで全部だ」と思い込むため。

対象の仕様: uc-read-comments
"""
from __future__ import annotations

from application.artifact_access import require_manageable
from application.ports import Caller
from application.ports.comment_repository import CommentRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository


def read(artifacts: SharedArtifactRepository, comments: CommentRepository, caller: Caller, artifact_id: str) -> dict:
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

    return {"artifactId": artifact_id, "comments": rows, "unreadable": unreadable}
