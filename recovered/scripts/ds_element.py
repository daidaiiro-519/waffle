"""要素の同一性を扱う業務サービスを2件起こす。"""
from __future__ import annotations

import json
import subprocess
import sys

sys.path.insert(0, "/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
                   "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
from ds_helper import create, run  # noqa: E402

CWD = "/home/daidaiiro/workspace/waffle"
BC = ".waffle/documents/specs/bc-waffle/bc-waffle." + "json"

NEW_TERMS = [
    ("要素の鍵", "配列の中で要素を一意に指す欄。どの欄が鍵かは配列ごとに宣言され、"
                "欄の名前は配列によって異なる（id・name・code・term など）。"),
    ("参照関係の宣言", "ある配列の要素の鍵が、Document のどこから指されるかの宣言。"
                     "取り下げてよいかの判断と、参照の欠けの検知の両方がここから導かれる。"),
    ("順序の宣言", "その配列が、要素の集まりではなく並び全体でひとつの値であることの宣言。"
                 "宣言された配列に要素単位の編集は使えない。"),
]

items = json.loads(run("query", "--operation", "query_path", "--path", BC,
                       "--blockKey", "ubiquitousLanguage", "--expression", "items"))["value"]
have = {x["term"] for x in items}
added = [t for t, d in NEW_TERMS if t not in have]
for t, d in NEW_TERMS:
    if t not in have:
        items.append({"term": t, "definition": d})
if added:
    subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill", "--path", BC,
                    "--values", json.dumps({"content.ubiquitousLanguage.items": items},
                                           ensure_ascii=False)],
                   capture_output=True, text=True, cwd=CWD)
    run("render", "--path", BC)
    print(f"  語彙に {added} を追加（計 {len(items)} 語）")

# ── 1件目：鍵で要素を書き換える写像 ────────────────────────────
create("ds-patch-array-element", {
    "content.title.title": "鍵で配列の要素を書き換える：ds-patch-array-element",
    "content.description.items": [
        "鍵の宣言と配列、それに要素操作を受け取り、書き換えたあとの配列を返す。",
        "足す・欄を直す・取り除くの3つを扱い、どれも鍵を通して要素を指す。",
        "配列そのものは受け取るだけで、どの Document から来たかは知らない。",
    ],
    "content.existenceRationale.title": "存在意義",
    "content.existenceRationale.items": [
        "測る対象が集約の外にある。どの欄が鍵かという宣言は Schema 側にあり、"
        "Document 集約はそれを持っていない。宣言と配列を突き合わせるこの計算は、"
        "持っていないものを対象にするので集約の内側に置けない。",
        "この計算はどの集約の状態も変えない。受け取った配列から新しい配列を作って返すだけで、"
        "書き戻す先を知らない。",
    ],
    "content.referencedAggregates.title": "参照する集約",
    "content.referencedAggregates.items": [],
    "content.inputsOutputs.title": "入力と出力",
    "content.inputsOutputs.inputs": [
        {"name": "要素の鍵", "meaning": "配列の中で要素を一意に指す欄の名前。"},
        {"name": "配列", "meaning": "書き換える対象の、要素の集まり。"},
        {"name": "要素操作", "meaning": "足す・欄を直す・取り除くのいずれかと、その対象と値。"},
        {"name": "要素の固定値", "meaning": "Schema が要素に宣言する、書き手が決めない値。"},
    ],
    "content.inputsOutputs.outputs": [
        {"name": "書き換えたあとの配列", "meaning": "すべての要素操作を適用した結果。"},
        {"name": "適用できなかった操作", "meaning": "鍵が見つからない等で受け付けられなかった操作と、その理由。"},
    ],
    "content.inputsOutputs.undefinedInputs": [
        "配列の中に同じ鍵を持つ要素が2つ以上あるとき（要素を一意に指せないため、"
        "この計算は答えを持たない。一意性は適合の検証が先に担保する）。",
        "鍵の宣言が、要素に実在しない欄を指しているとき。",
    ],
    "content.acceptanceCriteria.items": [
        {"id": "adds-to-tail",
         "text": "When 足す操作が与えられたとき、システムは配列の末尾へその要素を加えた配列を返す shall。"},
        {"id": "fills-const-on-add",
         "text": "When 足す要素に固定値の欄が含まれていないとき、システムはその固定値を補って加える shall。"},
        {"id": "edits-named-fields-only",
         "text": "When 欄を直す操作が与えられたとき、システムは鍵が一致する要素の、"
                 "指定された欄だけを書き換えた配列を返す shall（鍵と他の欄は変えない）。"},
        {"id": "removes-by-key",
         "text": "When 取り除く操作が与えられたとき、システムは鍵が一致する要素を除いた配列を返す shall。"},
        {"id": "unknown-key-is-not-created",
         "text": "If 指定された鍵を持つ要素が配列に無いとき、システムはその操作を適用できなかったものとして返し、"
                 "要素を新たに作らない shall。"},
        {"id": "all-or-nothing",
         "text": "If ひとつでも適用できない操作があるとき、システムはどの操作も適用していない配列を返す shall。"},
        {"id": "preserves-order-of-untouched",
         "text": "While 操作の対象になっていない要素があるとき、システムはそれらの並び順を変えない shall。"},
    ],
    "content.acceptanceScenarios.background": "",
    "content.acceptanceScenarios.scenarios": [
        {"name": "足した要素は末尾に付く",
         "category": "正常系",
         "viewpoint": "書き換えの写像：足す位置が定まっているか",
         "satisfies": ["adds-to-tail", "preserves-order-of-untouched"],
         "gherkin": "Scenario: 足した要素は末尾に付く\n"
                    "  Given 3件の要素を持つ配列\n"
                    "  When 要素を1件足す\n"
                    "  Then 4件になり、元の3件は同じ順序で先頭から並んでいる"},
        {"name": "足す要素に固定値が補われる",
         "category": "正常系",
         "viewpoint": "書き換えの写像：宣言された固定値が欠けたまま残らないか",
         "satisfies": ["fills-const-on-add"],
         "gherkin": "Scenario: 足す要素に固定値が補われる\n"
                    "  Given 固定値の欄を宣言している要素の配列\n"
                    "  When 固定値の欄を含めずに要素を足す\n"
                    "  Then 加わった要素に固定値が入っている"},
        {"name": "欄を直しても鍵と他の欄は変わらない",
         "category": "正常系",
         "viewpoint": "書き換えの写像：直すことと別物に置き換えることを分けられるか",
         "satisfies": ["edits-named-fields-only"],
         "gherkin": "Scenario: 欄を直しても鍵と他の欄は変わらない\n"
                    "  Given 鍵と2つの欄を持つ要素\n"
                    "  When 片方の欄だけを直す\n"
                    "  Then その欄だけが変わり、鍵ともう片方の欄は元のまま"},
        {"name": "鍵が一致する要素だけが取り除かれる",
         "category": "正常系",
         "viewpoint": "書き換えの写像：指した1件だけに効くか",
         "satisfies": ["removes-by-key", "preserves-order-of-untouched"],
         "gherkin": "Scenario: 鍵が一致する要素だけが取り除かれる\n"
                    "  Given 3件の要素を持つ配列\n"
                    "  When 真ん中の要素の鍵を指して取り除く\n"
                    "  Then 2件になり、残った2件の順序は変わらない"},
        {"name": "無い鍵を指しても要素は作られない",
         "category": "異常系",
         "viewpoint": "指し間違い：黙って足すことで埋めないか",
         "satisfies": ["unknown-key-is-not-created"],
         "gherkin": "Scenario: 無い鍵を指しても要素は作られない\n"
                    "  Given その鍵を持つ要素が無い配列\n"
                    "  When その鍵を指して欄を直す\n"
                    "  Then 適用できなかった操作として返り、配列の件数は変わらない"},
        {"name": "1件でも適用できなければ何も適用しない",
         "category": "異常系",
         "viewpoint": "全か無か：途中まで適用された配列を返さないか",
         "satisfies": ["all-or-nothing"],
         "gherkin": "Scenario: 1件でも適用できなければ何も適用しない\n"
                    "  Given 3件の操作のうち1件が無い鍵を指している\n"
                    "  When 3件をまとめて適用する\n"
                    "  Then 返る配列は操作前と同じ"},
    ],
})

# ── 2件目：鍵への参照を集める ────────────────────────────────
create("ds-collect-key-references", {
    "content.title.title": "宣言をたどって、鍵を指している場所を集める：ds-collect-key-references",
    "content.description.items": [
        "参照関係の宣言と Document を受け取り、ある鍵を指している場所を集めて返す。",
        "集めた結果は、要素を取り下げてよいかの判断と、参照の欠けの検知の両方に使う。",
        "宣言されていない参照は集めない。どこが指しうるかは宣言だけが決める。",
    ],
    "content.existenceRationale.title": "存在意義",
    "content.existenceRationale.items": [
        "測る対象が集約の外にある。どこがどこを指すかという参照関係は Schema 側の宣言であり、"
        "Document 集約はそれを持っていない。宣言に沿って自分の中を走査するという計算は、"
        "持っていない物差しを必要とするので集約の内側に置けない。",
        "この計算はどの集約の状態も変えない。読み取った時点の中身から答えが決まる。",
    ],
    "content.referencedAggregates.title": "参照する集約",
    "content.referencedAggregates.items": [],
    "content.inputsOutputs.title": "入力と出力",
    "content.inputsOutputs.inputs": [
        {"name": "参照関係の宣言", "meaning": "ある配列の鍵が、Document のどこから指されるかの宣言。"},
        {"name": "Document の中身", "meaning": "走査の対象。"},
        {"name": "探す鍵", "meaning": "指されているかを知りたい鍵。"},
    ],
    "content.inputsOutputs.outputs": [
        {"name": "指している場所", "meaning": "その鍵を指していた場所と、その場所が属する要素を人が見分けられる手がかり。"},
        {"name": "指す先が無い参照", "meaning": "宣言に沿って集めた参照のうち、対応する鍵が存在しなかったもの。"},
    ],
    "content.inputsOutputs.undefinedInputs": [
        "参照関係が宣言されていないとき（集める対象が定まらない。"
        "宣言が無い配列は、指されていないものとして扱う）。",
    ],
    "content.acceptanceCriteria.items": [
        {"id": "collects-declared-references",
         "text": "When 参照関係が宣言されているとき、システムはその宣言がたどる場所だけを走査し、"
                 "探す鍵を指している場所を集める shall。"},
        {"id": "ignores-undeclared-places",
         "text": "While 宣言されていない場所に同じ文字列があるとき、システムはそれを参照として集めない shall。"},
        {"id": "no-declaration-means-unreferenced",
         "text": "While その配列に参照関係が宣言されていないとき、システムは指している場所が無いものとして返す shall。"},
        {"id": "identifies-referring-element",
         "text": "When 指している場所を返すとき、システムはその場所が属する要素を人が見分けられる手がかりを添える shall"
                 "（どこを直せば取り下げられるかが分かるようにするため）。"},
        {"id": "collects-dangling-references",
         "text": "When 宣言に沿って集めた参照のうち、対応する鍵が配列に存在しないものがあるとき、"
                 "システムはそれを指す先が無い参照として返す shall。"},
    ],
    "content.acceptanceScenarios.background": "",
    "content.acceptanceScenarios.scenarios": [
        {"name": "宣言がたどる場所から参照を集める",
         "category": "正常系",
         "viewpoint": "宣言だけをたどる：指している場所を見つけられるか",
         "satisfies": ["collects-declared-references", "identifies-referring-element"],
         "gherkin": "Scenario: 宣言がたどる場所から参照を集める\n"
                    "  Given 受け入れ基準の鍵がシナリオの satisfies から指されると宣言された Document\n"
                    "  When ある基準の鍵を指している場所を集める\n"
                    "  Then そのシナリオが、名前とともに返る"},
        {"name": "宣言されていない場所の同じ文字列は参照ではない",
         "category": "境界値",
         "viewpoint": "宣言だけをたどる：たまたま一致した文字列を参照と数えないか",
         "satisfies": ["ignores-undeclared-places"],
         "gherkin": "Scenario: 宣言されていない場所の同じ文字列は参照ではない\n"
                    "  Given 宣言されていない欄に、探す鍵と同じ文字列がある Document\n"
                    "  When その鍵を指している場所を集める\n"
                    "  Then 指している場所は無いと返る"},
        {"name": "参照関係が宣言されていなければ指されていない",
         "category": "境界値",
         "viewpoint": "宣言だけをたどる：宣言が無いことを、答えの不在として扱えるか",
         "satisfies": ["no-declaration-means-unreferenced"],
         "gherkin": "Scenario: 参照関係が宣言されていなければ指されていない\n"
                    "  Given 参照関係を宣言していない配列\n"
                    "  When その要素の鍵を指している場所を集める\n"
                    "  Then 指している場所は無いと返る"},
        {"name": "指す先が無い参照を見つける",
         "category": "異常系",
         "viewpoint": "対の照合：宣言された参照の先が欠けていることを見つけられるか",
         "satisfies": ["collects-dangling-references"],
         "gherkin": "Scenario: 指す先が無い参照を見つける\n"
                    "  Given 存在しない基準の鍵を satisfies が指している Document\n"
                    "  When 宣言に沿って参照を集める\n"
                    "  Then その参照が、指す先が無い参照として返る"},
    ],
})
