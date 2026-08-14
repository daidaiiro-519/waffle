"""所属の宣言を、あるべき形（一覧・所在の規則・走査の領域）として書き直す。

既存の欄の形に合わせず、何が宣言されていれば所属を機械が判定できるか
という側から導く。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
ROOT = ".waffle/documents/knowledge"
C2 = "knowledge-cand-one-binding-for-all-contract-levels"


def q(block: str, expr: str):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", f"{ROOT}/{C2}.json", "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


def fill(values: dict) -> None:
    r = subprocess.run(
        ["uv", "run", "waffle", "scaffold", "--operation", "fill",
         "--path", f"{ROOT}/{C2}.json",
         "--values", json.dumps(values, ensure_ascii=False)],
        capture_output=True, text=True, cwd=CWD)
    print((r.stdout or r.stderr).strip()[:200])


ps = q("principles", "items")
# 所属についての原則を、あるべき形として置き換える
keep = [x for x in ps if not x.startswith("所属は契約とは別種の宣言であり、別に照合される")]
idx = next(i for i, x in enumerate(keep) if x.startswith("ただし、契約の対を持たないことと"))
keep[idx + 1:idx + 1] = [
    "所属を機械が判定できるようにするには、3つの宣言が要る——"
    "その文脈に属する要素の一覧（意図）、各種別が仕様側と実装側のどこにどういう名前で在るかという所在の規則、"
    "そしてその規則が及ぶ走査の領域。",

    "この3つが揃うと、所属は2方向で照合できる。"
    "一覧から実物へ辿る向きは欠けを見つけ、領域から一覧へ戻る向きは余りを見つける。"
    "見つかる失敗が違うので、片方だけでは足りない。",

    "一覧が無ければ欠けの向きは定義できず、走査の領域が無ければ余りの向きは定義できない。"
    "どちらか一方だけを持つ設計は、必ずもう一方の失敗を見逃す。",

    "照合の起点は一覧でなければならない。"
    "領域の走査を起点にすると、一覧に載っていないものも普通に処理され、"
    "一覧が唯一の正である意味が消える。走査は余りを出すためだけに使う。",

    "所属の照合に使える手がかりは、要素の種類によって深さが違う。"
    "ファイルの存在までしか言えないもの、クラスの名前まで言えるもの、"
    "クラスの中身（属性の一致）まで言えるもの、"
    "そして説明文の一字一句まで言えるもの（振る舞いのシナリオ）がある。"
    "深く言える要素ほど、所属の宣言が実装の実態から離れにくい。",

    "実装側に対応物を持たない要素（業務領域の分類など）は、仕様側だけで照合する。"
    "鏡にできるのは成果物を持つ要素だけで、これは欠陥ではなく、"
    "その要素が解決空間に属していないというだけのことである。",
]
fill({"content.principles.items": keep})

ap = q("antiPatterns", "items")
ap = [x for x in ap if x["name"] != "所属の照合を片方向だけにする"]
ap += [
    {"name": "所属の照合を片方向だけにする",
     "problem": "一覧だけを持つと領域に紛れ込んだ余りが見えず、領域だけを持つと宣言されているのに存在しない欠けが見えない。"},
    {"name": "所属の照合を、領域の走査から始める",
     "problem": "一覧に載っていない要素も走査に拾われて普通に処理されるため、"
                "一覧が唯一の正でなくなり、実際にディスクの実在が正として振る舞いはじめる。"},
]
fill({"content.antiPatterns.items": ap})

cv = q("provenance", "caveats")
cv = cv.split("\n(4) 所属の宣言について")[0]
fill({"content.provenance.caveats": cv +
      "\n(4) 所属の宣言について、手がかりも両方向の照合も大半は既に存在し、"
      "欠けと余りを実際に検出している。ただし照合の起点が一覧ではなく領域の走査になっており、"
      "仕様文書がディスクに在れば一覧に載っていなくても通る。"
      "所属の一覧が唯一の正として機能していない。"
      "あわせて、一覧の種別に業務サービスが無く、集約は仕様側の余りの向きが見られていない。"})

r = subprocess.run(["uv", "run", "waffle", "validate", "--path", f"{ROOT}/{C2}.json"],
                   capture_output=True, text=True, cwd=CWD)
print((r.stdout or r.stderr).strip()[:160])
