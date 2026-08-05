"""文書が自分自身を名乗る形の契約を、書く側から確かめる。

この形は、文書を作る側が書き、公開の受け口が読む。両者は別のリポジトリとして
出荷されうる別のものであり、互いを直接呼べない。契約の表が唯一の共通点で、
読む側の検証も同じ表を読む。

ここが確かめるのは欄の名前だけで、中身の値ではない。値はHandoffごとに変わるが、
名乗り方が変わると読む側が黙って拾えなくなる——そこだけを止める。

表を読んでいるのは、この検証自身が欄の名前を書き写さないため。書き写すと、
表を直したのにここが古いまま緑で通る。
"""
import json
import re
from pathlib import Path

from waffle.domain.services.completion_image_layout import compute_layout
from waffle.domain.services.handoff_html_template import render_handoff_html

CONTRACT = json.loads(
    (Path(__file__).resolve().parents[3]
     / ".waffle" / "skills" / "artifact-share" / "infra" / "contract" / "document-meta.json")
    .read_text(encoding="utf-8")
)


def _declared_names() -> dict[str, str]:
    """契約が挙げる欄と、その名乗りの綴り。"""
    names = {}
    for field, shape in CONTRACT["形式"].items():
        if not isinstance(shape, str):
            continue
        m = re.search(r'<meta name="([^"]+)"', shape)
        if m:
            names[field] = m.group(1)
    return names


def _rendered() -> str:
    layout = compute_layout([], [])
    return render_handoff_html(
        title="タイトル", document_id="handoff-x", spec_ref="uc-x", layout=layout,
        layers=[], review_counts=[], design_viewpoints=[], implementation_viewpoints=[],
        constraints=[], handoff_kind="specToImplementation", usage_examples=[],
        description="説明文です", tags=["context:waffle", "kind:handoff"],
    )


def test_契約が挙げる全ての欄を名乗る():
    """
    Given 契約が5つの欄（識別子・種別・題名・要約・分類の目印）を挙げている
    When Handoffを描画する
    Then そのすべてがheadのmetaとして出力される
    """
    html = _rendered()
    declared = _declared_names()
    assert set(declared) == {"識別子", "種別", "題名", "要約", "分類の目印"}
    missing = [f for f, name in declared.items() if f'<meta name="{name}" content=' not in html]
    assert missing == []


def test_必須の欄は空にならない():
    """
    Given 契約が識別子と種別を必須としている
    When Handoffを描画する
    Then そのどちらも空文字では出力されない（揃っていないと読まれてしまう）
    """
    html = _rendered()
    declared = _declared_names()
    for field in CONTRACT["形式"]["必須"]:
        assert f'<meta name="{declared[field]}" content="">' not in html


def test_分類の目印は契約の区切りで並べる():
    """
    Given 契約が分類の目印の区切りを定めている
    When 複数の目印を持つHandoffを描画する
    Then その区切りで並べて出力される（前後の空白は読む側が取り除く）
    """
    html = _rendered()
    name = _declared_names()["分類の目印"]
    m = re.search(rf'<meta name="{name}" content="([^"]*)">', html)
    assert m is not None
    separator = CONTRACT["形式"]["分類の目印の区切り"]
    assert [t.strip() for t in m.group(1).split(separator)] == ["context:waffle", "kind:handoff"]
