"""捨てた語「被覆」を残らず置き換える。"""
from __future__ import annotations

import json
import pathlib
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
RULES = [
    ("受け入れ基準の被覆を確かめる", "受け入れ基準にシナリオが付いているかを確かめる"),
    ("受け入れ基準の被覆を確かめ", "受け入れ基準にシナリオが付いているかを確かめ"),
    ("被覆の確認", "基準とシナリオの結び付きの確認"),
    ("被覆の突き合わせ", "結び付きの突き合わせ"),
    ("被覆判定", "結び付きの判定"),
    ("被覆を測る", "結び付きを測る"),
    ("被覆で測る", "結び付きで測る"),
    ("被覆の読み手", "結び付きの読み手"),
    ("被覆率", "結び付きの充足"),
    ("被覆", "結び付き"),
]


def convert(t: str) -> str:
    for a, b in RULES:
        t = t.replace(a, b)
    return t


def walk(n):
    if isinstance(n, str):
        return convert(n)
    if isinstance(n, list):
        return [walk(x) for x in n]
    if isinstance(n, dict):
        return {k: walk(v) for k, v in n.items()}
    return n


def q(p, b, e):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", p, "--blockKey", b, "--expression", e],
                       capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout)["value"]
    except Exception:
        return None


TARGETS = {
    ".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/usecase/uc-check-criteria-coverage.json": [
        ("title", "title", "content.title.title"),
        ("actorIntent", "intent", "content.actorIntent.intent"),
        ("usecaseRationale", "items", "content.usecaseRationale.items"),
        ("description", "items", "content.description.items"),
        ("mainFlow", "participants", "content.mainFlow.participants"),
        ("mainFlow", "steps", "content.mainFlow.steps"),
        ("postconditions", "items", "content.postconditions.items"),
        ("acceptanceCriteria", "items", "content.acceptanceCriteria.items"),
        ("acceptanceScenarios", "scenarios", "content.acceptanceScenarios.scenarios"),
        ("operationGuarantees", "items", "content.operationGuarantees.items"),
        ("guaranteeScenarios", "scenarios", "content.guaranteeScenarios.scenarios"),
    ],
    ".waffle/documents/handoff/handoff-criteria-scenario-link.json": [
        ("designViewpoints", "items", "content.designViewpoints.items"),
        ("implementationViewpoints", "items", "content.implementationViewpoints.items"),
        ("constraints", "items", "content.constraints.items"),
        ("completionImage", "layers", "content.completionImage.layers"),
        ("usageExamples", "items", "content.usageExamples.items"),
        ("expectedScope", "items", "content.expectedScope.items"),
        ("reviewStatus", "findings", "content.reviewStatus.findings"),
        ("description", "text", "content.description.text"),
    ],
    ".waffle/documents/knowledge/knowledge-cand-one-binding-for-all-contract-levels.json": [
        ("principles", "items", "content.principles.items"),
        ("antiPatterns", "items", "content.antiPatterns.items"),
        ("provenance", "caveats", "content.provenance.caveats"),
        ("examples", "text", "content.examples.text"),
        ("description", "text", "content.description.text"),
    ],
}

for path, specs in TARGETS.items():
    values = {}
    for block, expr, fp in specs:
        cur = q(path, block, expr)
        if cur is None:
            continue
        new = walk(cur)
        if new != cur:
            values[fp] = new
    if values:
        r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill",
                            "--path", path, "--values", json.dumps(values, ensure_ascii=False)],
                           capture_output=True, text=True, cwd=CWD)
        print(f"[{pathlib.Path(path).name}] {len(values)} ブロック更新")
    else:
        print(f"[{pathlib.Path(path).name}] 変更なし")

for name in ("spec-structure.html", "adr-criteria-scenario-link.html"):
    p = pathlib.Path("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
                     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad") / name
    t = p.read_text(encoding="utf-8")
    n = convert(t)
    if n != t:
        p.write_text(n, encoding="utf-8")
        print(f"[{name}] 更新")
    else:
        print(f"[{name}] 変更なし")
