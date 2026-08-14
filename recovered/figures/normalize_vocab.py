"""語彙を、描画される見出しに合わせてそろえる。

受け入れ「条件」→「基準」、「筋書き」「振る舞いのシナリオ」→「シナリオ」。
不変条件・事前条件・事後条件は別語なので触らない。
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"

RULES = [
    ("振る舞いのシナリオ", "シナリオ"),
    ("振る舞いの筋書き", "シナリオ"),
    ("振る舞いの側", "シナリオの側"),
    ("筋書き", "シナリオ"),
    ("受け入れ条件", "受け入れ基準"),
    ("条件と筋書き", "基準とシナリオ"),
    ("条件とシナリオ", "基準とシナリオ"),
    ("どの条件", "どの基準"),
    ("その条件", "その基準"),
    ("1つの条件", "1つの受け入れ基準"),
    ("各条件", "各基準"),
    ("条件の側", "基準の側"),
    ("条件の欠け", "基準の欠け"),
    ("条件の識別子", "基準の識別子"),
    ("条件ブロック", "基準ブロック"),
    ("条件の書き漏れ", "基準の書き漏れ"),
    ("条件の並び", "基準の並び"),
    ("条件の配列", "基準の配列"),
    ("条件の欄", "基準の欄"),
    ("条件の文", "基準の文"),
    ("条件の粒度", "基準の粒度"),
    ("条件が2つ", "基準が2つ"),
    ("条件を指す", "基準を指す"),
    ("条件を満たす", "基準を満たす"),
    ("条件を書き足す", "基準を書き足す"),
    ("条件を数え", "基準を数え"),
    ("条件を分ける", "基準を分ける"),
    ("条件に対する", "基準に対する"),
    ("条件にシナリオ", "基準にシナリオ"),
    ("条件を担当", "基準を担当"),
    ("条件17件", "基準17件"),
    ("条件の集合", "基準の集合"),
]
# 「不変条件」等を壊さないための保護
GUARD = ("不変条件", "事前条件", "事後条件", "前提条件", "成立条件", "条件付き", "条件分岐")


def convert(text: str) -> str:
    holes = {}
    for i, g in enumerate(GUARD):
        key = f"\x00{i}\x00"
        holes[key] = g
        text = text.replace(g, key)
    for a, b in RULES:
        text = text.replace(a, b)
    for key, g in holes.items():
        text = text.replace(key, g)
    return text


def walk(node):
    if isinstance(node, str):
        return convert(node)
    if isinstance(node, list):
        return [walk(x) for x in node]
    if isinstance(node, dict):
        return {k: walk(v) for k, v in node.items()}
    return node


def q(path, block, expr):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", path, "--blockKey", block, "--expression", expr],
                       capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout)["value"]
    except Exception:
        return None


def fill(path, values):
    r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill",
                        "--path", path, "--values", json.dumps(values, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


TARGETS = {
    ".waffle/documents/knowledge/knowledge-cand-one-binding-for-all-contract-levels.json": [
        ("title", "title", "content.title.title"),
        ("description", "text", "content.description.text"),
        ("description", "questions", "content.description.questions"),
        ("principles", "items", "content.principles.items"),
        ("classifications", "items", "content.classifications.items"),
        ("decisionCriteria", "stages", "content.decisionCriteria.stages"),
        ("examples", "text", "content.examples.text"),
        ("antiPatterns", "items", "content.antiPatterns.items"),
        ("provenance", "source", "content.provenance.source"),
        ("provenance", "caveats", "content.provenance.caveats"),
        ("relatedConcepts", "items", "content.relatedConcepts.items"),
    ],
    ".waffle/documents/knowledge/knowledge-cand-operation-contract-closes-invariants.json": [
        ("title", "title", "content.title.title"),
        ("description", "text", "content.description.text"),
        ("description", "questions", "content.description.questions"),
        ("principles", "items", "content.principles.items"),
        ("classifications", "items", "content.classifications.items"),
        ("decisionCriteria", "stages", "content.decisionCriteria.stages"),
        ("examples", "text", "content.examples.text"),
        ("antiPatterns", "items", "content.antiPatterns.items"),
        ("provenance", "caveats", "content.provenance.caveats"),
        ("relatedConcepts", "items", "content.relatedConcepts.items"),
    ],
    ".waffle/documents/handoff/handoff-criteria-scenario-link.json": [
        ("title", "title", "content.title.title"),
        ("description", "text", "content.description.text"),
        ("designViewpoints", "items", "content.designViewpoints.items"),
        ("implementationViewpoints", "items", "content.implementationViewpoints.items"),
        ("constraints", "items", "content.constraints.items"),
        ("completionImage", "layers", "content.completionImage.layers"),
        ("completionImage", "relationships", "content.completionImage.relationships"),
        ("usageExamples", "items", "content.usageExamples.items"),
        ("expectedScope", "items", "content.expectedScope.items"),
        ("reviewStatus", "findings", "content.reviewStatus.findings"),
    ],
    ".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/usecase/uc-check-criteria-coverage.json": [
        ("title", "title", "content.title.title"),
        ("actorIntent", "intent", "content.actorIntent.intent"),
        ("usecaseRationale", "items", "content.usecaseRationale.items"),
        ("description", "items", "content.description.items"),
        ("preconditions", "items", "content.preconditions.items"),
        ("inputs", "items", "content.inputs.items"),
        ("mainFlow", "steps", "content.mainFlow.steps"),
        ("postconditions", "items", "content.postconditions.items"),
        ("acceptanceCriteria", "items", "content.acceptanceCriteria.items"),
        ("acceptanceScenarios", "scenarios", "content.acceptanceScenarios.scenarios"),
        ("operationGuarantees", "items", "content.operationGuarantees.items"),
        ("guaranteeScenarios", "scenarios", "content.guaranteeScenarios.scenarios"),
    ],
}

for path, specs in TARGETS.items():
    values = {}
    for block, expr, fillpath in specs:
        cur = q(path, block, expr)
        if cur is None:
            continue
        new = walk(cur)
        if new != cur:
            values[fillpath] = new
    if values:
        out = fill(path, values)
        print(f"[{pathlib.Path(path).name}] 変更 {len(values)} ブロック")
    else:
        print(f"[{pathlib.Path(path).name}] 変更なし")

# ---- ADR（手書きHTML）
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
