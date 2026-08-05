"""招かれている顔ぶれを見る操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-list-publishers
"""
import pytest

from publisher_setup import ADMIN, SOMEONE, setup
from application.usecases.list_publishers import ListPublishers
from shared.errors import PublisherError
from usecase_builder import build


def _rows(deps, caller=ADMIN):
    return {row.id: row for row in build(deps, ListPublishers).run(caller)}


def test_招かれている人がすべて並ぶ():
    """
    Scenario: 招かれている人がすべて並ぶ
    When 管理者Aが一覧を求める
    Then 管理者Aと投稿者Xの両方が並ぶ
    """
    deps, _ = setup()

    rows = _rows(deps)

    assert set(rows) == {"admin-1", "publisher-2"}


def test_管理者かどうかが分かる():
    """
    Scenario: 管理者かどうかが分かる
    When 管理者Aが一覧を求める
    Then A は管理者として、X はそうでないと分かる
    """
    deps, _ = setup()

    rows = _rows(deps)

    assert rows["admin-1"].admin is True
    assert rows["publisher-2"].admin is False


def test_まだ入っていない人を見分けられる():
    """
    Scenario: まだ入っていない人を見分けられる
    Given 投稿者Zが招かれたが、まだ自分の合言葉を決めていない
    When 管理者Aが一覧を求める
    Then Z が、まだ入っていない状態として並ぶ
    """
    deps, _ = setup(people={
        "admin-1": {"email": "admin@example.com", "status": "active"},
        "invited-1": {"email": "yet@example.com", "status": "invited"},
    })

    rows = _rows(deps)

    assert rows["invited-1"].status == "invited"
    assert rows["admin-1"].status == "active"


def test_合言葉に関わるものは一切出ない():
    """
    Scenario: 合言葉に関わるものは一切出ない
    When 管理者Aが一覧を求める
    Then 返った一覧のどこにも、合言葉や仮の合言葉は現れない
    """
    deps, _ = setup()

    rows = _rows(deps)

    for row in rows.values():
        assert not hasattr(row, "password")
        assert not hasattr(row, "temporaryPassword")
    assert "password" not in repr(rows).lower()


def test_管理者でない者は顔ぶれを見られない():
    """
    Scenario: 管理者でない者は顔ぶれを見られない
    When 投稿者Xが一覧を求める
    Then 管理者でないことを理由に拒まれる
    And 顔ぶれは一切返らない
    """
    deps, _ = setup()

    with pytest.raises(PublisherError) as x:
        build(deps, ListPublishers).run(SOMEONE)

    assert x.value.code == "NOT_ADMINISTRATOR"
