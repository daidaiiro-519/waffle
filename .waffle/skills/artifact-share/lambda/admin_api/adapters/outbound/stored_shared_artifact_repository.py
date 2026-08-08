"""共有アーティファクトの読み書きを、保管の上で実現する。

鍵の組み立て（meta/{識別子}.json）と、保管の記録と集約の間の変換を、ここだけが
知る。保管は name / uploadedBy / contentHash と呼び、業務は表示名・投稿者・
指紋と呼ぶ。この対応を application まで漏らすと、保管の置き方を変えるたびに
すべての操作が壊れる。

保管の欄名は変えない。既に置かれている記録がそのまま読めることが、この形を
選んだ理由である。

集約が知らない欄（wrapperHash 等）は、書き戻すときに元の記録から引き継ぐ。
集約の外にあるものを、集約を保存したついでに消してはならない。
"""
from __future__ import annotations

import json

from domain.shared_artifact import (
    ArtifactDescriptor,
    ArtifactId,
    ArtifactStatus,
    EXTRACTED,
    MANUAL,
    PUBLISHED,
    PublisherId,
    SUSPENDED,
    SharedArtifact,
)
from domain.view_token import (
    ACTIVE,
    NO_EXPIRY,
    ViewToken,
    ViewTokenExpiry,
    ViewTokenId,
    ViewTokenStatus,
)

PREFIX = "meta/"

# 保管に残っている公開状態の綴り。業務の語とは別で、ここでだけ対応づける
STORED_PUBLISHED = "active"
STORED_SUSPENDED = "disabled"


def from_record(record: dict) -> SharedArtifact:
    """保管の記録を、業務の語彙を持つ共有アーティファクトへ直す。

    Args:
        record: 保管から読んだ記録。

    Returns:
        業務の語彙を持つ共有アーティファクト。

    Raises:
        なし。
    """
    return SharedArtifact(
        artifact_id=ArtifactId(record.get("artifactId", "")),
        display_name=record.get("name", ""),
        content_fingerprint=record.get("contentHash", ""),
        view_tokens=tuple(_token_from(t) for t in record.get("viewTokens") or []),
        status=ArtifactStatus(
            SUSPENDED if record.get("status") == STORED_SUSPENDED else PUBLISHED),
        published_by=PublisherId(record.get("uploadedBy", "")),
        descriptor=ArtifactDescriptor(
            document_id=record.get("documentId", ""),
            doc_type=record.get("docType", ""),
            title=record.get("name", ""),
            description=record.get("description", ""),
            labels=tuple(record.get("tags") or []),
            source=EXTRACTED if record.get("metaSource") == EXTRACTED else MANUAL,
        ),
        published_at=record.get("publishedAt", 0),
        updated_at=record.get("updatedAt", 0),
        projects=tuple(record.get("projects") or []),
        external_resource_count=record.get("externalRefs", 0),
    )


def to_record(artifact: SharedArtifact, base: dict | None = None) -> dict:
    """共有アーティファクトを、保管の記録へ戻す。

    base には元の記録を渡す。集約が知らない欄をそこから引き継ぐため——渡さないと、
    保存のたびに閲覧の面の関心事が消える。

    Args:
        artifact: 保管へ戻す共有アーティファクト。
        base: 元の記録。

    Returns:
        保管の記録。

    Raises:
        なし。
    """
    record = dict(base or {})
    record.update({
        "artifactId": artifact.artifact_id.value,
        "name": artifact.display_name,
        "status": STORED_SUSPENDED if artifact.status.is_suspended() else STORED_PUBLISHED,
        "projects": list(artifact.projects),
        "metaSource": artifact.descriptor.source,
        "docType": artifact.descriptor.doc_type,
        "documentId": artifact.descriptor.document_id,
        "description": artifact.descriptor.description,
        "tags": list(artifact.descriptor.labels),
        "uploadedBy": artifact.published_by.value,
        "externalRefs": artifact.external_resource_count,
        "contentHash": artifact.content_fingerprint,
        "publishedAt": artifact.published_at,
        "updatedAt": artifact.updated_at,
        "viewTokens": [_token_to(t) for t in artifact.view_tokens],
    })
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


class StoredSharedArtifactRepository:
    """共有アーティファクトを、保管の上で読み書きする。"""
    def __init__(self, store):
        self._store = store

    def find(self, artifact_id: str) -> SharedArtifact | None:
        """1件の共有アーティファクトを読む。

        Args:
            artifact_id: 読む対象の識別子。

        Returns:
            その共有アーティファクト。無ければ None。

        Raises:
            なし。
        """
        record = self._raw(artifact_id)
        return from_record(record) if record is not None else None

    def save(self, artifact: SharedArtifact) -> None:
        """1件の共有アーティファクトを残す。

        Args:
            artifact: 残す共有アーティファクト。

        Returns:
            なし。

        Raises:
            なし。
        """
        base = self._raw(artifact.artifact_id.value) or {}
        self._store.put(_key(artifact.artifact_id.value),
                        json.dumps(to_record(artifact, base), ensure_ascii=False),
                        "application/json")

    def all(self) -> tuple[list[SharedArtifact], int]:
        """保管にある全ての共有アーティファクトを並べる。

        Returns:
            共有アーティファクトの一覧と、その総数。

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

    def _raw(self, artifact_id: str) -> dict | None:
        try:
            return json.loads(self._store.get(_key(artifact_id)))
        except Exception:
            return None


def _key(artifact_id: str) -> str:
    return f"{PREFIX}{artifact_id}.json"
