"""版ドリフト検査に、滞留の宣言との2方向照合を入れる（v10へ移しつつ書き直す）。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/"
     "usecase/uc-check-schema-version-drift." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def gk(n, g, w, t):
    return f"Scenario: {n}\n  Given {g}\n  When {w}\n  Then {t}"


CRITERIA = [
    ("broken-reference",
     "When Documentのschema参照が指す版が実在しないとき、システムはその組を、"
     "指す先の無い参照として返す shall。"),
    ("undeclared-lag",
     "If Documentが最新でない版を指しており、その滞留が宣言されていないとき、"
     "システムはその組を違反として返す shall"
     "（宣言の無い滞留を情報として流すと、古いまま置くことに帰結が無くなり、"
     "版がいつまでも追いつかなくなる）。"),
    ("declared-lag",
     "While Documentが最新でない版を指しており、その滞留が理由とともに宣言されているとき、"
     "システムはそれを違反とせず、宣言された理由を添えて滞留中として返す shall。"),
    ("stale-declaration-caught-up",
     "When 滞留が宣言されている対象が、既に最新の版を指しているとき、"
     "システムはその宣言を、役目を終えた宣言として返す shall。"),
    ("stale-declaration-missing-target",
     "When 滞留が宣言されている対象が、走査の領域に1件も見つからないとき、"
     "システムはその宣言を、役目を終えた宣言として返す shall。"),
    ("missing-declared-fields",
     "When 参照先Schemaが宣言する値フィールドのpathを、Documentの実データが持たないとき、"
     "システムはその組を、追従していない欄として返す shall。"),
    ("empty-when-aligned",
     "While 全Documentのschema参照が実在しかつ最新であり、宣言済みフィールドにも追従しており、"
     "役目を終えた宣言も無いとき、システムは全ての一覧を空で返す shall。"),
    ("invalid-path",
     "If 走査の対象が存在しないとき、システムは INVALID_PATH エラーを返す shall。"),
]

SCEN_OLD = {
    "全Documentが最新版を参照しているとき差分なしと判定する": ["empty-when-aligned"],
    "実在しない版を指すschemaRefを検出する": ["broken-reference"],
    "最新でない版を参照しているDocumentを検出する": ["undeclared-lag"],
    "Schemaが宣言する値フィールドをDocumentが持たないことを検出する": ["missing-declared-fields"],
    "対象のdocuments_rootが存在しないときのときINVALID_PATH": ["invalid-path"],
}

NEW = [
    {"name": "宣言の無い滞留は違反として上がる", "category": "異常系",
     "viewpoint": "滞留の帰結：古いまま置くことに帰結があるか",
     "satisfies": ["undeclared-lag"],
     "gherkin": gk("宣言の無い滞留は違反として上がる",
                   "最新でない版を指しており、滞留が宣言されていない Document",
                   "版の追従を調べる", "その Document が違反として返る")},
    {"name": "宣言のある滞留は違反にならない", "category": "正常系",
     "viewpoint": "滞留の帰結：理由のある先送りの道を塞いでいないか",
     "satisfies": ["declared-lag"],
     "gherkin": gk("宣言のある滞留は違反にならない",
                   "最新でない版を指し、理由とともに滞留が宣言されている Document",
                   "版の追従を調べる", "違反にはならず、宣言された理由を添えて滞留中として返る")},
    {"name": "追いついた対象の宣言は役目を終えたものとして上がる", "category": "境界値",
     "viewpoint": "2方向の照合：宣言の側の余りを見つけられるか",
     "satisfies": ["stale-declaration-caught-up"],
     "gherkin": gk("追いついた対象の宣言は役目を終えたものとして上がる",
                   "滞留が宣言されているが、既に最新の版を指している Document",
                   "版の追従を調べる", "その宣言が、役目を終えた宣言として返る")},
    {"name": "対象が見つからない宣言は役目を終えたものとして上がる", "category": "境界値",
     "viewpoint": "2方向の照合：消えた対象を指したままの宣言を残さないか",
     "satisfies": ["stale-declaration-missing-target"],
     "gherkin": gk("対象が見つからない宣言は役目を終えたものとして上がる",
                   "走査の領域に1件も見つからない対象を指す滞留の宣言",
                   "版の追従を調べる", "その宣言が、役目を終えた宣言として返る")},
]

DESC = [
    "Document の schema 参照を、実在する Schema の版と突き合わせ、"
    "指す先の無い参照・最新でない参照・追従していない欄を機械的に検出する。",
    "最新でない参照は、滞留の宣言と2方向で照合する。"
    "宣言の無い滞留は違反として上げ、理由のある滞留は通す。"
    "宣言の側に余り（既に追いついた対象・見つからない対象）があれば、それも上げる。",
    "先送りそのものを禁じるのではなく、黙って先送りされることを禁じる。"
    "宣言の不在を「問題なし」と読むと、古いまま置くことに帰結が無くなる。",
]

INPUTS = [
    {"name": "documentsRoot", "description": "Documentの実インスタンス群を走査する対象ディレクトリ"},
    {"name": "滞留の宣言", "description": "最新でない版に留まってよい対象と、その理由・待っているものの一覧。"
                                     "宣言を持たない滞留は違反になる"},
]

print(run("scaffold", "--operation", "clear_field", "--path", P,
          "--fieldPath", "content.operationGuarantees")[:110])
print(run("scaffold", "--operation", "clear_field", "--path", P,
          "--fieldPath", "content.guaranteeScenarios")[:110])
print(run("scaffold", "--operation", "migrate_schema", "--path", P,
          "--schemaRef", "DomainSpecSchema/v10")[:110])

cur = json.loads(run("query", "--operation", "query_path", "--path", P,
                     "--blockKey", "acceptanceScenarios", "--expression", "scenarios"))["value"]
out = []
for s in cur:
    ids = SCEN_OLD.get(s["name"])
    if not ids:
        print("  対応づけできず:", s["name"])
        continue
    s = dict(s)
    s.pop("covers", None)
    s["satisfies"] = ids
    out.append(s)
out.extend(NEW)

vals = {
    "content.description.items": DESC,
    "content.inputs.items": INPUTS,
    "content.acceptanceCriteria.items": [{"id": i, "text": t} for i, t in CRITERIA],
    "content.acceptanceScenarios.scenarios": out,
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:200])
print(run("validate", "--path", P)[:250])
print(f"基準 {len(CRITERIA)} / シナリオ {len(out)}")
