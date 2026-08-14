"""出力形式そのものの原文は囲わない、を仕様へ足す。

Markdown の表を ```markdown で囲うと、表として読めなくなる。
原文を変換しないことと、原文が意図した見え方を保つことは両立させる。
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
by["verbatim-is-rendered-as-source"]["text"] = (
    "When 原文の宣言を描画するとき、システムは意図と読み取りを文章として描画し、"
    "原文を宣言された種類のコードブロックとしてそのまま描画する shall（原文を変換しない）。"
    "ただし宣言された種類が描画の出力形式そのものであるとき、システムは囲わずにそのまま置く shall"
    "（囲うと、表が表として読めなくなるなど、原文が意図した見え方を失う）。")

scen = q("acceptanceScenarios", "scenarios")
scen.append({
    "name": "出力形式そのものの原文は囲わずに置かれる",
    "category": "境界値",
    "viewpoint": "原文の見え方：囲うことで原文が意図した形を失わないか",
    "satisfies": ["verbatim-is-rendered-as-source"],
    "gherkin": "Scenario: 出力形式そのものの原文は囲わずに置かれる\n"
               "  Given 種類が描画の出力形式そのものである原文の宣言\n"
               "  When 描画する\n"
               "  Then 原文はコードブロックに囲われず、そのまま置かれる",
})

print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps({"content.acceptanceCriteria.items": crit,
                                  "content.acceptanceScenarios.scenarios": scen},
                                 ensure_ascii=False))[:150])
print(run("validate", "--path", P)[:180])
print(run("render", "--path", P)[:100])
