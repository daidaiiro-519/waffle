"""受け取った操作名が、正しい行き先へ渡ることを確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

ここは長らく検証の外に置かれていた（実際の接続を組み立てるだけ、という
理由で）。だが振り分け自体は接続を要さない純粋な対応づけで、しかも
間違えたときの被害が大きい——以前は連なった分岐の最後が名簿からの削除で、
行き先を書き忘れた操作はすべて黙って削除を実行する形だった。

ユースケースが型になったので、差し替えるのは唯一の入口（run）にする。届いた
時点で止め、どの型のどの操作へ届いたかだけを見る。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main  # noqa: E402
from adapters.inbound import admin_api  # noqa: E402
from application.ports import Caller  # noqa: E402
from shared.errors import ManageError  # noqa: E402


class Reached(Exception):
    """行き先へ届いたことだけを確かめたいので、届いた時点で止める。"""

    def __init__(self, where, passed):
        # args という名前は Exception 自身が使うため避ける
        super().__init__(where)
        self.where, self.passed = where, passed


# 行き先として名乗る型。ここに無い型へ届いたら、その時点で分かる
USECASES = [
    "AssignArtifactToProject", "BrowseProjects", "ControlProjectAccess", "CreateProject",
    "ExportArtifact", "InvitePublisher", "IssueViewToken", "ListMyArtifacts",
    "ListPublishers", "ListViewTokens", "ReadComments", "ReplaceArtifactContent",
    "ResumeArtifact", "RevokeAllViewTokens", "RevokeViewToken", "SuspendArtifact",
    "TransferArtifact",
]


@pytest.fixture(autouse=True)
def stub_every_destination(monkeypatch):
    """どの型へ届いても、その名前を持って止まるようにする。"""
    for name in USECASES:
        usecase = getattr(admin_api, name)
        monkeypatch.setattr(
            usecase, "run",
            (lambda n: lambda self, *a, **k: (_ for _ in ()).throw(
                Reached(n, a + tuple(k.values()))))(name),
            raising=False)


# 行き先だけを見たいので、結線は空でよい。ただし経路表は束から口を取り出して
# 渡すため、属性そのものは在る必要がある
EMPTY = main.Connections(store=None, keys=None, now=None)


def destination_of(action, body=None):
    with pytest.raises(Reached) as x:
        admin_api.dispatch(action, EMPTY, Caller("p1"), body or {})
    passed = x.value.passed
    # 操作を分岐で持つ型は、最初の引数がその識別子になる
    if passed and isinstance(passed[0], str):
        return f"{x.value.where}.{passed[0]}"
    return x.value.where


# ── 行き先の対応 ────────────────────────────────────────

ROUTING = {
    "list": "ListMyArtifacts",
    "replace": "ReplaceArtifactContent",
    "disable": "SuspendArtifact",
    "enable": "ResumeArtifact",
    "assign": "AssignArtifactToProject.assign",
    "unassign": "AssignArtifactToProject.unassign",
    "transfer": "TransferArtifact",
    "issue-token": "IssueViewToken",
    "view-tokens": "ListViewTokens",
    "revoke-token": "RevokeViewToken",
    "revoke-all-tokens": "RevokeAllViewTokens",
    "comments": "ReadComments",
    "export": "ExportArtifact",
    "invite": "InvitePublisher.invite",
    "publishers": "ListPublishers",
    "resend-invite": "InvitePublisher.resend",
    "remove-publisher": "InvitePublisher.remove",
    "projects": "BrowseProjects.list",
    "project": "BrowseProjects.detail",
    "create-project": "CreateProject",
    "disable-project": "ControlProjectAccess.suspend",
    "enable-project": "ControlProjectAccess.resume",
}


@pytest.mark.parametrize("action,expected", sorted(ROUTING.items()))
def test_操作が意図した行き先へ届く(action, expected):
    assert destination_of(action) == expected


def test_名簿からの削除はその操作でしか起きない():
    """以前は、行き先の無い操作すべてがここへ落ちていた"""
    reached = [a for a in ROUTING if destination_of(a) == "InvitePublisher.remove"]
    assert reached == ["remove-publisher"]


def test_知らない操作は落ちる():
    with pytest.raises(ManageError) as x:
        admin_api.dispatch("こんな操作はない", EMPTY, Caller("p1"), {})
    assert x.value.code == "UNKNOWN_ACTION"


# ── 表と受け付ける操作の一致 ────────────────────────────

def test_受け付ける操作はすべて行き先を持つ():
    """片方だけ増やすと、受け付けたのに行き先が無い操作ができる"""
    assert admin_api.ACTIONS - {"publish"} == set(admin_api.ROUTES)


def test_この検証が表の全部を見ている():
    assert set(ROUTING) == set(admin_api.ROUTES)


# ── 渡す値 ──────────────────────────────────────────────

def test_body_の値がそのまま渡る():
    with pytest.raises(Reached) as x:
        admin_api.dispatch("assign", EMPTY, Caller("p1"),
                       {"artifactId": "aaa", "projectId": "ppp"})
    _operation, caller, artifact_id, project_id = x.value.passed
    assert (caller.id, artifact_id, project_id) == ("p1", "aaa", "ppp")


def test_無い値は空文字として渡る():
    """呼び出し側の欠落を、行き先の手前で例外にしない（判定は行き先が持つ）"""
    with pytest.raises(Reached) as x:
        admin_api.dispatch("disable", EMPTY, Caller("p1"), {})
    assert x.value.passed[-1] == ""
