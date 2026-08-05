"""公開済みのものを扱うテストが共有する結線と補助。

偽実装をテストごとに作ると少しずつ食い違い、実物なら失敗する場面で緑になる。
1か所に置いて、公開後の操作に関わるすべてのテストがここを使う。
"""
import json

import main
from application.ports import Caller
from application.usecases.create_project import CreateProject
from application.usecases.publish_artifact import PublishArtifact
from usecase_builder import build

from fakes import FakeKeyStore, FakeStore  # noqa: F401  再輸出

HTML = """<!doctype html><html><head>
<meta name="id" content="adr-x"><meta name="type" content="DecisionRecord">
<meta name="title" content="検索基盤の選定"><title>別</title></head><body>本文</body></html>"""

NOW = 1_700_000_000
LATER = NOW + 100
VIEWER_DOMAIN = "viewer.example.net"

ME = Caller("publisher-1")
SOMEONE_ELSE = Caller("publisher-2")
OTHER = Caller("publisher-9")
ADMIN = Caller("admin-1", is_admin=True)


def setup(keys=None):
    """公開済みのものが1件ある状態を作り、結線と公開の結果を返す。"""
    store = FakeStore()
    key_store = keys if keys is not None else FakeKeyStore()

    publishing = main.Connections(
        store=store, keys=key_store, identify=lambda _t: ME.id,
        wrapper_template="<html>{{アーティファクトID}}</html>",
        now=lambda: NOW, viewer_domain=VIEWER_DOMAIN)
    result = build(publishing, PublishArtifact).run(
        {"html": HTML, "authorization": "Bearer x"})

    deps = main.Connections(store=store, keys=key_store, now=lambda: LATER,
                            viewer_domain=VIEWER_DOMAIN)
    return deps, result


def with_project(scope, owner=None):
    """公開済みのもの1件と、プロジェクト1つがある状態。既定では自分が作ったもの。"""
    deps, r = setup()
    deps.project_page = "<html>{{プロジェクトID}}</html>"
    p = build(deps, CreateProject).run(owner or ME, "まとめ", scope)
    return deps, r, p.project_id


def project(deps, scope="SHARED", owner=None, name="別のまとめ"):
    """もう1つプロジェクトを足す。"""
    return build(deps, CreateProject).run(owner or ME, name, scope).project_id


def meta_of(deps, artifact_id):
    """保管に残っている共有アーティファクトの記録。"""
    return json.loads(deps.store.get(f"meta/{artifact_id}.json"))


def listing_of(deps, project_id):
    """閲覧の面へ置かれた、そのプロジェクトの中身の一覧。"""
    return json.loads(deps.store.get(f"proj/{project_id}/index.json"))


def publish_other(deps, caller, html=None):
    """別の投稿者として、もう1件公開する。"""
    publishing = main.Connections(
        store=deps.store, keys=deps.keys, identify=lambda _t: caller.id,
        wrapper_template="<html>{{アーティファクトID}}</html>",
        now=lambda: NOW, viewer_domain=VIEWER_DOMAIN)
    return build(publishing, PublishArtifact).run(
        {"html": html or HTML, "authorization": "Bearer x"})
