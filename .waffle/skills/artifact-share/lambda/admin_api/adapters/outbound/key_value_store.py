"""鍵と値で置いて取り出す保管。

これは application の口ではない。application はもう「鍵に値を置く」という
語彙を持たず、閲覧の面への口だけを通す。ここにあるのは、その実装が載って
いる土台であり、outbound 側の内輪の取り決めである。
"""
from __future__ import annotations

from typing import Protocol


class KeyValueStore(Protocol):
    """閲覧の面が同期で読める、鍵と値の保管。

    書くだけで、読み取りは持たない。読むのは別のランタイム（閲覧ゲート）で、
    そちらはこの口を通らず自分の手立てで読む。使う者の居ない読み取りを口へ
    宣言すると、鍵が無いときに何を返すかという答えの決まらない取り決めが残る。
    """

    def put(self, key: str, value: str) -> None:
        """指定した鍵で値を置く。既にあれば置き換える。"""
        ...

