"""文書を渡して公開する操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。仕様の文言が変われば、ここが古いままであることに
気づける。

対象の仕様: uc-publish-artifact
"""
import pytest

from publish_setup import (
    WITH_META, WITH_TWO_EXTERNAL, WITHOUT_META, FakeKeyStore, FakeStore, publishing,
)
from shared.errors import PublishError


def test_識別のための情報が添えられた文書を公開する():
    """
    Scenario: 識別のための情報が添えられた文書を公開する
    Given 文書に題名・要約・種別・分類の目印が添えられている
    When 投稿者がその文書を渡して公開する
    Then 共有URLと閲覧トークンが返る
    And 添えられていた情報が控えられている
    And 投稿者は何も尋ねられない
    """
    result = publishing().run({"html": WITH_META, "authorization": "Bearer x"})

    assert result.url.endswith("/p/" + result.artifact_id + "/")
    assert result.token
    assert result.descriptor.title == "検索基盤にPostgreSQLを採用する"
    assert result.descriptor.doc_type == "DecisionRecord"
    assert result.descriptor.document_id == "adr-search-backend"
    assert result.descriptor.tags == ("backend", "search", "database")
    assert result.meta_source == "extracted"
    assert result.needs_name is False


def test_識別のための情報が無い文書には題名だけを尋ねる():
    """
    Scenario: 識別のための情報が無い文書には題名だけを尋ねる
    Given 文書に識別のための情報が添えられていない
    When 投稿者がその文書を渡して公開しようとする
    Then 題名を尋ねられる
    And 題名を与えると共有URLと閲覧トークンが返る
    """
    with pytest.raises(PublishError) as e:
        publishing().run({"html": WITHOUT_META, "authorization": "Bearer x"})
    assert e.value.code == "NAME_REQUIRED"

    result = publishing().run(
        {"html": WITHOUT_META, "displayName": "離脱率メモ", "authorization": "Bearer x"})

    assert result.url.endswith("/p/" + result.artifact_id + "/")
    assert result.token
    assert result.descriptor.title == "離脱率メモ"
    assert result.meta_source == "manual"


def test_渡した文書がそのまま保たれる():
    """
    Scenario: 渡した文書がそのまま保たれる
    Given 投稿者が文書を渡している
    When 公開する
    Then 公開された中身は、渡した文書と完全に一致する
    """
    store = FakeStore()

    result = publishing(store=store).run({"html": WITH_META, "authorization": "Bearer x"})

    content = store.objects["p/" + result.artifact_id + "/content.html"]
    assert content["body"] == WITH_META
    assert content["content_type"].startswith("text/html")


def test_招かれていない者は公開できない():
    """
    Scenario: 招かれていない者は公開できない
    Given 操作する者が招かれた投稿者でない
    When 文書を渡して公開しようとする
    Then NOT_INVITED として拒まれる
    And 共有URLも閲覧トークンも発行されない
    """
    store, keys = FakeStore(), FakeKeyStore()

    with pytest.raises(PublishError) as e:
        publishing(store=store, keys=keys, user=None, wrapper="<html></html>").run(
            {"html": WITH_META, "authorization": "Bearer bad"})

    assert e.value.code == "NOT_INVITED"
    assert store.objects == {}
    assert keys.written == {}


def test_外部の場所を参照していれば件数を伝える():
    """
    Scenario: 外部の場所を参照していれば件数を伝える
    Given 文書が外部の場所にあるものを2件参照している
    When 投稿者がその文書を渡して公開する
    Then 参照が2件あることが投稿者に伝えられる
    And 公開そのものは行われる
    """
    result = publishing().run(
        {"html": WITH_TWO_EXTERNAL, "displayName": "ダッシュボード",
         "authorization": "Bearer x"})

    assert result.external_refs == 2
    assert result.artifact_id


def test_空の文書は公開できない():
    """
    Scenario: 空の文書は公開できない
    Given 渡された文書が空である
    When 公開しようとする
    Then EMPTY_CONTENT として拒まれる
    """
    with pytest.raises(PublishError) as e:
        publishing().run({"html": "   ", "authorization": "Bearer x"})

    assert e.value.code == "EMPTY_CONTENT"
