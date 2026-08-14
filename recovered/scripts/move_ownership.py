"""候補1の持ち主を ddd-advisor から Waffle 側へ移し、原則を整える。

業務領域駆動設計の知識体系は、特定の著者が提唱する完成された抽象概念として
保つ。派生をそこへ足すと、その知識を持つ助言役が派生を反証できなくなる。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
ROOT = ".waffle/documents/knowledge"
C1 = "knowledge-cand-operation-contract-closes-invariants"
C2 = "knowledge-cand-binding-differs-by-composition-level"

DERIVED = (
    "この規律は、業務領域駆動設計の原則から導いた派生であって、原典の主張ではない。"
    "原典が保証するのは「集約はルート経由でのみ変更される」ところまでで、"
    "そこから先の——閉包が宣言されていれば全称命題を分配できるという——主張は、この規律のものである。"
)

SEPARATION = (
    "この規律は、業務領域駆動設計の知識体系へは足さない。"
    "あちらは特定の著者が提唱する枯れた設計手法として完成された抽象概念であり、"
    "派生を混ぜると、その知識を背景に持つ助言役がこの派生を反証できなくなる。"
    "外に置いたままにすることで、次に検証させたときも敵対的に読める。"
)


def q(doc_id: str, block: str, expr: str):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", f"{ROOT}/{doc_id}.json", "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


def fill(doc_id: str, values: dict) -> None:
    r = subprocess.run(
        ["uv", "run", "waffle", "scaffold", "--operation", "fill",
         "--path", f"{ROOT}/{doc_id}.json",
         "--values", json.dumps(values, ensure_ascii=False)],
        capture_output=True, text=True, cwd=CWD)
    print(f"[{doc_id}] {(r.stdout or r.stderr).strip()[:200]}")


# ---- 候補1: 持ち主の付け替えと、原則の先頭への派生の明示
p1 = q(C1, "principles", "items")
p1 = [DERIVED, SEPARATION] + [x for x in p1]
fill(C1, {
    "skillRefs": [],
    "agentRefs": ["waffle"],
    "content.principles.items": p1,
    "content.provenance.caveats":
        "この規律は業務領域の分類（中核・一般・補完）に依存せず、すべてに適用されるものとして述べている。"
        "分類は導出の中で二度効いている——サブドメインが契約の段ではないという結論として、"
        "そして段の数が実装方法に依存するという原則として。"
        "領域の複雑さで成否が変わる性質のものではない。\n\n"
        "未検証の留保が4点ある。\n"
        "(1) 段の数が実装方法に依存することは原則として述べているが、"
        "「段が無い」と「段を書き忘れた」を宣言の上でどう区別するかは決まっていない。\n"
        "(2) 実際に当てはめて確かめた業務領域が、いまのところ補完（supporting）と分類されたもの1件しかない。"
        "これは抽象そのものの根拠ではなく、当てはめて得た測定値の偏りである。"
        "抽象は分類を踏まえて導いているため採用を妨げるものではないが、"
        "中核（core）の業務領域で一度確かめる価値はある。\n"
        "(3) コマンド数と不変条件数の掛け算が、中核領域の規模で現実的な大きさに収まるかは未実測。\n"
        "(4) 「情報の不在」を主張する規則の一覧（秘密の非保持・消去の完全性・追記専用性・保持期限）が"
        "この族を尽くしているかは確かめていない。\n\n"
        "なお検証の過程で、「中核領域はピラミッド形のテスト方針をとるため、"
        "不変条件を受け入れ基準へ寄せるとテスト方針の経験則と衝突する」という異議が出たが、これは採らなかった。"
        "この異議は「どこで宣言するか」と「どの層で検証するか」を混ぜている。"
        "コマンドへ分配した基準を単体テストで厚く検証することは矛盾なくできるため、"
        "分配（宣言の話）とピラミッド（検証層の話）は両立する。",
})

# ---- 候補2: 「別に管理する」理由を、持ち主が揃ったことに合わせて書き換える
p2 = q(C2, "principles", "items")
p2 = [x for x in p2 if not x.startswith("この設計前提は、業務領域駆動設計の規律とは別に管理する")]
p2.append(SEPARATION)
fill(C2, {"content.principles.items": p2})

for d in (C1, C2):
    r = subprocess.run(["uv", "run", "waffle", "validate", "--path", f"{ROOT}/{d}.json"],
                       capture_output=True, text=True, cwd=CWD)
    print(f"[validate {d}] {(r.stdout or r.stderr).strip()[:160]}")
    print(f"  skillRefs={q(d, 'title', '@') and ''}", end="")
    r2 = subprocess.run(["uv", "run", "waffle", "query", "--operation", "get_meta",
                         "--path", f"{ROOT}/{d}.json"], capture_output=True, text=True, cwd=CWD)
    print((r2.stdout or "").strip()[:220])
