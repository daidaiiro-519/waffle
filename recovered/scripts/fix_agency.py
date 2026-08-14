"""作業の主語を正す。

人が介入するのは意思決定だけで、それ以外は私が行う。
「人が読んで割る」「人が判断する」と書いていた箇所を直す。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
H = ".waffle/documents/handoff/handoff-criteria-scenario-link.json"


def q(b, e):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", H, "--blockKey", b, "--expression", e],
                       capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


def fill(v):
    r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill",
                        "--path", H, "--values", json.dumps(v, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    print((r.stdout or r.stderr).strip()[:150])


# ---- 設計観点：識別子の語彙の件を落とし、割る作業の主語を正す
ds = [x for x in q("designViewpoints", "items")
      if not x["viewpoint"].startswith("識別子は業務の言葉ではない")]
for x in ds:
    if x["viewpoint"].startswith("1つの条件は1つの主張である"):
        x["consideration"] = (
            "1つの受け入れ条件に主張が2つ入っているとき（「目印を控え、かつ投稿者に尋ねない」等）、"
            "それは条件が2つある状態なので、2つに分ける。"
            "分けずに識別子を振ると、1つの識別子が2つの契約を指す状態が固定され、"
            "以後その識別子が何を指すかが読み手ごとに変わる。"
            "分ける作業は移行のときに行い、機械が主張の数を確かめられるかは未決のまま置く。")
fill({"content.designViewpoints.items": ds})

# ---- 制約：移行の作業主体を正す
cs = q("constraints", "items")
for i, x in enumerate(cs):
    if x.startswith("既存53文書の移行は実装ではなく仕様の修正作業である"):
        cs[i] = (
            "既存53文書の移行は実装ではなく仕様の修正作業である。"
            "識別子を振り、主張が2つ入っている条件を分け、"
            "どの筋書きがどの条件を満たすかの対応を書くまでを移行に含める。"
            "廃止する欄に残る約88%の記入が、対応を書くときの下書きになる。"
            "人の判断を仰ぐのは、分けるかどうか・対応をどう取るかが決定になる場面に限る。")
fill({"content.constraints.items": cs})

# ---- 未解決：割る手順の記述を、主語つきに直す
f = q("reviewStatus", "findings")
for x in f:
    n = x.get("note") or ""
    if "候補出しだけを機械化しても手数が減らない" in n:
        x["note"] = (
            "主張が2つ入っている条件を分ける専用の検知は作らない。"
            "受け入れ条件は EARS 形式のものとそうでないものが混在しており、"
            "文末表現の数え上げは全件には効かないため。"
            "移行のとき条件を1件ずつ読んで分ける。移行は文書単位で進めるので追加の走査は生じない。"
            "分けるかどうかが決定になる場面だけ、人へ確認する。")
fill({"content.reviewStatus.findings": f})
