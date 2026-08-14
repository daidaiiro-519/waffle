"""discriminatorキー抽出を、独自の文書として起こす。

測る対象（schema の分岐構造そのもの）が集約の外にある型。
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
                   "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
from ds_helper import create  # noqa: E402

create("ds-extract-discriminator-key", {
    "content.title.title": "Schema のどの欄が種別を決めているかを取り出す：ds-extract-discriminator-key",
    "content.description.items": [
        "Schema の分岐の書き方から、どの欄が種別の判別に使われているかを取り出す。",
        "取り出した欄の名前は、骨格を作るときや Document を読むときに、"
        "どの種別として扱うかを決める手がかりになる。",
    ],
    "content.existenceRationale.title": "存在意義",
    "content.existenceRationale.items": [
        "測る対象が集約の外にある。Schema 集約が持っているのは識別子・版・種別ごとの輪郭だけで、"
        "分岐がどう書かれているかという構造そのものは持っていない。"
        "構造を読むこの計算は、持っていないものを対象にするので集約の内側に置けない。",
        "この計算はどの集約の状態も変えない。読み取った構造から答えが決まるだけで、"
        "結果をどこかへ書き戻すこともない。",
    ],
    "content.referencedAggregates.title": "参照する集約",
    "content.referencedAggregates.items": [],
    "content.inputsOutputs.title": "入力と出力",
    "content.inputsOutputs.inputs": [
        {"name": "Schema の構造", "meaning": "分岐の書き方を含んだ、Schema の中身そのもの。"},
    ],
    "content.inputsOutputs.outputs": [
        {"name": "種別を決める欄の名前", "meaning": "分岐の判別に使われている欄の名前。分岐が無ければ答えは無い。"},
    ],
    "content.inputsOutputs.undefinedInputs": [],
    "content.acceptanceCriteria.items": [
        {"id": "top-level-branch",
         "text": "When Schema が最上位に分岐を持つとき、"
                 "システムはその分岐が判別に使っている欄の名前を返す shall。"},
        {"id": "nested-branch",
         "text": "When Schema が最上位に分岐を持たず、束ねられた要素の中に分岐を持つとき、"
                 "システムは最初に見つかった分岐が判別に使っている欄の名前を返す shall。"},
        {"id": "no-branch",
         "text": "While Schema が分岐をひとつも持たないとき、システムは答えが無いことを返す shall。"},
    ],
    "content.acceptanceScenarios.background": "",
    "content.acceptanceScenarios.scenarios": [
        {"name": "最上位の分岐から種別の欄を取り出す",
         "category": "正常系",
         "viewpoint": "分岐の読み取り：最上位に分岐があるとき、その判別の欄を返せるか",
         "satisfies": ["top-level-branch"],
         "gherkin": "Scenario: 最上位の分岐から種別の欄を取り出す\n"
                    "  Given 最上位に specKind で分岐する Schema\n"
                    "  When 種別を決める欄を取り出す\n"
                    "  Then specKind が返る"},
        {"name": "束ねられた要素の中の分岐から種別の欄を取り出す",
         "category": "正常系",
         "viewpoint": "分岐の読み取り：最上位に無くても、束の中を辿って見つけられるか",
         "satisfies": ["nested-branch"],
         "gherkin": "Scenario: 束ねられた要素の中の分岐から種別の欄を取り出す\n"
                    "  Given 最上位には分岐を持たず、束ねられた要素の中で codingKind により分岐する Schema\n"
                    "  When 種別を決める欄を取り出す\n"
                    "  Then codingKind が返る"},
        {"name": "分岐を持たない Schema は答えが無い",
         "category": "境界値",
         "viewpoint": "分岐の読み取り：分岐が無いことを、誤りではなく答えの不在として扱えるか",
         "satisfies": ["no-branch"],
         "gherkin": "Scenario: 分岐を持たない Schema は答えが無い\n"
                    "  Given 分岐をひとつも持たない Schema\n"
                    "  When 種別を決める欄を取り出す\n"
                    "  Then 答えが無いことが返る"},
    ],
})
