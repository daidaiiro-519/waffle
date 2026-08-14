"""enforcement を外した結論に合わせて、知識と引き継ぎ書をそろえる。

「情報の不在は書けなくすることでしか守れない」という原則は誤りだった。
構造の宣言（値オブジェクトと属性）がそれを担保するので、
そもそも不変条件として重ねて書くべきものではない。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
K = ".waffle/documents/knowledge/knowledge-cand-one-binding-for-all-contract-levels.json"
H = ".waffle/documents/handoff/handoff-criteria-scenario-link.json"


def q(p, b, e):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", p, "--blockKey", b, "--expression", e],
                       capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


def fill(p, v):
    r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill",
                        "--path", p, "--values", json.dumps(v, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    print((r.stdout or r.stderr).strip()[:140])


# ---- 知識：誤っていた原則を差し替える
ps = q(K, "principles", "items")
ps = [x for x in ps if not x.startswith("転写して照合する経路が届かない規則が、わずかに残る")]
anchor = next(i for i, x in enumerate(ps) if x.startswith("したがって担保の不足は"))
ps[anchor:anchor] = [
    "仕様と実装をつなぐ担保は2つある。"
    "振る舞いが仕様どおりかは、基準とシナリオを転写して照合することで担保する。"
    "在るべきものが在るべき形で在るかは、構造の宣言（値オブジェクト・属性・置き場所・所属）を"
    "実物と突き合わせることで担保する。",

    "構造の宣言が言えることを、不変条件へ重ねて書かない。"
    "「その項目を持たない」「値そのものを保持しない」は、属性や値オブジェクトの宣言が既に言っている。"
    "重ねて書くと、同じことを2箇所で保つことになる。",

    "したがって、不変条件として残るものはすべて振る舞いの主張であり、"
    "すべてシナリオを持つ。シナリオを持てない不変条件は存在しない——"
    "持てないように見えるものは、構造の宣言が言うべきことを不変条件へ書いている。",
]
fill(K, {"content.principles.items": ps})

# 判断基準：観測できないときの帰結を、構造の宣言へ寄せる
st = q(K, "decisionCriteria", "stages")
for s in st:
    if s["label"] == "その基準は、どの操作の結果としても観測できないか？":
        s["label"] = "その主張は、値オブジェクトや属性の宣言が既に言っているか？"
    if s["label"] == "実装でそう書けない形にする":
        s["label"] = "不変条件から外す。構造の宣言が担保する"
fill(K, {"content.decisionCriteria.stages": st})

ap = q(K, "antiPatterns", "items")
ap.append({
    "name": "構造の宣言が言えることを、不変条件へ重ねて書く",
    "problem": "同じ主張を2箇所で保つことになり、"
               "しかも片方はシナリオを持てないため、担保できない基準が在るように見えてしまう。",
})
fill(K, {"content.antiPatterns.items": ap})

cv = q(K, "provenance", "caveats")
cv = cv.replace(
    "(3) 情報の不在を主張する規則について、"
    "観測できる部分をシナリオへ、保管についての言明を書けなさへ、という切り分けは"
    "まだ実際に当てはめていない。切り分けたあと何が残るかは未確認。",
    "(3) 「構造の宣言が言えることは不変条件へ重ねて書かない」を既存の不変条件へ当てると、"
    "何件が削除対象になり、何件がシナリオの追加対象になるかは未確認。"
    "1件ずつ読んで分ける必要がある。")
fill(K, {"content.provenance.caveats": cv})

# ---- 引き継ぎ書：問い自体が消えた観点を差し替える
ds = [x for x in q(H, "designViewpoints", "items")
      if not x["viewpoint"].startswith("シナリオを持てない条件を、欠けとして数えない")]
ds.append({
    "advisor": "ddd-advisor",
    "viewpoint": "不変条件はすべてシナリオを持つ",
    "consideration":
        "「値そのものを保持しない」のように、値オブジェクトや属性の宣言が既に言っていることは、"
        "不変条件へ重ねて書かない。構造の宣言と、それを実物と突き合わせる検知が担保する。"
        "重複を外すと、残る不変条件はすべて操作をまたぐ振る舞いの主張になり、例外なくシナリオを持つ。"
        "守り方を区別する欄（enforcement）は、この整理で不要になったので v9 から外した。",
})
fill(H, {"content.designViewpoints.items": ds})

f = [x for x in q(H, "reviewStatus", "findings")
     if "どう名乗るか" not in (x.get("note") or "")]
f.append({"advisor": "ddd-advisor", "refBlock": "designViewpoints", "refIndex": 8,
          "resolutionStatus": "resolved",
          "note": "シナリオを持てない基準は存在しないと整理できたため、"
                  "『基準の側でどう名乗るか』という問い自体が消えた。"
                  "移行では、構造の宣言と重複している不変条件を1件ずつ外す。"})
fill(H, {"content.reviewStatus.findings": f})
