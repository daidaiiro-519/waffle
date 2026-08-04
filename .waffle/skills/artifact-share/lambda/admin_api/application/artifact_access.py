"""扱ってよい共有アーティファクトを取り出す。

読み出し（repository）と、手入れしてよいかの判定（domain）と、扱えないことを
どう伝えるか（ここ）は別のことなので、それぞれの持ち場に置く。ここが担うのは
最後の1つだけ——判定の結果を、受け口が分岐できるコードへ写す。

扱えないものを「拒む」ではなく「見つからない」と答えるのは、拒否と区別できると
存在そのものが伝わるため。この言い換えはドメインの判断ではなく、外へ何を見せる
かの決定なので、domain ではなくここにある。

複数の操作が同じ取り出し方をするため、1か所に置く。以前は manage の非公開の
関数を comments が取り込んでおり、モジュールの内側へ手を伸ばしていた。
"""
from __future__ import annotations

from application.ports.shared_artifact_repository import SharedArtifactRepository
from domain.caller import Caller
from domain.publication import manageable_by
from shared.errors import ManageError

NOT_FOUND = "ARTIFACT_NOT_FOUND"


def require_manageable(artifacts: SharedArtifactRepository, caller: Caller,
                       artifact_id: str) -> dict:
    """手入れしてよい共有アーティファクトを取り出す。

    無いときも、扱えないときも、同じ答えを返す。
    """
    meta = artifacts.find(artifact_id)
    if meta is None or not manageable_by(meta, caller):
        raise ManageError(NOT_FOUND, "見つかりません。")
    return meta
