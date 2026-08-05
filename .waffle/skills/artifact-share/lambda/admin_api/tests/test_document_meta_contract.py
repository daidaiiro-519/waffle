"""文書が自分自身を名乗る形の契約を、読む側から確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

この形は、文書を作る側が書き、ここが読む。書く側は複数あり、互いを知らない。
infra/contract/document-meta.json が全員の唯一の共通点で、書く側の検証も
同じ表を読む。

表は読む側の内部の呼び名で書かれていない。ここで写しているのがその境目で、
内部の呼び名を変えてもこの写し方を直すだけで済み、契約そのものは動かない。

表の値は実装から生成していない。生成すると同じ規則の写しが増えるだけで、
突き合わせにならない。
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain.html_inspection import inspect_html  # noqa: E402

CONTRACT = json.loads(
    (Path(__file__).resolve().parents[3] / "infra" / "contract" / "document-meta.json")
    .read_text(encoding="utf-8")
)

# 契約の言葉と、この実装の内部の呼び名の対応。ここだけが境目。
INWARD = {
    "識別子": "documentId",
    "種別": "docType",
    "題名": "title",
    "要約": "description",
    "分類の目印": "tags",
    "外部への参照": "externalRefs",
    "揃っている": "detected",
}


def cases():
    return CONTRACT["ケース"]


@pytest.mark.parametrize("case", cases(), ids=[c["名前"] for c in cases()])
def test_読み取りが契約と一致する(case):
    got = inspect_html(case["文書"])
    expected = {INWARD[k]: v for k, v in case["読み取り"].items()}
    assert {k: got[k] for k in expected} == expected


def test_契約が挙げる必須の欄が揃わなければ名乗れていない():
    """必須は識別子と種別の2つ。片方だけでは名乗れていないと見なす。"""
    required = CONTRACT["形式"]["必須"]
    assert required == ["識別子", "種別"]

    for missing in required:
        present = [f for f in required if f != missing]
        tags = "".join(
            f'<meta name="{ {"識別子": "id", "種別": "type"}[f] }" content="x">'
            for f in present
        )
        assert inspect_html(f"<html><head>{tags}</head></html>")["detected"] is False


def test_契約の全ての欄が読み取りに現れる():
    """表に欄を足したのに読む側が拾っていない、を防ぐ。"""
    for case in cases():
        assert set(case["読み取り"]) == set(INWARD)
