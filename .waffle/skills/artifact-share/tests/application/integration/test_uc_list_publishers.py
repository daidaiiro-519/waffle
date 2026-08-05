"""顔ぶれを見る操作が守る約束を確かめる。

対象の仕様: uc-list-publishers（操作保証）
"""
from publisher_setup import ADMIN, setup
from application.usecases.list_publishers import ListPublishers
from usecase_builder import build


def test_何度見ても名簿は変わらない():
    """
    Scenario: 何度見ても名簿は変わらない
    Given 管理者Aが一覧を見ている
    When 同じ一覧をもう一度求める
    Then 同じ顔ぶれが返る
    And 誰の状態も変わっていない
    """
    deps, directory = setup()
    first = build(deps, ListPublishers).run(ADMIN)
    people_before = {pid: dict(p) for pid, p in directory.people.items()}

    second = build(deps, ListPublishers).run(ADMIN)

    assert second == first
    assert directory.people == people_before
