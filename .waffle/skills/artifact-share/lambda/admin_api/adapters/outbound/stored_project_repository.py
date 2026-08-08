"""プロジェクトの読み書きを、保管の上で実現する。

鍵の組み立て（projects/{識別子}.json）と、保管の記録と集約の間の変換を、
ここだけが知る。

memberArtifactIds は記録に残るが、集約の状態ではない。所属の正は共有
アーティファクトの側にあり、この一覧は閲覧者へ見せるために組み立て直せる
投影である。だから読み出しでは集約へ入れず、書き戻しでは元の記録から引き継ぐ。
"""
from __future__ import annotations

import json

from domain.project import (
    PUBLISHED,
    Project,
    ProjectId,
    ProjectKey,
    ProjectOwner,
    ProjectScope,
    ProjectStatus,
    SUSPENDED,
)
from domain.view_token import (
    ACTIVE,
    NO_EXPIRY,
    ViewToken,
    ViewTokenExpiry,
    ViewTokenId,
    ViewTokenStatus,
)

PREFIX = "projects/"

# 保管に残っている公開状態の綴り
STORED_PUBLISHED = "active"
STORED_SUSPENDED = "disabled"


def from_record(record: dict) -> Project:
    """保管の記録を、業務の語彙を持つプロジェクトへ直す。

    Args:
        record: 保管から読んだ記録。

    Returns:
        業務の語彙を持つプロジェクト。

    Raises:
        なし。
    """
    return Project(
        project_id=ProjectId(record.get("projectId", "")),
        display_name=record.get("displayName", ""),
        project_key=ProjectKey(record.get("projectKey", "")),
        status=ProjectStatus(
            SUSPENDED if record.get("status") == STORED_SUSPENDED else PUBLISHED),
        owner=ProjectOwner(record.get("owner", "")),
        scope=ProjectScope(record.get("scope", "")),
        created_at=record.get("createdAt", 0),
        view_tokens=tuple(_token_from(t) for t in record.get("viewTokens") or []),
        updated_at=record.get("updatedAt", 0),
    )


def to_record(project: Project, base: dict | None = None) -> dict:
    """プロジェクトを、保管の記録へ戻す。投影は元の記録から引き継ぐ。

    Args:
        project: 保管へ戻すプロジェクト。
        base: 元の記録。投影はここから引き継ぐ。

    Returns:
        保管の記録。

    Raises:
        なし。
    """
    record = dict(base or {})
    record.update({
        "projectId": project.project_id.value,
        "displayName": project.display_name,
        "projectKey": project.project_key.value,
        "owner": project.owner.value,
        "scope": project.scope.value,
        "status": STORED_SUSPENDED if project.status.is_suspended() else STORED_PUBLISHED,
        "viewTokens": [_token_to(t) for t in project.view_tokens],
        "createdAt": project.created_at,
        "updatedAt": project.updated_at,
    })
    record.setdefault("memberArtifactIds", [])
    return record


def _token_from(t: dict) -> ViewToken:
    return ViewToken(
        token_id=ViewTokenId(t.get("tokenId", "")),
        name=t.get("name", ""),
        fingerprint=t.get("fingerprint", ""),
        expires_at=ViewTokenExpiry(t.get("expiresAt", NO_EXPIRY)),
        status=ViewTokenStatus(t.get("status", ACTIVE)),
        issued_at=t.get("issuedAt", 0),
    )


def _token_to(t: ViewToken) -> dict:
    return {
        "tokenId": t.token_id.value,
        "name": t.name,
        "fingerprint": t.fingerprint,
        "expiresAt": t.expires_at.value,
        "status": t.status.value,
        "issuedAt": t.issued_at,
    }


class StoredProjectRepository:
    """プロジェクトを、保管の上で読み書きする。"""
    def __init__(self, store):
        self._store = store

    def find(self, project_id: str) -> Project | None:
        """1つのプロジェクトを読む。

        Args:
            project_id: 読む対象の識別子。

        Returns:
            そのプロジェクト。無ければ None。

        Raises:
            なし。
        """
        record = self._raw(project_id)
        return from_record(record) if record is not None else None

    def save(self, project: Project) -> None:
        """1つのプロジェクトを残す。

        Args:
            project: 残すプロジェクト。

        Returns:
            なし。

        Raises:
            なし。
        """
        base = self._raw(project.project_id.value) or {}
        self._store.put(_key(project.project_id.value),
                        json.dumps(to_record(project, base), ensure_ascii=False),
                        "application/json")

    def all(self) -> tuple[list[Project], int]:
        """保管にある全てのプロジェクトを並べる。

        Returns:
            プロジェクトの一覧と、その総数。

        Raises:
            なし。
        """
        found, unreadable = [], 0
        for key in self._store.list(PREFIX):
            try:
                found.append(from_record(json.loads(self._store.get(key))))
            except Exception:
                unreadable += 1
        return found, unreadable

    def members_of(self, project_id: str) -> list[str]:
        """その単位に入っているものの一覧。集約の状態ではなく投影として読む。"""
        return (self._raw(project_id) or {}).get("memberArtifactIds", [])

    def replace_members(self, project_id: str, artifact_ids: list[str]) -> None:
        """投影を書き直す。失敗しても作り直せるので、正が二重になることはない。"""
        record = self._raw(project_id)
        if record is None:
            return
        record["memberArtifactIds"] = list(artifact_ids)
        self._store.put(_key(project_id), json.dumps(record, ensure_ascii=False),
                        "application/json")

    def _raw(self, project_id: str) -> dict | None:
        try:
            return json.loads(self._store.get(_key(project_id)))
        except Exception:
            return None


def _key(project_id: str) -> str:
    return f"{PREFIX}{project_id}.json"
