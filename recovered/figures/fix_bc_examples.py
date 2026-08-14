"""bounded-context の実例を、書籍のものから架空の題材へ置き換える。

構造（何を示す例か・図の関係）は保ち、題材だけを差し替える。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = ".waffle/documents/knowledge/bounded-context." + "json"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


items = json.loads(run("query", "--operation", "query_path", "--path", P,
                       "--blockKey", "nodes", "--expression", "items"))["value"]


def walk(nodes):
    for nd in nodes:
        yield nd
        yield from walk(nd.get("children", []))


by_name = {nd["name"]: nd for nd in walk(items)}

# 1. 見込み客（書籍のオンライン広告代理店の例）→ 注文（受注と倉庫）
by_name["なぜ必要か"]["figure"] = {
    "intent": "同じ言葉が文脈ごとに別の意味を持つことと、文脈を区切ればそれが解けることを示す",
    "reading": "「注文」という同じ言葉が、受注の文脈では顧客が出した申込みを指し、"
               "倉庫の文脈では棚から品を集める作業の単位を指す。"
               "文脈を分けることで、それぞれの内側で言葉の意味が一つに定まる。",
    "direction": "LR",
    "groups": [
        {"label": "受注の文脈", "nodes": ["注文（顧客の申込み）", "顧客"]},
        {"label": "倉庫の文脈", "nodes": ["注文（集品の作業単位）", "棚"]},
    ],
    "nodes": [],
    "edges": [{"from": "注文（顧客の申込み）", "to": "顧客"},
              {"from": "注文（集品の作業単位）", "to": "棚"}],
}

# 2. 地図のたとえ（書籍）→ 建物の図面
by_name["地図のたとえ"]["summary"] = (
    "建物の意匠図・構造図・設備図は、それぞれ異なる目的に特化したモデルであり、"
    "設備図を見ても柱がどこまで細くできるかは判断できない。"
    "同じ言葉も同様で、ある文脈で使われる言葉が別の文脈ではまったく役に立たないことがある。")

# 3. トマトの表（書籍）→ 「当日」の意味
by_name["言葉の意味論"]["verbatim"] = {
    "intent": "同じ言葉が文脈ごとに別の意味を持つことを、身近な例で示す",
    "reading": "「当日」は、受注の文脈では注文が入った日、倉庫の文脈では集品を行う日、"
               "会計の文脈では売上を計上する日、利用者の文脈では荷物が届く日を指す。"
               "どれも誤りではなく、それぞれの文脈の内側で正しい。言葉の意味は文脈が決める。",
    "lang": "markdown",
    "source": ("| 文脈 | 「当日」の意味 |\n"
               "|---|---|\n"
               "| 受注の文脈 | 注文が入った日 |\n"
               "| 倉庫の文脈 | 棚から品を集める作業を行う日 |\n"
               "| 会計の文脈 | 売上を計上する日 |\n"
               "| 利用者の文脈 | 荷物が届く日 |"),
}

# 4. 科学の理論（書籍）→ 見積りのモデル
sci = by_name.pop("科学の理論も文脈を持つ", None)
if sci is not None:
    sci["name"] = "両立しないモデルが、それぞれの文脈で役に立つ"
    sci["summary"] = (
        "同じ工事に対して、概算の見積りと詳細の見積りは異なる金額を出す。"
        "概算は商談の初期に、詳細は着工前に役に立つ。"
        "数字が食い違うからどちらかが誤りだ、とはならない。"
        "知識の本当の評価基準は真理かどうかではなく、役に立つかどうかである。")
    sci["sourceRef"] = "3.5.2"

# 5. 冷蔵庫の話（書籍）→ サーバーラックの搬入
fridge = by_name.get("大きなモデルを1つ作らない")
if fridge is not None:
    fridge["summary"] = (
        "新しいサーバーラックが機械室の扉を通るかを確かめるのに、"
        "建物の3次元モデルを作るのは明らかに過剰である。"
        "床に引いた幅の印と、扉の高さを測ったメモという2つの小さなモデルで足りる。"
        "個別の課題を解決するシンプルなモデルを組み合わせて目的を達成できるなら、"
        "「何にでも手を出して、どれもちゃんとできていない」単一の入り組んだモデルは要らない。")

# 6. 図3-8 の文脈名（書籍）→ 中立な文脈名
by_name["所有権の境界"]["figure"] = {
    "intent": "チームと文脈の担当関係が単方向であることを示す",
    "reading": "1つのチームが複数の文脈を担当することはできるが、"
               "1つの文脈を複数のチームが担当することはできない。関係は単方向である。",
    "direction": "TD",
    "groups": [],
    "nodes": ["チーム1", "チーム2", "受注の文脈", "在庫の文脈", "請求の文脈"],
    "edges": [{"from": "チーム1", "to": "受注の文脈", "label": "担当"},
              {"from": "チーム1", "to": "在庫の文脈", "label": "担当"},
              {"from": "チーム2", "to": "請求の文脈", "label": "担当"}],
}

print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps({"content.nodes.items": items}, ensure_ascii=False))[:150])
print(run("validate", "--path", P)[:180])
print(run("render", "--path", P)[:110])
