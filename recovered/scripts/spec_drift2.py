"""版ドリフト検査を、宣言の仕組みを持たない形へ書き直す。

古い版のままであることを情報ではなく違反として上げる。それだけ。
先送りしてよいかの判断は人が持ち、記録は記憶側に置く。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/"
     "usecase/uc-check-schema-version-drift." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


CRITERIA = [
    ("broken-reference",
     "When Documentのschema参照が指す版が実在しないとき、システムはその組を、"
     "指す先の無い参照として返す shall。"),
    ("lag-is-a-violation",
     "If Documentが最新でない版を指しているとき、システムはその組を違反として返す shall"
     "（情報として流すと、古いまま置くことに帰結が無くなり、いつまでも追いつかなくなる）。"),
    ("missing-declared-fields",
     "When 参照先Schemaが宣言する値フィールドのpathを、Documentの実データが持たないとき、"
     "システムはその組を、追従していない欄として返す shall。"),
    ("empty-when-aligned",
     "While 全Documentのschema参照が実在しかつ最新であり、宣言済みフィールドにも"
     "追従しているとき、システムは全ての一覧を空で返す shall。"),
    ("invalid-path",
     "If 走査の対象が存在しないとき、システムは INVALID_PATH エラーを返す shall。"),
]

SCEN = {
    "全Documentが最新版を参照しているとき差分なしと判定する": ["empty-when-aligned"],
    "実在しない版を指すschemaRefを検出する": ["broken-reference"],
    "最新でない版を参照しているDocumentを検出する": ["lag-is-a-violation"],
    "Schemaが宣言する値フィールドをDocumentが持たないことを検出する": ["missing-declared-fields"],
    "対象のdocuments_rootが存在しないときのときINVALID_PATH": ["invalid-path"],
}

DESC = [
    "Document の schema 参照を、実在する Schema の版と突き合わせ、"
    "指す先の無い参照・最新でない参照・追従していない欄を機械的に検出する。",
    "最新でない参照は情報ではなく違反として上げる。"
    "古いまま置くことに帰結が無いと、版はいつまでも追いつかない。",
]

INPUTS = [
    {"name": "documentsRoot", "description": "Documentの実インスタンス群を走査する対象ディレクトリ"},
]

cur = json.loads(run("query", "--operation", "query_path", "--path", P,
                     "--blockKey", "acceptanceScenarios", "--expression", "scenarios"))["value"]
out = []
for s in cur:
    ids = SCEN.get(s["name"])
    if not ids:
        continue                      # 宣言まわりで足した筋書きは落とす
    s = dict(s)
    s["satisfies"] = ids
    out.append(s)

vals = {
    "content.description.items": DESC,
    "content.inputs.items": INPUTS,
    "content.acceptanceCriteria.items": [{"id": i, "text": t} for i, t in CRITERIA],
    "content.acceptanceScenarios.scenarios": out,
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:180])
print(run("validate", "--path", P)[:200])
print(run("render", "--path", P)[:110])
print(f"基準 {len(CRITERIA)} / シナリオ {len(out)}")
