"""配布物に何を含めるかを決める純ロジック。

配布は「渡した先がこちらの道具立てを持たないまま使えること」を目的とする。
そこから2つの選別規則が出る。仕上がっていないものは渡さないこと、そして
渡した先が自分で用意すべきものは持ち込まないことである。

「仕上がっているか」を status で見るのは、それを表す語が既に存在するため。
配布側に別の目印を立てると、同じ事実を指す語が2つになり、食い違ったときに
どちらが正しいかを決める術がなくなる。

ファイルI/Oは一切行わない。読み込み済みのdictと相対パスだけを受け取る。
"""
from __future__ import annotations

NOT_READY_TO_DISTRIBUTE = "NOT_READY_TO_DISTRIBUTE"

_NOT_READY_STATUSES = frozenset({"DRAFT"})

RECEIVER_PROVIDED_SUBPATHS: tuple[str, ...] = ("references/coding",)
"""渡した先が自分で用意すべきもの。

コーディングの決まりごとは、渡した先のプロジェクト自身のものでなければ意味を
なさない。こちらのものを持ち込むと、相手のコードがこちらの決まりごとで書かれる。
渡した先がそれを作る道具（spec-authoringが同梱する雛形）は一式の中にある。
"""


def is_ready_to_distribute(document: dict) -> bool:
    """その文書が配布してよい段階にあるか。

    Args:
        document: 対象のdocument（status を持つ）。

    Returns:
        配布してよければ True。仕上がっていなければ False。
    """
    return document.get("status") not in _NOT_READY_STATUSES


def exclusion_reason(document: dict) -> str | None:
    """配布から外す理由。外さないなら None。

    Args:
        document: 対象のdocument。

    Returns:
        外す理由の識別子。外さないなら None。
    """
    return None if is_ready_to_distribute(document) else NOT_READY_TO_DISTRIBUTE
