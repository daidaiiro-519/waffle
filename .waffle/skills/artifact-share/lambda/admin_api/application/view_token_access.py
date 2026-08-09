"""閲覧トークンを扱ってよい対象を取り出し、書き戻す。

共有アーティファクトとプロジェクトのどちらにも同じ形で閲覧トークンを渡すため、
置き場所の違いだけをここで吸収する。4つの操作が同じ取り出し方をするので、
1か所に置く。
"""
from __future__ import annotations

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from domain.value_objects.view_subject import ARTIFACT, ViewSubject
from shared.errors import ApplicationError

TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
TOKEN_NOT_FOUND = "TOKEN_NOT_FOUND"
TOKEN_LIMIT_REACHED = "TOKEN_LIMIT_REACHED"
DUPLICATE_TOKEN_NAME = "DUPLICATE_TOKEN_NAME"
EXPIRY_TOO_FAR = "EXPIRY_TOO_FAR"


class ViewTokenError(ApplicationError):
    """閲覧トークンを扱えない。"""


def require_manageable_subject(artifacts: SharedArtifactRepository,
                               projects: ProjectRepository, caller: Caller,
                               subject: ViewSubject):
    """扱ってよい対象を取り出す。扱えないものは見つからないものとして扱う。

    共有アーティファクトかプロジェクトのどちらかを返す。どちらも
    with_view_tokens で顔ぶれを差し替えられるので、呼び出し側は種別を
    見分けなくてよい。

    Args:
        artifacts: 共有アーティファクトの保管。
        projects: プロジェクトの保管。
        caller: 要求してきた人。
        subject: 閲覧トークンで開ける対象。

    Returns:
        扱ってよい対象の集約。

    Raises:
        ArtifactError: 共有アーティファクトが見つからない、または扱えない。
        ProjectError: プロジェクトが見つからない、または扱えない。
    """
    found = (artifacts if subject.kind == ARTIFACT else projects).find(subject.id)
    if found is None or not found.manageable_by(caller.id, caller.is_admin):
        raise ViewTokenError(TARGET_NOT_FOUND, "見つかりません。")
    return found


def save_tokens(artifacts: SharedArtifactRepository, projects: ProjectRepository,
                clock: Clock, subject: ViewSubject, target, tokens) -> None:
    """顔ぶれを差し替えて残す。置き場所だけを種別で振り分ける。

    Args:
        artifacts: 共有アーティファクトの保管。
        projects: プロジェクトの保管。
        clock: いまの時点を得る手段。
        subject: 閲覧トークンで開ける対象。
        target: 対象の集約。
        tokens: 差し替える閲覧トークンの顔ぶれ。

    Returns:
        なし。

    Raises:
        なし。
    """
    updated = target.with_view_tokens(tuple(tokens), clock())
    if subject.kind == ARTIFACT:
        artifacts.save(updated)
    else:
        projects.save(updated)
