"""管理APIの振る舞いを、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-publish-artifact（受け入れ基準6件・エラー3件・操作保証2件）
外部への接続は依存として渡す形にしてあるため、この検証では偽の依存を渡す。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from application.usecases import (  # noqa: E402
    publish_artifact,
)

from shared.errors import PublishError  # noqa: E402

from adapters.outbound.kvs_view_gate import KvsViewGate  # noqa: E402
from adapters.outbound.stored_viewer_site import StoredViewerSite  # noqa: E402
from adapters.outbound.stored_shared_artifact_repository import (  # noqa: E402
    StoredSharedArtifactRepository,
)
from domain import html_inspection, identifier  # noqa: E402


# ── 偽の依存 ────────────────────────────────────────────

class FakeStore:
    """保管への書き込みを記録するだけの偽物。失敗させることもできる。"""

    def __init__(self, fail_on=None):
        self.objects = {}
        self.fail_on = fail_on

    def put(self, key, body, content_type):
        if self.fail_on and self.fail_on in key:
            raise RuntimeError("書き込みに失敗しました")
        self.objects[key] = {"body": body, "content_type": content_type}


class FakeKeyStore:
    def __init__(self, fail=False):
        self.keys = {}
        self.fail = fail

    def put(self, key, value):
        if self.fail:
            raise RuntimeError("トークンの保管に失敗しました")
        self.keys[key] = value


def wiring(store=None, keys=None, user="publisher-1", wrapper="<html>{{アーティファクトID}}</html>"):
    """公開が要る口を組み立てて返す。名前で渡すので、口が増えても呼び側は動かない。"""
    store = store if store is not None else FakeStore()
    return dict(
        artifacts=StoredSharedArtifactRepository(store),
        viewer=StoredViewerSite(store, wrapper_template=wrapper),
        gate=KvsViewGate(keys if keys is not None else FakeKeyStore()),
        identify=lambda _token: user,
        clock=lambda: 1_700_000_000,
    )


WITH_META = """<!doctype html><html><head>
<meta name="id" content="adr-search-backend">
<meta name="type" content="DecisionRecord">
<meta name="title" content="検索基盤にPostgreSQLを採用する">
<meta name="description" content="新規ミドルウェアを入れず既存DBの拡張で実装する判断">
<meta name="tags" content="backend, search, database">
<title>別の題名</title></head><body>本文</body></html>"""

WITHOUT_META = """<!doctype html><html><head>
<title>会員登録フローの離脱率メモ</title></head><body>本文</body></html>"""

WITH_EXTERNAL = """<!doctype html><html><head>
<link rel="stylesheet" href="https://fonts.example.com/x.css">
<title>ダッシュボード</title></head><body>
<img src="https://images.example.com/a.png"><script src="https://cdn.example.com/b.js"></script>
</body></html>"""


# ── 受け入れシナリオ ────────────────────────────────────

def test_識別情報が添えられていれば何も尋ねずに公開できる():
    """Given metaタグがある / When 公開する / Then 居場所とトークンが返り、情報が控えられる"""
    result = publish_artifact.publish(request={"html": WITH_META, "authorization": "Bearer x"}, **wiring())

    assert result["artifactId"]
    assert result["token"]
    assert result["url"].endswith("/p/" + result["artifactId"] + "/")
    assert result["descriptor"]["title"] == "検索基盤にPostgreSQLを採用する"
    assert result["descriptor"]["docType"] == "DecisionRecord"
    assert result["descriptor"]["documentId"] == "adr-search-backend"
    assert result["descriptor"]["tags"] == ["backend", "search", "database"]
    assert result["metaSource"] == "extracted"
    assert result["needsName"] is False


def test_識別情報が無ければ題名を尋ねる():
    """Given metaタグが無い / When 題名を与えずに公開しようとする / Then 題名を尋ねられる"""
    with pytest.raises(PublishError) as e:
        publish_artifact.publish(request={"html": WITHOUT_META, "authorization": "Bearer x"}, **wiring())
    assert e.value.code == "NAME_REQUIRED"


def test_題名を与えれば識別情報が無くても公開できる():
    result = publish_artifact.publish(request={"html": WITHOUT_META, "displayName": "離脱率メモ", "authorization": "Bearer x"}, **wiring())
    assert result["artifactId"]
    assert result["descriptor"]["title"] == "離脱率メモ"
    assert result["metaSource"] == "manual"


def test_渡したHTMLがそのまま保たれる():
    """Given HTMLを渡す / When 公開する / Then 保管された中身は渡したものと完全に一致する"""
    store = FakeStore()
    result = publish_artifact.publish(request={"html": WITH_META, "authorization": "Bearer x"}, **wiring(store=store))

    content_key = "p/" + result["artifactId"] + "/content.html"
    assert store.objects[content_key]["body"] == WITH_META
    assert store.objects[content_key]["content_type"].startswith("text/html")


def test_閲覧画面が別に配置されアーティファクトIDが埋まる():
    store = FakeStore()
    result = publish_artifact.publish(request={"html": WITH_META, "authorization": "Bearer x"}, **wiring(store=store))

    index_key = "p/" + result["artifactId"] + "/index.html"
    assert result["artifactId"] in store.objects[index_key]["body"]
    assert "{{アーティファクトID}}" not in store.objects[index_key]["body"]


def test_招かれていない者は公開できない():
    """Given 招かれていない / When 公開しようとする / Then 拒まれ、何も残らない"""
    store, keys = FakeStore(), FakeKeyStore()
    d = wiring(store=store, keys=keys, user=None, wrapper="<html></html>")
    with pytest.raises(PublishError) as e:
        publish_artifact.publish(request={"html": WITH_META, "authorization": "Bearer bad"}, **d)
    assert e.value.code == "NOT_INVITED"
    assert store.objects == {}
    assert keys.keys == {}


def test_外部への参照は件数を添えて公開する():
    """Given 外部を3件参照している / When 公開する / Then 公開はされ、件数が伝わる"""
    result = publish_artifact.publish(request={"html": WITH_EXTERNAL, "displayName": "d", "authorization": "Bearer x"}, **wiring())
    assert result["externalRefs"] == 3
    assert result["artifactId"]


def test_空のHTMLは公開できない():
    with pytest.raises(PublishError) as e:
        publish_artifact.publish(request={"html": "   ", "authorization": "Bearer x"}, **wiring())
    assert e.value.code == "EMPTY_CONTENT"


# ── 操作保証 ────────────────────────────────────────────

def test_トークンは保管された記録から取り出せない():
    """返したトークンそのものは保管に残さない（照合の形と期限だけを残す）"""
    keys = FakeKeyStore()
    result = publish_artifact.publish(request={"html": WITH_META, "authorization": "Bearer x"}, **wiring(keys=keys))

    record = keys.keys["token:" + result["artifactId"]]
    value, expires = record.split("|")
    assert value != result["token"]          # そのままは残さない
    assert int(expires) > 0                  # 期限は必ず付く


def test_途中で失敗したら開ける状態のものが残らない():
    """Given 途中で失敗する / When 公開しようとする / Then トークンが無く、誰も開けない

    管理APIには削除の権限が無いため、置かれたファイルそのものは残る。開ける状態の
    ものが残らないことを、トークンを最後に書く順序で保証する。
    """
    store, keys = FakeStore(fail_on="index.html"), FakeKeyStore()
    with pytest.raises(PublishError) as e:
        publish_artifact.publish(request={"html": WITH_META, "authorization": "Bearer x"}, **wiring(store=store, keys=keys))
    assert e.value.code == "PUBLISH_FAILED"
    assert keys.keys == {}                   # トークンが無いので閲覧ゲートが拒む


def test_トークンは配置がすべて済んでから書かれる():
    """トークンの書き込みで失敗しても、それは最後の一手なので順序は崩れない"""
    store, keys = FakeStore(), FakeKeyStore(fail=True)
    with pytest.raises(PublishError):
        publish_artifact.publish(request={"html": WITH_META, "authorization": "Bearer x"}, **wiring(store=store, keys=keys))
    assert keys.keys == {}                   # 開ける状態にはならない
    assert len(store.objects) == 3           # 配置自体は済んでいる（到達はできない）


# ── 検査（純粋な処理） ──────────────────────────────────

def test_metaタグを読み取る():
    d = html_inspection.inspect_html(WITH_META)
    assert d["documentId"] == "adr-search-backend"
    assert d["docType"] == "DecisionRecord"
    assert d["title"] == "検索基盤にPostgreSQLを採用する"   # titleタグより優先する
    assert d["tags"] == ["backend", "search", "database"]
    assert d["detected"] is True


def test_metaタグが無ければタイトルだけ拾う():
    d = html_inspection.inspect_html(WITHOUT_META)
    assert d["detected"] is False
    assert d["title"] == "会員登録フローの離脱率メモ"
    assert d["docType"] == ""


def test_外部への参照を数える():
    assert html_inspection.inspect_html(WITH_EXTERNAL)["externalRefs"] == 3
    assert html_inspection.inspect_html(WITH_META)["externalRefs"] == 0


def test_data_URIは外部への参照に数えない():
    html = '<html><body><img src="data:image/png;base64,AAAA"></body></html>'
    assert html_inspection.inspect_html(html)["externalRefs"] == 0


def test_アーティファクトIDは紛らわしい文字を避ける():
    ids = {identifier.new_artifact_id() for _ in range(200)}
    assert len(ids) == 200                      # 重ならない
    for value in ids:
        assert len(value) == 8
        assert not set(value) & set("lo01")     # 読み間違えやすい文字を使わない
