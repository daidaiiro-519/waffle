"""生きている頁どうしの食い違いを探す。

3つを見る。
  1. ある決定への言及に付けた状態が、その決定の実際の状態と合っているか
  2. 落とすと決めた語が、まだどこかに残っていないか
  3. 置き換えられた・取り下げた決定を、生きている頁が指していないか

図の中身は走査しない ── 変更前の姿を描くのが図の仕事なので、落とした語が出てくるのは正しい。図は目で確かめる。
"""
from __future__ import annotations

import re
import sys
import pathlib

ADR = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr")

# 生きている頁（索引が載せているもの）
LIVE = """adr-schema-from-spec adr-tier1-tier2 adr-schema-operations adr-parts-key-and-gloss
adr-vocabulary-by-meaning adr-document-holds adr-value-object-as-a-unit adr-render-and-deploy-split
adr-aggregate-holds-its-inside
adr-figure-vocabulary adr-figure-schema adr-figure-placement adr-convention-is-not-a-layer
adr-no-spelling-in-spec adr-split-rule adr-knowledge-reference-direction adr-reason-as-a-chain
adr-self-contained-html adr-vessel-mock adr-spec-form
tier1-spec raise-walkthrough migration-plan artifact-index""".split()

# 落とすと決めた語 → 落とした理由（残っていたら食い違い）
DROPPED = {
    "読む必要の度合い": "部品として持たないと決着",
    "非推奨": "使ってよいかの値から落とした",
    "終端化": "操作ごと無くなった",
    "書誌": "表紙へ統一",
    "文書の骨": "表紙へ統一",
}
# 決着を記録している行では、その語が出てよい
ALLOW_NEAR = ("決着", "落とした", "落とす", "持たない", "統一", "要らない",
              "無くなる", "~~", "変更前", "いまの")


def load(name: str) -> str:
    p = ADR / f"{name}.html"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def title_of(s: str) -> str:
    m = re.search(r"<h1>(.*?)</h1>", s, re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""


def state_of(s: str) -> str:
    m = re.search(r'<span class="k">状態</span><span class="v">([^<]*)</span>', s)
    return m.group(1) if m else "状態の節が無い"


def main() -> int:
    pages = {n: load(n) for n in LIVE}
    pages = {n: s for n, s in pages.items() if s}

    # 題 → 状態（生きている頁に限らず、docs/adr の全 ADR から引く）
    state_by_title: dict[str, str] = {}
    for p in sorted(ADR.glob("adr-*.html")):
        s = p.read_text(encoding="utf-8")
        t = title_of(s)
        if t:
            state_by_title[t] = state_of(s)

    faults = 0

    print("■ 1. 他の決定への言及に付けた状態")
    for name, s in pages.items():
        for title, real in state_by_title.items():
            for m in re.finditer(re.escape(title) + r"</?[^>]*>?\s*[（(]([^）)]{2,8})[）)]", s):
                said = m.group(1)
                if said in ("承認済み", "未承認", "承認待ち", "取り下げ", "置き換えられた") and said != real:
                    print(f"   × {name}: 「{title[:28]}」を {said} と書いているが、実際は {real}")
                    faults += 1
    print("   （× が無ければ合っている）\n")

    print("■ 2. 落とすと決めた語の残り")
    for name, s in pages.items():
        body = s[s.find('<div class="wrap">'):]
        # 図は変更前の姿も描くので、この走査からは外す（図は目で確かめる）
        body = re.sub(r"<svg.*?</svg>", "", body, flags=re.S)
        for word, why in DROPPED.items():
            for m in re.finditer(re.escape(word), body):
                near = re.sub(r"<[^>]+>", "", body[max(0, m.start() - 400): m.start() + 400])
                if any(a in near for a in ALLOW_NEAR):
                    continue
                print(f"   × {name}: 「{word}」が残っている（{why}）")
                print(f"       …{near[100:220].strip()}…")
                faults += 1
                break
    print("   （× が無ければ合っている）\n")

    print("■ 3. 生きている頁の状態")
    for name in sorted(pages):
        if name.startswith("adr-"):
            print(f"   {state_of(pages[name]):<9} {name}")

    print(f"\n食い違い: {faults} 件")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
