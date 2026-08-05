"""ある相手にだけ見せるのをやめる。他の相手はそのまま見られるようにしておく。

対象の公開は止めない。1本を外すために他の相手まで巻き添えで外れると、外す操作が
使いにくくなり、結局使われなくなる。

対象の仕様: uc-revoke-view-token
"""
from __future__ import annotations

from dataclasses import dataclass

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.view_token_access import (ViewTokenError, require_manageable_subject,
                                           save_tokens)
from domain import view_token
from domain.view_subject import ViewSubject

from application.view_token_access import TOKEN_NOT_FOUND



@dataclass(frozen=True)
class RevokedViewToken:
    """1本を外した結果。他の相手はそのまま見られる。"""

    token_id: str
    revoked: bool = True

def _revoke(artifacts: SharedArtifactRepository, projects: ProjectRepository,
           gate: ViewGatePort, clock: Clock, caller: Caller, subject: ViewSubject,
           token_id: str) -> RevokedViewToken:
    """その1本だけを使えなくする。他の相手はそのまま見られる。"""
    target = require_manageable_subject(artifacts, projects, caller, subject)
    now = clock()
    tokens = view_token.without_expired(target.view_tokens, now)

    if all(t.token_id.value != token_id for t in tokens):
        raise ViewTokenError(TOKEN_NOT_FOUND, "その閲覧トークンはありません。")

    tokens = view_token.revoked(tokens, token_id)
    save_tokens(artifacts, projects, clock, subject, target, tokens)
    gate.replace_grants(subject, view_token.grants(tokens, now))
    return RevokedViewToken(token_id=token_id)


class RevokeViewToken:
    """ある相手にだけ見せるのをやめる。他の相手はそのまま見られるようにしておく。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, gate: ViewGatePort, clock: Clock) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._gate = gate
        self._clock = clock

    def run(self, caller: Caller, subject: ViewSubject, token_id: str) -> RevokedViewToken:
        """このユースケースの唯一の入口。"""
        return _revoke(self._artifacts, self._projects, self._gate, self._clock, caller, subject, token_id)
