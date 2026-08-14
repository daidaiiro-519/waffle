"""引き継ぎ書と知識のずれを埋める。

引き継ぎ書にしか無い一般的な原則を知識へ。
知識にあって引き継ぎ書が扱っていない論点を引き継ぎ書へ。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
K = ".waffle/documents/knowledge/knowledge-cand-one-binding-for-all-contract-levels.json"
H = ".waffle/documents/handoff/handoff-criteria-scenario-link.json"


def q(p, b, e):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", p, "--blockKey", b, "--expression", e],
                       capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


def fill(p, v):
    r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill",
                        "--path", p, "--values", json.dumps(v, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    print((r.stdout or r.stderr).strip()[:160])


# ---- 知識へ：引き継ぎ書にしか無かった5件
ps = q(K, "principles", "items")
anchor = next(i for i, x in enumerate(ps) if x.startswith("受け入れ条件は「主張」で切り"))
ps[anchor + 1:anchor + 1] = [
    "1つの受け入れ条件は1つの主張である。"
    "1項目に主張が2つ入っているものは、条件が1つではなく2つある状態にすぎない。"
    "対応の識別子を振る前に割らないと、1つの識別子が2つの契約を指す状態が固定され、"
    "以後その識別子が何を指すかが読み手ごとに変わる。",

    "既定の多重度は、受け入れ条件と不変条件で違う。"
    "受け入れ条件はトリガを持つため1対1が既定になる。"
    "不変条件は「常に」であり、1つの筋書きが示せるのは反例の起きない一断面にすぎないため、"
    "1対多が既定になる。同じ既定を当てると集約側がほぼ全件逸脱扱いになる。",
]
anchor2 = next(i for i, x in enumerate(ps) if x.startswith("対応を運ぶ識別子が満たすべきことは"))
ps[anchor2 + 1:anchor2 + 1] = [
    "識別子は業務の言葉ではない。どう名付けても業務語彙にはならないため、"
    "それが仕様を指す一次的な手段になると、業務に詳しい人が参加できない語彙が中心に座る。"
    "人が読む成果物と会話では、識別子ではなく条件の文そのものを引用する。",

    "どの条件も指さない筋書きを許さない趣旨は、不要な筋書きの排除ではなく、"
    "条件の書き漏れを発見させることにある。"
    "0件で止まったとき、書き手が取るべき行動は筋書きを消すことではなく条件を書き足すことだと"
    "明示しない限り、この規則は逆向きに働く。",
]
anchor3 = next(i for i, x in enumerate(ps) if x.startswith("検知が「宣言が無ければ黙って対象外にする」"))
ps[anchor3 + 1:anchor3 + 1] = [
    "欠落を欠落として報告することと、報告が読まれる量に収まっていることは、どちらも譲れない。"
    "読まれない量の報告は、報告しないのと同じである。"
    "両立させる唯一の手は、出す場面によって量を変えることである。",

    "筋書きを持てない受け入れ条件が、正当に存在する。"
    "情報の不在を主張する規則がそれで、観測するための操作を作った時点で規則そのものが壊れる。"
    "対応の欠けを数える仕組みは、この種の条件を欠けとして数え続けてはならない。"
    "担保の手段が振る舞いではないことを条件の側が名乗り、数える側がそれを外す。",
]
fill(K, {"content.principles.items": ps})

ap = q(K, "antiPatterns", "items")
ap.append({
    "name": "筋書きで担保できない条件を、欠けとして数え続ける",
    "problem": "直しようのない報告が残り続け、その中に本物の欠けが埋もれる。"
               "報告が読まれなくなり、報告しないのと同じ状態に戻る。",
})
fill(K, {"content.antiPatterns.items": ap})


# ---- 引き継ぎ書へ：知識にあって扱っていなかった2件
ds = q(H, "designViewpoints", "items")
ds.append({
    "advisor": "ddd-advisor",
    "viewpoint": "筋書きを持てない条件を、欠けとして数えない",
    "consideration":
        "情報の不在を主張する規則（保持しない・残らない・追記しかできない・保持期限を超えない）は、"
        "観測するための操作を作った時点で規則そのものが壊れるため、筋書きを持てない。"
        "そのまま数えると欠けとして永久に鳴り続け、本物の欠けがその中に埋もれる。"
        "担保の手段が振る舞いではないことを条件の側が名乗れるようにし、数える側がそれを外す。",
})
fill(H, {"content.designViewpoints.items": ds})

vs = q(H, "implementationViewpoints", "items")
vs.append({
    "advisor": "tech-lead-advisor",
    "viewpoint": "対の充足と、転写の到達を別々に測る",
    "consideration":
        "受け入れ条件に筋書きが付いていることと、その筋書きが実装へ実際に届いていることは別である。"
        "対が揃っていても転写が行われていなければ何も担保されない。"
        "新しい検査は前者だけを測るので、後者を測る既存の照合と組み合わせて読む。"
        "片方だけを見て「担保できている」と読まない。",
})
fill(H, {"content.implementationViewpoints.items": vs})

f = q(H, "reviewStatus", "findings")
f.append({"advisor": "ddd-advisor", "refBlock": "designViewpoints", "refIndex": 11,
          "resolutionStatus": "open",
          "note": "筋書きを持てない条件を、条件の側がどう名乗るかは未決。"
                  "既存の『守り方』の欄を使うか、新しい欄を設けるかを実装時に決める。"})
fill(H, {"content.reviewStatus.findings": f})

for p in (K, H):
    r = subprocess.run(["uv", "run", "waffle", "validate", "--path", p],
                       capture_output=True, text=True, cwd=CWD)
    print((r.stdout or r.stderr).strip()[:140])
