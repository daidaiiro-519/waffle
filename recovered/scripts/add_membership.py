"""候補2へ、境界づけられたコンテキストが担う「所属の宣言」を足す。

契約の対を持たないことと、何も担わないことは違う。
文脈は所属を担い、それは仕様が正であることの参照構造そのものである。
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
    print((r.stdout or r.stderr).strip()[:220])


ps = q("principles", "items")
# 「文脈に独立した仕組みは要らない」の直後へ所属の話を差し込む
idx = next(i for i, x in enumerate(ps) if x.startswith("境界づけられたコンテキストとして満たすべきこと"))
ps[idx] = (
    "境界づけられたコンテキストとして満たすべきことは、"
    "この3つの対が揃っていれば担保される。文脈が受け入れ条件と振る舞いの対を独自に持つ必要はない。"
)
ps[idx + 1:idx + 1] = [
    "ただし、契約の対を持たないことと、何も担わないことは違う。"
    "境界づけられたコンテキストは所属を担う——この文脈に何が属するかという参照構造そのものである。",

    "所属は契約とは別種の宣言であり、別に照合される。"
    "宣言されているのに実在しない／実在するのに宣言されていない、の両方向を見る。"
    "片方向だけでは、宣言から漏れた要素が誰にも気づかれずに増える。",

    "仕様が唯一の正であるなら、実装側も同じ参照構造で照合できることが望ましい。"
    "ただし鏡にできるのは実装の成果物を持つ要素だけで、"
    "業務領域の分類や不変条件のように対応物を持たないものは、仕様側だけで照合する。",
]
fill({"content.principles.items": ps})

ap = q("antiPatterns", "items")
ap.append({
    "name": "所属の照合を片方向だけにする",
    "problem": "宣言されたものが実在するかは見えるが、実在するのに宣言されていないものが見えず、"
               "どの仕様も名指ししていない実装や文書が誰にも気づかれずに増える。",
})
fill({"content.antiPatterns.items": ap})

cs = q("classifications", "items")
cs.append({
    "name": "所属の宣言",
    "description": "受け入れ条件と振る舞いの対ではなく、その文脈に何が属するかを宣言するもの。両方向で照合する。",
})
fill({"content.classifications.items": cs})

cv = q("provenance", "caveats")
fill({"content.provenance.caveats": cv +
      "\n(4) 所属の宣言について、仕様側の照合は動いているが（宣言とディスクの両方向・4観点）、"
      "欠けが3つある。所属の一覧の種別に業務サービスが無い。"
      "集約だけディスクから宣言への向きが見られていない。"
      "実装側は要素ごとには照合されているが、"
      "「この文脈の実装根の下に在るのはこの集合で全部」という集合としての照合になっていない。"})

r = subprocess.run(["uv", "run", "waffle", "validate", "--path", f"{ROOT}/{C2}.json"],
                   capture_output=True, text=True, cwd=CWD)
print((r.stdout or r.stderr).strip()[:160])
