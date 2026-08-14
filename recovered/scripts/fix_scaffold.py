"""検証で出た指摘に沿って uc-scaffold-document を直す。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/"
     "usecase/uc-scaffold-document." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(block, expr="@"):
    return json.loads(run("query", "--operation", "query_path", "--path", P,
                          "--blockKey", block, "--expression", expr))["value"]


# ── 入力：要素操作の引数を宣言し、二重に書かれた fieldPath を1つにする ──
inputs = [x for x in q("inputs", "items")]
seen, dedup = set(), []
for x in inputs:
    if x["name"] in seen:
        continue
    seen.add(x["name"])
    dedup.append(x)
dedup.append({
    "name": "elementOps",
    "description": "要素操作の並び。1回の呼び出しで複数を受け取り、全か無かで適用される。"
                   "各操作は「種類（足す／欄を直す／取り下げる）・対象の配列の道・鍵の値・"
                   "書き込む中身」を持つ。values とは別の引数であり、"
                   "配列を丸ごと渡す経路とは混ざらない",
})

# ── 事前条件 ──
pre = q("preconditions", "items")
pre.append("要素操作の場合: 対象のdocumentPathが与えられ、その document が適合の検証を通っている"
           "（鍵を宣言した配列に鍵の重複が無いことは、要素操作より先に検証が担保する）")

# ── エラー：新設の4件を、条件が重ならない形で登録する ──
errors = q("errors", "items")
errors += [
    {"code": "UNKNOWN_ELEMENT_KEY",
     "condition": ["要素操作が指した鍵を持つ要素が、対象の配列に存在しない"]},
    {"code": "STILL_REFERENCED",
     "condition": ["取り下げようとした要素の鍵が、宣言された参照からまだ指されている"]},
    {"code": "WHOLESALE_REPLACE_NOT_ALLOWED",
     "condition": ["鍵を宣言した配列に対して、values で配列全体が与えられた"]},
    {"code": "ELEMENT_OPS_NOT_APPLICABLE",
     "condition": ["順序そのものが意味を持つと宣言された配列に対して、要素操作が与えられた",
                   "同じ配列に順序の宣言と鍵の宣言が両方あるとき（宣言そのものの誤りであり、"
                   "鍵を見に行く前にこれを返す）"]},
]

# ── 受け入れ基準の差し替えと追加 ──
crit = q("acceptanceCriteria", "items")
by_id = {c["id"]: c for c in crit}
by_id["element-retire"]["text"] = (
    "When 鍵を宣言した配列へ retire_element で鍵が与えられ、"
    "宣言された参照のどこからもその鍵が指されていないとき、"
    "システムはその要素を配列から取り除く shall。")
by_id["retire-blocked-by-reference"]["text"] = (
    "If retire_element の対象の鍵が、宣言された参照のいずれかからまだ指されているとき、"
    "システムは STILL_REFERENCED を返し、指している場所を示して取り除かない shall。")
crit.append({
    "id": "ordered-and-key-declarations-are-exclusive",
    "text": "If 同じ配列に順序の宣言と鍵の宣言が両方あるとき、システムは "
            "ELEMENT_OPS_NOT_APPLICABLE を返し、宣言そのものが誤っていることを示す shall"
            "（どちらが優先かを実装が黙って決めないため）。"})

# ── シナリオ：取り下げも順序配列で試す／宣言の併存 ──
scen = q("acceptanceScenarios", "scenarios")


def sc(name, cat, view, sat, given, when, then):
    return {"name": name, "category": cat, "viewpoint": view, "satisfies": sat,
            "gherkin": f"Scenario: {name}\n  Given {given}\n  When {when}\n  Then {then}"}


scen += [
    sc("順序が意味を持つ配列からは取り下げもできない", "異常系",
       "並びの扱い：3つの要素操作すべてが等しく塞がれているか",
       ["ordered-array-rejects-element-ops"],
       "順序そのものが意味を持つと宣言された手順の配列",
       "その配列へ retire_element する",
       "ELEMENT_OPS_NOT_APPLICABLE が返り、丸ごと置き換えて書き換えるものだと案内される"),
    sc("順序と鍵を両方宣言した配列は宣言の誤りとして返る", "異常系",
       "宣言の整合：実装が優先順位を黙って決めないか",
       ["ordered-and-key-declarations-are-exclusive"],
       "順序の宣言と鍵の宣言を両方持つ配列", "その配列へ add_element する",
       "ELEMENT_OPS_NOT_APPLICABLE が返り、宣言そのものの誤りとして示される"),
]

# ── 操作保証シナリオ：中核の主張に筋書きを付ける ──
gs = q("guaranteeScenarios", "scenarios")
gs.append({
    "name": "要素操作でも読み書きの対象は Document 全体である",
    "category": "境界値",
    "viewpoint": "集約の単位：要素だけを切り離して指させないこと",
    "gherkin": "Scenario: 要素操作でも読み書きの対象は Document 全体である\n"
               "  Given 鍵を宣言した配列を持つ Document\n"
               "  When 要素を1件 add_element する\n"
               "  Then 読み書きの対象は Document 全体であり、"
               "配列や要素だけを指す経路は外部へ現れない",
    "covers": "操作保証: 要素操作でも対象は Document 全体",
})

vals = {
    "content.inputs.items": dedup,
    "content.preconditions.items": pre,
    "content.errors.items": errors,
    "content.acceptanceCriteria.items": crit,
    "content.acceptanceScenarios.scenarios": scen,
    "content.guaranteeScenarios.scenarios": gs,
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:400])
print(run("validate", "--path", P)[:300])
print(f"入力 {len(dedup)} / エラー {len(errors)} / 基準 {len(crit)} / "
      f"シナリオ {len(scen)} / 保証シナリオ {len(gs)}")
