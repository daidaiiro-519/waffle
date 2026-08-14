"""受け入れ基準・操作保証・不変条件に識別子を持たせ、シナリオが満たす基準を指せるようにする。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
REF = "DomainSpecSchema/v9"

ID_PROMPT = (
    "この基準を指すための短い符号を書いてください。"
    "シナリオがこの符号で「どの基準を満たすか」を指します。"
    "位置にも本文にも依存しない語にしてください——連番は並べ替えで指す先が変わり、"
    "本文から作った名前は文言を直すと壊れます。"
    "一度振った符号は変えないでください（例: rejects-duplicate-name）。"
)
SATISFIES_PROMPT = (
    "このシナリオが満たす基準の符号を、同じ文書の中から選んで並べてください。"
    "1つのシナリオが複数の基準を満たすことは普通にあります"
    "（1回の流れで観測できることが複数あるため）。"
    "どの基準も満たさないシナリオは書けません——"
    "指す先が無いときは、シナリオを消すのではなく、満たすべき基準のほうを書き足してください。"
    "ここに書くのは符号だけで、説明文は書かないでください。"
)


def patch(operation: str, params: dict) -> str:
    r = subprocess.run(["uv", "run", "waffle", "patch-schema", "--schemaRef", REF,
                        "--operation", operation, "--params", json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()[:220]


def criteria_element(text_prompt: str) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string", "x-prompt-write": ID_PROMPT},
            "text": {"type": "string", "x-prompt-write": text_prompt},
        },
        "required": ["id", "text"],
    }


EDITS = [
    ("AcceptanceCriteria", "properties.items.items", criteria_element(
        "この基準の本文を EARS で書いてください（When/While/If … shall …）。"
        "1つの基準は1つの主張にしてください——"
        "「〜し、かつ〜する」のように主張が2つ入っているものは、基準が2つある状態です。"
        "一意・検証可能・ドメイン語彙のみ。")),
    ("OperationGuarantees", "properties.items.items", criteria_element(
        "この保証の本文を EARS で書いてください。"
        "書いてよいのは『何を保証するか』だけ（べき等性・一貫性・提供チャネルの一貫性等）で、"
        "『どう実現するか』は書きません。1つの保証は1つの主張にしてください。")),
]

for def_name, field_path, value in EDITS:
    print(f"── {def_name}.{field_path}")
    print("   ", patch("set_field", {"defName": def_name, "fieldPath": field_path, "value": value}))

# 不変条件は既に構造なので、識別子の項目だけを足す
print("── Invariants に識別子を足す")
print("   ", patch("set_field", {
    "defName": "Invariants",
    "fieldPath": "properties.items.items.properties.id",
    "value": {"type": "string", "x-prompt-write": ID_PROMPT},
}))
print("   ", patch("set_field", {
    "defName": "Invariants",
    "fieldPath": "properties.items.items.required",
    "value": ["id", "rule", "enforcement", "rationale"],
}))

# シナリオ3種：covers を捨て、satisfies を置く
for def_name in ("AcceptanceScenarios", "GuaranteeScenarios", "InvariantScenarios"):
    print(f"── {def_name} の covers を satisfies へ")
    print("   ", patch("set_field", {
        "defName": def_name,
        "fieldPath": "properties.scenarios.items.properties.satisfies",
        "value": {"type": "array", "items": {"type": "string"},
                  "minItems": 1, "x-prompt-write": SATISFIES_PROMPT},
    }))
    print("   ", patch("remove_field", {
        "defName": def_name,
        "fieldPath": "properties.scenarios.items.properties.covers",
    }))
