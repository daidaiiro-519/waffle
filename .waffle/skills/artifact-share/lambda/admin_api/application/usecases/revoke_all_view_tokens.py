"""渡した相手を一度にすべて外す。誰に渡したかを思い出さずに、まとめて閉じる。

対象の公開は止めない。入っているまとめの閲覧トークンも使えたまま残る。

対象の仕様: uc-revoke-all-view-tokens
"""
from __future__ import annotations

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.view_token_access import (ViewTokenError, require_manageable_subject,
                                           save_tokens)
from domain import view_token
from domain.view_subject import ViewSubject



def _revoke_all(artifacts: SharedArtifactRepository, projects: ProjectRepository,
               gate: ViewGatePort, clock: Clock, caller: Caller,
               subject: ViewSubject) -> dict:
    """渡した相手を一度にすべて外す。公開そのものは止めない。"""
    target = require_manageable_subject(artifacts, projects, caller, subject)
    now = clock()
    tokens = view_token.without_expired(target.view_tokens, now)
    revoked_count = len(view_token.usable(tokens, now))

    tokens = view_token.all_revoked(tokens, now)
    save_tokens(artifacts, projects, clock, subject, target, tokens)
    gate.replace_grants(subject, view_token.grants(tokens, now))
    return {"revoked": revoked_count}


class RevokeAllViewTokens:
    """渡した相手を一度にすべて外す。誰に渡したかを思い出さずに、まとめて閉じる。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, gate: ViewGatePort, clock: Clock) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._gate = gate
        self._clock = clock

    def run(self, caller: Caller, subject: ViewSubject) -> dict:
        """このユースケースの唯一の入口。"""
        return _revoke_all(self._artifacts, self._projects, self._gate, self._clock, caller, subject)
