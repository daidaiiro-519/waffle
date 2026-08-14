"""uc-validate-document を v9 へ移し、鍵の一意性の基準を足す。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-validation/"
     "usecase/uc-validate-document." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


CRITERIA = [
    {"id": "conformant-is-validated",
     "text": "When 適合する Document が与えられたとき、システムは VALIDATED 判定を返す shall。"},
    {"id": "nonconformant-fails-with-details",
     "text": "When 不適合のとき、システムは違反詳細つきで失敗を返す shall。"},
    {"id": "missing-schema-ref",
     "text": "If schemaRef が無いとき、システムは MISSING_SCHEMA_REF を返す shall。"},
    {"id": "writes-judged-status",
     "text": "When 適合し状態遷移も可能なとき、システムは判定したstatusを実際にDocumentへ書き込む shall。"},
    {"id": "unparsable-input",
     "text": "If 対象ファイルが JSON として解釈できないとき、システムは INVALID_JSON を返す shall。"},
    {"id": "terminal-status-rejected",
     "text": "If Document が終端の状態にあるとき、システムは INVALID_TRANSITION を返し、状態を変えない shall。"},
    # ここから、要素単位の編集を成り立たせるための基準
    {"id": "duplicate-element-key-rejected",
     "text": "If 鍵を宣言した配列の中に、同じ鍵を持つ要素が2つ以上あるとき、"
             "システムは不適合として、その配列と重複した鍵を違反詳細に含めて返す shall。"},
]

SCEN = [
    ("適合する Document は VALIDATED 判定になる", ["conformant-is-validated"]),
    ("不適合は違反詳細つきで失敗する", ["nonconformant-fails-with-details"]),
    ("schemaRef を持たない Document は検証できない", ["missing-schema-ref"]),
    ("既存documentはschemaに適合する", ["conformant-is-validated", "writes-judged-status"]),
    ("SUPERSEDEDは終端でありvalidateを受け付けない", ["terminal-status-rejected"]),
    ("不正なJSONはINVALID_JSON", ["unparsable-input"]),
    ("適合判定は実際にstatusをdocumentへ書き込む", ["writes-judged-status"]),
]

NEW_SCEN = [
    {"name": "鍵が重複した配列は不適合になる",
     "category": "異常系",
     "viewpoint": "要素の同一性：鍵が要素を一意に指すという前提が崩れていないか",
     "satisfies": ["duplicate-element-key-rejected"],
     "gherkin": "Scenario: 鍵が重複した配列は不適合になる\n"
                "  Given 鍵を宣言した配列に、同じ鍵を持つ要素が2つある Document\n"
                "  When 適合を検証する\n"
                "  Then 不適合となり、違反詳細にその配列と重複した鍵が含まれる"},
    {"name": "鍵を宣言していない配列は値が重なっていても適合する",
     "category": "境界値",
     "viewpoint": "要素の同一性：一意性の要求が、宣言した配列にだけ及んでいるか",
     "satisfies": ["duplicate-element-key-rejected"],
     "gherkin": "Scenario: 鍵を宣言していない配列は値が重なっていても適合する\n"
                "  Given 鍵を宣言していない配列に、同じ値の要素が2つある Document\n"
                "  When 適合を検証する\n"
                "  Then 適合と判定される"},
]

# 1. 版を上げる
print(run("scaffold", "--operation", "migrate_schema", "--path", P,
          "--schemaRef", "DomainSpecSchema/v9")[:200])

# 2. 既存シナリオを読み、covers を satisfies へ差し替える
cur = json.loads(run("query", "--operation", "query_path", "--path", P,
                     "--blockKey", "acceptanceScenarios",
                     "--expression", "scenarios"))["value"]
by_name = {s["name"]: s for s in cur}
sat = {n: s for n, s in SCEN}
out = []
for name, ids in SCEN:
    s = dict(by_name[name])
    s.pop("covers", None)
    s["satisfies"] = ids
    out.append(s)
out.extend(NEW_SCEN)

vals = {
    "content.acceptanceCriteria.items": CRITERIA,
    "content.acceptanceScenarios.scenarios": out,
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:300])
print(run("validate", "--path", P)[:400])
