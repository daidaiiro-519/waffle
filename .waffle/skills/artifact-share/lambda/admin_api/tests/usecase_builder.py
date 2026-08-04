"""検証のために、結線からユースケースを組み立てる。

合成ルート（main.py）は行き先ごとに手で組み立てる。そこは配線が読めることが
値打ちなので、名前で自動に結ぶと何が渡っているか読めなくなる。

検証はそうではない。確かめたいのは操作の振る舞いであって結線ではないので、
口の名前を見て結ぶ。口を1つ足すたびに全ての検証を直すことにもならない。
"""
from __future__ import annotations

import inspect

# ユースケースが名乗る口の名前 → 結線が持つ属性の名前
ATTR = {"artifacts": "artifacts", "projects": "projects", "comments": "comments",
        "viewer": "viewer", "gate": "gate", "directory": "directory",
        "identify": "identify", "clock": "now"}


def build(connections, usecase):
    """そのユースケースが求める口だけを、結線から渡して組み立てる。"""
    needs = [p for p in inspect.signature(usecase.__init__).parameters if p != "self"]
    return usecase(*(getattr(connections, ATTR[p]) for p in needs))
