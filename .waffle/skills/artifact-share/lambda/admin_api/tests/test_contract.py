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

import main
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from application.usecases.assign_artifact_to_project import (  # noqa: E402
    _write_membership as write_membership,
)


from shared.errors import ManageError  # noqa: E402

from adapters.outbound.kvs_view_gate import KvsViewGate  # noqa: E402
from domain.view_subject import ViewSubject  # noqa: E402

CONTRACT = json.loads(
    (Path(__file__).resolve().parents[3] / "infra" / "contract" / "token-records.json")
    .read_text(encoding="utf-8")
)


def cases():
    """書き手が作る形の事例。読み手だけの事例（期限切れが残った状態など）は除く。"""
    return [c for c in CONTRACT["ケース"] if not c.get("書き手は作らない")]


def _stored(case):
    """実際に書き出す経路を通して、保管へ残った記録を取り出す。

    組み立ての関数を直接呼ぶのではなく口を通すのは、経路の途中で形が変わって
    いたら気づけないため。ずれたまま両側の検証が緑で通ったのが、この検証を
    置くきっかけだった。
    """
    keys = _Collector()
    gate = KvsViewGate(keys)
    gate.replace_grants(
        ViewSubject.artifact("aaaaaaaa"),
        [(gate.fingerprint_of(token), expiry)
         for token, expiry in zip(case["合言葉"], case["期限"])])
    return keys.written["token:aaaaaaaa"]


@pytest.mark.parametrize("case", cases(), ids=[c["名前"] for c in cases()])
def test_保管へ残す形が契約と一致する(case):
    assert _stored(case) == case["保管の記録"]


@pytest.mark.parametrize("case", cases(), ids=[c["名前"] for c in cases()])
def test_手元の記録は各記録の1つ目の欄(case):
    """閲覧ゲートが手元へ渡す値。組み立てるのは向こうだが、材料はこちらが決める。"""
    stored = _stored(case)
    got = [r.split("|")[0] for r in stored.split(";")] if stored else []
    assert got == case["手元の記録"]


def test_合言葉そのものは記録に現れない():
    for case in CONTRACT["ケース"]:
        for token in case["合言葉"]:
            assert token not in case["保管の記録"]


def test_所属の記録が契約と一致する():
    """書き手と読み手が同じ区切りを使っていることを確かめる。"""
    membership = CONTRACT["所属の記録"]
    deps = main.Connections(store=None, keys=_Collector(), now=None)

    for case in membership["ケース"]:
        write_membership(deps.gate, "aaaaaaaa", case["プロジェクト"])
        assert deps.keys.written["pp:aaaaaaaa"] == case["記録"]


def test_上限を超える所属は受け付けない():
    """読み手は先頭から上限までしか見ない。書き手が黙って超えると、
    投稿者には成功が返り、閲覧者だけが開けない状態になる。"""
    limit = CONTRACT["所属の記録"]["上限"]
    deps = main.Connections(store=None, keys=_Collector(), now=None)

    with pytest.raises(ManageError) as x:
        write_membership(deps.gate, "aaaaaaaa", [f"p{i}" for i in range(limit + 1)])
    assert x.value.code == "TOO_MANY_PROJECTS"


class _Collector:
    def __init__(self):
        self.written = {}

    def put(self, key, value):
        self.written[key] = value
