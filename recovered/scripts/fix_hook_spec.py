"""hook の判定仕様を v9 へ移し、要素操作との干渉を解く基準を足す。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/"
     "usecase/uc-check-query-precedes-array-fill." + "json")
SC = (".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/"
      "usecase/uc-scaffold-document." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(path, block, expr="@"):
    return json.loads(run("query", "--operation", "query_path", "--path", path,
                          "--blockKey", block, "--expression", expr))["value"]


def gherkin(n, g, w, t):
    return f"Scenario: {n}\n  Given {g}\n  When {w}\n  Then {t}"


print(run("scaffold", "--operation", "migrate_schema", "--path", P,
          "--schemaRef", "DomainSpecSchema/v9")[:140])

CRIT = [
    ("denies-array-fill-without-query",
     "When 配列の値を含む書き込みで、対象の道が先行して読まれていないとき、"
     "システムは拒否判定と理由を返す shall。"),
    ("allows-array-fill-after-query",
     "When 配列の値を含む書き込みで、対象の道が先行して読まれているとき、"
     "システムは許可判定を返す shall。"),
    ("allows-non-array-fill",
     "While 配列の値を含まない書き込みのとき、システムは先行して読まれたかに関わらず"
     "許可判定を返す shall。"),
    ("does-not-prescribe-forbidden-procedure",
     "When 拒否判定の理由を返すとき、システムは丸ごとの置き換えだけを手順として示さず、"
     "鍵を宣言した配列では要素操作を使うことも併せて示す shall"
     "（鍵を宣言した配列では丸ごとの置き換えが engine 側で拒まれるため、"
     "この判定より手前で拒否しながら engine が禁じた手順を勧めると、進む道が無くなる）。"),
    ("element-ops-are-out-of-scope",
     "While 書き込みが要素操作として与えられたとき、システムは配列の値を含む書き込みとして"
     "扱わず、許可判定を返す shall"
     "（要素操作は既存の要素を読まずに済ませるための経路であり、"
     "先行して読ませることはその目的と正面から反するため）。"),
]

SCEN = [
    ("配列値を含むfillで先行queryが無い場合は拒否される", ["denies-array-fill-without-query"]),
    ("配列値を含むfillで先行queryがある場合は許可される", ["allows-array-fill-after-query"]),
    ("配列値を含まないfillは先行queryの有無に関わらず許可される", ["allows-non-array-fill"]),
]

NEW = [
    {"name": "拒否の理由は要素操作の道も示す", "category": "境界値",
     "viewpoint": "案内の整合：手前の判定が、engine の禁じた手順だけを勧めていないか",
     "satisfies": ["does-not-prescribe-forbidden-procedure"],
     "gherkin": gherkin("拒否の理由は要素操作の道も示す",
                        "配列の値を含み、先行して読まれていない書き込み",
                        "判定する",
                        "拒否判定とともに、丸ごとの置き換えと要素操作の двух方の道が示される")},
    {"name": "要素操作は先行して読むことを求められない", "category": "正常系",
     "viewpoint": "案内の整合：要素操作の目的を、この判定が打ち消していないか",
     "satisfies": ["element-ops-are-out-of-scope"],
     "gherkin": gherkin("要素操作は先行して読むことを求められない",
                        "先行して読まれていない、要素操作としての書き込み",
                        "判定する",
                        "許可判定が返る")},
]

cur = q(P, "acceptanceScenarios", "scenarios")
by_name = {s["name"]: s for s in cur}
out = []
for name, ids in SCEN:
    s = dict(by_name[name])
    s.pop("covers", None)
    s["satisfies"] = ids
    out.append(s)
out.extend(NEW)

vals = {
    "content.acceptanceCriteria.items": [{"id": i, "text": t} for i, t in CRIT],
    "content.acceptanceScenarios.scenarios": out,
    "content.operationGuarantees.items": [{
        "id": "same-verdict-regardless-of-caller",
        "text": "When 同一の入力を渡したとき、システムは呼び出し経路（直接呼び出し／CLI）に"
                "よらず同一の判定結果を返す shall。"}],
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:200])
print(run("validate", "--path", P)[:250])

# 記入指示へ鍵の宣言が抜けることを、基準として書く
crit = q(SC, "acceptanceCriteria", "items")
crit.append({
    "id": "fill-template-carries-element-declarations",
    "text": "When 記入対象の道と執筆ガイダンスを返すとき、システムは配列については"
            "鍵の宣言・参照関係の宣言・順序の宣言も併せて返す shall"
            "（書き手に渡る指示に現れない宣言は、書き手にとって存在しないため）。"})
scen = q(SC, "acceptanceScenarios", "scenarios")
scen.append({
    "name": "記入指示に鍵の宣言が現れる", "category": "正常系",
    "viewpoint": "宣言の到達：宣言が engine の内側だけで使われていないか",
    "satisfies": ["fill-template-carries-element-declarations"],
    "gherkin": gherkin("記入指示に鍵の宣言が現れる",
                       "鍵と参照関係を宣言した配列を持つ schema",
                       "骨格を生成して記入指示を受け取る",
                       "その配列の記入指示に、鍵の欄と参照関係の宣言が現れている")})
print(run("scaffold", "--operation", "fill", "--path", SC,
          "--values", json.dumps({"content.acceptanceCriteria.items": crit,
                                  "content.acceptanceScenarios.scenarios": scen},
                                 ensure_ascii=False))[:200])
print(run("validate", "--path", SC)[:250])
