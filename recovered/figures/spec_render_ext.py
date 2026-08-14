"""描画部品の拡張を、uc-render-document の仕様へ書く。

足すのは3つ:
  1. 入れ子のオブジェクトへ降りる（ノードの中の図・原文へ届かせる）
  2. 囲み（図の中で節点をまとめる。何が1つの塊かを示す）
  3. 節点を文字列で書ける（宣言を冗長にしない）
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


def gk(n, g, w, t):
    return f"Scenario: {n}\n  Given {g}\n  When {w}\n  Then {t}"


NEW_CRITERIA = [
    ("descends-into-nested-object",
     "When 部品が入れ子のオブジェクトを指す宣言（object）を持つとき、システムはその中へ降りて、"
     "宣言された部品の並びをそのオブジェクトの中身に対して描画する shall"
     "（降りられないと、要素の中に持たせた図や原文が成果物へ現れず、"
     "データには在るのに読み手に届かない状態になる）。"),
    ("nested-object-absent-is-omitted",
     "While 入れ子のオブジェクトを指す宣言の対象が存在しないとき、システムはその部分を省略し、"
     "見出しだけを残さない shall。"),
    ("figure-groups-are-drawn-as-enclosures",
     "When 図の宣言が囲みを持つとき、システムは囲みに属する節点をひとまとまりとして描き、"
     "囲みの名前を添える shall（何が1つの塊かは、図が示す内容そのものであることが多いため）。"),
    ("figure-nodes-accept-plain-names",
     "When 図の節点が名前だけで宣言されているとき、システムはその名前を識別子と表示名の両方に使う shall"
     "（識別子と表示名が同じでよい場合に、同じ文字列を2度書かせない）。"),
    ("figure-reading-is-rendered-with-the-figure",
     "When 図を描画するとき、システムは図に添えられた意図と読み取りを、図と一緒に描画する shall"
     "（図を描画できない読み手が、そこだけで意味を取れるようにするため）。"),
    ("verbatim-is-rendered-as-source",
     "When 原文の宣言を描画するとき、システムは意図と読み取りを文章として描画し、"
     "原文を宣言された種類のコードブロックとしてそのまま描画する shall（原文を変換しない）。"),
]

NEW_SCEN = [
    ("入れ子のオブジェクトの中身が描画される", "正常系",
     "入れ子への到達：要素の中に持たせた図や原文が成果物へ現れるか",
     ["descends-into-nested-object"],
     "要素の中に図の宣言を持つブロック", "描画する",
     "図の中身が成果物に現れる"),
    ("入れ子の対象が無ければ見出しごと省略される", "境界値",
     "入れ子への到達：空の見出しを残さないか",
     ["nested-object-absent-is-omitted"],
     "図の宣言を持たない要素", "描画する", "その部分は成果物に現れない"),
    ("囲みは、ひとまとまりとして描かれる", "正常系",
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

crit = q("acceptanceCriteria", "items")
is_v9 = bool(crit) and isinstance(crit[0], dict)
if not is_v9:
    print("この仕様はまだ v8（基準が文字列）。先に移設が要る。中止。")
    raise SystemExit

crit.extend({"id": i, "text": t} for i, t in NEW_CRITERIA)
scen = q("acceptanceScenarios", "scenarios")
scen.extend({"name": n, "category": c, "viewpoint": v, "satisfies": s,
             "gherkin": gk(n, g, w, t)} for n, c, v, s, g, w, t in NEW_SCEN)

print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps({"content.acceptanceCriteria.items": crit,
                                  "content.acceptanceScenarios.scenarios": scen},
                                 ensure_ascii=False))[:180])
print(run("validate", "--path", P)[:220])
