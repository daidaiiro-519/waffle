"""止めていたものを、もう一度見てもらえる状態に戻す。

止める前に渡していた閲覧トークンのうち、期限内で無効にしていないものをそのまま
使える状態に戻す。止めるのは全ての経路を一度に閉じる操作であって、渡した相手を
選び直す操作ではない——選び直したいなら1本ずつ外せばよい。

対象の仕様: uc-resume-artifact
"""
from __future__ import annotations

from dataclasses import dataclass

from application.artifact_access import require_manageable
from application.ports import Caller, Clock
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from domain import view_token
from domain.shared_artifact import PUBLISHED
from domain.view_subject import ViewSubject
from shared.errors import ManageError



@dataclass(frozen=True)
class ResumedArtifact:
    """再開した結果。共有URLは止める前と同じで、閲覧者は何もしなくてよい。"""

    artifact_id: str
    url: str
    status: str

def _resume(artifacts: SharedArtifactRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, artifact_id: str) -> ResumedArtifact:
    """再び開けるようにする。

    止める前に渡していた閲覧トークンのうち、期限内で無効にしていないものを
    そのまま使える状態に戻す。止めるのは全ての経路を一度に閉じる操作であって、
    渡した相手を選び直す操作ではない——選び直したいなら1本ずつ外せばよい。
    """
    artifact = require_manageable(artifacts, caller, artifact_id)
    if not artifact.status.is_suspended():
        raise ManageError("NOT_SUSPENDED", "公開は止まっていません。")

    now = clock()
    gate.replace_grants(ViewSubject.artifact(artifact_id),
                        view_token.grants(artifact.view_tokens, now))
    artifacts.save(artifact.resumed(now))

    return ResumedArtifact(artifact_id=artifact_id,
                           url=viewer.artifact_url(artifact_id), status=PUBLISHED)


class ResumeArtifact:
    """止めていたものを、もう一度見てもらえる状態に戻す。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock) -> None:
        self._artifacts = artifacts
        self._viewer = viewer
        self._gate = gate
        self._clock = clock

    def run(self, caller: Caller, artifact_id: str) -> ResumedArtifact:
        """このユースケースの唯一の入口。"""
        return _resume(self._artifacts, self._viewer, self._gate, self._clock, caller, artifact_id)
