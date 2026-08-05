"""プロジェクトのテストが共有する結線と補助。

偽実装をテストごとに作ると少しずつ食い違い、実物なら失敗する場面で緑になる。
1か所に置いて、プロジェクトに関わるすべてのテストがここを使う。

個人と共有の別は、閲覧の可否ではなく書き換えの可否である。したがって
閲覧ゲートはこの別を知らず、判定はすべて業務の側に閉じる。
"""
import json

import main
from application.ports import Caller
from application.usecases.create_project import CreateProject
from usecase_builder import build

from publish_setup import FakeKeyStore, FakeStore  # noqa: F401  再輸出

X = Caller("publisher-x")
Y = Caller("publisher-y")
ADMIN = Caller("admin-1", is_admin=True)

NOW = 1_700_000_000
VIEWER_DOMAIN = "viewer.example.net"


def setup():
    return main.Connections(
        store=FakeStore(), keys=FakeKeyStore(),
        project_page='<html data-project="{{プロジェクトID}}"></html>',
        now=lambda: NOW, viewer_domain=VIEWER_DOMAIN,
    )


def index_of(deps, project_id):
    """保管に残っているプロジェクトの記録。"""
    return json.loads(deps.store.get(f"projects/{project_id}.json"))


def listing_of(deps, project_id):
    """閲覧の面へ置かれた、そのプロジェクトの中身の一覧。"""
    return json.loads(deps.store.get(f"proj/{project_id}/index.json"))


def owned(deps, caller=X, name="検索基盤リニューアル", scope="PERSONAL"):
    return build(deps, CreateProject).run(caller, name, scope)
