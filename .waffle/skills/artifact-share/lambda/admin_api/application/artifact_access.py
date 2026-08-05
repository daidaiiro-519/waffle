"""扱ってよい共有アーティファクトを取り出す。

読み出し（repository）と、手入れしてよいかの判定（集約自身）と、扱えないことを
どう伝えるか（ここ）は別のことなので、それぞれの持ち場に置く。ここが担うのは
最後の1つだけ——判定の結果を、受け口が分岐できるコードへ写す。

扱えないものを「拒む」ではなく「見つからない」と答えるのは、拒否と区別できると
存在そのものが伝わるため。この言い換えはドメインの判断ではなく、外へ何を見せる
かの決定なので、集約ではなくここにある。
"""
from __future__ import annotations

from application.ports import Caller
from application.ports.shared_artifact_repository import SharedArtifactRepository
from domain.shared_artifact import SharedArtifact
from shared.errors import ManageError

NOT_FOUND = "ARTIFACT_NOT_FOUND"


def require_manageable(artifacts: SharedArtifactRepository, caller: Caller,
                       artifact_id: str) -> SharedArtifact:
    """手入れしてよい共有アーティファクトを取り出す。

    無いときも、扱えないときも、同じ答えを返す。
    """
    artifact = artifacts.find(artifact_id)
    if artifact is None or not artifact.manageable_by(caller.id, caller.is_admin):
        raise ManageError(NOT_FOUND, "見つかりません。")
    return artifact
