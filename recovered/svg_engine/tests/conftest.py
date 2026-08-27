"""svg_engine は Waffle 本体の import グラフの外にある独立パッケージなので、
本体の tests/ とは別に、自分で自分の import 経路を通す。
"""
from __future__ import annotations

import pathlib
import sys

_ENGINE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ENGINE.parent))       # recovered/ ── svg_engine を import する
sys.path.insert(0, str(_ENGINE / "examples"))  # 例の図の表を import する


import pytest


@pytest.fixture
def style():
    """既定のテーマを解決したもの。部品を単体で描くときに要る。"""
    from svg_engine.style import resolve_style
    from svg_engine.tokens import DEFAULT_THEME
    return resolve_style("plain", None, DEFAULT_THEME)


@pytest.fixture
def sample_props():
    """台帳の全部品を1つずつ描くための、最小の入力。

    部品を足したらここへ1行足す。足し忘れると、その部品は契約の試験を
    通らないまま台帳に載る ── だから足りない部品が出たら試験で落とす。
    """
    from svg_engine.boolean import circle_polygon
    slices = [{"name": "文書", "value": 13}, {"name": "図", "value": 5}]
    props = {
        "box": {}, "hex": {}, "dot": {}, "icon": {"name": "check"},
        "donut": {"slices": slices, "centre": "18"},
        "pie": {"slices": slices, "centre": "18"},
        "boolean": {"shapes": [circle_polygon(40, 40, 34), circle_polygon(66, 40, 34)],
                    "op": "subtract"},
        "gradient_rect": {"width": 90, "height": 48},
        "path": {"d": "M0,40 Q30,0 60,40 Q90,80 120,40"},
        "titled": {"of": "donut", "slices": slices, "centre": "18"},
        "bars": {"bars": [{"name": "文書", "value": 13}, {"name": "図", "value": 5}]},
        "ranking": {"items": [{"name": "文書", "value": 13}, {"name": "図", "value": 5}]},
        "lanes": {"rows": [{"name": "設計", "bars": [{"from": 0, "to": 3}]}]},
        "scatter": {"points": [{"name": "a", "x": 1, "y": 2}, {"name": "b", "x": 3, "y": 4}]},
        "flow": {"links": [{"from": "A", "to": "B", "value": 5}]},
        "spatial": {"items": [{"name": "領域", "depth": 2}], "cols": 1},
        "table": {"headers": ["部品", "数"], "rows": [["形", "7"]]},
        "exchange": {"participants": ["甲", "乙"],
                     "steps": [{"from": "甲", "to": "乙", "label": "渡す"}]},
        "title": {"text": "見出し"}, "divider": {"width": 120},
        "frame": {"x": 0, "y": 0, "width": 80, "height": 40},
        "frame_label": {"x": 0, "y": 20, "label": "札"},
        "edge": {"points": [(0, 0), (60, 40)]},
    }
    return {k: {"label": "名前", **v} for k, v in props.items()}
