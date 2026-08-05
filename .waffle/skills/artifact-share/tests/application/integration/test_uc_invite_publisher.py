"""招く・外す操作が守る約束を確かめる。

対象の仕様: uc-invite-publisher（操作保証）
"""
from publisher_setup import ADMIN, artifact_owned_by, setup
from application.usecases.invite_publisher import InvitePublisher
from usecase_builder import build


def test_外しても閲覧トークンは失効しない():
    """
    Scenario: 外しても閲覧トークンは失効しない
    Given 閲覧者が共有アーティファクトAの閲覧トークンを持っている
    When 管理者がAの投稿者を外す
    Then 閲覧者はそれまでの閲覧トークンでAを開ける
    """
    deps, _ = setup(objects=artifact_owned_by("publisher-2"))
    deps.keys.put("token:aaaaaaaa", "abc|0|1")
    before = dict(deps.keys.keys)

    build(deps, InvitePublisher).run("remove", ADMIN, publisher_id="publisher-2")

    assert deps.keys.keys == before
