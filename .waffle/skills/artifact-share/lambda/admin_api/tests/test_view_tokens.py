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

from usecase_builder import build  # noqa: E402
from application.usecases.issue_view_token import IssueViewToken  # noqa: E402
from application.usecases.list_view_tokens import ListViewTokens  # noqa: E402
from application.usecases.revoke_all_view_tokens import RevokeAllViewTokens  # noqa: E402
from application.usecases.revoke_view_token import RevokeViewToken  # noqa: E402

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


class Wiring:
    """検証のための結線の束。合成ルートが持つのと同じ名前で口を持つ。"""

    def __init__(self, artifacts, projects, gate, at=None):
        self.artifacts, self.projects, self.gate = artifacts, projects, gate
        self.comments = self.viewer = self.directory = self.identify = None
        self.now = (lambda: at) if at is not None else (lambda: NOW)

    def at(self, when):
        """時計だけを進めた同じ結線。"""
        return Wiring(self.artifacts, self.projects, self.gate, at=when)


def setup(tokens=None, owner="publisher-1"):
    """公開済みのものが1件あり、プロジェクトも1つある状態を作る。"""
    artifacts = FakeRepo({AID: {"artifactId": AID, "uploadedBy": owner,
                                "status": "active", "viewTokens": list(tokens or [])}})
    projects = FakeRepo({PID: {"projectId": PID, "owner": owner,
                               "status": "active", "viewTokens": list(tokens or [])}})
    gate = KvsViewGate(FakeKeys())
    return Wiring(artifacts, projects, gate)


def issue(deps, name, ttl=None, caller=ME, subject=None, at=NOW):
    return build(deps.at(at), IssueViewToken).run(
        caller, subject or ViewSubject.artifact(AID), name, ttl)


# ── 発行 ────────────────────────────────────────────────

def test_名前と期限を指定して発行すると値が一度だけ返る():
    """Given 公開済み / When 名前を付けて発行する / Then 値と期限が返る"""
    deps = setup()

    r = issue(deps, "レビュー班", ttl=view_token.WEEK)

    assert r["token"]
    assert r["name"] == "レビュー班"
    assert r["expiresAt"] == NOW + view_token.WEEK
    assert r["tokenShownOnce"] is True
    # 記録には値そのものが残らない
    stored = deps.artifacts.find(AID)["viewTokens"]
    assert r["token"] not in str(stored)


def test_期限を指定しなければ1週間になる():
    deps = setup()

    r = issue(deps, "レビュー班")

    assert r["expiresAt"] == NOW + view_token.WEEK


def test_共有アーティファクトへ1ヶ月を超える期限は付けられない():
    """遠い先を選べると、期限があることが形だけになる"""
    deps = setup()

    with pytest.raises(ViewTokenError) as x:
        issue(deps, "ずっと", ttl=view_token.MONTH + 1)
    assert x.value.code == "EXPIRY_TOO_FAR"
    assert deps.artifacts.find(AID)["viewTokens"] == []


def test_プロジェクトには期限なしを選べる():
    """回覧するものと、置いておく場は別の扱いにする"""
    deps = setup()

    r = issue(deps, "常設", ttl=0,
              subject=ViewSubject.project(PID))

    assert r["expiresAt"] == view_token.NO_EXPIRY


def test_上限に達していたら発行しない():
    deps = setup()
    for i in range(view_token.MAX_ACTIVE):
        issue(deps, f"相手{i}")

    with pytest.raises(ViewTokenError) as x:
        issue(deps, "もう1人")
    assert x.value.code == "TOKEN_LIMIT_REACHED"
    assert len(deps.artifacts.find(AID)["viewTokens"]) == view_token.MAX_ACTIVE


def test_期限切れは上限の数に含めない():
    """外す対象にならないものが枠を埋め続けると、いつか頭打ちになる"""
    deps = setup()
    for i in range(view_token.MAX_ACTIVE):
        issue(deps, f"相手{i}", ttl=view_token.WEEK)

    later = NOW + view_token.WEEK + 1
    r = issue(deps, "新しい相手", at=later)

    assert r["token"]
    assert len(deps.artifacts.find(AID)["viewTokens"]) == 1


def test_有効なものに同じ名前があれば発行しない():
    """同じ名前が2つあると、どれを外すか選ぶ操作そのものが成り立たない"""
    deps = setup()
    issue(deps, "レビュー班")

    with pytest.raises(ViewTokenError) as x:
        issue(deps, "レビュー班")
    assert x.value.code == "DUPLICATE_TOKEN_NAME"


def test_発行しても前の閲覧トークンは無効にならない():
    deps = setup()
    first = issue(deps, "1人目")

    issue(deps, "2人目")

    names = [t["name"] for t in
             view_token.active_tokens(deps.artifacts.find(AID)["viewTokens"], NOW)]
    assert names == ["1人目", "2人目"]
    assert deps.gate._keys.written["token:" + AID].count(";") == 1
    assert first["token"]


def test_招かれていない者は発行できない():
    deps = setup()

    with pytest.raises(ViewTokenError) as x:
        issue(deps, "勝手に", caller=OTHER)
    assert x.value.code == "TARGET_NOT_FOUND"


# ── 一覧 ────────────────────────────────────────────────

def test_一覧は名前と期限を返し値は返さない():
    deps = setup()
    issue(deps, "レビュー班", ttl=view_token.WEEK)

    got = build(deps, ListViewTokens).run(ME, ViewSubject.artifact(AID))

    assert [t["name"] for t in got["viewTokens"]] == ["レビュー班"]
    assert got["viewTokens"][0]["expiresAt"] == NOW + view_token.WEEK
    assert "token" not in got["viewTokens"][0]
    assert "fingerprint" not in got["viewTokens"][0]


def test_期限を過ぎたものは一覧に現れず記録も残らない():
    deps = setup()
    issue(deps, "短い", ttl=view_token.WEEK)

    later = NOW + view_token.WEEK + 1
    got = build(deps.at(later), ListViewTokens).run(ME, ViewSubject.artifact(AID))
    assert got["viewTokens"] == []

    # 次に何かを書くときに記録からも消える
    issue(deps, "新しい相手", at=later)
    assert len(deps.artifacts.find(AID)["viewTokens"]) == 1


def test_1本も無ければ空の一覧が返る():
    deps = setup()

    got = build(deps, ListViewTokens).run(ME, ViewSubject.artifact(AID))
    assert got["viewTokens"] == []


# ── 無効化 ──────────────────────────────────────────────

def test_1本だけを無効にでき他はそのまま():
    deps = setup()
    a = issue(deps, "1人目")
    issue(deps, "2人目")

    build(deps, RevokeViewToken).run(ME, ViewSubject.artifact(AID), a["tokenId"])

    left = view_token.active_tokens(deps.artifacts.find(AID)["viewTokens"], NOW)
    assert [t["name"] for t in left] == ["2人目"]
    # 閲覧の面へも、残った1本だけが渡っている
    assert deps.gate._keys.written["token:" + AID].count(";") == 0


def test_無効化しても公開は止まらない():
    deps = setup()
    a = issue(deps, "1人目")

    build(deps, RevokeViewToken).run(ME, ViewSubject.artifact(AID), a["tokenId"])

    assert deps.artifacts.find(AID)["status"] == "active"
    assert deps.gate._keys.written["token:" + AID] != "DISABLED"


def test_既に無効なものを無効にしても成功する():
    deps = setup()
    a = issue(deps, "1人目")
    subject = ViewSubject.artifact(AID)
    build(deps, RevokeViewToken).run(ME, subject, a["tokenId"])

    got = build(deps, RevokeViewToken).run(ME, subject, a["tokenId"])
    assert got["revoked"] is True


def test_無い閲覧トークンは無効にできない():
    deps = setup()

    with pytest.raises(ViewTokenError) as x:
        build(deps, RevokeViewToken).run(ME, ViewSubject.artifact(AID), "nope")
    assert x.value.code == "TOKEN_NOT_FOUND"


def test_一括で外しても公開は止まらない():
    deps = setup()
    issue(deps, "1人目")
    issue(deps, "2人目")

    got = build(deps, RevokeAllViewTokens).run(ME, ViewSubject.artifact(AID))

    assert got["revoked"] == 2
    assert view_token.active_tokens(deps.artifacts.find(AID)["viewTokens"], NOW) == []
    assert deps.artifacts.find(AID)["status"] == "active"
    assert deps.gate._keys.written["token:" + AID] == ""


def test_一括で外してもまとめの閲覧トークンは使えたまま():
    """共有アーティファクト側を全部外しても、入っているプロジェクトからは開ける"""
    deps = setup()
    issue(deps, "まとめ", subject=ViewSubject.project(PID))
    issue(deps, "個別")

    build(deps, RevokeAllViewTokens).run(ME, ViewSubject.artifact(AID))

    assert deps.gate._keys.written["proj:" + PID] != ""


def test_1本も無い状態で一括して外しても成功する():
    deps = setup()

    got = build(deps, RevokeAllViewTokens).run(ME, ViewSubject.artifact(AID))
    assert got["revoked"] == 0


def test_管理者は他人のものも扱える():
    deps = setup(owner="publisher-2")

    r = issue(deps, "管理者から", caller=ADMIN)
    assert r["token"]
