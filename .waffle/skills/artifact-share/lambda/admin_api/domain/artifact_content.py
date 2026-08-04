"""公開された中身そのもの。

集約の一貫性の境界の外にあり、共有アーティファクトはその指紋だけを持つ。
公開後に部分的な書き換えは行わず、差し替えのときだけ丸ごと置き換わる。

指紋を控えるのは、手元へ取り出したものが公開した中身と一致することを、
あとから確かめられるようにするため。

対象の仕様: agg-shared-artifact
"""
from __future__ import annotations

import hashlib


def fingerprint(content: str) -> str:
    """中身から、同じものかを確かめるための形を作る。"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
