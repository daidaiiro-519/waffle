"""図の読み取りを、図の後ろに置く——を仕様へ足す。

図の前に置くと要約として読まれ、図を見る前の前置きになる。
読み取りは図を見たあとに解釈を固定するためのものなので、図の後ろに来る必要がある。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/"
     "usecase/uc-render-document." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(block, expr="@"):
    return json.loads(run("query", "--operation", "query_path", "--path", P,
                          "--blockKey", block, "--expression", expr))["value"]


crit = q("acceptanceCriteria", "items")
by = {c["id"]: c for c in crit}
by["figure-reading-is-rendered-with-the-figure"]["text"] = (
    "When 図を描画するとき、システムは図に添えられた意図を図の前に、読み取りを図の後ろに描画する shall"
    "（意図は何を見るかを先に告げるもの、読み取りは見たあとに解釈を固定するもので、"
    "順序を入れ替えると読み取りが図を見る前の要約として読まれる）。")

scen = q("acceptanceScenarios", "scenarios")
scen.append({
    "name": "図の読み取りは図の後ろに置かれる",
    "category": "正常系",
    "viewpoint": "図と説明の順序：説明が図を見たあとの解釈として読めるか",
    "satisfies": ["figure-reading-is-rendered-with-the-figure"],
    "gherkin": "Scenario: 図の読み取りは図の後ろに置かれる\n"
               "  Given 意図と読み取りを持つ図の宣言\n"
               "  When 描画する\n"
               "  Then 意図・図・読み取りの順に並ぶ",
})

print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps({"content.acceptanceCriteria.items": crit,
                                  "content.acceptanceScenarios.scenarios": scen},
                                 ensure_ascii=False))[:140])
print(run("validate", "--path", P)[:180])
print(run("render", "--path", P)[:100])