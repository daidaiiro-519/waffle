"""公開できる人の出し入れを、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-invite-publisher（受け入れ基準8件・エラー3件・操作保証2件）
名簿への接続は依存として渡す形にしてあるため、この検証では偽の名簿を渡す。
"""

import main
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import manage  # noqa: E402
import publishers  # noqa: E402

from test_manage import FakeKeyStore, FakeStore  # noqa: E402

ADMIN = manage.Caller("admin-1", is_admin=True)
SOMEONE = manage.Caller("publisher-2")


class FakeDirectory:
    """招かれている人の名簿。実物はこの文脈の外にある。"""

    def __init__(self, people=None):
        self.people = dict(people or {})   # id -> {"email", "status"}

    def find(self, publisher_id):
        return self.people.get(publisher_id)

    def invite(self, email):
        # 宛先で入る設定のため、名簿が持つ識別子は宛先とは別の値になる
        for pid, person in self.people.items():
            if person["email"] == email:
                return pid                  # 既に招かれていればそのまま返す
        pid = f"id-{len(self.people) + 1}"
        self.people[pid] = {"email": email, "status": "invited"}
        return pid

    def remove(self, publisher_id):
        self.people.pop(publisher_id, None)

    def list(self):
        return [{"id": pid, "email": p["email"], "status": p["status"]}
                for pid, p in sorted(self.people.items())]

    def admins(self):
        return {"admin-1"}

    def resend(self, publisher_id):
        self.resent = getattr(self, "resent", [])
        self.resent.append(publisher_id)


def setup(people=None, objects=None):
    directory = FakeDirectory(people if people is not None else {
        "admin-1": {"email": "admin@example.com", "status": "active"},
        "publisher-2": {"email": "p2@example.com", "status": "active"},
    })
    deps = main.Connections(
        store=FakeStore(objects or {}), keys=FakeKeyStore(),
        directory=directory, now=lambda: 1_700_000_000,
        viewer_domain="viewer.example.net",
    )
    return deps, directory


def artifact_owned_by(publisher, artifact_id="aaaaaaaa", status="active"):
    meta = {"artifactId": artifact_id, "name": "文書", "status": status,
            "projects": [], "tags": [], "uploadedBy": publisher, "updatedAt": 1}
    return {f"meta/{artifact_id}.json": {"body": json.dumps(meta),
                                         "content_type": "application/json"}}


# ── 招く ────────────────────────────────────────────────

def test_招かれた人は公開できるようになる():
    deps, directory = setup()
    result = publishers.invite(deps.directory, ADMIN, "new@example.com")

    assert directory.find(result["publisherId"])["email"] == "new@example.com"
    assert result["event"] == "PublisherInvited"


def test_管理者でない者は招けない():
    deps, directory = setup()
    before = dict(directory.people)

    with pytest.raises(publishers.PublisherError) as x:
        publishers.invite(deps.directory, SOMEONE, "new@example.com")

    assert x.value.code == "NOT_ADMINISTRATOR"
    assert directory.people == before      # 名簿は変わっていない


def test_重ねて招いても増えず状態も変わらない():
    """Given 既に招かれている / When もう一度招く / Then 二重にならない"""
    deps, directory = setup()
    first = publishers.invite(deps.directory, ADMIN, "new@example.com")
    count = len(directory.people)

    again = publishers.invite(deps.directory, ADMIN, "new@example.com")

    assert again["publisherId"] == first["publisherId"]
    assert len(directory.people) == count


# ── 外す ────────────────────────────────────────────────

def test_外された人は名簿から消える():
    deps, directory = setup()
    publishers.remove(deps.artifacts, deps.store, deps.directory, ADMIN, "publisher-2")
    assert directory.find("publisher-2") is None


def test_外しても公開したものは残る():
    """Given その人が公開している / When 外す / Then 公開されたまま残る

    閲覧者の手元の共有URLが、投稿者の異動で黙って死んではならない。
    """
    deps, _ = setup(objects=artifact_owned_by("publisher-2"))
    deps.keys.put("token:aaaaaaaa", "abc|0|1")

    publishers.remove(deps.artifacts, deps.store, deps.directory, ADMIN, "publisher-2")

    meta = json.loads(deps.store.get("meta/aaaaaaaa.json"))
    assert meta["status"] == "active"
    assert deps.keys.get("token:aaaaaaaa") == "abc|0|1"   # 閲覧トークンも失効しない


def test_手入れできなくなるものがあれば件数を伝える():
    objects = {}
    for i in range(3):
        objects.update(artifact_owned_by("publisher-2", f"art{i}"))
    deps, _ = setup(objects=objects)

    result = publishers.remove(deps.artifacts, deps.store, deps.directory, ADMIN, "publisher-2")

    assert result["orphanedArtifacts"] == 3


def test_管理者は自分自身を外せない():
    """管理者が一人もいない状態へ落ちる経路を塞ぐ"""
    deps, directory = setup()
    with pytest.raises(publishers.PublisherError) as x:
        publishers.remove(deps.artifacts, deps.store, deps.directory, ADMIN, ADMIN.id)
    assert x.value.code == "CANNOT_REMOVE_SELF"
    assert directory.find(ADMIN.id) is not None


def test_招かれていない人は外せない():
    deps, _ = setup()
    with pytest.raises(publishers.PublisherError) as x:
        publishers.remove(deps.artifacts, deps.store, deps.directory, ADMIN, "no-such-person")
    assert x.value.code == "PUBLISHER_NOT_FOUND"


def test_管理者でない者は外せない():
    deps, directory = setup()
    with pytest.raises(publishers.PublisherError) as x:
        publishers.remove(deps.artifacts, deps.store, deps.directory, SOMEONE, "admin-1")
    assert x.value.code == "NOT_ADMINISTRATOR"
    assert directory.find("admin-1") is not None


# ── 一覧 ────────────────────────────────────────────────

def test_招かれている人を一覧できる():
    deps, _ = setup()
    rows = {r["id"]: r for r in publishers.list_publishers(deps.directory, ADMIN)}

    assert set(rows) == {"admin-1", "publisher-2"}
    assert rows["admin-1"]["admin"] is True       # 管理者は印がつく
    assert rows["publisher-2"]["admin"] is False
    assert rows["publisher-2"]["email"] == "p2@example.com"


def test_管理者でなければ一覧できない():
    """誰が招かれているかは、投稿者どうしには見せない"""
    deps, _ = setup()
    with pytest.raises(publishers.PublisherError) as x:
        publishers.list_publishers(deps.directory, SOMEONE)
    assert x.value.code == "NOT_ADMINISTRATOR"


def test_一覧に合言葉に関わるものが含まれない():
    deps, _ = setup()
    for row in publishers.list_publishers(deps.directory, ADMIN):
        assert set(row) == {"id", "name", "email", "status", "admin"}


# ── 招待を送り直す ──────────────────────────────────────

def test_招待に応じていない人へ送り直せる():
    """仮のパスワードを無くした人は、自分では解決できない。
    その状態では利用者プールの再設定が使えないため、招き直すしかない。"""
    deps, directory = setup(people={
        "admin-1": {"email": "admin@example.com", "status": "active"},
        "newbie": {"email": "new@example.com", "status": "invited"},
    })

    result = publishers.resend_invite(deps.directory, ADMIN, "newbie")

    assert result["event"] == "PublisherInvited"
    assert directory.resent == ["newbie"]


def test_既に入っている人へは送り直さない():
    """送り直すと仮のパスワードに戻り、本人が決めたものが使えなくなる"""
    deps, directory = setup()
    with pytest.raises(publishers.PublisherError) as x:
        publishers.resend_invite(deps.directory, ADMIN, "publisher-2")
    assert x.value.code == "ALREADY_ACTIVE"
    assert getattr(directory, "resent", []) == []


def test_管理者でなければ送り直せない():
    deps, _ = setup(people={
        "admin-1": {"email": "admin@example.com", "status": "active"},
        "newbie": {"email": "new@example.com", "status": "invited"},
    })
    with pytest.raises(publishers.PublisherError) as x:
        publishers.resend_invite(deps.directory, manage.Caller("newbie"), "newbie")
    assert x.value.code == "NOT_ADMINISTRATOR"


def test_招かれていない人へは送り直せない():
    deps, _ = setup()
    with pytest.raises(publishers.PublisherError) as x:
        publishers.resend_invite(deps.directory, ADMIN, "no-such-person")
    assert x.value.code == "PUBLISHER_NOT_FOUND"


def test_招待が返す識別子は一覧のものと揃っている():
    """揃っていないと、招いた直後に引き継ぎ先として指せない。
    宛先で入る設定のため、名簿の識別子は宛先そのものではない。"""
    deps, _ = setup()
    invited = publishers.invite(deps.directory, ADMIN, "new@example.com")

    listed = {r["id"] for r in publishers.list_publishers(deps.directory, ADMIN)}
    assert invited["publisherId"] in listed
