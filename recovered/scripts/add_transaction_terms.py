"""トランザクションと、その境界を語彙へ入れる。

概念は書き起こし版に「1集約インスタンス = 1トランザクション単位」としてあったが、
bc-waffle の語彙へ持ち込まれておらず、同じことを3箇所でその場の言葉で書いていた。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
B = ".waffle/documents/specs/bc-waffle/bc-waffle." + "json"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


items = json.loads(run("query", "--operation", "query_path", "--path", B,
                       "--blockKey", "ubiquitousLanguage", "--expression", "items"))["value"]
have = {x["term"] for x in items}

ADD = [
    ("トランザクション",
     "全部成るか全部成らないかで扱う、ひと塊の変更。実装が何か"
     "（保存の呼び出し・ファイルの書き込み・メモリ上の値）は問わない。"
     "1つの集約は1つのトランザクションで変更される。"),
    ("トランザクション境界",
     "トランザクションとして扱う範囲。どこからどこまでが一度に成るか。"
     "不変条件は、依存する変更がこの境界の内側に収まっているときにだけ守られる。"),
]

new = [t for t, _ in ADD if t not in have]
if not new:
    print("既にあり")
else:
    items.extend({"term": t, "definition": d} for t, d in ADD if t not in have)
    print(run("scaffold", "--operation", "fill", "--path", B,
              "--values", json.dumps({"content.ubiquitousLanguage.items": items},
                                     ensure_ascii=False))[:150])
    print(run("validate", "--path", B)[:150])
    run("render", "--path", B)
    print(f"語彙 {len(items)} 語（{new} を追加）")
