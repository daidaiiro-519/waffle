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



def revoke_all(artifacts: SharedArtifactRepository, projects: ProjectRepository,
               gate: ViewGatePort, clock: Clock, caller: Caller,
               subject: ViewSubject) -> dict:
    """渡した相手を一度にすべて外す。公開そのものは止めない。"""
    record = require_manageable_subject(artifacts, projects, caller, subject)
    now = clock()
    tokens = view_token.without_expired(record.get("viewTokens"), now)
    revoked_count = len(view_token.active_tokens(tokens, now))

    tokens = view_token.all_revoked(tokens, now)
    save_tokens(artifacts, projects, clock, record, tokens)
    gate.replace_grants(subject, view_token.grants(tokens, now))
    return {"revoked": revoked_count}
