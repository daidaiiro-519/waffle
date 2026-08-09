"""公開について、受け入れシナリオの外側で守りたいこと。

実行:  python3 -m pytest tests/ -v

シナリオと1対1で対応するものは application/acceptance/ と
application/integration/ にある。ここに残すのは、どのシナリオにも書かれて
いないが崩れると困ること——閲覧画面の組み立て、metaタグの読み取り、
外部参照の数え方、識別子の作り方。

対象の仕様: uc-publish-artifact（受け入れ基準のうち、シナリオを持たないもの）
"""
import pytest

from publish_setup import (
    WITH_META, WITH_THREE_EXTERNAL, WITHOUT_META, FakeKeyStore, FakeStore, publishing,
)
from adapters.outbound.random_identifier import RandomIdGenerator
from domain.services import html_inspection
from shared.errors import PublishError


def test_閲覧画面が別に配置されアーティファクトIDが埋まる():
    store = FakeStore()

    result = publishing(store=store).run({"html": WITH_META, "authorization": "Bearer x"})

    index = store.objects["p/" + result.artifact_id + "/index.html"]["body"]
    assert result.artifact_id in index
    assert "{{アーティファクトID}}" not in index


def test_トークンは配置がすべて済んでから書かれる():
    """トークンの書き込みで失敗しても、それは最後の一手なので順序は崩れない"""
    store, keys = FakeStore(), FakeKeyStore(fail=True)

    with pytest.raises(PublishError):
        publishing(store=store, keys=keys).run(
            {"html": WITH_META, "authorization": "Bearer x"})

    assert keys.keys == {}  # 開ける状態にはならない
    # 中身・閲覧画面・雛形の版・記録の4つは置き終えている（到達はできない）
    assert len(store.objects) == 4


def test_metaタグを読み取る():
    d = html_inspection.inspect_html(WITH_META)
    assert d.document_id == "adr-search-backend"
    assert d.doc_type == "DecisionRecord"
    assert d.title == "検索基盤にPostgreSQLを採用する"   # titleタグより優先する
    assert d.labels == ("backend", "search", "database")
    assert d.detected is True


def test_metaタグが無ければタイトルだけ拾う():
    d = html_inspection.inspect_html(WITHOUT_META)
    assert d.detected is False
    assert d.title == "会員登録フローの離脱率メモ"
    assert d.doc_type == ""


def test_外部への参照を数える():
    assert html_inspection.inspect_html(WITH_THREE_EXTERNAL).external_refs == 3
    assert html_inspection.inspect_html(WITH_META).external_refs == 0


def test_data_URIは外部への参照に数えない():
    html = '<html><body><img src="data:image/png;base64,AAAA"></body></html>'
    assert html_inspection.inspect_html(html).external_refs == 0


def test_アーティファクトIDは紛らわしい文字を避ける():
    ids = {RandomIdGenerator().new_artifact_id().value for _ in range(200)}
    assert len(ids) == 200                      # 重ならない
    for value in ids:
        assert len(value) == 8
        assert not set(value) & set("lo01")     # 読み間違えやすい文字を使わない
