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

import main  # noqa: E402
import manage  # noqa: E402


class Reached(Exception):
    """行き先へ届いたことだけを確かめたいので、届いた時点で止める。"""

    def __init__(self, where, passed):
        # args という名前は Exception 自身が使うため避ける
        super().__init__(where)
        self.where, self.passed = where, passed


@pytest.fixture(autouse=True)
def stub_every_destination(monkeypatch):
    for module_name in ("manage", "publishers", "projects", "comment_store"):
        module = getattr(main, module_name)
        for name in dir(module):
            attr = getattr(module, name)
            if callable(attr) and not name.startswith("_") and name.islower():
                monkeypatch.setattr(
                    module, name,
                    (lambda m, n: lambda *a, **k: (_ for _ in ()).throw(
                        Reached(f"{m}.{n}", a)))(module_name, name),
                    raising=False)


def destination_of(action, body=None):
    with pytest.raises(Reached) as x:
        main._dispatch(action, None, manage.Caller("p1"), body or {})
    return x.value.where


# ── 行き先の対応 ────────────────────────────────────────

ROUTING = {
    "list": "manage.list_artifacts",
    "replace": "manage.replace_content",
    "rotate": "manage.reissue_token",
    "disable": "manage.suspend",
    "enable": "manage.resume",
    "assign": "manage.assign",
    "unassign": "manage.unassign",
    "transfer": "manage.transfer",
    "comments": "comment_store.read",
    "export": "comment_store.export",
    "invite": "publishers.invite",
    "publishers": "publishers.list_publishers",
    "resend-invite": "publishers.resend_invite",
    "remove-publisher": "publishers.remove",
    "projects": "projects.list_projects",
    "project": "projects.detail",
    "create-project": "projects.create",
    "reissue-project": "projects.reissue_token",
    "disable-project": "projects.suspend",
    "enable-project": "projects.resume",
}


@pytest.mark.parametrize("action,expected", sorted(ROUTING.items()))
def test_操作が意図した行き先へ届く(action, expected):
    assert destination_of(action) == expected


def test_名簿からの削除はその操作でしか起きない():
    """以前は、行き先の無い操作すべてがここへ落ちていた"""
    reached_remove = [a for a in ROUTING if destination_of(a) == "publishers.remove"]
    assert reached_remove == ["remove-publisher"]


def test_知らない操作は落ちる():
    with pytest.raises(manage.ManageError) as x:
        main._dispatch("こんな操作はない", None, manage.Caller("p1"), {})
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
        main._dispatch("assign", None, manage.Caller("p1"),
                       {"artifactId": "aaa", "projectId": "ppp"})
    _deps, caller, artifact_id, project_id = x.value.passed
    assert (caller.id, artifact_id, project_id) == ("p1", "aaa", "ppp")


def test_無い値は空文字として渡る():
    """呼び出し側の欠落を、行き先の手前で例外にしない（判定は行き先が持つ）"""
    with pytest.raises(Reached) as x:
        main._dispatch("rotate", None, manage.Caller("p1"), {})
    assert x.value.passed[2] == ""
