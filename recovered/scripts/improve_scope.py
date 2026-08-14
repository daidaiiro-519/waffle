"""evidence-based-scope に、衝突の裁き方と種別の見分けを足す。

first-class-concept-vs-premature-generalization の候補のうち、
既存に無い2点だけを移す。既にある内容は重ねて書かない。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = ".waffle/documents/knowledge/architecture-evidence-based-scope." + "json"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(block, expr="@"):
    return json.loads(run("query", "--operation", "query_path", "--path", P,
                          "--blockKey", block, "--expression", expr))["value"]


NEW_PRINCIPLES = [
    "この規律が『振る舞いが異なるなら別概念として名前を持たせよ』という原則と衝突して見えるときは、"
    "提案されている変更が『既に観測されている違いに名前と居場所を与える』側なのか、"
    "『まだ観測されていない変種を吸収する枠組みを作る』側なのかを判別する。"
    "多くの場合、いずれか一方の射程にしか入らず、衝突は消える。",
    "名前を与える変更（列挙値や属性を1つ増やす）は、この規律の射程外である。"
    "この規律が対象とするのは、形の分からない変種を先回りして吸収する汎用機構"
    "（ポリシーエンジン・DSL・設定駆動の分岐）である。",
    "概念を種別（discriminator）の値として表すと、その種別に対応する内容の形を定義する義務が生じる。"
    "内容の形が既存の値と同一になる場合、それは種別ではなく直交する軸であるという徴候であり、"
    "属性として表すほうが、以後2つを同期し続ける義務を負わずに済む。",
]

NEW_CLASSIFICATION = {
    "name": "名前を与える変更（対象外）",
    "description": "既に観測されている振る舞いの違いに、正式な識別子と構造上の居場所を与える。"
                   "実例1件でも成立し、この規律の射程に入らない。"
                   "『まだ形の分からない変種を吸収する枠組みを作る』変更とは別物として扱う",
}

NEW_ANTIPATTERNS = [
    {"name": "他の原則と衝突して見えるとき、射程を確かめずにこの規律を優先する",
     "problem": "『別概念として名前を持たせよ』と『実例1件から一般化するな』は、同じ変更に対して"
                "逆の結論を出すことがある。射程を判別せずにこの規律を当てると、"
                "既に観測されている違いを構造へ刻む機会を逃す。"
                "判別の問いは『名前を与える変更か、枠組みを作る変更か』である"},
    {"name": "直交する軸を種別の値として表す",
     "problem": "種別ごとに内容の形を定義する必要があるため、既存の値と同一の形をもう1つ定義することになり、"
                "以後その2つを同期し続ける義務が生まれる。内容の形が同一になるなら、"
                "それは種別ではなく属性である"},
]

principles = q("principles", "items")
principles.extend(NEW_PRINCIPLES)

classifications = q("classifications", "items")
classifications.append(NEW_CLASSIFICATION)

anti = q("antiPatterns", "items")
anti.extend(NEW_ANTIPATTERNS)

vals = {
    "content.principles.items": principles,
    "content.classifications.items": classifications,
    "content.antiPatterns.items": anti,
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:180])
print(run("validate", "--path", P)[:200])
print(run("render", "--path", P)[:120])
print(f"原則 {len(principles)} / 分類 {len(classifications)} / アンチパターン {len(anti)}")
