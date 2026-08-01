"""保管へ残す形の契約を、書く側から確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

この形は、公開する側（このPython）が書き、閲覧ゲート（JavaScript）が読む。
両者は別の言語・別の実行環境にあり、互いを直接呼べない。
infra/contract/token-records.json が両者の唯一の共通点で、
JavaScript側の検証も同じ表を読む。

2026-08-01に、この契約がずれたまま両側の検証が緑で通った。保管には
ハッシュを入れているのに、閲覧ゲートは平文と比べていた。実装も検証も
同じ誤解で書かれており、実環境でだけ「正しいトークンでも開けない」として
現れた。この検証は、その再発を止めるために置いている。

表の値は実装から生成していない。生成すると同じ規則の写しが増えるだけで、
突き合わせにならない。
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import manage  # noqa: E402
import publish  # noqa: E402

CONTRACT = json.loads(
    (Path(__file__).resolve().parents[3] / "infra" / "contract" / "token-records.json")
    .read_text(encoding="utf-8")
)


def cases():
    return CONTRACT["ケース"]


@pytest.mark.parametrize("case", cases(), ids=[c["名前"] for c in cases()])
def test_保管へ残す形が契約と一致する(case):
    got = publish.token_record(
        case["合言葉"], case["発行時刻"],
        ttl=case["有効期間"], generation=case["世代"],
    )
    assert got == case["保管の記録"]


@pytest.mark.parametrize("case", cases(), ids=[c["名前"] for c in cases()])
def test_手元の記録は保管の1つ目の欄と世代をつないだもの(case):
    """閲覧ゲートが手元へ渡す値。組み立てるのは向こうだが、材料はこちらが決める。"""
    stored = publish.token_record(
        case["合言葉"], case["発行時刻"],
        ttl=case["有効期間"], generation=case["世代"],
    )
    fingerprint, _expires, generation = stored.split("|")
    assert f"{fingerprint}.{generation}" == case["手元の記録"]


def test_合言葉そのものは記録に現れない():
    for case in cases():
        assert case["合言葉"] not in case["保管の記録"]


def test_所属の記録が契約と一致する():
    """書き手と読み手が同じ区切りを使っていることを確かめる。"""
    membership = CONTRACT["所属の記録"]
    deps = manage.Deps(store=None, keys=_Collector())

    for case in membership["ケース"]:
        manage._write_membership(deps, "aaaaaaaa", case["プロジェクト"])
        assert deps.keys.written["pp:aaaaaaaa"] == case["記録"]


def test_上限を超える所属は受け付けない():
    """読み手は先頭から上限までしか見ない。書き手が黙って超えると、
    投稿者には成功が返り、閲覧者だけが開けない状態になる。"""
    limit = CONTRACT["所属の記録"]["上限"]
    deps = manage.Deps(store=None, keys=_Collector())

    with pytest.raises(manage.ManageError) as x:
        manage._write_membership(deps, "aaaaaaaa", [f"p{i}" for i in range(limit + 1)])
    assert x.value.code == "TOO_MANY_PROJECTS"


class _Collector:
    def __init__(self):
        self.written = {}

    def put(self, key, value):
        self.written[key] = value
