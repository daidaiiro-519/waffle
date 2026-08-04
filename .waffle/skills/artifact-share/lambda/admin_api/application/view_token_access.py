"""閲覧トークンを扱ってよい対象を取り出し、書き戻す。

共有アーティファクトとプロジェクトのどちらにも同じ形で閲覧トークンを渡すため、
置き場所の違いだけをここで吸収する。4つの操作が同じ取り出し方をするので、
1か所に置く。
"""
from __future__ import annotations

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from domain.publication import manageable_by
from domain.view_subject import ARTIFACT, ViewSubject
from shared.errors import ApplicationError

TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
TOKEN_NOT_FOUND = "TOKEN_NOT_FOUND"
TOKEN_LIMIT_REACHED = "TOKEN_LIMIT_REACHED"
DUPLICATE_TOKEN_NAME = "DUPLICATE_TOKEN_NAME"
EXPIRY_TOO_FAR = "EXPIRY_TOO_FAR"


class ViewTokenError(ApplicationError):
    """閲覧トークンを扱えない。"""


def require_manageable_subject(artifacts: SharedArtifactRepository, projects: ProjectRepository,
          caller: Caller, subject: ViewSubject) -> dict:
    """扱ってよい対象を取り出す。扱えないものは見つからないものとして扱う。"""
    if subject.kind == ARTIFACT:
        record = artifacts.find(subject.id)
        allowed = record is not None and manageable_by(record, caller)
    else:
        record = projects.find(subject.id)
        allowed = record is not None and (
            caller.is_admin or record.get("owner") == caller.id)

    if not allowed:
        raise ViewTokenError(TARGET_NOT_FOUND, "見つかりません。")
    return record


def save_tokens(artifacts: SharedArtifactRepository, projects: ProjectRepository,
          clock: Clock, record: dict, tokens: list[dict]) -> None:
    record["viewTokens"] = tokens
    record["updatedAt"] = clock()
    if "artifactId" in record:
        artifacts.save(record)
    else:
        projects.save(record)
