"""公開について、受け入れシナリオの外側で守りたいこと。

実行:  python3 -m pytest tests/ -v

シナリオと1対1で対応するものは application/acceptance/ と
application/integration/ にある。ここに残すのは、どのシナリオにも書かれて
いないが崩れると困ること——閲覧画面の組み立てと、置く順序。

上げられたHTMLの読み取りは、契約表を回す検証が上位互換に覆っている。
識別子の作り方は、作る側の層で確かめる。

対象の仕様: uc-publish-artifact（受け入れ基準のうち、シナリオを持たないもの）
"""
import pytest

from publish_setup import WITH_META, FakeKeyStore, FakeStore, publishing
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

    assert keys.written == {}  # 開ける状態にはならない

