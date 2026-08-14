"""識別子を発行する口が守る約束を、本物と偽物の両方に対して確かめる。

実行:  python3 -m pytest tests/ -v

どんな形なら識別子として通るかは業務の語彙の側が正本として持ち、作る側はその形を
満たすだけである。ここが崩れると、検証だけが通る値を偽物が作れてしまう。

偽物の説明には「読み違えやすい文字を避ける決まりは偽の口にもかかっている」と
書いてあったが、それは注釈としてしか存在せず、実際に確かめてはいなかった。
この束がそれを実行される検証にする。

対象の仕様: agg-shared-artifact / agg-project（識別子の値の性質）
"""
import pytest

from adapters.outbound.random_identifier import RandomIdGenerator
from domain.value_objects.identifier import (
    ARTIFACT_ID_LENGTH, ID_ALPHABET, PROJECT_ID_LENGTH,
)
from domain.value_objects.project import ProjectId
from domain.value_objects.shared_artifact import ArtifactId
from domain.value_objects.view_token import TOKEN_ID_LENGTH, ViewTokenId
from fakes import FakeIdGenerator

GENERATORS = [
    pytest.param(RandomIdGenerator, id="本物"),
    pytest.param(FakeIdGenerator, id="偽物"),
]


@pytest.mark.parametrize("make", GENERATORS)
def test_発行したものは業務の語彙が定める型で返る(make):
    """素の文字列で返すと、形を確かめる道を通らない値が出回る。"""
    ids = make()

    assert isinstance(ids.new_artifact_id(), ArtifactId)
    assert isinstance(ids.new_project_id(), ProjectId)
    assert isinstance(ids.new_view_token_id(), ViewTokenId)
    assert isinstance(ids.new_view_token_secret(), str)


@pytest.mark.parametrize("make", GENERATORS)
def test_発行したものは字種と桁数の決まりを満たす(make):
    """読み間違えやすい文字を避ける決まりは、偽物にもかかっている。"""
    ids = make()

    artifact = ids.new_artifact_id().value
    project = ids.new_project_id().value

    assert len(artifact) == ARTIFACT_ID_LENGTH
    assert len(project) == PROJECT_ID_LENGTH
    for value in (artifact, project, ids.new_view_token_id().value):
        assert set(value) <= set(ID_ALPHABET), value


@pytest.mark.parametrize("make", GENERATORS)
def test_続けて発行すると別の値になる(make):
    """同じ値を返す口だと、別々に渡したはずのものが取り違えられる。"""
    ids = make()

    assert ids.new_artifact_id() != ids.new_artifact_id()
    assert ids.new_project_id() != ids.new_project_id()
    assert ids.new_view_token_id() != ids.new_view_token_id()
    assert ids.new_view_token_secret() != ids.new_view_token_secret()


@pytest.mark.parametrize("make", GENERATORS)
def test_一覧で選ぶための識別子は決まった桁で返る(make):
    assert len(make().new_view_token_id().value) == TOKEN_ID_LENGTH
