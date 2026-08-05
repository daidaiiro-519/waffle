"""投稿者を招く・外す操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-invite-publisher
"""
import json

import pytest

from publisher_setup import ADMIN, SOMEONE, artifact_owned_by, setup
from application.usecases.invite_publisher import InvitePublisher
from shared.errors import PublisherError
from usecase_builder import build


def _invite(deps, caller=ADMIN, **kwargs):
    return build(deps, InvitePublisher).run("invite", caller, **kwargs)


def _remove(deps, caller=ADMIN, **kwargs):
    return build(deps, InvitePublisher).run("remove", caller, **kwargs)


def test_招かれた人が公開できるようになる():
    """
    Scenario: 招かれた人が公開できるようになる
    Given ある人がまだ招かれていない
    When 管理者がその人を招く
    Then その人は文書を公開できる
    """
    deps, directory = setup()
    assert not any(p["email"] == "new@example.com" for p in directory.people.values())

    result = _invite(deps, email="new@example.com")

    person = directory.find(result.publisher_id)
    assert person["email"] == "new@example.com"
    assert person["status"] == "invited"


def test_管理者でない者は招けない():
    """
    Scenario: 管理者でない者は招けない
    Given 操作する者が管理者でない投稿者である
    When 誰かを招こうとする
    Then NOT_ADMINISTRATOR として拒まれる
    And 招かれた人は増えていない
    """
    deps, directory = setup()
    before = dict(directory.people)

    with pytest.raises(PublisherError) as x:
        _invite(deps, caller=SOMEONE, email="new@example.com")

    assert x.value.code == "NOT_ADMINISTRATOR"
    assert directory.people == before


def test_重ねて招いても状態は変わらない():
    """
    Scenario: 重ねて招いても状態は変わらない
    Given ある人が既に招かれており、共有アーティファクトを公開している
    When 管理者が同じ人をもう一度招く
    Then 招かれた人は増えていない
    And その人が公開した共有アーティファクトは公開されたまま残っている
    """
    deps, directory = setup(objects=artifact_owned_by("publisher-2"))
    count = len(directory.people)

    again = _invite(deps, email="p2@example.com")

    assert again.publisher_id == "publisher-2"
    assert len(directory.people) == count
    assert json.loads(deps.store.get("meta/aaaaaaaa.json"))["status"] == "active"


def test_外された人は新たに公開できない():
    """
    Scenario: 外された人は新たに公開できない
    Given ある人が招かれている
    When 管理者がその人を外す
    Then その人は新たに文書を公開できない
    """
    deps, directory = setup()

    _remove(deps, publisher_id="publisher-2")

    assert directory.find("publisher-2") is None


def test_外しても公開したものは残る():
    """
    Scenario: 外しても公開したものは残る
    Given ある人が共有アーティファクトAを公開している
    When 管理者がその人を外す
    Then 共有アーティファクトAは公開されたまま残っている
    And 閲覧トークンを持つ閲覧者はAを開ける

    閲覧者の手元の共有URLが、投稿者の異動で黙って死んではならない。
    """
    deps, _ = setup(objects=artifact_owned_by("publisher-2"))
    deps.keys.put("token:aaaaaaaa", "abc|0|1")

    _remove(deps, publisher_id="publisher-2")

    assert json.loads(deps.store.get("meta/aaaaaaaa.json"))["status"] == "active"
    assert deps.keys.get("token:aaaaaaaa") == "abc|0|1"


def test_手入れできなくなるものがあれば件数を伝える():
    """
    Scenario: 手入れできなくなるものがあれば件数を伝える
    Given ある人が共有アーティファクトを3件公開しており、いずれも引き継ぎ先が決まっていない
    When 管理者がその人を外そうとする
    Then 引き継ぎ先の決まっていないものが3件あることが管理者に伝えられる
    """
    objects = {}
    for i in range(3):
        objects.update(artifact_owned_by("publisher-2", f"art{i}"))
    deps, _ = setup(objects=objects)

    result = _remove(deps, publisher_id="publisher-2")

    assert result.orphaned_artifacts == 3


def test_管理者は自分自身を外せない():
    """
    Scenario: 管理者は自分自身を外せない
    Given 操作する者が管理者である
    When 自分自身を外そうとする
    Then CANNOT_REMOVE_SELF として拒まれる

    管理者が一人もいない状態へ落ちる経路を塞ぐ。
    """
    deps, directory = setup()

    with pytest.raises(PublisherError) as x:
        _remove(deps, publisher_id=ADMIN.id)

    assert x.value.code == "CANNOT_REMOVE_SELF"
    assert directory.find(ADMIN.id) is not None


def test_招かれていない人は外せない():
    """
    Scenario: 招かれていない人は外せない
    Given ある人が招かれていない
    When 管理者がその人を外そうとする
    Then PUBLISHER_NOT_FOUND として拒まれる
    """
    deps, _ = setup()

    with pytest.raises(PublisherError) as x:
        _remove(deps, publisher_id="no-such-person")

    assert x.value.code == "PUBLISHER_NOT_FOUND"


def test_仮の合言葉を無くした人を招き直せる():
    """
    Scenario: 仮の合言葉を無くした人を招き直せる
    Given ある人が招かれ、まだ一度も入っていない
    When 管理者が招待を送り直す
    Then 新しい仮の合言葉がその人の宛先へ届く
    And その仮の合言葉で入って、自分の合言葉を決められる
    """
    deps, directory = setup(people={
        "admin-1": {"email": "admin@example.com", "status": "active"},
        "invited-1": {"email": "yet@example.com", "status": "invited"},
    })

    build(deps, InvitePublisher).run("resend", ADMIN, publisher_id="invited-1")

    assert directory.resent == ["invited-1"]
    assert directory.find("invited-1")["status"] == "invited"


def test_既に入っている人へは送り直さない():
    """
    Scenario: 既に入っている人へは送り直さない
    Given ある人が既に自分の合言葉を決めて入っている
    When 管理者がその人へ招待を送り直そうとする
    Then ALREADY_ACTIVE として拒まれる
    And その人の合言葉は変わっていない
    """
    deps, directory = setup()

    with pytest.raises(PublisherError) as x:
        build(deps, InvitePublisher).run("resend", ADMIN, publisher_id="publisher-2")

    assert x.value.code == "ALREADY_ACTIVE"
    assert not hasattr(directory, "resent")
