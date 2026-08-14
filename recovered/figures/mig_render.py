"""uc-render-document を v10 へ移し、描画部品の拡張の基準を足す。"""
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


IDS = [
    "renders-per-x-render", "writes-canonical-and-deploy", "deploy-per-discriminator",
    "tool-mappings-nested", "path-vars-from-content", "path-vars-per-discriminator",
    "frontmatter-per-discriminator", "frontmatter-omits-absent", "missing-schema-ref",
    "table-bullet-column", "bullet-wins-over-join", "malformed-content",
    "skips-unresolvable-deploy", "frontmatter-block-shape", "no-render-target",
    "fan-out-multiple-array-path-vars", "canonical-only-when-no-target",
    "deploy-target-owned-by-other", "reports-skipped-targets",
    "template-has-no-entity-target", "absent-role-is-entity",
    "path-not-found", "schema-ref-unresolvable", "invalid-transition",
    "deterministic-output", "supports-all-part-kinds", "omits-empty-block",
    "x-render-hidden-not-drawn", "no-divider-after-h1",
]

SCEN_IDS = [
    ["renders-per-x-render"], ["missing-schema-ref"], ["writes-canonical-and-deploy"],
    ["renders-per-x-render"], ["path-vars-from-content"], ["renders-per-x-render"],
    ["supports-all-part-kinds"], ["supports-all-part-kinds"], ["malformed-content"],
    ["deploy-per-discriminator"], ["tool-mappings-nested"], ["path-vars-from-content"],
    ["path-vars-per-discriminator"], ["frontmatter-per-discriminator"],
    ["frontmatter-omits-absent"], ["table-bullet-column"], ["bullet-wins-over-join"],
    ["malformed-content"], ["skips-unresolvable-deploy"],
    ["fan-out-multiple-array-path-vars"], ["frontmatter-block-shape"],
    ["frontmatter-per-discriminator"], ["no-render-target"],
    ["fan-out-multiple-array-path-vars"], ["tool-mappings-nested"], ["tool-mappings-nested"],
    ["template-has-no-entity-target"], ["absent-role-is-entity"],
    ["deploy-target-owned-by-other"], ["reports-skipped-targets"],
    ["path-not-found"], ["schema-ref-unresolvable"], ["invalid-transition"],
    ["deterministic-output"], ["deterministic-output"], ["omits-empty-block"],
    ["x-render-hidden-not-drawn"], ["no-divider-after-h1"],
]

NEW_CRITERIA = [
    ("descends-into-nested-object",
     "When 部品が入れ子のオブジェクトを指す宣言を持つとき、システムはその中へ降りて、"
     "宣言された部品の並びをそのオブジェクトの中身に対して描画する shall"
     "（降りられないと、要素の中に持たせた図や原文が成果物へ現れず、"
     "データには在るのに読み手へ届かない状態になる）。"),
    ("nested-object-absent-is-omitted",
     "While 入れ子のオブジェクトを指す宣言の対象が存在しないとき、"
     "システムはその部分を省略し、見出しだけを残さない shall。"),
    ("figure-groups-are-drawn-as-enclosures",
     "When 図の宣言が囲みを持つとき、システムは囲みに属する節点をひとまとまりとして描き、"
     "囲みの名前を添える shall（何が1つの塊かは、図が示す内容そのものであることが多いため）。"),
    ("figure-nodes-accept-plain-names",
     "When 図の節点が名前だけで宣言されているとき、"
     "システムはその名前を識別子と表示名の両方に使う shall。"),
    ("figure-reading-is-rendered-with-the-figure",
     "When 図を描画するとき、システムは図に添えられた意図と読み取りを、図と一緒に描画する shall"
     "（図を描画できない読み手が、そこだけで意味を取れるようにするため）。"),
    ("verbatim-is-rendered-as-source",
     "When 原文の宣言を描画するとき、システムは意図と読み取りを文章として描画し、"
     "原文を宣言された種類のコードブロックとしてそのまま描画する shall（原文を変換しない）。"),
]


def gk(n, g, w, t):
    return f"Scenario: {n}\n  Given {g}\n  When {w}\n  Then {t}"


NEW_SCEN = [
    ("入れ子のオブジェクトの中身が描画される", "正常系",
     "入れ子への到達：要素の中に持たせた図や原文が成果物へ現れるか",
     ["descends-into-nested-object"],
     "要素の中に図の宣言を持つブロック", "描画する", "図の中身が成果物に現れる"),
    ("入れ子の対象が無ければ何も描かれない", "境界値",
     "入れ子への到達：空の見出しを残さないか",
     ["nested-object-absent-is-omitted"],
     "図の宣言を持たない要素", "描画する", "その部分は成果物に現れない"),
    ("囲みはひとまとまりとして描かれる", "正常系",
     "図の意味：何が1つの塊かが図に出るか",
     ["figure-groups-are-drawn-as-enclosures"],
     "5つの節点を1つの囲みに入れた図の宣言", "描画する",
     "5つがひとまとまりとして描かれ、囲みの名前が添えられている"),
    ("節点は名前だけで宣言できる", "境界値",
     "宣言の簡潔さ：同じ文字列を2度書かせないか",
     ["figure-nodes-accept-plain-names"],
     "名前だけで宣言された節点", "描画する", "その名前が表示される"),
    ("図には意図と読み取りが添えられる", "正常系",
     "図の到達性：図を描画できない読み手にも意味が届くか",
     ["figure-reading-is-rendered-with-the-figure"],
     "意図と読み取りを持つ図の宣言", "描画する",
     "図とともに意図と読み取りが文章として現れる"),
    ("原文は変換されずに描画される", "正常系",
     "原文の保存：構造化できないものを変えずに運べるか",
     ["verbatim-is-rendered-as-source"],
     "種類と原文を持つ宣言", "描画する",
     "意図と読み取りが文章として現れ、原文が宣言された種類のコードブロックとして現れる"),
]

print(run("scaffold", "--operation", "clear_field", "--path", P,
          "--fieldPath", "content.operationGuarantees")[:100])
print(run("scaffold", "--operation", "clear_field", "--path", P,
          "--fieldPath", "content.guaranteeScenarios")[:100])
print(run("scaffold", "--operation", "migrate_schema", "--path", P,
          "--schemaRef", "DomainSpecSchema/v10")[:110])

old_c = q("acceptanceCriteria", "items")
assert len(old_c) == len(IDS), (len(old_c), len(IDS))
crit = [{"id": i, "text": t} for i, t in zip(IDS, old_c)]
crit += [{"id": i, "text": t} for i, t in NEW_CRITERIA]

cur = q("acceptanceScenarios", "scenarios")
assert len(cur) == len(SCEN_IDS), (len(cur), len(SCEN_IDS))
scen = []
for s, ids in zip(cur, SCEN_IDS):
    s = dict(s)
    s.pop("covers", None)
    s["satisfies"] = ids
    scen.append(s)
scen += [{"name": n, "category": c, "viewpoint": v, "satisfies": s,
          "gherkin": gk(n, g, w, t)} for n, c, v, s, g, w, t in NEW_SCEN]

print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps({"content.acceptanceCriteria.items": crit,
                                  "content.acceptanceScenarios.scenarios": scen},
                                 ensure_ascii=False))[:170])
print(run("validate", "--path", P)[:220])
print(f"基準 {len(crit)} / シナリオ {len(scen)}")
