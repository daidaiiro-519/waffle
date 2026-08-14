"""保証を1件ずつ、帰る先の候補ごとに仕分けて表示する（判定は人が読む）。"""
from __future__ import annotations

import json
import re

SRC = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
       "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad/guarantees_dump." + "json")

with open(SRC, encoding="utf-8") as f:
    d = json.load(f)

ALL_INV = [(a, r) for a, rs in d["aggregates"].items() for r in rs]
ERRLIKE = re.compile(r"エラーを返す shall|[A-Z]{3,}(_[A-Z]+)+")


def overlap(text: str) -> list[str]:
    """語の重なりで、同じ主張を述べている不変条件の候補を挙げる。"""
    words = set(re.findall(r"[ぁ-んァ-ヶ一-龠]{3,}", text))
    hits = []
    for agg, rule in ALL_INV:
        w = set(re.findall(r"[ぁ-んァ-ヶ一-龠]{3,}", rule))
        common = words & w
        if len(common) >= 2:
            hits.append((len(common), agg, rule))
    hits.sort(reverse=True)
    return [f"{a}: {r[:70]}" for _, a, r in hits[:2]]


for bc in ("bc-artifact-share", "bc-waffle"):
    ucs = {k: v for k, v in d["usecases"].items() if v["bc"] == bc}
    print(f"\n{'=' * 70}\n{bc}  （業務ユースケース {len(ucs)} 件）\n{'=' * 70}")
    for name, v in ucs.items():
        for gi, g in enumerate(v["guarantees"]):
            t = g if isinstance(g, str) else g.get("text", "")
            gid = "" if isinstance(g, str) else f" [{g.get('id')}]"
            print(f"\n■ {name}{gid}")
            print(f"  {t[:120]}")
            if ERRLIKE.search(t):
                codes = [c for c in v["errorCodes"] if c in t]
                print(f"  → 個別のエラー契約。errors登録: {codes or '無し（要追加）'}")
            else:
                hits = overlap(t)
                if hits:
                    print("  → 不変条件の候補:")
                    for h in hits:
                        print(f"      {h}")
                else:
                    print("  → 対応する不変条件が見つからない（要判定）")
