"""共有アーティファクトの読み書きを、保管の上で実現する。

鍵の組み立て（meta/{識別子}.json）と、記録と保管の間の変換をここだけが知る。
application 側にこの形が漏れると、保管の置き方を変えるたびに全ての操作が
壊れる。

読めない記録を飛ばすのはここではなく all() の約束であり、その約束は
port の宣言が持つ。
"""
from __future__ import annotations

import json

PREFIX = "meta/"


class StoredSharedArtifactRepository:
    def __init__(self, store):
        self._store = store

    def find(self, artifact_id: str) -> dict | None:
        try:
            return json.loads(self._store.get(_key(artifact_id)))
        except Exception:
            return None

    def save(self, artifact: dict) -> None:
        self._store.put(_key(artifact["artifactId"]),
                        json.dumps(artifact, ensure_ascii=False), "application/json")

    def all(self) -> tuple[list[dict], int]:
        found, unreadable = [], 0
        for key in self._store.list(PREFIX):
            try:
                found.append(json.loads(self._store.get(key)))
            except Exception:
                unreadable += 1
        return found, unreadable


def _key(artifact_id: str) -> str:
    return f"{PREFIX}{artifact_id}.json"
