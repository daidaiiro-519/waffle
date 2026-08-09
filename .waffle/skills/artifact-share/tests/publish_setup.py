"""公開のテストが共有する結線と偽実装。

偽実装をテストごとに作ると少しずつ食い違い、実物なら失敗する場面で緑になる。
1か所に置いて、公開に関わるすべてのテストがここを使う。

外部への接続は依存として渡す形にしてあるため、この検証では偽の依存を渡す。
"""
from adapters.outbound.kvs_view_gate import KvsViewGate
from adapters.outbound.stored_shared_artifact_repository import (
    StoredSharedArtifactRepository,
)
from adapters.outbound.stored_viewer_site import StoredViewerSite
from application.usecases.publish_artifact import PublishArtifact

from fakes import FakeIdGenerator, FakeKeyStore, FakeStore  # noqa: F401  再輸出

NOW = 1_700_000_000


def publishing(store=None, keys=None, user="publisher-1",
               wrapper="<html>{{アーティファクトID}}</html>"):
    """公開の口を組み立てたユースケースを返す。"""
    store = store if store is not None else FakeStore()
    return PublishArtifact(
        StoredSharedArtifactRepository(store),
        StoredViewerSite(store, wrapper_template=wrapper),
        KvsViewGate(keys if keys is not None else FakeKeyStore()),
        lambda _token: user,
        lambda: NOW,
        FakeIdGenerator(),
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

# 外部の場所を2件参照する文書。件数は仕様のシナリオが述べる数に合わせる
WITH_TWO_EXTERNAL = """<!doctype html><html><head>
<link rel="stylesheet" href="https://fonts.example.com/x.css">
<title>ダッシュボード</title></head><body>
<img src="https://images.example.com/a.png"></body></html>"""

WITH_THREE_EXTERNAL = """<!doctype html><html><head>
<link rel="stylesheet" href="https://fonts.example.com/x.css">
<title>ダッシュボード</title></head><body>
<img src="https://images.example.com/a.png"><script src="https://cdn.example.com/b.js"></script>
</body></html>"""
