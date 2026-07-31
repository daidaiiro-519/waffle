"""CLIの振る舞いを、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest scripts/tests/ -v

外部への接続は依存として渡す形にしてあるため、この検証では偽の依存を渡す。
公開の検査そのものは公開の受け口と同じ処理を共有しており、そちらの検証で
確かめてあるため、ここでは CLI が担う部分だけを見る。

対象の仕様:
  uc-publish-artifact / uc-replace-content / uc-reissue-view-token /
  uc-suspend-artifact / uc-resume-artifact / uc-assign-to-project
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import artifactshare as cli  # noqa: E402


class FakeStore:
    def __init__(self, objects=None):
        self.objects = dict(objects or {})
        self.deleted = []

    def put(self, key, body, content_type):
        self.objects[key] = {"body": body, "content_type": content_type}

    def get(self, key):
        if key not in self.objects:
            raise KeyError(key)
        return self.objects[key]["body"]

    def list(self, prefix):
        return [k for k in sorted(self.objects) if k.startswith(prefix)]

    def remove(self, key):
        self.objects.pop(key, None)
        self.deleted.append(key)


class FakeKeyStore:
    def __init__(self, keys=None):
        self.keys = dict(keys or {})

    def put(self, key, value):
        self.keys[key] = value

    def get(self, key):
        if key not in self.keys:
            raise KeyError(key)
        return self.keys[key]


def env(store=None, keys=None):
    return cli.Env(
        store=store if store is not None else FakeStore(),
        keys=keys if keys is not None else FakeKeyStore(),
        wrapper_template="<html>{{アーティファクトID}}/{{表示名}}</html>",
        viewer_domain="viewer.example.net",
        now=lambda: 1_700_000_000,
        publisher="operator",
    )


HTML = """<!doctype html><html><head>
<meta name="id" content="adr-x"><meta name="type" content="DecisionRecord">
<meta name="title" content="検索基盤の選定"><title>別</title></head><body>本文</body></html>"""


def published(e):
    """公開済みの状態を1件作る補助。"""
    return cli.publish(e, html=HTML, display_name=None, projects=[])


# ── 公開 ────────────────────────────────────────────────

def test_公開するとURLとトークンが返り索引が残る():
    e = env()
    r = published(e)

    assert r["url"] == f"https://viewer.example.net/p/{r['artifactId']}/"
    assert r["token"]
    meta = json.loads(e.store.get(f"meta/{r['artifactId']}.json"))
    assert meta["name"] == "検索基盤の選定"
    assert meta["status"] == "active"
    assert meta["uploadedBy"] == "operator"


def test_公開時にプロジェクトへ入れられる():
    e = env(keys=FakeKeyStore({"proj:ppp": "v|0|1"}))
    r = cli.publish(e, html=HTML, display_name=None, projects=["ppp"])

    meta = json.loads(e.store.get(f"meta/{r['artifactId']}.json"))
    assert meta["projects"] == ["ppp"]
    assert e.keys.get(f"pp:{r['artifactId']}") == "ppp"


# ── 差し替え ────────────────────────────────────────────

def test_差し替えてもURLとトークンと索引の同一性が保たれる():
    """Given 公開済み / When 差し替える / Then IDもトークンも変わらない"""
    e = env()
    r = published(e)
    before = e.keys.get(f"token:{r['artifactId']}")

    new_html = HTML.replace("本文", "直した本文")
    cli.replace_content(e, r["artifactId"], new_html)

    assert e.store.get(f"p/{r['artifactId']}/content.html") == new_html
    assert e.keys.get(f"token:{r['artifactId']}") == before   # トークンは変わらない


def test_差し替えると区切りの記録が反応の並びに残る():
    """これより前の指摘が差し替え前のものだと読み取れるようにする"""
    e = env()
    r = published(e)
    cli.replace_content(e, r["artifactId"], HTML.replace("本文", "直した"))

    dividers = [
        json.loads(e.store.get(k))
        for k in e.store.list(f"comments/{r['artifactId']}/")
    ]
    assert len(dividers) == 1
    assert dividers[0]["kind"] == "divider"


def test_公開が止まっているものは差し替えられない():
    e = env()
    r = published(e)
    cli.suspend(e, r["artifactId"])

    with pytest.raises(cli.CliError) as x:
        cli.replace_content(e, r["artifactId"], HTML)
    assert x.value.code == "NOT_PUBLISHED"


# ── トークンの再発行 ────────────────────────────────────

def test_再発行するとトークンと世代が変わりURLは変わらない():
    e = env()
    r = published(e)
    before = e.keys.get(f"token:{r['artifactId']}")

    again = cli.reissue_token(e, r["artifactId"])

    after = e.keys.get(f"token:{r['artifactId']}")
    assert after != before
    assert after.split("|")[2] == "2"                 # 世代が上がる
    assert before.split("|")[2] == "1"
    assert again["url"] == r["url"]                   # URLは不変
    assert again["token"] != r["token"]


# ── 停止と再開 ──────────────────────────────────────────

def test_停止すると開けなくなるがデータは残る():
    e = env()
    r = published(e)
    cli.suspend(e, r["artifactId"])

    assert e.keys.get(f"token:{r['artifactId']}") == "DISABLED"
    assert e.store.get(f"p/{r['artifactId']}/content.html")        # 中身は残る
    assert json.loads(e.store.get(f"meta/{r['artifactId']}.json"))["status"] == "disabled"


def test_再開するとトークンが必ず新しくなる():
    """止めた意図が、再開によって失われないことを確かめる"""
    e = env()
    r = published(e)
    cli.suspend(e, r["artifactId"])

    again = cli.resume(e, r["artifactId"])

    assert again["token"] != r["token"]
    assert e.keys.get(f"token:{r['artifactId']}").split("|")[2] == "2"
    assert json.loads(e.store.get(f"meta/{r['artifactId']}.json"))["status"] == "active"


def test_止まっていないものは再開できない():
    e = env()
    r = published(e)
    with pytest.raises(cli.CliError) as x:
        cli.resume(e, r["artifactId"])
    assert x.value.code == "NOT_SUSPENDED"


# ── プロジェクトへの出し入れ ────────────────────────────

def test_加えるとプロジェクトのトークンで開ける範囲に入る():
    e = env(keys=FakeKeyStore({"proj:ppp": "v|0|1"}))
    r = published(e)

    cli.assign(e, r["artifactId"], "ppp")

    assert e.keys.get(f"pp:{r['artifactId']}") == "ppp"
    assert json.loads(e.store.get(f"meta/{r['artifactId']}.json"))["projects"] == ["ppp"]


def test_重ねて加えても二重に入らない():
    e = env(keys=FakeKeyStore({"proj:ppp": "v|0|1"}))
    r = published(e)
    cli.assign(e, r["artifactId"], "ppp")
    cli.assign(e, r["artifactId"], "ppp")

    assert json.loads(e.store.get(f"meta/{r['artifactId']}.json"))["projects"] == ["ppp"]


def test_外してもアーティファクト自体は生き続ける():
    e = env(keys=FakeKeyStore({"proj:ppp": "v|0|1"}))
    r = published(e)
    cli.assign(e, r["artifactId"], "ppp")

    cli.unassign(e, r["artifactId"], "ppp")

    assert json.loads(e.store.get(f"meta/{r['artifactId']}.json"))["projects"] == []
    assert e.keys.get(f"token:{r['artifactId']}") != "DISABLED"   # 個別には開ける
    assert e.store.get(f"p/{r['artifactId']}/content.html")


def test_中身に書いた分類の目印では所属できない():
    """所属は人の明示的な操作でしか成立しない"""
    e = env(keys=FakeKeyStore({"proj:ppp": "v|0|1"}))
    tagged = HTML.replace('content="DecisionRecord"', 'content="DecisionRecord"') \
                 .replace("</head>", '<meta name="tags" content="ppp"></head>')

    r = cli.publish(e, html=tagged, display_name=None, projects=[])

    meta = json.loads(e.store.get(f"meta/{r['artifactId']}.json"))
    assert meta["tags"] == ["ppp"]      # 目印としては控える
    assert meta["projects"] == []       # 所属は変わらない
    with pytest.raises(KeyError):
        e.keys.get(f"pp:{r['artifactId']}")


# ── 一覧 ────────────────────────────────────────────────

def test_一覧は公開中と停止中を区別して返す():
    e = env()
    a = published(e)
    b = published(e)
    cli.suspend(e, b["artifactId"])

    rows = {row["artifactId"]: row for row in cli.list_artifacts(e)}
    assert rows[a["artifactId"]]["status"] == "active"
    assert rows[b["artifactId"]]["status"] == "disabled"


def test_一覧にトークンは含まれない():
    """トークンは発行の一度きり。一覧から取り出せてはならない"""
    e = env()
    published(e)
    for row in cli.list_artifacts(e):
        assert "token" not in row
