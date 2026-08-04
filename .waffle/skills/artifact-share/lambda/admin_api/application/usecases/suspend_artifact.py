"""見せるのを止めるが、記録は失わずに残しておく。

どの閲覧トークンでも開けなくなる。入っているプロジェクトの閲覧トークンからも
開けない——止めるのは配布先を選ばず全ての経路を閉じたいときの手立てだから。
中身も反応も消さない。

対象の仕様: uc-suspend-artifact
"""
from __future__ import annotations

from application.artifact_access import require_manageable
from application.ports import Caller, Clock
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from domain.publication import DISABLED, is_published
from domain.view_subject import ViewSubject
from shared.errors import ManageError


def _write_meta(artifacts: SharedArtifactRepository, clock: Clock, meta: dict) -> None:
    meta["updatedAt"] = clock()
    artifacts.save(meta)


def _require_published(meta: dict) -> None:
    if not is_published(meta):
        raise ManageError("NOT_PUBLISHED", "公開が止まっています。先に再公開してください。")


def suspend(artifacts: SharedArtifactRepository, gate: ViewGatePort, clock: Clock, caller: Caller, artifact_id: str) -> dict:
    """公開を止める。中身も反応も消さない。"""
    meta = require_manageable(artifacts, caller, artifact_id)
    _require_published(meta)

    gate.close(ViewSubject.artifact(artifact_id))
    meta["status"] = DISABLED
    _write_meta(artifacts, clock, meta)

    return {"artifactId": artifact_id, "status": DISABLED}
