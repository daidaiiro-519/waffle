"""見せるのを止めるが、記録は失わずに残しておく。

どの閲覧トークンでも開けなくなる。入っているプロジェクトの閲覧トークンからも
開けない——止めるのは配布先を選ばず全ての経路を閉じたいときの手立てだから。
中身も反応も消さない。

対象の仕様: uc-suspend-artifact
"""
from __future__ import annotations

from dataclasses import dataclass

from application.artifact_access import require_manageable
from application.ports import Caller, Clock
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from domain.value_objects.shared_artifact import SUSPENDED
from domain.value_objects.view_subject import ViewSubject
from shared.errors import ManageError



@dataclass(frozen=True)
class SuspendedArtifact:
    """止めた結果。どの閲覧トークンでも開けない状態になったことを伝える。"""

    artifact_id: str
    status: str

def _suspend(artifacts: SharedArtifactRepository, gate: ViewGatePort, clock: Clock, caller: Caller, artifact_id: str) -> SuspendedArtifact:
    """公開を止める。中身も反応も消さない。"""
    artifact = require_manageable(artifacts, caller, artifact_id)
    if not artifact.status.is_published():
        raise ManageError("NOT_PUBLISHED", "公開が止まっています。先に再公開してください。")

    gate.close(ViewSubject.artifact(artifact_id))
    artifacts.save(artifact.suspended(clock()))

    return SuspendedArtifact(artifact_id=artifact_id, status=SUSPENDED)


class SuspendArtifact:
    """見せるのを止めるが、記録は失わずに残しておく。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, gate: ViewGatePort, clock: Clock) -> None:
        self._artifacts = artifacts
        self._gate = gate
        self._clock = clock

    def run(self, caller: Caller, artifact_id: str) -> SuspendedArtifact:
        """このユースケースの唯一の入口。"""
        return _suspend(self._artifacts, self._gate, self._clock, caller, artifact_id)
