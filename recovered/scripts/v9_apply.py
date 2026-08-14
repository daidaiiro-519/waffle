"""v9：基準に識別子を持たせ、シナリオが満たす基準を指せるようにする。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
REF = "DomainSpecSchema/v9"

ID_PROMPT = (
    "この基準を指すための短い符号を書いてください。"
    "シナリオがこの符号で「どの基準を満たすか」を指します。"
    "位置にも本文にも依存しない語にしてください——"
    "連番は並べ替えで指す先が変わり、本文から作った名前は文言を直すと壊れます。"
    "一度振った符号は変えないでください（例: rejects-duplicate-name）。"
)
SATISFIES_PROMPT = (
    "このシナリオが満たす基準の符号を、同じ文書の中から選んで並べてください。"
    "1つのシナリオが複数の基準を満たすことは普通にあります"
    "（1回の流れで観測できることが複数あるため）。"
    "どの基準も満たさないシナリオは書けません——"
    "指す先が無いときは、シナリオを消すのではなく、満たすべき基準のほうを書き足してください。"
    "ここに書くのは符号だけで、説明文は書きません。"
)
SATISFIES_QUERY = (
    "このシナリオがどの基準を担っているかを読みます。"
    "符号が指す先が実在するかは機械が確かめますが、"
    "そのシナリオが実際にその基準を確かめているかは確かめません。読み手の責務です。"
)


def patch(op: str, params: dict) -> str:
    r = subprocess.run(["uv", "run", "waffle", "patch-schema", "--schemaRef", REF,
                        "--operation", op, "--params", json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    out = (r.stdout or r.stderr).strip()
    return "ok" if '"changed"' in out else out[:150]


def element(text_prompt: str) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string", "x-prompt-write": ID_PROMPT},
            "text": {"type": "string", "x-prompt-write": text_prompt},
        },
        "required": ["id", "text"],
    }


CRITERIA = [
    ("UsecaseContent", "acceptanceCriteria",
     "この基準の本文を EARS で書いてください（When/While/If … shall …）。"
     "1つの基準は1つの主張にしてください——"
     "「〜し、かつ〜する」のように主張が2つ入っているものは、基準が2つある状態です。"
     "一意・検証可能・ドメイン語彙のみ。"),
    ("UsecaseContent", "operationGuarantees",
     "この保証の本文を EARS で書いてください。"
     "書いてよいのは『何を保証するか』だけ（べき等性・一貫性・提供チャネルの一貫性等）で、"
     "『どう実現するか』は書きません。1つの保証は1つの主張にしてください。"),
]
for def_name, block, prompt in CRITERIA:
    print(f"── {def_name}.{block} を構造にする :",
          patch("set_field", {"defName": def_name,
                              "fieldPath": f"properties.{block}.properties.items.items",
                              "value": element(prompt)}))

print("── AggregateContent.invariants に符号を足す :",
      patch("set_field", {"defName": "AggregateContent",
                          "fieldPath": "properties.invariants.properties.items.items.properties.id",
                          "value": {"type": "string", "x-prompt-write": ID_PROMPT}}))
print("── invariants の必須を更新 :",
      patch("set_field", {"defName": "AggregateContent",
                          "fieldPath": "properties.invariants.properties.items.items.required",
                          "value": ["id", "rule", "enforcement", "rationale"]}))

SCEN = [
    ("UsecaseContent", "acceptanceScenarios"),
    ("UsecaseContent", "guaranteeScenarios"),
    ("AggregateContent", "invariantScenarios"),
    ("BoundedContextContent", "domainServiceScenarios"),
]
for def_name, block in SCEN:
    base = f"properties.{block}.properties.scenarios.items"
    print(f"── {block} に satisfies を置く :",
          patch("set_field", {"defName": def_name,
                              "fieldPath": f"{base}.properties.satisfies",
                              "value": {"type": "array", "items": {"type": "string"},
                                        "minItems": 1,
                                        "x-prompt-write": SATISFIES_PROMPT,
                                        "x-prompt-query": SATISFIES_QUERY}}))
    print(f"   covers を外す :",
          patch("remove_field", {"defName": def_name,
                                 "fieldPath": f"{base}.properties.covers"}))
