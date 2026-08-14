"""業務サービス文書に、存在意義・参照する集約・入力と出力を足す。

業務サービスは他の部品との関係で定義されるので、参照先と配置の否定形が無いと
定義が成立しない。エラーは独立させず、定義されない入力として入出力に含める。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
REF = "DomainSpecSchema/v9"

RATIONALE = {
    "type": "object", "additionalProperties": False,
    "x-render-order": 11, "x-render-level": 2,
    "x-render": [{"as": "list", "from": "items"}],
    "properties": {
        "blockType": {"const": "ExistenceRationale"},
        "title": {"type": "string",
                  "x-prompt-write": "このブロックの見出しを書いてください（例: 存在意義）。",
                  "x-prompt-query": "このブロックが何を語っているかの見出しです。"},
        "items": {"type": "array", "minItems": 1, "items": {"type": "string",
            "x-prompt-write":
                "なぜこの計算を集約の内側に置けないのかを、論点ごとに1件ずつ書いてください。"
                "「複数の集約にまたがるから」は理由になりません（同じことの言い換えです）。"
                "書くべきは、なぜその一貫性が結果整合で足りるのか——"
                "強い一貫性が要るなら、それは集約の境界の引き方を直すべき合図です。"}},
    },
    "required": ["blockType", "title", "items"],
    "x-prompt-query":
        "この計算が集約の内側に置けない理由を読みます。"
        "理由が同じことの言い換えになっていたら、集約の境界を引き直せる可能性があります。",
}

REFERENCED = {
    "type": "object", "additionalProperties": False,
    "x-render-order": 12, "x-render-level": 2,
    "x-render": [{"as": "table", "from": "items",
                  "columns": [{"field": "aggregate", "header": "集約"},
                              {"field": "mode", "header": "触れ方"},
                              {"field": "reason", "header": "何のために"}]}],
    "properties": {
        "blockType": {"const": "ReferencedAggregates"},
        "title": {"type": "string",
                  "x-prompt-write": "このブロックの見出しを書いてください（例: 参照する集約）。",
                  "x-prompt-query": "このブロックが何を語っているかの見出しです。"},
        "items": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "aggregate": {"type": "string",
                    "x-prompt-write": "触れる集約の識別子を書いてください。",
                    "x-prompt-query": "この計算がどの集約に触れるかを読みます。"},
                "mode": {"type": "string", "enum": ["参照のみ", "変更を伴う"],
                    "x-prompt-write":
                        "その集約を読むだけなら「参照のみ」、状態を変えるなら「変更を伴う」を選んでください。"
                        "変更を伴う集約が2つ以上並ぶなら、集約の境界の引き方を疑ってください。",
                    "x-prompt-query":
                        "その集約を読むだけか、変えるかを読みます。変えるものが2つ以上あれば境界の引き直しを検討します。"},
                "reason": {"type": "string",
                    "x-prompt-write": "その集約から何を得る（何を変える）のかを1文で書いてください。",
                    "x-prompt-query": "その集約に触れる目的を読みます。"},
            },
            "required": ["aggregate", "mode", "reason"]}},
    },
    "required": ["blockType", "title", "items"],
    "x-prompt-query":
        "この計算がどの集約にまたがるかを読みます。"
        "1つしか並んでいなければ、その集約の内側に置けたはずです。",
}

IO = {
    "type": "object", "additionalProperties": False,
    "x-render-order": 13, "x-render-level": 2,
    "x-render": [
        {"as": "table", "from": "inputs", "heading": "受け取るもの",
         "columns": [{"field": "name", "header": "名前"}, {"field": "meaning", "header": "意味"}]},
        {"as": "table", "from": "outputs", "heading": "返すもの",
         "columns": [{"field": "name", "header": "名前"}, {"field": "meaning", "header": "意味"}]},
        {"as": "list", "from": "undefinedInputs", "heading": "決められない入力",
         "emptyText": "決められない入力は無い。"},
    ],
    "properties": {
        "blockType": {"const": "InputsOutputs"},
        "title": {"type": "string",
                  "x-prompt-write": "このブロックの見出しを書いてください（例: 入力と出力）。",
                  "x-prompt-query": "このブロックが何を語っているかの見出しです。"},
        "inputs": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "name": {"type": "string",
                    "x-prompt-write": "受け取るものの名前を業務語彙で書いてください。",
                    "x-prompt-query": "この計算が何を受け取るかを読みます。"},
                "meaning": {"type": "string",
                    "x-prompt-write": "それが何を表すかを業務語彙で1文で書いてください。",
                    "x-prompt-query": "受け取るものの意味を読みます。"}},
            "required": ["name", "meaning"]}},
        "outputs": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "name": {"type": "string",
                    "x-prompt-write": "返すものの名前を業務語彙で書いてください。",
                    "x-prompt-query": "この計算が何を返すかを読みます。"},
                "meaning": {"type": "string",
                    "x-prompt-write": "それが何を表すかを業務語彙で1文で書いてください。",
                    "x-prompt-query": "返すものの意味を読みます。"}},
            "required": ["name", "meaning"]}},
        "undefinedInputs": {"type": "array", "items": {"type": "string",
            "x-prompt-write":
                "この計算が答えを決められない入力を書いてください。"
                "状態を持たない計算の失敗は、状態の不整合ではなく、"
                "写像が決まらない入力としてしか現れません。"
                "処理の後始末や代替の手順はここに書きません（それは呼ぶ側の仕事です）。"}},
    },
    "required": ["blockType", "title", "inputs", "outputs"],
    "x-prompt-query":
        "この計算が何から何を決めるかを読みます。"
        "集約にとっての不変条件に相当する固定点が、業務サービスではこの対応そのものです。",
}

DS_CONTENT = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"$ref": "#/$defs/TitleBlock"},
        "description": {"$ref": "#/$defs/SummaryBlock"},
        "existenceRationale": {"$ref": "#/$defs/ExistenceRationaleBlock"},
        "referencedAggregates": {"$ref": "#/$defs/ReferencedAggregatesBlock"},
        "inputsOutputs": {"$ref": "#/$defs/InputsOutputsBlock"},
        "acceptanceCriteria": {"$ref": "#/$defs/AcceptanceCriteriaBlock"},
        "acceptanceScenarios": {"$ref": "#/$defs/AcceptanceScenariosBlock"},
    },
    "required": ["title", "description", "existenceRationale", "referencedAggregates",
                 "inputsOutputs", "acceptanceCriteria", "acceptanceScenarios"],
}

extra = [
    {"defName": None, "fieldPath": "$defs.ExistenceRationaleBlock", "value": RATIONALE},
    {"defName": None, "fieldPath": "$defs.ReferencedAggregatesBlock", "value": REFERENCED},
    {"defName": None, "fieldPath": "$defs.InputsOutputsBlock", "value": IO},
    {"defName": None, "fieldPath": "$defs.DomainServiceContent", "value": DS_CONTENT},
]
pathlib.Path(CWD, "scratch_extra_edits.json").write_text(
    json.dumps(extra, ensure_ascii=False), encoding="utf-8")
print("追加する宣言を用意しました")
