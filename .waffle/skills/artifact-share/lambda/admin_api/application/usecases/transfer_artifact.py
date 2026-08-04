"""投稿者が抜けたあとも、その共有アーティファクトを手入れできる人を残す。

手入れできる人を替えるだけの操作で、共有URL・閲覧トークン・中身・反応・公開状態
は変わらない。渡した相手の手元で何かが変わると、投稿者の異動という内輪の事情が
閲覧者に漏れる。

対象の仕様: uc-transfer-artifact
"""
from __future__ import annotations

from application.artifact_access import require_manageable
from application.ports import Caller, Clock
from application.ports import PublisherDirectory
from application.ports.shared_artifact_repository import SharedArtifactRepository
from shared.errors import ManageError


def _write_meta(artifacts: SharedArtifactRepository, clock: Clock, meta: dict) -> None:
    meta["updatedAt"] = clock()
    artifacts.save(meta)


def transfer(artifacts: SharedArtifactRepository, directory: PublisherDirectory, clock: Clock, caller: Caller, artifact_id: str, to_publisher: str) -> dict:
    """投稿者を別の投稿者へ移す。手入れできる人が替わるだけの操作。

    共有URL・閲覧トークン・中身・コメント・公開状態のいずれも変えない。
    渡した相手の手元で何かが変わると、投稿者の異動という内輪の事情が
    閲覧者に漏れる。

    公開停止中のものも移せる。止まっているものこそ引き継ぎ先が要る。
    """
    if not caller.is_admin:
        # 自分のものを他人へ押し付ける経路と、他人のものを自分のものに
        # する経路の両方を、ここひとつで塞ぐ
        raise ManageError("NOT_ADMINISTRATOR", "投稿者を移せるのは管理者だけです。")

    meta = require_manageable(artifacts, caller, artifact_id)

    if not (directory and directory.find(to_publisher)):
        # 招かれていない人へ移すと、その場で誰も手入れできない状態に戻る
        raise ManageError("PUBLISHER_NOT_FOUND", "移す先が招かれていません。")

    previous = meta.get("uploadedBy", "")
    meta["uploadedBy"] = to_publisher
    _write_meta(artifacts, clock, meta)

    return {"artifactId": artifact_id, "from": previous, "to": to_publisher,
            "event": "ArtifactTransferred"}
