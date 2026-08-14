"""validate・criteria-coverage・業務サービス2件を、検証の指摘に沿って直す。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
S = ".waffle/documents/specs/bc-waffle"
VAL = f"{S}/subdomain/sd-validation/usecase/uc-validate-document." + "json"
COV = f"{S}/subdomain/sd-reconciliation/usecase/uc-check-criteria-coverage." + "json"
DSP = f"{S}/domain-service/ds-patch-array-element." + "json"
DSC = f"{S}/domain-service/ds-collect-key-references." + "json"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(path, block, expr="@"):
    return json.loads(run("query", "--operation", "query_path", "--path", path,
                          "--blockKey", block, "--expression", expr))["value"]


def fill(path, vals, label):
    out = run("scaffold", "--operation", "fill", "--path", path,
              "--values", json.dumps(vals, ensure_ascii=False))
    v = run("validate", "--path", path)
    print(f"  [{label}] {'検証を通過' if '\"VALIDATED\"' in v else (out[:120] + v[:220])}")
    if '"VALIDATED"' in v:
        run("render", "--path", path)


def gherkin(name, given, when, then):
    return f"Scenario: {name}\n  Given {given}\n  When {when}\n  Then {then}"


def sc(name, cat, view, sat, given, when, then):
    return {"name": name, "category": cat, "viewpoint": view, "satisfies": sat,
            "gherkin": gherkin(name, given, when, then)}


# ── 1. validate：宣言し忘れが黙って許可へ倒れないようにする ──────────
crit = q(VAL, "acceptanceCriteria", "items")
crit.append({
    "id": "keyed-array-declares-references",
    "text": "If 鍵を宣言した配列が、参照関係の宣言を持たないとき、システムは不適合として"
            "その配列を違反詳細に含めて返す shall"
            "（どこからも指されないことが正しいなら、指されない旨を宣言させるため。"
            "宣言の欠けを『指されていない』と読むと、取り下げの規律が黙って効かなくなる）。"})
scen = q(VAL, "acceptanceScenarios", "scenarios")
scen += [
    sc("鍵を宣言して参照関係を宣言していない配列は不適合になる", "異常系",
       "宣言の完全性：宣言の欠けが、規律の沈黙にならないか",
       ["keyed-array-declares-references"],
       "鍵は宣言しているが参照関係を宣言していない配列を持つ Schema と、それに従う Document",
       "適合を検証する",
       "不適合となり、違反詳細にその配列が含まれる"),
    sc("指されないことを宣言した配列は適合する", "境界値",
       "宣言の完全性：指されない配列を書けなくしていないか",
       ["keyed-array-declares-references"],
       "鍵を宣言し、どこからも指されない旨を宣言した配列",
       "適合を検証する", "適合と判定される"),
]
fill(VAL, {"content.acceptanceCriteria.items": crit,
           "content.acceptanceScenarios.scenarios": scen}, "uc-validate-document")

# ── 2. criteria-coverage：一意性の検知を validate へ寄せ、重複を解く ──
ccrit = [c for c in q(COV, "acceptanceCriteria", "items") if c["id"] != "reports-duplicate-ids"]
cscen = [s for s in q(COV, "acceptanceScenarios", "scenarios")
         if "reports-duplicate-ids" not in (s.get("satisfies") or [])]
fill(COV, {"content.acceptanceCriteria.items": ccrit,
           "content.acceptanceScenarios.scenarios": cscen}, "uc-check-criteria-coverage")

# ── 3. ds-patch-array-element：触れている集約を明かす ────────────────
fill(DSP, {
    "content.referencedAggregates.items": [
        {"name": "agg-document", "reason": "書き換える対象の配列は Document の中身であり、"
                                           "書き換えた結果は Document へ戻される。"},
        {"name": "agg-schema", "reason": "どの欄が鍵かという宣言と、要素に補うべき固定値は "
                                         "Schema 側の宣言から来る。"},
    ],
    "content.existenceRationale.items": [
        "2つの集約にまたがる。書き換える相手は Document の中身だが、"
        "どの欄が鍵かという物差しは Schema が持っている。"
        "どちらの集約も相手の中身を知らないので、この突き合わせをどちらの内側にも置けない。",
        "この計算はどの集約の状態も変えない。受け取った配列から新しい配列を作って返すだけで、"
        "書き戻す先を知らない。",
    ],
}, "ds-patch-array-element")

# ── 4. ds-collect-key-references：宣言の形と手がかりを入力として明かす ──
dcrit = q(DSC, "acceptanceCriteria", "items")
dcrit.append({
    "id": "declaration-has-no-conditions",
    "text": "While 参照関係の宣言をたどるとき、システムは配列へ降りることと欄をたどることだけを行い、"
            "値による絞り込みを行わない shall"
            "（絞り込みを書けるようにすると、宣言が小さな条件式の言語になり、"
            "Schema 側から規律を迂回できてしまうため）。"})
dscen = q(DSC, "acceptanceScenarios", "scenarios")
dscen.append(sc("宣言は値による絞り込みを持たない", "境界値",
                "宣言の表現力：条件式の言語を抱え込んでいないか",
                ["declaration-has-no-conditions"],
                "配列を2段またぐ参照関係の宣言",
                "その宣言をたどって参照を集める",
                "たどった経路には値による絞り込みが1つも現れず、"
                "配列へ降りることと欄をたどることだけで到達している"))

fill(DSC, {
    "content.referencedAggregates.items": [
        {"name": "agg-document", "reason": "走査して参照を集める相手は Document の中身である。"},
        {"name": "agg-schema", "reason": "どこがどこを指すかという参照関係の宣言は "
                                         "Schema 側にあり、走査の物差しになる。"},
    ],
    "content.existenceRationale.items": [
        "2つの集約にまたがる。走査する相手は Document の中身だが、"
        "どこをたどるべきかという宣言は Schema が持っている。"
        "Document は自分がどこから指されるかを知らず、Schema は中身を知らないので、"
        "この突き合わせをどちらの内側にも置けない。",
        "この計算はどの集約の状態も変えない。読み取った時点の中身から答えが決まる。",
    ],
    "content.inputsOutputs.inputs": [
        {"name": "参照関係の宣言",
         "meaning": "ある配列の鍵が Document のどこから指されるかの宣言。"
                    "配列へ降りることと欄をたどることだけを並べた道として書かれ、"
                    "値による絞り込みを持たない。"},
        {"name": "手がかりの欄",
         "meaning": "指している側の要素の、人が見分けるための欄の名前。"
                    "参照関係の宣言と一緒に置かれる。"},
        {"name": "Document の中身", "meaning": "走査の対象。"},
        {"name": "探す鍵", "meaning": "指されているかを知りたい鍵。"},
    ],
    "content.acceptanceCriteria.items": dcrit,
    "content.acceptanceScenarios.scenarios": dscen,
}, "ds-collect-key-references")
