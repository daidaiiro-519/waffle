"""主張から描く。

宣言の形は主張によらず同じ（asserts / items / links / frame）。
描き方は主張から決まるので、書き手は選ばない。ここはその対応表であり、
どの描く手へ渡すか・宣言のどの欄をその手の入力へ写すかだけを持つ。
"""
from __future__ import annotations
import sys
sys.path.insert(0, "recovered/figures")
import draw
import svg_chart as C

RELATION = ["つながり", "階層", "包含", "順序", "循環", "やり取り", "対応"]
AMOUNT = ["全体と部分", "量の大小", "順位", "時間変化", "分布", "偏差", "相関", "流量", "空間"]
CLAIMS = RELATION + AMOUNT


def _names(fig):
    return [it["name"] for it in fig.get("items", [])]


def _vals(fig):
    return [{"name": it["name"], "value": it.get("value", 0)} for it in fig.get("items", [])]


def _axis_unit(fig, i, dflt=""):
    ax = (fig.get("frame") or {}).get("axes") or []
    return ax[i].get("unit", dflt) if i < len(ax) else dflt


# ── 関係 ────────────────────────────────────────
def _tsunagari(fig):
    return draw.tsunagari(fig)


def _kaisou(fig):
    return draw.kaisou(fig)


def _hougan(fig):
    return draw.hougan(fig)


def _junjo(fig):
    return draw.junjo(fig)


def _junkan(fig):
    """並びが閉じる。最後から最初への結びを足して、つながりとして解かせる。"""
    names = _names(fig)
    links = [{"from": names[i], "to": names[(i + 1) % len(names)], "ends": "head:arrow"}
             for i in range(len(names))]
    return draw.tsunagari({**fig, "links": links})


def _yaritori(fig):
    """誰の間か、という軸を持つ。結びを順に並べた往復として描く。"""
    steps = []
    for lk in fig.get("links", []):
        kind = "return" if lk.get("ends") == "return" else "command"
        steps.append({"kind": kind, "from": lk["from"], "to": lk["to"],
                      "text": lk.get("name", "")})
    groups = (fig.get("frame") or {}).get("groups") or []
    for g in groups:
        at = g.get("span", [0, 1])
        steps.insert(at[0], {"kind": "frame", "label": g.get("name", ""), "span": at[1]})
    return C.exchange({"participants": _names(fig), "steps": steps})


def _taiou(fig):
    """面をまたぐ／格子で交わる。左右2列の対応として描く。"""
    cells = []
    for it in fig.get("items", []):
        cells.append({"name": it["name"]})
    return C.blocks({"cols": 2, "cells": cells})


# ── 量 ────────────────────────────────────────
def _zentai(fig):
    return C.share({"slices": _vals(fig), "centre": str(sum(v["value"] for v in _vals(fig)))})


def _daisho(fig):
    return C.bars({"slices": _vals(fig)})


def _juni(fig):
    return C.bars({"slices": sorted(_vals(fig), key=lambda v: -v["value"])})


def _jikan(fig):
    rows = []
    for it in fig.get("items", []):
        sp = it.get("span")
        bar = {"from": sp[0], "to": sp[1]} if sp else {"from": it.get("at", [0])[0],
                                                       "to": it.get("at", [0])[0] + 1}
        rows.append({"name": it["name"], "bars": [bar]})
    span = max((b["to"] for r in rows for b in r["bars"]), default=10)
    return C.lanes({"rows": rows, "span": span, "axis": _axis_unit(fig, 0, "時間")})


def _bunpu(fig):
    return C.bars({"slices": _vals(fig)})


def _hensa(fig):
    base = (fig.get("frame") or {}).get("baseline", 0)
    return C.bars({"slices": [{"name": v["name"], "value": v["value"] - base} for v in _vals(fig)]})


def _soukan(fig):
    xs = [it.get("at", [0, 0])[0] for it in fig.get("items", [])]
    ys = [it.get("at", [0, 0])[1] for it in fig.get("items", [])]
    mx, my = max(xs + [1]), max(ys + [1])
    pts = [{"name": it["name"], "x": it.get("at", [0, 0])[0] / mx,
            "y": it.get("at", [0, 0])[1] / my} for it in fig.get("items", [])]
    return C.matrix({"points": pts, "x": _axis_unit(fig, 0), "y": _axis_unit(fig, 1)})


def _ryuryo(fig):
    links = [{"from": lk["from"], "to": lk["to"], "value": lk.get("weight", 1)}
             for lk in fig.get("links", [])]
    return C.flow({"links": links})


def _kuukan(fig):
    """枠が既に知られている座標。位置が意味を運ぶので、並べた箱として描く。"""
    return C.blocks({"cols": 1, "cells": [{"name": it["name"]} for it in fig.get("items", [])]})


HANDS = {
    "つながり": _tsunagari, "階層": _kaisou, "包含": _hougan, "順序": _junjo,
    "循環": _junkan, "やり取り": _yaritori, "対応": _taiou,
    "全体と部分": _zentai, "量の大小": _daisho, "順位": _juni, "時間変化": _jikan,
    "分布": _bunpu, "偏差": _hensa, "相関": _soukan, "流量": _ryuryo, "空間": _kuukan,
}


def render(fig):
    """宣言から図を描く。主張ごとの描き分けはここだけが知っている。"""
    a = fig["asserts"]
    if a not in HANDS:
        raise ValueError(f"知らない主張です: {a}")
    return HANDS[a](fig)
