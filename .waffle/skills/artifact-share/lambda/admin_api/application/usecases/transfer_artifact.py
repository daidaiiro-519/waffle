"""投稿者が抜けたあとも、その共有アーティファクトを手入れできる人を残す。

手入れできる人を替えるだけの操作で、共有URL・閲覧トークン・中身・反応・公開状態
は変わらない。渡した相手の手元で何かが変わると、投稿者の異動という内輪の事情が
閲覧者に漏れる。

対象の仕様: uc-transfer-artifact
"""
from __future__ import annotations

from dataclasses import dataclass, field

from application.artifact_access import require_manageable
from application.ports import Caller, Clock
from domain.value_objects.shared_artifact import PublisherId
from application.ports import PublisherDirectory
from application.ports.shared_artifact_repository import SharedArtifactRepository
from shared.errors import ManageError



@dataclass(frozen=True)
class TransferredArtifact:
    """引き継いだ結果。誰から誰へ移ったかを、管理者が確かめられるようにする。"""

    artifact_id: str
    moved_from: str = field(metadata={"json": "from"}, default="")
    moved_to: str = field(metadata={"json": "to"}, default="")

def _transfer(artifacts: SharedArtifactRepository, directory: PublisherDirectory, clock: Clock, caller: Caller, artifact_id: str, to_publisher: str) -> TransferredArtifact:
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

    artifact = require_manageable(artifacts, caller, artifact_id)

    if not (directory and directory.find(to_publisher)):
        # 招かれていない人へ移すと、その場で誰も手入れできない状態に戻る
        raise ManageError("PUBLISHER_NOT_FOUND", "移す先が招かれていません。")

    previous = artifact.published_by.value
    artifacts.save(artifact.transferred_to(PublisherId(to_publisher), clock()))

    return TransferredArtifact(artifact_id=artifact_id, moved_from=previous,
                               moved_to=to_publisher)


class TransferArtifact:
    """投稿者が抜けたあとも、その共有アーティファクトを手入れできる人を残す。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, directory: PublisherDirectory, clock: Clock) -> None:
        self._artifacts = artifacts
        self._directory = directory
        self._clock = clock

    def run(self, caller: Caller, artifact_id: str, to_publisher: str) -> TransferredArtifact:
        """このユースケースの唯一の入口。"""
        return _transfer(self._artifacts, self._directory, self._clock, caller, artifact_id, to_publisher)
