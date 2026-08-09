"""公開が、成功しても失敗しても守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

ここで確かめるのは1回の公開の結果ではなく、公開という操作が全体として
守る約束。トークンは後から取り出せないこと、途中で倒れても開ける状態の
ものが残らないこと。

対象の仕様: uc-publish-artifact（操作保証）
"""
import pytest

from publish_setup import WITH_META, FakeKeyStore, FakeStore, publishing
from shared.errors import PublishError


def test_トークンは後から取り出せない():
    """
    Scenario: トークンは後から取り出せない
    Given アーティファクトが公開され、トークンが示されている
    When 一覧や記録からトークンを取り出そうとする
    Then トークンは得られない
    And 新しく発行する以外に手立てが無い
    """
    keys = FakeKeyStore()

    result = publishing(keys=keys).run({"html": WITH_META, "authorization": "Bearer x"})

    record = keys.written["token:" + result.artifact_id]
    value, expires = record.split("|")
    assert value != result.token       # そのままは残さない
    assert result.token not in record  # 部分としても残さない
    assert int(expires) > 0            # 期限は必ず付く


def test_失敗したら誰も開けない():
    """
    Scenario: 失敗したら誰も開けない
    Given 公開の途中で拒まれる条件が成立している
    When 公開しようとする
    Then トークンは発行されない
    And その共有URLを開こうとしても拒まれる

    管理APIには削除の権限が無いため、置かれたファイルそのものは残る。開ける
    状態のものが残らないことを、トークンを最後に書く順序で保証する。
    """
    store, keys = FakeStore(fail_on="index.html"), FakeKeyStore()

    with pytest.raises(PublishError) as e:
        publishing(store=store, keys=keys).run(
            {"html": WITH_META, "authorization": "Bearer x"})

    assert e.value.code == "PUBLISH_FAILED"
    assert keys.written == {}  # トークンが無いので閲覧ゲートが拒む
