"""受け取った操作名が、正しい行き先へ渡ることを確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

ここは長らく検証の外に置かれていた（実際の接続を組み立てるだけ、という
理由で）。だが振り分け自体は接続を要さない純粋な対応づけで、しかも
間違えたときの被害が大きい——以前は連なった分岐の最後が名簿からの削除で、
行き先を書き忘れた操作はすべて黙って削除を実行する形だった。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from application.usecases import (  # noqa: E402
    assign_artifact_to_project,
    browse_projects,
    control_project_access,
    create_project,
    export_artifact,
    invite_publisher,
    issue_view_token,
    list_my_artifacts,
    list_publishers,
    list_view_tokens,
    read_comments,
    replace_artifact_content,
    resume_artifact,
    revoke_all_view_tokens,
    revoke_view_token,
    suspend_artifact,
    transfer_artifact,
)
from application.ports import Caller  # noqa: E402
from shared.errors import ManageError  # noqa: E402

import main  # noqa: E402


class Reached(Exception):
    """行き先へ届いたことだけを確かめたいので、届いた時点で止める。"""

    def __init__(self, where, passed):
        # args という名前は Exception 自身が使うため避ける
        super().__init__(where)
        self.where, self.passed = where, passed


@pytest.fixture(autouse=True)
def stub_every_destination(monkeypatch):
    for module_name in (
        "assign_artifact_to_project",
        "browse_projects",
        "control_project_access",
        "create_project",
        "export_artifact",
        "invite_publisher",
        "issue_view_token",
        "list_my_artifacts",
        "list_publishers",
        "list_view_tokens",
        "publish_artifact",
        "read_comments",
        "replace_artifact_content",
        "resume_artifact",
        "revoke_all_view_tokens",
        "revoke_view_token",
        "suspend_artifact",
        "transfer_artifact",
    ):
        module = getattr(main, module_name)
        for name in dir(module):
            attr = getattr(module, name)
            if callable(attr) and not name.startswith("_") and name.islower():
                monkeypatch.setattr(
                    module, name,
                    (lambda m, n: lambda *a, **k: (_ for _ in ()).throw(
                        Reached(f"{m}.{n}", a)))(module_name, name),
                    raising=False)


# 行き先だけを見たいので、結線は空でよい。ただし経路表は束から口を取り出して
# 渡すため、属性そのものは在る必要がある
EMPTY = main.Connections(store=None, keys=None, now=None)


def destination_of(action, body=None):
    with pytest.raises(Reached) as x:
        main._dispatch(action, EMPTY, Caller("p1"), body or {})
    return x.value.where


# ── 行き先の対応 ────────────────────────────────────────

ROUTING = {
    "list": "list_my_artifacts.list_artifacts",
    "replace": "replace_artifact_content.replace_content",
    "disable": "suspend_artifact.suspend",
    "enable": "resume_artifact.resume",
    "assign": "assign_artifact_to_project.assign",
    "unassign": "assign_artifact_to_project.unassign",
    "transfer": "transfer_artifact.transfer",
    "issue-token": "issue_view_token.issue",
    "view-tokens": "list_view_tokens.list_tokens",
    "revoke-token": "revoke_view_token.revoke",
    "revoke-all-tokens": "revoke_all_view_tokens.revoke_all",
    "comments": "read_comments.read",
    "export": "export_artifact.export",
    "invite": "invite_publisher.invite",
    "publishers": "list_publishers.list_publishers",
    "resend-invite": "invite_publisher.resend_invite",
    "remove-publisher": "invite_publisher.remove",
    "projects": "browse_projects.list_projects",
    "project": "browse_projects.detail",
    "create-project": "create_project.create",
    "disable-project": "control_project_access.suspend",
    "enable-project": "control_project_access.resume",
}


@pytest.mark.parametrize("action,expected", sorted(ROUTING.items()))
def test_操作が意図した行き先へ届く(action, expected):
    assert destination_of(action) == expected


def test_名簿からの削除はその操作でしか起きない():
    """以前は、行き先の無い操作すべてがここへ落ちていた"""
    reached_remove = [a for a in ROUTING if destination_of(a) == "invite_publisher.remove"]
    assert reached_remove == ["remove-publisher"]


def test_知らない操作は落ちる():
    with pytest.raises(ManageError) as x:
        main._dispatch("こんな操作はない", None, Caller("p1"), {})
    assert x.value.code == "UNKNOWN_ACTION"


# ── 表と受け付ける操作の一致 ────────────────────────────

def test_受け付ける操作はすべて行き先を持つ():
    """片方だけ増やすと、受け付けたのに行き先が無い操作ができる"""
    assert main.ACTIONS - {"publish"} == set(main.ROUTES)


def test_この検証が表の全部を見ている():
    assert set(ROUTING) == set(main.ROUTES)


# ── 渡す値 ──────────────────────────────────────────────

def test_body_の値がそのまま渡る():
    with pytest.raises(Reached) as x:
        main._dispatch("assign", EMPTY, Caller("p1"),
                       {"artifactId": "aaa", "projectId": "ppp"})
    caller, artifact_id, project_id = x.value.passed[-3:]
    assert (caller.id, artifact_id, project_id) == ("p1", "aaa", "ppp")


def test_無い値は空文字として渡る():
    """呼び出し側の欠落を、行き先の手前で例外にしない（判定は行き先が持つ）"""
    with pytest.raises(Reached) as x:
        main._dispatch("disable", EMPTY, Caller("p1"), {})
    assert x.value.passed[-1] == ""
