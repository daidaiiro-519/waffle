"""公開された中身が同じものかを確かめるための形。

中身そのものは集約の一貫性の境界の外にあり、集約はこの形だけを持つ。公開後に
部分的な書き換えは行わず、差し替えのときだけ丸ごと置き換わる。

控えるのは、手元へ取り出したものが公開した中身と一致することを、あとから
確かめられるようにするため。

閲覧トークンの指紋とは別の概念である。同じ語で呼ぶと、どちらも素の文字列なので
取り違えても何も起きない。型を分けることでしか塞げない。

対象の仕様: agg-shared-artifact
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class ContentFingerprint:
    """公開された中身が同じものかを確かめるための形。"""

    value: str

    @staticmethod
    def of(content: str) -> "ContentFingerprint":
        """中身から、同じものかを確かめるための形を作る。

        Args:
            content: 中身そのもの。

        Returns:
            同じものかを確かめるための形。

        Raises:
            なし。
        """
        return ContentFingerprint(hashlib.sha256(content.encode("utf-8")).hexdigest())
