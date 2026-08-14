"""候補1の留保と関連概念を、適用範囲が全分類に及ぶ形へ直す。

元の書き方は、仮説そのものが補完（supporting）領域に限られるように読めていた。
実際には主張は構造についてのもので、分類に依存しない。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
PATH = ".waffle/documents/knowledge/knowledge-cand-operation-contract-closes-invariants.json"

values = {
    "content.provenance.caveats":
        "この規律は業務領域の分類（中核・一般・補完）に依存せず、すべてに適用されるものとして述べている。"
        "主張の芯は「状態を変える経路が閉じていれば全称命題を有限のコマンド集合へ分配できる」という構造についてのもので、"
        "領域の複雑さで成否が変わる性質のものではない。"
        "分類によって変わるのはコマンド数と不変条件数の掛け算というコストだけで、それは原則の側に書いてある。\n\n"
        "未検証の留保が3点ある。\n"
        "(1) 実際に当てはめて確かめた業務領域が、いまのところ補完（supporting）と分類されたもの1件しかない。"
        "これは適用範囲の限界ではなく、実例の偏りである。中核（core）の業務領域で一度確かめる必要がある。\n"
        "(2) コマンド数と不変条件数の掛け算が、中核領域の規模で現実的な大きさに収まるかは未実測。"
        "収まらない場合、規律が誤りなのか集約が大きすぎるのかを見分ける手段が要る。\n"
        "(3) 「情報の不在」を主張する規則の一覧（秘密の非保持・消去の完全性・追記専用性・保持期限）が"
        "この族を尽くしているかは確かめていない。\n\n"
        "なお検証の過程で、「中核領域はピラミッド形のテスト方針をとるため、"
        "不変条件を受け入れ基準へ寄せるとテスト方針の経験則と衝突する」という異議が出たが、これは採らなかった。"
        "この異議は「どこで宣言するか」と「どの層で検証するか」を混ぜている。"
        "コマンドへ分配した基準を単体テストで厚く検証することは矛盾なくできるため、"
        "分配（宣言の話）とピラミッド（検証層の話）は両立する。"
        "異議が実際に反対しているのは「だからすべてを受け入れテストで測れ」という、この規律が述べていない主張である。",
}

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill",
     "--path", PATH, "--values", json.dumps(values, ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout.strip()[:400] or r.stderr.strip()[:400])

# 関連概念のうち、design-heuristics の注記が「衝突相手」のままなので直す
q = subprocess.run(
    ["uv", "run", "waffle", "query", "--operation", "query_path", "--path", PATH,
     "--blockKey", "relatedConcepts", "--expression", "items"],
    capture_output=True, text=True, cwd=CWD)
items = json.loads(q.stdout)["value"]
for it in items:
    if it["conceptId"] == "design-heuristics":
        it["note"] = ("業務領域の分類から実装方法・テスト方針が連鎖する経験則。"
                      "この規律は宣言の置き場所を定めるもので、検証層の選択には踏み込まないため、"
                      "分類ごとのテスト方針とは両立する。")
    if it["conceptId"] == "subdomain":
        it["note"] = ("サブドメインが振る舞いの単位でない根拠を与える。"
                      "この規律自体は分類に依存せず、中核・一般・補完のすべてに適用される。")

r2 = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill", "--path", PATH,
     "--values", json.dumps({"content.relatedConcepts.items": items}, ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r2.stdout.strip()[:300] or r2.stderr.strip()[:300])
