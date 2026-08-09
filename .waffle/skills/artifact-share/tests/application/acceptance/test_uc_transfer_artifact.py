"""投稿者を別の人へ移す操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-transfer-artifact
"""
import pytest

from transfer_setup import ADMIN, X, Y, setup
from manage_setup import HTML, meta_of
from application.usecases.replace_artifact_content import ReplaceArtifactContent
from application.usecases.suspend_artifact import SuspendArtifact
from application.usecases.transfer_artifact import TransferArtifact
from shared.errors import ManageError, PublisherError
from usecase_builder import build

import json


def _transfer(deps, caller, artifact_id, to):
    return build(deps, TransferArtifact).run(caller, artifact_id, to)


def test_移した先が手入れできるようになる():
    """
    Scenario: 移した先が手入れできるようになる
    Given 共有アーティファクトAの投稿者がXである
    When 管理者がAの投稿者をYへ移す
    Then YはAを差し替え・公開停止・閲覧トークンの発行と無効化できる
    """
    deps, r = setup()

    _transfer(deps, ADMIN, r.artifact_id, Y.id)

    assert meta_of(deps, r.artifact_id)["uploadedBy"] == Y.id
    build(deps, ReplaceArtifactContent).run(Y, r.artifact_id, HTML.replace("本文", "直した"))
    build(deps, SuspendArtifact).run(Y, r.artifact_id)
    assert meta_of(deps, r.artifact_id)["status"] == "disabled"


def test_移す前の人は扱えなくなる():
    """
    Scenario: 移す前の人は扱えなくなる
    Given 共有アーティファクトAの投稿者がYへ移されている
    When XがAを公開停止しようとする
    Then Xからは見つからないものとして拒まれる
    """
    deps, r = setup()
    _transfer(deps, ADMIN, r.artifact_id, Y.id)

    with pytest.raises(ManageError) as x:
        build(deps, SuspendArtifact).run(X, r.artifact_id)

    assert x.value.code == "ARTIFACT_NOT_FOUND"


def test_閲覧者から見て何も変わらない():
    """
    Scenario: 閲覧者から見て何も変わらない
    Given 閲覧者が共有アーティファクトAの閲覧トークンを持っている
    When 管理者がAの投稿者をYへ移す
    Then 閲覧者はそれまでの共有URLと閲覧トークンでAを開ける
    And 中身もそれまでのコメントもそのまま見える

    引き継ぎは手入れできる人を替えるだけの操作で、投稿者の異動という内輪の
    事情が閲覧者へ漏れてはならない。
    """
    deps, r = setup()
    deps.store.put(f"comments/{r.artifact_id}/1700000010-abcd1234.json",
                   json.dumps({"kind": "comment", "author": "田中",
                               "decision": "comment", "body": "意見",
                               "parentId": None,
                               "postedAt": "2026-07-01T10:00:00Z"},
                              ensure_ascii=False), "application/json")
    token_before = deps.keys.written[f"token:{r.artifact_id}"]
    content_before = deps.store.get(f"p/{r.artifact_id}/content.html")

    _transfer(deps, ADMIN, r.artifact_id, Y.id)

    assert deps.keys.written[f"token:{r.artifact_id}"] == token_before
    assert deps.store.get(f"p/{r.artifact_id}/content.html") == content_before
    assert len(deps.store.list(f"comments/{r.artifact_id}/")) == 1


def test_管理者でない者は移せない():
    """
    Scenario: 管理者でない者は移せない
    Given 操作する者が管理者でない投稿者Xである
    When XがAの投稿者をYへ移そうとする
    Then NOT_ADMINISTRATOR として拒まれる
    And Aの投稿者はXのままである
    """
    deps, r = setup()

    with pytest.raises((ManageError, PublisherError)) as x:
        _transfer(deps, X, r.artifact_id, Y.id)

    assert x.value.code == "NOT_ADMINISTRATOR"
    assert meta_of(deps, r.artifact_id)["uploadedBy"] == X.id


def test_招かれていない人へは移せない():
    """
    Scenario: 招かれていない人へは移せない
    Given ある人が招かれていない
    When 管理者がAの投稿者をその人へ移そうとする
    Then PUBLISHER_NOT_FOUND として拒まれる
    And Aの投稿者はXのままである
    """
    deps, r = setup()

    with pytest.raises((ManageError, PublisherError)) as x:
        _transfer(deps, ADMIN, r.artifact_id, "no-such-person")

    assert x.value.code == "PUBLISHER_NOT_FOUND"
    assert meta_of(deps, r.artifact_id)["uploadedBy"] == X.id


def test_公開停止されているものも移せる():
    """
    Scenario: 公開停止されているものも移せる
    Given 共有アーティファクトAが公開停止されている
    When 管理者がAの投稿者をYへ移す
    Then 引き継がれる
    And Aは公開停止されたままである
    """
    deps, r = setup()
    build(deps, SuspendArtifact).run(X, r.artifact_id)

    _transfer(deps, ADMIN, r.artifact_id, Y.id)

    meta = meta_of(deps, r.artifact_id)
    assert meta["uploadedBy"] == Y.id
    assert meta["status"] == "disabled"
