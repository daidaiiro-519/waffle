"""KnowledgeSchema v6 を切る。平らな5ブロックを、概念の木へ畳む。

深さは3で有界（agg-schema の不変条件「再帰は常に有界」に従い、段ごとに型を分ける）。
図は節点と関係の宣言。表とコードは原文のまま持つ。いずれも意図と読み取りを必須にする。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"

KIND_WRITE = (
    "このノードが何を述べるものかを書いてください。"
    "推奨: 定義／分類／判断基準／実例／対比／補足／アンチパターン／関連。"
    "どれにも当てはまらないなら、当てはまる言葉を自分で書いてかまいません"
    "（列挙で縛ると、入らないものが黙って落ちるため）。")
KIND_QUERY = ("このノードが何を述べるものかを読みます。"
              "推奨値以外が書かれている場合、それは器が受け止めきれていない種類が"
              "現れた合図かもしれません。")

FIGURE = {
    "type": "object",
    "properties": {
        "intent": {"type": "string",
                   "x-prompt-write": "この図が何を示すためのものかを1文で書いてください。",
                   "x-prompt-query": "この図が何を示すためのものかを読みます。"},
        "reading": {"type": "string",
                    "x-prompt-write": "この図から何が言えるかを書いてください。"
                                      "図を描画できない読み手が、この文だけで意味を取れるように書きます。",
                    "x-prompt-query": "この図から何が言えるかを読みます。"
                                      "図を見なくても、この文だけで意味が取れるはずです。"},
        "direction": {"type": "string",
                      "x-prompt-write": "並びの向きを LR（左から右）か TD（上から下）で書いてください。",
                      "x-prompt-query": "並びの向きを読みます。"},
        "groups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string",
                              "x-prompt-write": "この囲みの名前を書いてください。",
                              "x-prompt-query": "囲みの名前を読みます。"},
                    "nodes": {"type": "array", "items": {"type": "string"},
                              "x-prompt-write": "この囲みに入る節点を並べてください。",
                              "x-prompt-query": "囲みに入る節点を読みます。"},
                },
                "required": ["label", "nodes"], "additionalProperties": False,
            },
            "x-prompt-write": "節点をまとめる囲みがあれば並べてください。無ければ空で。",
            "x-prompt-query": "節点をまとめる囲みを読みます。",
        },
        "nodes": {"type": "array", "items": {"type": "string"},
                  "x-prompt-write": "囲みに属さない節点を並べてください。",
                  "x-prompt-query": "囲みに属さない節点を読みます。"},
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from": {"type": "string",
                             "x-prompt-write": "矢印の元の節点を書いてください。",
                             "x-prompt-query": "矢印の元を読みます。"},
                    "to": {"type": "string",
                           "x-prompt-write": "矢印の先の節点を書いてください。",
                           "x-prompt-query": "矢印の先を読みます。"},
                    "label": {"type": "string",
                              "x-prompt-write": "矢印に添える言葉があれば書いてください。",
                              "x-prompt-query": "矢印に添えられた言葉を読みます。"},
                },
                "required": ["from", "to"], "additionalProperties": False,
            },
            "x-prompt-write": "節点どうしのつながりを並べてください。",
            "x-prompt-query": "節点どうしのつながりを読みます。"
                              "この一覧だけで、図を描かずに関係が追えるはずです。",
        },
    },
    "required": ["intent", "reading", "edges"],
    "additionalProperties": False,
    "x-prompt-query": "節点と関係の宣言を読みます。図は単独では置けません——"
                      "意図と読み取りが必ず添えられており、図を描画できなくても意味が取れます。",
}

VERBATIM = {
    "type": "object",
    "properties": {
        "intent": {"type": "string",
                   "x-prompt-write": "この原文が何を示すためのものかを1文で書いてください。",
                   "x-prompt-query": "この原文が何を示すためのものかを読みます。"},
        "reading": {"type": "string",
                    "x-prompt-write": "この原文から何が言えるかを書いてください。"
                                      "原文を読み解かなくても、この文だけで要点が取れるように書きます。",
                    "x-prompt-query": "この原文から何が言えるかを読みます。"},
        "lang": {"type": "string",
                 "x-prompt-write": "原文の種類を書いてください（csharp・sql・markdown・mermaid など）。",
                 "x-prompt-query": "原文の種類を読みます。"},
        "source": {"type": "string",
                   "x-prompt-write": "原文をそのまま書いてください。構造へ変換しません"
                                     "（変換すると肝が消える種類のものだけがここに入ります）。",
                   "x-prompt-query": "原文を読みます。変換されていない、そのままのものです。"},
    },
    "required": ["intent", "reading", "lang", "source"],
    "additionalProperties": False,
    "x-prompt-query": "規則性が無いため構造にできなかったものを読みます。"
                      "表・コード・特殊な図がここに入ります。意図と読み取りが必ず添えられています。",
}


def node_def(child_ref: str | None) -> dict:
    props = {
        "name": {"type": "string",
                 "x-prompt-write": "この概念の名前を書いてください。",
                 "x-prompt-query": "この概念の名前を読みます。"},
        "kind": {"type": "string",
                 "x-prompt-write": KIND_WRITE, "x-prompt-query": KIND_QUERY},
        "sourceRef": {"type": "string",
                      "x-prompt-write": "出典の位置を書いてください（図1-3・1.2.3.3 など）。"
                                        "これが無いと、後から原本へ当たり直せません。",
                      "x-prompt-query": "出典の位置を読みます。原本へ当たり直すときの手がかりです。"},
        "summary": {"type": "string",
                    "x-prompt-write": "この概念が述べることを文章で書いてください。"
                                      "図や原文があっても、この文だけで要点が取れるように書きます。",
                    "x-prompt-query": "この概念が述べることを読みます。"},
        "figure": {"$ref": "#/$defs/Figure"},
        "verbatim": {"$ref": "#/$defs/Verbatim"},
    }
    if child_ref:
        props["children"] = {
            "type": "array",
            "items": {"$ref": f"#/$defs/{child_ref}"},
            "x-prompt-write": "この概念の下にぶら下がる概念を並べてください。無ければ空で。",
            "x-prompt-query": "この概念の下にぶら下がる概念を読みます。",
        }
    return {
        "type": "object", "properties": props,
        "required": ["name", "kind", "summary"],
        "additionalProperties": False,
    }


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


NODES_BLOCK = {
    "type": "object",
    "properties": {
        "blockType": {"const": "Nodes"},
        "title": {"type": "string",
                  "x-prompt-write": "この knowledge の中身の見出しを書いてください。",
                  "x-prompt-query": "中身の見出しを読みます。"},
        "items": {
            "type": "array", "minItems": 1,
            "items": {"$ref": "#/$defs/ConceptNode"},
            "x-prompt-write": "この knowledge が扱う概念を並べてください。"
                              "元にした資料の見出し1つに対して、ノード1つを対応させます"
                              "（粒度を落とさないため）。",
            "x-prompt-query": "この knowledge が扱う概念を読みます。"
                              "元の資料の見出しと1対1で対応しているはずです——"
                              "対応が取れないものがあれば、変換で粒度が落ちています。",
        },
    },
    "required": ["blockType", "title", "items"],
    "additionalProperties": False,
    "x-render": [{"as": "section", "each": "items", "titleFrom": "name"}],
    "x-prompt-query": "概念の木を読みます。ノードは名前・種別・出典の位置・文章を必ず持ち、"
                      "図や原文、そして子ノードを持つことがあります。",
}

edits = [
    {"defName": None, "fieldPath": "properties.schemaRef.const", "value": "KnowledgeSchema/v6"},
    {"defName": None, "fieldPath": "$defs.Figure", "value": FIGURE},
    {"defName": None, "fieldPath": "$defs.Verbatim", "value": VERBATIM},
    {"defName": None, "fieldPath": "$defs.ConceptNodeLeaf", "value": node_def(None)},
    {"defName": None, "fieldPath": "$defs.ConceptNodeChild", "value": node_def("ConceptNodeLeaf")},
    {"defName": None, "fieldPath": "$defs.ConceptNode", "value": node_def("ConceptNodeChild")},
    {"defName": None, "fieldPath": "$defs.NodesBlock", "value": NODES_BLOCK},
    {"defName": None, "fieldPath": "$defs.KnowledgeContent.properties", "value": {
        "description": {"$ref": "#/$defs/OverviewBlock"},
        "nodes": {"$ref": "#/$defs/NodesBlock"},
        "provenance": {"$ref": "#/$defs/ProvenanceBlock"},
        "relatedConcepts": {"$ref": "#/$defs/RelatedConceptsBlock"},
    }},
    {"defName": None, "fieldPath": "$defs.KnowledgeContent.required",
     "value": ["description", "nodes", "provenance", "relatedConcepts"]},
]

print(run("patch-schema", "--operation", "create_version",
          "--schemaRef", "KnowledgeSchema/v6",
          "--params", json.dumps({"fromSchemaRef": "KnowledgeSchema/v5", "edits": edits},
                                 ensure_ascii=False))[:220])
