"""再定義の作業における、方針と実測の関係を知識として記録する。

3度繰り返した誤りなので、次のセッションへ引き継げる形にする。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
ROOT = ".waffle/documents/knowledge"
DOC = "knowledge-cand-policy-is-ssot-measurement-is-judged"


def run(*a: str) -> str:
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


print(run("scaffold", "--operation", "create",
          "--schemaRef", "KnowledgeSchema", "--documentId", DOC)[:90])

values = {
    "status": "DRAFT",
    "knowledgeKind": "process",
    "agentRefs": ["waffle"],
    "tags": ["topic:redefinition", "topic:evidence"],
    "content.title.title":
        "再定義では方針が正で、実測は判定される側であること："
        "knowledge-cand-policy-is-ssot-measurement-is-judged",
    "content.description.text":
        "既存の仕組みを作り直す作業において、新しく定めた方針が唯一の正であり、"
        "既存の実測はその方針に照らして判定される対象であるという関係。"
        "実測を当てること自体は有用で、避けるべきなのは実測を根拠に方針を決めることである。",
    "content.description.questions": [
        "作り直しの設計判断で、既存の実測をどこまで根拠にしてよいか",
        "実測が方針から大きく外れているとき、方針を緩めるべきか",
        "自分の主張が既存に引っ張られているかを、どう見分けるか",
        "既存を参照してよいのは、どういう目的のときか",
    ],
    "content.principles.items": [
        "既存の仕組みを作り直す作業では、新しく定めた方針が唯一の正であり、"
        "既存の実測はその方針に照らして判定される対象である。",

        "実測を当てること自体は有用である。"
        "方針からの逸脱を見つけ、移行で直すべき対象を特定できる。"
        "敵対的に当てるほど価値が出る。",

        "避けるべきなのは、実測を根拠にして方針を決める・裁くことである。"
        "既存は、いま置き換えようとしている方式の下で作られたものなので、"
        "目標の形がどうあるべきかについての証拠にならない。",

        "既存を根拠にしてよい範囲は3つに限られる——"
        "実装をどこに置くか、実現できるかどうか、そして移行の入力として。"
        "宣言や概念の形そのものを決めるのには使えない。",

        "見分け方は単純である。"
        "その主張が「既存がこうだから」で終わるなら越境している。"
        "「方針がこうだから、既存のここが外れている」なら向きが正しい。",

        "逸脱が多いことは、方針が誤っている証拠ではない。"
        "旧方式の下で書かれた以上、逸脱があるのは当然であり、"
        "逸脱の量を理由に方針を緩めると、作り直す意味が消える。",

        "この誤りは、実測が手元にあるときほど起きやすい。"
        "数えた結果は根拠として強く見えるため、"
        "何の問いに答えるために数えたのかを見失うと、そのまま方針の根拠に転用してしまう。",
    ],
    "content.classifications.items": [
        {"name": "実装の置き場所",
         "description": "どの層のどこに置くか。既存の配置を参照してよい。"},
        {"name": "実現可能性",
         "description": "その形が既存の仕組みで表現できるか。既存を参照して確かめてよい。"},
        {"name": "移行の入力",
         "description": "何件あるか、どこから翻訳できるか。既存の実測がそのまま材料になる。"},
        {"name": "宣言や概念の形",
         "description": "何をどう宣言するか。既存を根拠にしてはならない唯一の領域。"},
    ],
    "content.classifications.emptyReason": "",
    "content.decisionCriteria.stages": [
        {"id": "q1", "label": "その主張の根拠は「既存がこうだから」で終わるか？"},
        {"id": "q2", "label": "既存を参照している目的は、置き場所・実現可能性・移行のいずれかか？"},
        {"id": "r1", "label": "越境している。方針から導き直す"},
        {"id": "r2", "label": "向きが正しい。そのまま進めてよい"},
    ],
    "content.decisionCriteria.transitions": [
        {"from": "q1", "to": "r1", "label": "はい"},
        {"from": "q1", "to": "q2", "label": "いいえ"},
        {"from": "q2", "to": "r2", "label": "いずれか"},
        {"from": "q2", "to": "r1", "label": "どれでもない"},
    ],
    "content.decisionCriteria.emptyReason": "",
    "content.examples.text":
        "架空の題材として、社内の備品貸出の仕組みを作り直す場面を考える。\n\n"
        "新しい方針として「貸出の記録は、備品ではなく借り主に紐づける」と定めたとする。"
        "そのうえで既存の記録を数えたところ、9割が備品に紐づいていた。\n\n"
        "ここで「9割がそうなっているのだから、備品に紐づける形のほうが実態に合う」と読むと、"
        "方針を実測が裁いている。作り直す前の形が多数派なのは当然で、それは証拠にならない。\n\n"
        "正しい読み方は「9割が方針から外れている。移行で直す対象が9割ある」である。"
        "同じ数字が、方針を覆す根拠ではなく、移行の見積もりになる。\n\n"
        "一方で、既存を参照してよい場面もある。"
        "「借り主に紐づける形を、いまの記録の仕組みで表現できるか」は実現可能性の問いなので、"
        "既存を調べて確かめてよい。"
        "「新しい記録をどのファイルに置くか」も置き場所の問いなので、既存の配置に合わせてよい。",
    "content.antiPatterns.items": [
        {"name": "実測を根拠に方針を決める",
         "problem": "置き換えようとしている方式の下で作られたものが、目標の形を規定してしまい、"
                    "作り直しが旧方式の追認に終わる。"},
        {"name": "既存に前例があることを設計判断の理由にする",
         "problem": "前例が正しかったかは検証されていないため、"
                    "誤った設計が「既にそうなっている」というだけで再生産される。"},
        {"name": "逸脱の量を理由に方針を緩める",
         "problem": "旧方式の下では逸脱があるのが当然なので、"
                    "この理由を認めると、どんな方針も既存の形へ引き戻される。"},
        {"name": "何のために数えたのかを見失う",
         "problem": "数えた結果は根拠として強く見えるため、"
                    "移行の見積もりのために取った数字が、そのまま設計判断の根拠へ転用される。"},
    ],
    "content.antiPatterns.emptyReason": "",
    "content.provenance.source":
        "外部の一般原則ではなく、実際の作り直しの作業で3度繰り返した誤りを、"
        "ユーザーからの訂正を受けて定式化したもの。",
    "content.provenance.caveats":
        "この規律は「既存を見るな」ではない。"
        "実測を敵対的に当てて逸脱を洗い出すことは、むしろ推奨される。"
        "境界は、実測が答えている問いが「方針はどうあるべきか」なのか"
        "「既存は方針からどれだけ外れているか」なのかにある。\n\n"
        "見分けが常に容易とは限らない。とくに実現可能性の問いは、"
        "「表現できないから形を変える」という形で宣言の形の決定へ滑り込みやすい。"
        "その場合は、表現できない理由が原理的なものか、いまの仕組みの都合かを分けて確かめる必要がある。",
    "content.relatedConcepts.items": [
        {"conceptId": "knowledge-cand-one-binding-for-all-contract-levels",
         "note": "この規律が守られなかった実際の対象。宣言の形を、旧方式の文書から裁こうとした。"},
        {"conceptId": "architecture-evidence-based-scope",
         "note": "実例が揃うまで抽象化しないという規律。実例を根拠に使う向きが逆になると、"
                 "この規律と衝突する。"},
        {"conceptId": "knowledge-cand-investigate-before-explain",
         "note": "主張の前に実物を確認する規律。確認した実物をどう使うかを、この規律が定める。"},
    ],
    "content.relatedConcepts.emptyReason": "",
}

r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill",
                    "--path", f"{ROOT}/{DOC}.json",
                    "--values", json.dumps(values, ensure_ascii=False)],
                   capture_output=True, text=True, cwd=CWD)
print((r.stdout or r.stderr).strip()[:220])
print(run("validate", "--path", f"{ROOT}/{DOC}.json")[:200])
