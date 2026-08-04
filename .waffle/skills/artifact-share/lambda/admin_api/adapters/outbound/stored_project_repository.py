"""プロジェクトの読み書きを、保管の上で実現する。

鍵の組み立て（projects/{識別子}.json）と、記録と保管の間の変換をここだけが
知る。
"""
from __future__ import annotations

import json

PREFIX = "projects/"


class StoredProjectRepository:
    def __init__(self, store):
        self._store = store

    def find(self, project_id: str) -> dict | None:
        try:
            return json.loads(self._store.get(_key(project_id)))
        except Exception:
            return None

    def save(self, project: dict) -> None:
        self._store.put(_key(project["projectId"]),
                        json.dumps(project, ensure_ascii=False), "application/json")

    def all(self) -> tuple[list[dict], int]:
        found, unreadable = [], 0
        for key in self._store.list(PREFIX):
            try:
                found.append(json.loads(self._store.get(key)))
            except Exception:
                unreadable += 1
        return found, unreadable


def _key(project_id: str) -> str:
    return f"{PREFIX}{project_id}.json"
