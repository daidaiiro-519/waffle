"""1つの対象へ複数の閲覧トークンを渡す操作を、受け入れ基準に沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

相手ごとに別々の閲覧トークンを渡し、あとから1本だけ外せることがこの仕組みの
要になる。1本を外すために他の相手まで巻き添えで外れると、外す操作が使いにくく
なり、結局使われなくなる。

対象の仕様:
  uc-issue-view-token / uc-list-view-tokens /
  uc-revoke-view-token / uc-revoke-all-view-tokens
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from application.usecases import (  # noqa: E402
    issue_view_token,
    list_view_tokens,
    revoke_all_view_tokens,
    revoke_view_token,
)
from application.view_token_access import ViewTokenError  # noqa: E402

from adapters.outbound.kvs_view_gate import KvsViewGate  # noqa: E402
from application.ports import Caller  # noqa: E402
from domain import view_token  # noqa: E402
from domain.view_subject import ViewSubject  # noqa: E402

ME = Caller("publisher-1")
OTHER = Caller("publisher-2")
ADMIN = Caller("admin-1", is_admin=True)

NOW = 1_700_000_000
AID = "aaaaaaaa"
PID = "p7k2xq"


class FakeKeys:
    def __init__(self):
        self.written = {}

    def put(self, key, value):
        self.written[key] = value

    def get(self, key):
        return self.written[key]


class FakeRepo:
    """識別子で引ける記録の置き場所。共有アーティファクトにもプロジェクトにも使う。"""

    def __init__(self, records=None):
        self.records = dict(records or {})

    def find(self, key):
        return self.records.get(key)

    def save(self, record):
        self.records[record.get("artifactId") or record["projectId"]] = record

    def all(self):
        return list(self.records.values()), 0


def setup(tokens=None, owner="publisher-1"):
    """公開済みのものが1件あり、プロジェクトも1つある状態を作る。"""
    artifacts = FakeRepo({AID: {"artifactId": AID, "uploadedBy": owner,
                                "status": "active", "viewTokens": list(tokens or [])}})
    projects = FakeRepo({PID: {"projectId": PID, "owner": owner,
                               "status": "active", "viewTokens": list(tokens or [])}})
    return artifacts, projects, KvsViewGate(FakeKeys())


def clock_at(t=NOW):
    return lambda: t


def issue(artifacts, projects, gate, name, ttl=None, caller=ME,
          subject=None, at=NOW):
    return issue_view_token.issue(artifacts, projects, gate, clock_at(at), caller,
                             subject or ViewSubject.artifact(AID), name, ttl)


# ── 発行 ────────────────────────────────────────────────

def test_名前と期限を指定して発行すると値が一度だけ返る():
    """Given 公開済み / When 名前を付けて発行する / Then 値と期限が返る"""
    artifacts, projects, gate = setup()

    r = issue(artifacts, projects, gate, "レビュー班", ttl=view_token.WEEK)

    assert r["token"]
    assert r["name"] == "レビュー班"
    assert r["expiresAt"] == NOW + view_token.WEEK
    assert r["tokenShownOnce"] is True
    # 記録には値そのものが残らない
    stored = artifacts.find(AID)["viewTokens"]
    assert r["token"] not in str(stored)


def test_期限を指定しなければ1週間になる():
    artifacts, projects, gate = setup()

    r = issue(artifacts, projects, gate, "レビュー班")

    assert r["expiresAt"] == NOW + view_token.WEEK


def test_共有アーティファクトへ1ヶ月を超える期限は付けられない():
    """遠い先を選べると、期限があることが形だけになる"""
    artifacts, projects, gate = setup()

    with pytest.raises(ViewTokenError) as x:
        issue(artifacts, projects, gate, "ずっと", ttl=view_token.MONTH + 1)
    assert x.value.code == "EXPIRY_TOO_FAR"
    assert artifacts.find(AID)["viewTokens"] == []


def test_プロジェクトには期限なしを選べる():
    """回覧するものと、置いておく場は別の扱いにする"""
    artifacts, projects, gate = setup()

    r = issue(artifacts, projects, gate, "常設", ttl=0,
              subject=ViewSubject.project(PID))

    assert r["expiresAt"] == view_token.NO_EXPIRY


def test_上限に達していたら発行しない():
    artifacts, projects, gate = setup()
    for i in range(view_token.MAX_ACTIVE):
        issue(artifacts, projects, gate, f"相手{i}")

    with pytest.raises(ViewTokenError) as x:
        issue(artifacts, projects, gate, "もう1人")
    assert x.value.code == "TOKEN_LIMIT_REACHED"
    assert len(artifacts.find(AID)["viewTokens"]) == view_token.MAX_ACTIVE


def test_期限切れは上限の数に含めない():
    """外す対象にならないものが枠を埋め続けると、いつか頭打ちになる"""
    artifacts, projects, gate = setup()
    for i in range(view_token.MAX_ACTIVE):
        issue(artifacts, projects, gate, f"相手{i}", ttl=view_token.WEEK)

    later = NOW + view_token.WEEK + 1
    r = issue(artifacts, projects, gate, "新しい相手", at=later)

    assert r["token"]
    assert len(artifacts.find(AID)["viewTokens"]) == 1


def test_有効なものに同じ名前があれば発行しない():
    """同じ名前が2つあると、どれを外すか選ぶ操作そのものが成り立たない"""
    artifacts, projects, gate = setup()
    issue(artifacts, projects, gate, "レビュー班")

    with pytest.raises(ViewTokenError) as x:
        issue(artifacts, projects, gate, "レビュー班")
    assert x.value.code == "DUPLICATE_TOKEN_NAME"


def test_発行しても前の閲覧トークンは無効にならない():
    artifacts, projects, gate = setup()
    first = issue(artifacts, projects, gate, "1人目")

    issue(artifacts, projects, gate, "2人目")

    names = [t["name"] for t in
             view_token.active_tokens(artifacts.find(AID)["viewTokens"], NOW)]
    assert names == ["1人目", "2人目"]
    assert gate._keys.written["token:" + AID].count(";") == 1
    assert first["token"]


def test_招かれていない者は発行できない():
    artifacts, projects, gate = setup()

    with pytest.raises(ViewTokenError) as x:
        issue(artifacts, projects, gate, "勝手に", caller=OTHER)
    assert x.value.code == "TARGET_NOT_FOUND"


# ── 一覧 ────────────────────────────────────────────────

def test_一覧は名前と期限を返し値は返さない():
    artifacts, projects, gate = setup()
    issue(artifacts, projects, gate, "レビュー班", ttl=view_token.WEEK)

    got = list_view_tokens.list_tokens(artifacts, projects, clock_at(), ME,
                                  ViewSubject.artifact(AID))

    assert [t["name"] for t in got["viewTokens"]] == ["レビュー班"]
    assert got["viewTokens"][0]["expiresAt"] == NOW + view_token.WEEK
    assert "token" not in got["viewTokens"][0]
    assert "fingerprint" not in got["viewTokens"][0]


def test_期限を過ぎたものは一覧に現れず記録も残らない():
    artifacts, projects, gate = setup()
    issue(artifacts, projects, gate, "短い", ttl=view_token.WEEK)

    later = NOW + view_token.WEEK + 1
    got = list_view_tokens.list_tokens(artifacts, projects, clock_at(later), ME,
                                  ViewSubject.artifact(AID))
    assert got["viewTokens"] == []

    # 次に何かを書くときに記録からも消える
    issue(artifacts, projects, gate, "新しい相手", at=later)
    assert len(artifacts.find(AID)["viewTokens"]) == 1


def test_1本も無ければ空の一覧が返る():
    artifacts, projects, gate = setup()

    got = list_view_tokens.list_tokens(artifacts, projects, clock_at(), ME,
                                  ViewSubject.artifact(AID))
    assert got["viewTokens"] == []


# ── 無効化 ──────────────────────────────────────────────

def test_1本だけを無効にでき他はそのまま():
    artifacts, projects, gate = setup()
    a = issue(artifacts, projects, gate, "1人目")
    issue(artifacts, projects, gate, "2人目")

    revoke_view_token.revoke(artifacts, projects, gate, clock_at(), ME,
                       ViewSubject.artifact(AID), a["tokenId"])

    left = view_token.active_tokens(artifacts.find(AID)["viewTokens"], NOW)
    assert [t["name"] for t in left] == ["2人目"]
    # 閲覧の面へも、残った1本だけが渡っている
    assert gate._keys.written["token:" + AID].count(";") == 0


def test_無効化しても公開は止まらない():
    artifacts, projects, gate = setup()
    a = issue(artifacts, projects, gate, "1人目")

    revoke_view_token.revoke(artifacts, projects, gate, clock_at(), ME,
                       ViewSubject.artifact(AID), a["tokenId"])

    assert artifacts.find(AID)["status"] == "active"
    assert gate._keys.written["token:" + AID] != "DISABLED"


def test_既に無効なものを無効にしても成功する():
    artifacts, projects, gate = setup()
    a = issue(artifacts, projects, gate, "1人目")
    subject = ViewSubject.artifact(AID)
    revoke_view_token.revoke(artifacts, projects, gate, clock_at(), ME, subject, a["tokenId"])

    got = revoke_view_token.revoke(artifacts, projects, gate, clock_at(), ME,
                             subject, a["tokenId"])
    assert got["revoked"] is True


def test_無い閲覧トークンは無効にできない():
    artifacts, projects, gate = setup()

    with pytest.raises(ViewTokenError) as x:
        revoke_view_token.revoke(artifacts, projects, gate, clock_at(), ME,
                           ViewSubject.artifact(AID), "nope")
    assert x.value.code == "TOKEN_NOT_FOUND"


def test_一括で外しても公開は止まらない():
    artifacts, projects, gate = setup()
    issue(artifacts, projects, gate, "1人目")
    issue(artifacts, projects, gate, "2人目")

    got = revoke_all_view_tokens.revoke_all(artifacts, projects, gate, clock_at(), ME,
                                 ViewSubject.artifact(AID))

    assert got["revoked"] == 2
    assert view_token.active_tokens(artifacts.find(AID)["viewTokens"], NOW) == []
    assert artifacts.find(AID)["status"] == "active"
    assert gate._keys.written["token:" + AID] == ""


def test_一括で外してもまとめの閲覧トークンは使えたまま():
    """共有アーティファクト側を全部外しても、入っているプロジェクトからは開ける"""
    artifacts, projects, gate = setup()
    issue(artifacts, projects, gate, "まとめ", subject=ViewSubject.project(PID))
    issue(artifacts, projects, gate, "個別")

    revoke_all_view_tokens.revoke_all(artifacts, projects, gate, clock_at(), ME,
                           ViewSubject.artifact(AID))

    assert gate._keys.written["proj:" + PID] != ""


def test_1本も無い状態で一括して外しても成功する():
    artifacts, projects, gate = setup()

    got = revoke_all_view_tokens.revoke_all(artifacts, projects, gate, clock_at(), ME,
                                 ViewSubject.artifact(AID))
    assert got["revoked"] == 0


def test_管理者は他人のものも扱える():
    artifacts, projects, gate = setup(owner="publisher-2")

    r = issue(artifacts, projects, gate, "管理者から", caller=ADMIN)
    assert r["token"]
