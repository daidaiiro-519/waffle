"""投稿者の名簿を扱うテストが共有する結線と偽実装。

偽実装をテストごとに作ると少しずつ食い違い、実物なら失敗する場面で緑になる。
1か所に置いて、名簿に関わるすべてのテストがここを使う。
"""
import json

import main
from application.ports import Caller
from usecase_builder import build  # noqa: F401  再輸出

from fakes import FakeKeyStore, FakeStore  # noqa: F401  再輸出

ADMIN = Caller("admin-1", is_admin=True)
SOMEONE = Caller("publisher-2")
NOW = 1_700_000_000


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
