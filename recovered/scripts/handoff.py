"""配列の要素単位編集の Handoff を書く。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = ".waffle/documents/handoff/handoff-array-element-editing." + "json"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


D = ("Document の配列を要素の鍵で部分編集できるようにする capability の引き継ぎ。"
     "担うユースケース: uc-scaffold-document / uc-validate-document / uc-patch-schema / "
     "uc-check-query-precedes-array-fill / uc-check-criteria-coverage、"
     "および業務サービス ds-patch-array-element / ds-collect-key-references。"
     "配列は今、記入可能な道の走査が配列で止まるため丸ごとしか書き換えられず、"
     "足したい1件だけを渡すと既存が黙って消えて成功と報告される（実測で確認済み）。"
     "これを、鍵の宣言・参照関係の宣言・順序の宣言という3つの宣言と、"
     "add_element / edit_element / retire_element の3操作で置き換える。")

VP_DESIGN = [
    {"advisor": "ddd-advisor",
     "viewpoint": "集約の原則と要素編集は矛盾しない",
     "consideration":
        "集約の原則は「丸ごとしか書き換えられない」ではなく「1つの集約は1つのトランザクションで"
        "変更される」であり、集約ルートを経由して内部要素を足すのは正しい使い方そのもの。"
        "矛盾が生じるのは要素を Document から切り離して単独に指せるようにしたときだけなので、"
        "対象は常に Document、検証単位も Document 全体という2条件を成立条件として置いた。"},
    {"advisor": "ddd-advisor",
     "viewpoint": "汎用CRUDでは、削除に伴う業務ルールが潰れる",
     "consideration":
        "「基準を足す」と「基準を取り下げる」は守るべきことが違い、汎用の add/remove/replace は"
        "この違いを同じ形に潰す。sd-document-management / sd-schema-management がどちらも"
        "中核と宣言されている以上、名付ける側に倒すべきという判断。"
        "そこで retire_element（取り下げる）という語を選び、"
        "参照が先に外れていることを語自体に含意させた。"},
    {"advisor": "ddd-advisor",
     "viewpoint": "宣言の不在が、許可へ倒れてはならない",
     "consideration":
        "「宣言が無い＝指されていない」と読むと、鍵だけ宣言して参照関係を宣言し忘れた配列で"
        "取り下げが常に成功する。engine が業務を知ったのではなく、"
        "書き手が毎回思い出したときだけ業務が守られる状態になる。"
        "そこで uc-validate-document に keyed-array-declares-references を置き、"
        "鍵を宣言した配列は参照関係の宣言を持つことを不適合の検査で強制した。"
        "指されないことが正しいなら、指されない旨を宣言させる。"},
    {"advisor": "ddd-advisor",
     "viewpoint": "同義語を並立させない",
     "consideration":
        "Document 側の「取り下げ」と Schema 側の「除去」は同じ業務ルール（指されているものは"
        "取り除けない）でありながら、語も返す名も参照の集め方も違っていた。"
        "同一の境界づけられたコンテキストの中の同義語の乱立として指摘を受け、"
        "Schema 側にも同じ規律を通す形で解いた。"},
    {"advisor": "tech-lead-advisor",
     "viewpoint": "業務サービスの分け方は、変更理由の違いに対応している",
     "consideration":
        "ds-patch-array-element は鍵の指し方の規則が変われば変わり、"
        "ds-collect-key-references は参照のたどり方が変われば変わる。"
        "変更理由が別なので統合しない。両者とも agg-document と agg-schema の2つに"
        "またがるため、referencedAggregates にそれを明記した。"},
]

VP_IMPL = [
    {"advisor": "tech-lead-advisor",
     "viewpoint": "丸ごと置き換えしかできないのは、走査が配列で止まっているから",
     "consideration":
        "fill_template.py:331-356 の _walk_fill は配列に達すると再帰を止め、"
        "要素の中身を entry['element'] にしまうだけで、要素の道を allowed に1本も積まない。"
        "運用の癖ではなく allowed 集合の作り方そのものに由来する。"
        "したがって判定を「集合への所属」から「分解」へ変える必要がある。"},
    {"advisor": "tech-lead-advisor",
     "viewpoint": "互換の関門は単一で、取り消しが自分に拒まれる",
     "consideration":
        "patch_schema.py:134 の check_backward_compatible は create_version を除く全 operation が"
        "必ず通る唯一の関門。remove_kind_branch は定義上必ず enum 値を除去するため、"
        "enum 除去を違反として実装すると remove_kind_branch が自分の生んだ除去に自分で拒まれ、"
        "そのシナリオは絶対に緑にならない。"
        "免除を operation 単位で明示列挙し、免除された操作は自分の基準で何を壊すかを述べる形にした。"},
    {"advisor": "tech-lead-advisor",
     "viewpoint": "宣言の表記は、条件式の言語にしない",
     "consideration":
        "参照関係は配列を2段またぐ道を表せる必要があるが、述語を書けるようにすると"
        "「条件式言語を持たせない」という設計判断を Schema 側から迂回できてしまう。"
        "配列へ降りることと欄をたどることだけを並べたセグメント列とし、"
        "人が見分けるための欄（手がかり）を同じ宣言の中に並記する。"
        "JMESPath の流用は、ドメイン層への式評価器の降下と述語による迂回の2点で採らない。"},
    {"advisor": "tech-lead-advisor",
     "viewpoint": "業務サービスのテストが全部緑でも、固定値の欠落は検出されない",
     "consideration":
        "fill_template.py:168-176 の _walk_const は object にしか降りず配列へ入らない。"
        "ds 側は固定値を入力として受け取る設計なので、単体テストでは手で渡せば緑になる。"
        "element-add-fills-const は必ず業務ユースケース側の受け入れテストとして"
        "端から端まで通すこと。"},
    {"advisor": "tech-lead-advisor",
     "viewpoint": "鍵の一意性検査は、外部ライブラリのアダプターへ入れない",
     "consideration":
        "jsonschema_validator.py は外部 library を閉じ込める outbound adapter であり、"
        "Waffle 固有の業務ルールの置き場所ではない。ここへ入れるとポートの契約が"
        "コア側の知らない検査を含み始める。ドメインサービスとして書き、"
        "validate_document.py の run() が既存の errors と併合する。"},
    {"advisor": "tech-lead-advisor",
     "viewpoint": "hook が engine より手前で、engine が禁じた手順を勧める",
     "consideration":
        "require-query-before-array-fill は PreToolUse で deny するため、"
        "鍵を宣言した配列への丸ごと置き換えは engine へ到達せず、"
        "利用者は「query してから丸ごと置き換えろ」という、この仕様が禁じた手順だけを見る。"
        "要素操作は values とは別の引数にして hook の判定に掛からないようにし、"
        "拒否の理由には両方の道を示させる。"},
]

CONSTRAINTS = [
    "要素を Document から切り離して単独に指せるようにしない。対象は常に Document 全体、"
    "検証単位も Document 全体。",
    "鍵の欄名を共通の名前へ統一しない。id / name / code / term の書き分けをそのまま保つ。",
    "文字列の並びで値そのものを鍵にしない。部分編集が要るほど重要なら構造化して欄を与える。",
    "順序が意味を持つ配列を「鍵が無い配列」として表さない。順序であることを積極的に宣言する。",
    "参照関係の宣言に、値による絞り込み（述語）を書けるようにしない。",
    "鍵の一意性検査を ValidateDocument へ同時に入れる。別の回へ送るなら要素編集自体を送る。",
    "要素操作は、1つでも受け付けられないものがあれば何も適用しない。",
    "PatchSchema に Document の走査を持ち込まない。取り消される種別を指す Document が"
    "残っていないかの確認は、schema版のドリフトを見る側の責務。",
]

SCOPE = [
    {"path": "src/waffle/domain/services/element_key_declaration.py",
     "reason": "鍵・参照関係・順序の3つの宣言を schema から読み出す語彙。"
               "fill 経路と validate 経路の2つの usecase が使うため、"
               "fill_template.py へ寄せず独立させる。鍵の一意性検査もここへ同居させる。"},
    {"path": "src/waffle/domain/services/patch_array_element.py",
     "reason": "ds-patch-array-element の実装。鍵で要素を足す・欄を直す・取り除く写像と、全か無か。"},
    {"path": "src/waffle/domain/services/collect_key_references.py",
     "reason": "ds-collect-key-references の実装。宣言のセグメント列をたどって参照を集める。"},
    {"path": "src/waffle/domain/services/fill_template.py",
     "reason": "_walk_const を配列へ降ろす（要素の固定値）。"
               "entry へ鍵・参照関係・順序の宣言を載せて記入指示へ抜けさせる。"},
    {"path": "src/waffle/application/usecases/scaffold_document.py",
     "reason": "elementOps の受け付け、丸ごと置き換えの拒否と案内、全か無かの保存。"
               "着手前に allowed / const_paths / protected の組み立てを切り出す"
               "（_fill と _clear_field で既に重複しており、要素操作で3箇所目になる）。"},
    {"path": "src/waffle/application/usecases/validate_document.py",
     "reason": "鍵の一意性と、鍵を宣言した配列が参照関係の宣言を持つことを、既存の errors へ併合。"},
    {"path": "src/waffle/domain/services/schema_patch.py",
     "reason": "check_backward_compatible へ enum 値除去と参照された $defs 除去を追加。"
               "remove_kind_branch を add_kind_branch の隣に新設。"},
    {"path": "src/waffle/application/usecases/patch_schema.py",
     "reason": "remove_kind_branch の分岐追加と、互換の関門を通らない操作の明示列挙。"},
    {"path": ".waffle/hooks/require-query-before-array-fill.py",
     "reason": "要素操作を配列の値を含む書き込みとして扱わない。拒否の理由に要素操作の道も示す。"},
    {"path": "src/waffle/domain/model/DomainSpecSchema/v9.json",
     "reason": "受け入れ基準とシナリオの配列へ、鍵の宣言と参照関係の宣言を実際に置く"
               "（この capability の最初の適用先であり、dogfood の対象そのもの）。"},
]

LAYERS = [
    {"label": "宣言（Schema 側）",
     "nodes": ["鍵の宣言", "参照関係の宣言", "順序の宣言"],
     "description": "配列ノードごとに置かれ、記入指示へも抜ける。"
                    "要素側の共有定義には置かない（巻き添えを避けるため）。"},
    {"label": "業務サービス",
     "nodes": ["ds-patch-array-element", "ds-collect-key-references"],
     "description": "宣言と Document の中身を突き合わせる純粋な計算。"
                    "どちらも状態を変えず、書き戻す先を知らない。"},
    {"label": "業務ユースケース",
     "nodes": ["uc-scaffold-document", "uc-validate-document", "uc-patch-schema"],
     "description": "読み込み・書き込み先の解決・保存の編成。新しい usecase は立てない。"},
    {"label": "受け口",
     "nodes": ["CLI", "MCP", "hook"],
     "description": "operation 名と引数を素通しするだけ。判定を持たせない。"},
]

REL = [
    {"from": "鍵の宣言", "to": "ds-patch-array-element", "kind": "uses", "label": "要素を一意に指す"},
    {"from": "参照関係の宣言", "to": "ds-collect-key-references", "kind": "uses", "label": "たどる道"},
    {"from": "ds-collect-key-references", "to": "uc-scaffold-document", "kind": "uses",
     "label": "取り下げてよいかを導く"},
    {"from": "ds-patch-array-element", "to": "uc-scaffold-document", "kind": "uses",
     "label": "書き換えた配列"},
    {"from": "鍵の宣言", "to": "uc-validate-document", "kind": "uses", "label": "一意性を検査する"},
    {"from": "参照関係の宣言", "to": "uc-check-criteria-coverage", "kind": "uses",
     "label": "参照の欠けを検知する"},
]

vals = {
    "status": "CREATED",
    "tags": ["framework:waffle"],
    "content.title.title": "配列を、要素の鍵で編集できるようにする",
    "content.specRef.specRef": "uc-scaffold-document",
    "content.description.text": D,
    "content.designViewpoints.items": VP_DESIGN,
    "content.implementationViewpoints.items": VP_IMPL,
    "content.constraints.items": CONSTRAINTS,
    "content.expectedScope.items": SCOPE,
    "content.completionImage.layers": LAYERS,
    "content.completionImage.relationships": REL,
    "content.reviewStatus.requiredAdvisors": ["ddd-advisor", "tech-lead-advisor"],
    "content.reviewStatus.findings": [
        {"advisor": "ddd-advisor", "refBlock": "acceptanceCriteria", "refIndex": 0,
         "resolutionStatus": "resolved",
         "note": "宣言の不在が許可へ倒れる問題。uc-validate-document に "
                 "keyed-array-declares-references を置いて解いた。"},
        {"advisor": "ddd-advisor", "refBlock": "acceptanceCriteria", "refIndex": 1,
         "resolutionStatus": "resolved",
         "note": "PRECONDITION_NOT_MET が汎用名だった。STILL_REFERENCED へ改め、"
                 "新設の4コードを errors ブロックへ登録した。"},
        {"advisor": "tech-lead-advisor", "refBlock": "acceptanceCriteria", "refIndex": 2,
         "resolutionStatus": "resolved",
         "note": "enum 除去と remove_kind_branch の矛盾。互換の関門を通らない操作を"
                 "明示列挙する形で解き、免除された操作が何を壊すかを基準として書いた。"},
        {"advisor": "tech-lead-advisor", "refBlock": "inputs", "refIndex": 0,
         "resolutionStatus": "resolved",
         "note": "要素操作の引数が inputs に無く、テストの Given が書けなかった。"
                 "elementOps を宣言し、二重に書かれていた fieldPath を1つにした。"},
        {"advisor": "ddd-advisor", "refBlock": "referencedAggregates", "refIndex": 0,
         "resolutionStatus": "resolved",
         "note": "存在意義が「集約の外」と述べながら referencedAggregates が空だった。"
                 "agg-document と agg-schema を明記し、存在意義も2集約にまたがる形へ書き直した。"
                 "既存の3件（ds-resolve-path-template 等）にも同じ穴が残っており、別途直す。"},
        {"advisor": "ddd-advisor", "refBlock": "description", "refIndex": 0,
         "resolutionStatus": "open",
         "note": "「参照の欠けの検知」に消費者が無いという指摘を両advisorから受けたが、"
                 "uc-check-criteria-coverage の reports-dangling が消費者として実在した。"
                 "見落としではなく、私がその仕様をdispatchに渡し忘れたことが原因。"
                 "指摘自体は解消だが、dispatch時に関連仕様を渡す手順は未整備。"},
    ],
    "content.reviewStatus.completionImageConfirmedBy.confirmed": False,
    "content.reviewStatus.completionImageConfirmedBy.note":
        "ユーザーへの提示待ち。実装の着手はこの確認のあと。",
}

print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:300])
print(run("validate", "--path", P)[:400])
