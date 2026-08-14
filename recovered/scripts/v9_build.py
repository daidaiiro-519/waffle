"""v9 を、破壊的な変更も含めて一度に作る。

未公開の版なので、create_version の edits に渡せば後方互換の検査を通らずに済む。
"""
from __future__ import annotations

import json
import pathlib
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
ID_QUERY = (
    "シナリオがこの基準を指すための符号です。"
    "業務の語彙ではないので、人へ説明するときはこの符号ではなく本文を引用してください。"
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


def criteria_items(text_prompt: str) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string", "x-prompt-write": ID_PROMPT, "x-prompt-query": ID_QUERY},
            "text": {"type": "string", "x-prompt-write": text_prompt},
        },
        "required": ["id", "text"],
    }


satisfies = {"type": "array", "items": {"type": "string"}, "minItems": 1,
             "x-prompt-write": SATISFIES_PROMPT, "x-prompt-query": SATISFIES_QUERY}

edits = [
    # 受け入れ基準・操作保証を、符号を持つ構造にする
    {"defName": "AcceptanceCriteriaBlock", "fieldPath": "properties.items.items",
     "value": criteria_items(
         "この基準の本文を EARS で書いてください（When/While/If … shall …）。"
         "1つの基準は1つの主張にしてください——"
         "「〜し、かつ〜する」のように主張が2つ入っているものは、基準が2つある状態です。"
         "一意・検証可能・ドメイン語彙のみ。")},
    {"defName": "OperationGuaranteesBlock", "fieldPath": "properties.items.items",
     "value": criteria_items(
         "この保証の本文を EARS で書いてください。"
         "書いてよいのは『何を保証するか』だけ（べき等性・一貫性・提供チャネルの一貫性等）で、"
         "『どう実現するか』は書きません。1つの保証は1つの主張にしてください。")},

    # 不変条件に符号を足す
    {"defName": "InvariantsBlock", "fieldPath": "properties.items.items.properties.id",
     "value": {"type": "string", "x-prompt-write": ID_PROMPT, "x-prompt-query": ID_QUERY}},
    {"defName": "InvariantsBlock", "fieldPath": "properties.items.items.required",
     "value": ["id", "rule", "enforcement", "rationale"]},
]

# シナリオ4種：satisfies を置き、covers を落とす
for d in ("AcceptanceScenariosBlock", "GuaranteeScenariosBlock",
          "InvariantScenariosBlock", "DomainServiceScenariosBlock"):
    edits.append({"defName": d, "fieldPath": "properties.scenarios.items.properties.satisfies",
                  "value": satisfies})

pathlib.Path(CWD, "src/waffle/domain/model/DomainSpecSchema/v9.json").unlink(missing_ok=True)
r = subprocess.run(["uv", "run", "waffle", "patch-schema", "--schemaRef", REF,
                    "--operation", "create_version",
                    "--params", json.dumps({"fromSchemaRef": "DomainSpecSchema/v8",
                                            "edits": edits}, ensure_ascii=False)],
                   capture_output=True, text=True, cwd=CWD)
print("create_version:", (r.stdout or r.stderr).strip()[:200])

# covers は remove_field で落とす（create_version の edits は set_field のみ）
for d in ("AcceptanceScenariosBlock", "GuaranteeScenariosBlock",
          "InvariantScenariosBlock", "DomainServiceScenariosBlock"):
    rr = subprocess.run(["uv", "run", "waffle", "patch-schema", "--schemaRef", REF,
                         "--operation", "remove_field",
                         "--params", json.dumps({"defName": d,
                                                 "fieldPath": "properties.scenarios.items.properties.covers"})],
                        capture_output=True, text=True, cwd=CWD)
    out = (rr.stdout or rr.stderr).strip()
    print(f"covers を落とす [{d}]:", "ok" if '"changed"' in out else out[:120])
