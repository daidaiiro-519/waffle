"""層2 ── 組み立てたSVGを検査に通す。16主張 × 倍率 と組み合わせの全通り。

1件ずつ独立した試験にしてあるので、崩れたときにどの図のどの倍率かが
そのまま試験名に出る。組み立ては各試験の中で行う ── 表を作る時点で全部
組んでしまうと、1件の例外が収集ごと巻き込んで、何件通ったのかが分からない。
"""
from __future__ import annotations

import pytest

from matrix_cases import cases
from svg_engine.verify import check, check_attachment, check_shapes

CASES = cases()


@pytest.mark.parametrize("scale,name,build",
                         CASES, ids=[f"{s}-{n}" for s, n, _ in CASES])
def test_崩れていない(scale, name, build):
    svg = build()
    faults = check(svg) + check_shapes(svg) + check_attachment(svg)
    assert faults == [], f"[{scale}] {name}: " + " / ".join(dict.fromkeys(faults))
