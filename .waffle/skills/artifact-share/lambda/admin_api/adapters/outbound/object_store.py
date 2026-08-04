"""鍵と値で置いて取り出す保管。

これは application の口ではない。application はもう「置く・取り出す」という
語彙を持たず、repository と閲覧の面の口だけを通す。ここにあるのは、それらの
実装が共通して載っている土台であり、outbound 側の内輪の取り決めである。

application/ports に置かないのは、口は常に application が「何を必要として
いるか」の視点で宣言するという決まりによる。誰も必要としていない口を
application 側に置いたままにすると、その形がふたたび呼び出し側へ漏れる。
"""
from __future__ import annotations

from typing import Protocol


class ObjectStore(Protocol):
    """置いたものを鍵で取り出せる保管。削除は持たない。"""

    def put(self, key: str, body: bytes | str, content_type: str) -> None:
        """指定した場所へ置く。既にあれば置き換える。"""
        ...

    def get(self, key: str) -> bytes | None:
        """指定した場所から取り出す。"""
        ...

    def list(self, prefix: str) -> list[str]:
        """その始まりを持つ場所を列挙する。"""
        ...
