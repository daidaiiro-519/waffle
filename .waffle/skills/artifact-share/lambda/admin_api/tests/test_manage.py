"""公開したあとの管理操作を、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

これらの操作は、Cognitoで本人確認を通った投稿者がブラウザから呼ぶ。
手元のCLIは環境の構築だけを担い、ここには関わらない。

対象の仕様:
  uc-replace-content / uc-reissue-view-token / uc-suspend-artifact /
  uc-resume-artifact / uc-assign-to-project
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import manage  # noqa: E402
import publish  # noqa: E402


class FakeStore:
    def __init__(self, objects=None):
        self.objects = dict(objects or {})

    def put(self, key, body, content_type):
        self.objects[key] = {"body": body, "content_type": content_type}

    def get(self, key):
        if key not in self.objects:
            raise KeyError(key)
        return self.objects[key]["body"]

    def list(self, prefix):
        return [k for k in sorted(self.objects) if k.startswith(prefix)]


class FakeKeyStore:
    def __init__(self, keys=None):
        self.keys = dict(keys or {})

    def put(self, key, value):
        self.keys[key] = value

    def get(self, key):
        if key not in self.keys:
            raise KeyError(key)
        return self.keys[key]


HTML = """<!doctype html><html><head>
<meta name="id" content="adr-x"><meta name="type" content="DecisionRecord">
<meta name="title" content="検索基盤の選定"><title>別</title></head><body>本文</body></html>"""

ME = manage.Caller("publisher-1")
SOMEONE_ELSE = manage.Caller("publisher-2")


def setup(keys=None):
    """公開済みのものが1件ある状態を作り、依存と公開の結果を返す。"""
    store = FakeStore()
    key_store = keys if keys is not None else FakeKeyStore()

    result = publish.publish(
        {"html": HTML, "authorization": "Bearer x"},
        publish.Deps(
            store=store, keys=key_store,
            identify=lambda _t: ME.id,
            wrapper_template="<html>{{アーティファクトID}}</html>",
            now=lambda: 1_700_000_000,
            viewer_domain="viewer.example.net",
        ),
    )
    deps = manage.Deps(
        store=store, keys=key_store,
        now=lambda: 1_700_000_100,
        viewer_domain="viewer.example.net",
    )
    return deps, result


def meta_of(deps, artifact_id):
    return json.loads(deps.store.get(f"meta/{artifact_id}.json"))


# ── 本人以外は触れない ──────────────────────────────────

def test_他人が公開したものは存在しないものとして扱う():
    """存在そのものを漏らさないため、拒否ではなく見つからない扱いにする"""
    deps, r = setup()

    for call in (
        lambda: manage.replace_content(deps, SOMEONE_ELSE, r["artifactId"], HTML),
        lambda: manage.reissue_token(deps, SOMEONE_ELSE, r["artifactId"]),
        lambda: manage.suspend(deps, SOMEONE_ELSE, r["artifactId"]),
    ):
        with pytest.raises(manage.ManageError) as x:
            call()
        assert x.value.code == "ARTIFACT_NOT_FOUND"


def test_一覧には自分が公開したものだけが並ぶ():
    deps, mine = setup()
    other = dict(meta_of(deps, mine["artifactId"]),
                 artifactId="zzzzzzzz", uploadedBy=SOMEONE_ELSE.id)
    deps.store.put("meta/zzzzzzzz.json", json.dumps(other), "application/json")

    ids = [row["artifactId"] for row in manage.list_artifacts(deps, ME)]
    assert ids == [mine["artifactId"]]


def test_一覧にトークンは含まれない():
    """トークンは発行の一度きり。一覧から取り出せてはならない"""
    deps, _ = setup()
    for row in manage.list_artifacts(deps, ME):
        assert "token" not in row


def test_一覧は公開中と停止中を区別して返す():
    deps, r = setup()
    assert manage.list_artifacts(deps, ME)[0]["status"] == "active"
    manage.suspend(deps, ME, r["artifactId"])
    assert manage.list_artifacts(deps, ME)[0]["status"] == "disabled"


# ── 差し替え ────────────────────────────────────────────

def test_差し替えてもURLとトークンの同一性が保たれる():
    """Given 公開済み / When 差し替える / Then IDもトークンも変わらない"""
    deps, r = setup()
    before = deps.keys.get(f"token:{r['artifactId']}")

    new_html = HTML.replace("本文", "直した本文")
    manage.replace_content(deps, ME, r["artifactId"], new_html)

    assert deps.store.get(f"p/{r['artifactId']}/content.html") == new_html
    assert deps.keys.get(f"token:{r['artifactId']}") == before


def test_差し替えると区切りの記録が反応の並びに残る():
    """これより前の指摘が差し替え前のものだと読み取れるようにする"""
    deps, r = setup()
    manage.replace_content(deps, ME, r["artifactId"], HTML.replace("本文", "直した"))

    records = [json.loads(deps.store.get(k))
               for k in deps.store.list(f"comments/{r['artifactId']}/")]
    assert len(records) == 1
    assert records[0]["kind"] == "divider"


def test_公開が止まっているものは差し替えられない():
    deps, r = setup()
    manage.suspend(deps, ME, r["artifactId"])

    with pytest.raises(manage.ManageError) as x:
        manage.replace_content(deps, ME, r["artifactId"], HTML)
    assert x.value.code == "NOT_PUBLISHED"


def test_空の中身には差し替えられない():
    deps, r = setup()
    with pytest.raises(manage.ManageError) as x:
        manage.replace_content(deps, ME, r["artifactId"], "   ")
    assert x.value.code == "EMPTY_CONTENT"


# ── トークンの再発行 ────────────────────────────────────

def test_再発行するとトークンと世代が変わりURLは変わらない():
    deps, r = setup()
    before = deps.keys.get(f"token:{r['artifactId']}")

    again = manage.reissue_token(deps, ME, r["artifactId"])

    after = deps.keys.get(f"token:{r['artifactId']}")
    assert after != before
    assert before.split("|")[2] == "1"
    assert after.split("|")[2] == "2"        # 世代が上がる
    assert again["url"] == r["url"]          # URLは変わらない
    assert again["token"] != r["token"]


# ── 停止と再開 ──────────────────────────────────────────

def test_停止すると開けなくなるがデータは残る():
    deps, r = setup()
    manage.suspend(deps, ME, r["artifactId"])

    assert deps.keys.get(f"token:{r['artifactId']}") == "DISABLED"
    assert deps.store.get(f"p/{r['artifactId']}/content.html")
    assert meta_of(deps, r["artifactId"])["status"] == "disabled"


def test_再開するとトークンが必ず新しくなる():
    """止めた意図が、再開によって失われないことを確かめる"""
    deps, r = setup()
    manage.suspend(deps, ME, r["artifactId"])

    again = manage.resume(deps, ME, r["artifactId"])

    assert again["token"] != r["token"]
    assert deps.keys.get(f"token:{r['artifactId']}").split("|")[2] == "2"
    assert meta_of(deps, r["artifactId"])["status"] == "active"


def test_止まっていないものは再開できない():
    deps, r = setup()
    with pytest.raises(manage.ManageError) as x:
        manage.resume(deps, ME, r["artifactId"])
    assert x.value.code == "NOT_SUSPENDED"


# ── プロジェクトへの出し入れ ────────────────────────────

def test_加えるとプロジェクトのトークンで開ける範囲に入る():
    deps, r = setup(keys=FakeKeyStore({"proj:ppp": "v|0|1"}))

    manage.assign(deps, ME, r["artifactId"], "ppp")

    assert deps.keys.get(f"pp:{r['artifactId']}") == "ppp"
    assert meta_of(deps, r["artifactId"])["projects"] == ["ppp"]


def test_重ねて加えても二重に入らない():
    deps, r = setup(keys=FakeKeyStore({"proj:ppp": "v|0|1"}))
    manage.assign(deps, ME, r["artifactId"], "ppp")
    manage.assign(deps, ME, r["artifactId"], "ppp")

    assert meta_of(deps, r["artifactId"])["projects"] == ["ppp"]


def test_無いプロジェクトへは加えられない():
    deps, r = setup()
    with pytest.raises(manage.ManageError) as x:
        manage.assign(deps, ME, r["artifactId"], "nope")
    assert x.value.code == "PROJECT_NOT_FOUND"


def test_外してもアーティファクト自体は生き続ける():
    deps, r = setup(keys=FakeKeyStore({"proj:ppp": "v|0|1"}))
    manage.assign(deps, ME, r["artifactId"], "ppp")

    manage.unassign(deps, ME, r["artifactId"], "ppp")

    assert meta_of(deps, r["artifactId"])["projects"] == []
    assert deps.keys.get(f"token:{r['artifactId']}") != "DISABLED"   # 個別には開ける
    assert deps.store.get(f"p/{r['artifactId']}/content.html")


def test_中身に書いた分類の目印では所属できない():
    """所属は人の明示的な操作でしか成立しない"""
    deps, r = setup(keys=FakeKeyStore({"proj:ppp": "v|0|1"}))
    tagged = HTML.replace("</head>", '<meta name="tags" content="ppp"></head>')

    manage.replace_content(deps, ME, r["artifactId"], tagged)

    meta = meta_of(deps, r["artifactId"])
    assert meta["tags"] == ["ppp"]      # 目印としては控える
    assert meta["projects"] == []       # 所属は変わらない
    with pytest.raises(KeyError):
        deps.keys.get(f"pp:{r['artifactId']}")
