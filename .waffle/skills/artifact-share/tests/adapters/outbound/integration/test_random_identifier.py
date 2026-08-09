"""推測できない並びの作り方を確かめる。

実行:  python3 -m pytest tests/ -v

どんな形なら識別子として通るか（字種・桁数）は業務の語彙の側が正本として持ち、
ここが確かめるのは作る側がその形を実際に満たすこと。作る手立てが実行環境の
予測できない値に結びついているため、この層に居る。

シナリオには紐づかない。どの受け入れ基準にも書かれていないが、崩れると
識別子から他人のものを数え上げられるようになり、人が読み上げたときに
取り違えが起きる。

対象の仕様: agg-shared-artifact / agg-project（識別子の値の性質）
"""
from adapters.outbound.random_identifier import RandomIdGenerator


def test_アーティファクトIDは紛らわしい文字を避ける():
    ids = {RandomIdGenerator().new_artifact_id().value for _ in range(200)}
    assert len(ids) == 200                      # 重ならない
    for value in ids:
        assert len(value) == 8
        assert not set(value) & set("lo01")     # 読み間違えやすい文字を使わない
