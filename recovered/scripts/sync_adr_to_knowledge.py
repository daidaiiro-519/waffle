"""ADRで導いたことを、知識と引き継ぎ書へ反映する。

資料にしか無い状態だと次のセッションへ渡らず、実装側にも理由が伝わらない。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
K = ".waffle/documents/knowledge/knowledge-cand-one-binding-for-all-contract-levels.json"
H = ".waffle/documents/handoff/handoff-criteria-scenario-link.json"


def q(p: str, b: str, e: str):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", p, "--blockKey", b, "--expression", e],
                       capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


def fill(p: str, v: dict) -> None:
    r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill",
                        "--path", p, "--values", json.dumps(v, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    print((r.stdout or r.stderr).strip()[:170])


# ---- 知識へ、対応の形とその理由を足す
ps = q(K, "principles", "items")
anchor = next(i for i, x in enumerate(ps)
              if x.startswith("欠けを機械が数えるには"))
ps[anchor + 1:anchor + 1] = [
    "受け入れ条件は「主張」で切り、振る舞いのシナリオは「流れ」で切る。"
    "同じものを違う軸で切った2つの分割の間の対応は、一般に多対多になる。",

    "主張は複数の状況にまたがり、流れは1つの状況しか通らない。"
    "したがって1つの主張を確かめる流れは複数ありうる——境界の内と外、別の入口、別の前提。",

    "1つの流れを通すと結果と状態の変化が同時に生じ、そこで観測できることは1つとは限らない。"
    "したがって1つの流れが複数の主張を同時に満たしうる。",

    "1つのシナリオが1つの主張だけを確かめるよう強制しない。"
    "同じ流れに対して Then を分けて別のシナリオにすると Given と When が複製され、"
    "その複製には検知が付かない——文言の照合はシナリオ単位なので、片方だけを直しても何も落ちない。"
    "宣言の複製に検知が無い状態を、構造的に生み出す設計は採らない。",

    "「1つの流れですべて述べると、どの主張が破れたか特定しにくい」は理由にならない。"
    "特定は実行時に得られる。シナリオは実装へ転写され、Then の行ごとに確かめられるため、"
    "落ちればどの行かは結果に現れる。仕様側の粒度で特定する必要はない。",

    "多対多を表せる形は参照である。"
    "入れ子は、1つの流れが複数の主張を満たす側を表せない——その流れをどれか1つの主張の下にしか置けず、"
    "残りは「シナリオを持たない主張」に見えてしまう。"
    "参照が壊れうることは検査で判定できるが、入れ子が表せないことは検査では埋められない。",

    "契約の対は、それを担う要素が持つ。"
    "文書そのものが担い手なら条件も筋書きも文書レベルに来る（業務ユースケース・集約）。"
    "文書の中に担い手が複数いるなら、条件も筋書きも要素の中に持つ（業務サービス）。",

    "対応を運ぶ識別子が満たすべきことは2つだけである——"
    "並べ替えで指す先が変わらないこと、文言の修正で壊れないこと。"
    "連番は前者に、本文から導く名前は後者に反する。"
    "どちらも満たすのは、位置にも本文にも依存しない手書きの符号である。",

    "対応を宣言しても、その対応が正しいことは担保されない。"
    "指すことは主張であって、検証ではない。"
    "担保できるのは「誰も担当していない条件が無いこと」までで、"
    "「担当していると言っているが実は確かめていない」は範囲外である。"
    "したがって位置づけは品質のゲートではなく、読むべき箇所の当たり付けとする。",
]
fill(K, {"content.principles.items": ps})

ap = q(K, "antiPatterns", "items")
ap.append({
    "name": "1つのシナリオが1つの主張だけを確かめるよう強制する",
    "problem": "同じ流れに対する Given と When が複製され、"
               "その複製には検知が付かないため、片方だけが古くなっても誰も気づかない。",
})
ap.append({
    "name": "対応が緑であることを、条件が守られている証拠として読む",
    "problem": "指しただけで確かめたことにはならないため、"
               "意味的に無関係な対応が書かれていても検査は通り、"
               "人が読むべき箇所を機械が確かめてくれたものと誤解される。",
})
fill(K, {"content.antiPatterns.items": ap})


# ---- 引き継ぎ書へ、縦を強制しない理由と、入れ子を採らない理由を足す
ds = q(H, "designViewpoints", "items")
ds.insert(1, {
    "advisor": "ddd-advisor",
    "viewpoint": "1つのシナリオを1つの主張に絞らない",
    "consideration":
        "同じ流れに対して Then を分けて別のシナリオにすると、Given と When が複製される。"
        "文言の照合はシナリオ単位なので、複製された前提には検知が付かない。"
        "「どの主張が破れたか特定しにくい」は理由にならず、特定は実行時に得られる。"
        "実装で条件を1対1へ揃え直したくなっても、この理由に立ち返ること。",
})
ds.insert(2, {
    "advisor": "tech-lead-advisor",
    "viewpoint": "参照を採り、入れ子を採らない",
    "consideration":
        "入れ子は、1つの流れが複数の主張を満たす側を表せない。"
        "その流れをどれか1つの主張の下にしか置けず、残りは筋書きを持たない主張に見える。"
        "参照が壊れうることは検査で判定できるが、入れ子が表せないことは検査では埋められない。",
})
fill(H, {"content.designViewpoints.items": ds})

for p in (K, H):
    r = subprocess.run(["uv", "run", "waffle", "validate", "--path", p],
                       capture_output=True, text=True, cwd=CWD)
    print((r.stdout or r.stderr).strip()[:150])
