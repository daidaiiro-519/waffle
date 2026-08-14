"""候補2を、段の梯子の形へ書き直す。

元は「抽象概念は2つ」としていたが、実際は1つの対が合成の段を変えて
繰り返しているだけだった。識別子にも誤りが入っているため作り直す。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
ROOT = ".waffle/documents/knowledge"
OLD = "knowledge-cand-two-abstractions-bind-spec-to-implementation"
NEW = "knowledge-cand-binding-differs-by-composition-level"
C1 = "knowledge-cand-operation-contract-closes-invariants"


def run(*args: str) -> str:
    r = subprocess.run(["uv", "run", "waffle", *args],
                       capture_output=True, text=True, cwd=CWD)
    return r.stdout.strip() or r.stderr.strip()


def fill(doc_id: str, values: dict) -> None:
    out = run("scaffold", "--operation", "fill",
              "--path", f"{ROOT}/{doc_id}.json",
              "--values", json.dumps(values, ensure_ascii=False))
    print(f"[fill {doc_id}] {out[:300]}")


print(run("scaffold", "--operation", "create",
          "--schemaRef", "KnowledgeSchema", "--documentId", NEW)[:120])

fill(NEW, {
    "status": "DRAFT",
    "knowledgeKind": "process",
    "agentRefs": ["waffle"],
    "tags": ["topic:traceability", "topic:drift-detection"],
    "content.title.title":
        "仕様と実装のつなぎ方が段によって変わること："
        "knowledge-cand-binding-differs-by-composition-level",
    "content.description.text":
        "受け入れ基準と振る舞いという1つの対が、合成の段を変えて繰り返すこと。"
        "および、段によって照合の相手が変わること——末端の段は実装のコードと文言で照合し、"
        "それより上の段はひとつ下の宣言の集合と被覆で照合する。",
    "content.description.questions": [
        "仕様と実装のトレーサビリティは、どの宣言とどの宣言を突き合わせれば取れるか",
        "実装側に対応する成果物が無い段の宣言は、何と照合すればよいか",
        "転記して照合できない規則に出会ったとき、それをどう扱うべきか",
        "新しい宣言欄を足すべきか、既存の欄に読み手を作るべきか",
        "検知が緑を返したとき、それは何を担保していて何を担保していないのか",
    ],
    "content.principles.items": [
        "仕様と実装をつなぐ抽象概念は1つであり、受け入れ基準と振る舞いの対である。"
        "種類が複数あるのではなく、段が複数あるだけである。",

        "各段の振る舞いは、ひとつ下の段の単位そのものである。"
        "だから同じ対が、合成の段を変えて繰り返す。",

        "照合の相手は段によって変わる。"
        "末端の段は実装のコードと文言の一致で照合し、"
        "それより上の段はひとつ下の宣言の集合と被覆で照合する。",

        "実装側に対応する成果物を持たない段があっても、それは欠陥ではない。"
        "その段の照合の相手はコードではなく宣言の集合であり、"
        "末端が実装と一致していれば、上の段は被覆だけで実装まで届く。",

        "全称命題——あらゆる操作列のあとで成り立つという主張——の居場所は、合成の段の受け入れ基準である。"
        "同じ段には書けないが、ひとつ上の段には書ける。",

        "「実装でそう書けないようにする」は抽象概念ではなく担保手段である。"
        "つなぐ概念は1つのままで、それを守る手段が、段や規則の性質によって変わる。",

        "転記して照合する手段が届かない規則がある。"
        "「保持しない」「残らない」という情報の不在を主張する規則は、"
        "観測するための操作を作った時点で規則そのものが壊れるため、"
        "実装でそう書けない形にすることでしか守れない。",

        "宣言は、読み手が居て初めて機能する。"
        "欄が存在することと、機械がその欄を読むことは別であり、"
        "読み手の居ない欄は、記入されていない状態と検査に通った状態が同じ見た目になる。",

        "検知が「宣言が無ければ黙って対象外にする」形になっていると、"
        "宣言の欠落と検査の合格が区別できなくなる。欠落は欠落として報告する。",

        "この設計前提は、業務領域駆動設計の規律とは別に管理する。"
        "反証されたとき答える相手が違うため——"
        "前者はこの仕組みを持つ側の設計判断であり、後者は業務領域駆動設計として正しいかを問う。",
    ],
    "content.classifications.items": [
        {"name": "末端の段",
         "description": "振る舞いが実装のコードに対応する段。仕様の文言を実装へ転記し、一致で照合する。"},
        {"name": "合成の段",
         "description": "振る舞いがひとつ下の段の宣言の集合である段。覆えているかで照合する。"},
    ],
    "content.classifications.emptyReason": "",
    "content.decisionCriteria.stages": [
        {"id": "q1", "label": "その段の振る舞いは、実装のコードか？"},
        {"id": "q2", "label": "その規則は、情報の不在を主張しているか？"},
        {"id": "q3", "label": "その宣言を読む機械が既に存在するか？"},
        {"id": "r1", "label": "転記して文言の一致で照合する"},
        {"id": "r2", "label": "実装でそう書けない形にする"},
        {"id": "r3", "label": "ひとつ下の宣言の集合との被覆で照合する"},
        {"id": "r4", "label": "読み手を先に作る。作れないなら宣言欄を増やさない"},
    ],
    "content.decisionCriteria.transitions": [
        {"from": "q1", "to": "q2", "label": "はい"},
        {"from": "q1", "to": "r3", "label": "いいえ（下の宣言の集合）"},
        {"from": "q2", "to": "r2", "label": "はい"},
        {"from": "q2", "to": "r1", "label": "いいえ"},
        {"from": "r1", "to": "q3", "label": "照合を作る前に"},
        {"from": "r3", "to": "q3", "label": "照合を作る前に"},
        {"from": "q3", "to": "r4", "label": "いいえ"},
    ],
    "content.decisionCriteria.emptyReason": "",
    "content.examples.text":
        "架空の題材として、社内の備品貸出を扱う仕組みを考える。\n\n"
        "【末端の段】「貸出を延長するとき、上限回数を超えていれば延長は断られる」。"
        "この段の振る舞いは実装のコードに対応するので、"
        "仕様に書かれた筋書きをそのまま実装の検証へ転記し、文言が一致しているかで照合する。"
        "文言が食い違えば落ちるので、仕様と実装は同期し続ける。\n\n"
        "【合成の段】集約「貸出台帳」の「同じ備品が同時に2人へ貸し出されている状態には、常にならない」。"
        "この段の振る舞いは台帳のコマンド群（借りる・返す・延長する・紛失を記録する）であり、"
        "実装のどこか1箇所に対応するわけではない。"
        "照合の相手はコマンド群という宣言の集合で、"
        "4つ全部を覆う筋書きが揃っているかで測る。\n"
        "5つ目のコマンド「他部署へ移管する」を足したとき、"
        "既存の受け入れ基準は1つも壊れないが、被覆は欠ける。この欠けが検知になる。\n\n"
        "【転記も被覆も届かないもの】「借り主の連絡先は、返却が済んだ時点から常に保持しない」。"
        "返却後に連絡先を読み出す操作を作れば観測できるが、作った時点で規則が壊れる。"
        "したがってこれは、返却後の台帳を表す型がそもそも連絡先を持てない、"
        "という書けなさで守る。抽象概念が変わるのではなく、担保手段が変わる。",
    "content.antiPatterns.items": [
        {"name": "段ごとに別の抽象概念を用意する",
         "problem": "同じ対の繰り返しにすぎないものを種類の違いと取り違え、段が増えるたびに新しい仕組みが要ると誤解する。"},
        {"name": "実装に対応物が無い段の宣言を「検証できないから」と畳む",
         "problem": "全称命題の居場所が失われ、操作を1つ足したときに既存の基準は1つも赤くならないまま、誰も気づかない。"},
        {"name": "転記できない規則を仕様から追い出す",
         "problem": "検証しやすさで仕様を選別することになり、失敗の損害が最も大きい種類の規則ほど構造的に取り残される。"},
        {"name": "読み手の居ない宣言欄を足す",
         "problem": "記入されていない状態と検査に通った状態が同じ見た目になり、欄が増えるほど「宣言したから守られている」という誤った安心が積み上がる。"},
        {"name": "検知が、宣言の無いものを黙って対象外にする",
         "problem": "検知が緑を返しても、それが「適合している」なのか「そもそも見ていない」なのか区別できなくなる。"},
    ],
    "content.antiPatterns.emptyReason": "",
    "content.provenance.source":
        "業務領域駆動設計の原則から直接導かれるものではなく、"
        "「受け入れ基準と振る舞いのドリフトをなくすことで仕様と実装のトレーサビリティを取る」という構想を、"
        "全称命題と「情報の不在」を主張する規則が末端では表現できないという制約に照らして再構成したもの。"
        "この仕組みを持つ側の設計判断であり、外部の一般原則の要約ではない。",
    "content.provenance.caveats":
        "未検証の留保が3点ある。\n"
        "(1) この前提はまだ実装で検証されていない。"
        "実測では、機械が読んでいるのは振る舞いの側の4ブロックだけで、"
        "受け入れ基準・操作保証・不変条件・集約のコマンド・基準と振る舞いの対応・不変条件の守り方の"
        "6ブロックは、実装のどこからも読まれていない。\n"
        "(2) 合成の段の照合（被覆）を測る仕組みは存在せず、"
        "基準と振る舞いの対応を運ぶ欄は、必須でも型付きでもない。\n"
        "(3) 「実装でそう書けない形にする」具体的な手段は未着手で、"
        "手段が成立するかどうかもまだ確かめていない。\n\n"
        "なお元の定式化では「仕様と実装をつなぐ抽象概念は2つ（転記して照合するものと、書けないようにするもの）」"
        "としていたが、これは誤りとして退けた。"
        "後者は抽象概念ではなく担保手段であり、"
        "抽象概念そのものは受け入れ基準と振る舞いの対1つで、段が複数あるだけである。",
    "content.relatedConcepts.items": [
        {"conceptId": C1,
         "note": "どの要素が段になりうるかを定める、業務領域駆動設計側の規律。対をなす。"},
        {"conceptId": "knowledge-cand-avoidable-friction-is-not-detection",
         "note": "困りごとを消すだけの対応が原因を残すという規律で、読み手の居ない欄を足す誤りと同じ形をしている。"},
        {"conceptId": "self-improving-generation-cycle",
         "note": "段ごとの照合による担保を、一発の生成でなく測定と修正の反復として回すための土台。"},
    ],
    "content.relatedConcepts.emptyReason": "",
})

# 候補1が旧識別子を指しているので張り替える
q = subprocess.run(
    ["uv", "run", "waffle", "query", "--operation", "query_path",
     "--path", f"{ROOT}/{C1}.json", "--blockKey", "relatedConcepts",
     "--expression", "items"],
    capture_output=True, text=True, cwd=CWD)
items = json.loads(q.stdout)["value"]
for it in items:
    if it["conceptId"] == OLD:
        it["conceptId"] = NEW
        it["note"] = ("この規律を前提として成り立つ、段ごとのつなぎ方についての設計前提。対をなす。")
fill(C1, {"content.relatedConcepts.items": items})

# 旧文書を落とす
old_path = pathlib.Path(CWD) / ROOT / f"{OLD}.json"
if old_path.exists():
    old_path.unlink()
    print(f"[removed] {OLD}")

for d in (NEW, C1):
    print(f"[validate {d}] {run('validate', '--path', f'{ROOT}/{d}.json')[:200]}")
