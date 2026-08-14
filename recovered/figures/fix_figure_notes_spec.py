"""図の注釈を表として図の後ろに置く——を仕様へ足す。

前の版で「読み取りを図の後ろへ」と書いたが、読み取りは図全体の一文に戻し、
要素ごとの注意書きは注釈として持つ形に決め直したので、基準を書き換える。
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
    "When 図を描画するとき、システムは図に添えられた意図と読み取りを図の前に描画する shall"
    "（図を描画できない読み手が、そこだけで何の図かを取れるようにするため）。")
crit.append({
    "id": "figure-notes-are-rendered-as-a-table-after-the-figure",
    "text": "When 図の宣言が注釈を持つとき、システムは注釈を、図の要素の名前と"
            "その要素について図から決められないことの対にして、図の後ろに表として描画する shall"
            "（図は読み手に推測の余地を残すので、どの要素についての話かを名指しした上で"
            "解釈を固定する必要がある。表にするのは、どこにも紐づかない一般論を書いたときに"
            "それが見えるようにするため）。",
})

scen = q("acceptanceScenarios", "scenarios")
scen = [s for s in scen if s["name"] != "図の読み取りは図の後ろに置かれる"]
scen.append({
    "name": "図の注釈は図の後ろに表として置かれる",
    "category": "正常系",
    "viewpoint": "図と注釈の対応：どの要素についての注意書きかが名指しされているか",
    "satisfies": ["figure-notes-are-rendered-as-a-table-after-the-figure"],
    "gherkin": "Scenario: 図の注釈は図の後ろに表として置かれる\n"
               "  Given 要素の名前と注意書きの対を持つ図の宣言\n"
               "  When 描画する\n"
               "  Then 図の後ろに、要素の名前と注意書きを列に持つ表が置かれる",
})
scen.append({
    "name": "注釈を持たない図には表が付かない",
    "category": "境界値",
    "viewpoint": "空の注釈：読み違えようのない図に空の表が残らないか",
    "satisfies": ["figure-notes-are-rendered-as-a-table-after-the-figure"],
    "gherkin": "Scenario: 注釈を持たない図には表が付かない\n"
               "  Given 注釈を持たない図の宣言\n"
               "  When 描画する\n"
               "  Then 図の後ろに表は置かれない",
})

print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps({"content.acceptanceCriteria.items": crit,
                                  "content.acceptanceScenarios.scenarios": scen},
                                 ensure_ascii=False))[:130])
print(run("validate", "--path", P)[:180])
print(run("render", "--path", P)[:100])