"""v9 を一度に組み立てる。

基準に符号を持たせ、シナリオが満たす基準を指し、守り方を分ける欄を捨て、
業務サービスを独自の文書種別にする。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
REF = "DomainSpecSchema/v9"
TARGET = pathlib.Path(CWD, "src/waffle/domain/model/DomainSpecSchema") / ("v9" + ".json")

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
RULE_PROMPT = (
    "この集約が常に満たす不変条件を「〜は常に〜」の形で書いてください。"
    "値オブジェクトや属性の宣言がすでに言っていることは、ここへ重ねて書かないでください"
    "（「その項目を持たない」等は、属性の宣言が言っています）。"
    "ここに書くのは、操作をまたいでも成り立つという振る舞いの主張だけです。"
)


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def patch(op, params):
    out = run("patch-schema", "--schemaRef", REF, "--operation", op,
              "--params", json.dumps(params, ensure_ascii=False))
    return "ok" if '"changed"' in out else out[:150]


def criteria_items(text_prompt):
    return {"type": "object", "additionalProperties": False,
            "properties": {
                "id": {"type": "string", "x-prompt-write": ID_PROMPT, "x-prompt-query": ID_QUERY},
                "text": {"type": "string", "x-prompt-write": text_prompt}},
            "required": ["id", "text"]}


satisfies = {"type": "array", "items": {"type": "string"}, "minItems": 1,
             "x-prompt-write": SATISFIES_PROMPT, "x-prompt-query": SATISFIES_QUERY}

DS_BLOCK = {
    "type": "object", "additionalProperties": False,
    "x-render-order": 20, "x-render-level": 2,
    "x-render": [{"as": "kvtable",
                  "columns": [{"field": "serviceName", "header": "実装の名前"},
                              {"field": "group", "header": "置き場所の束"},
                              {"field": "responsibility", "header": "引き受けていること"}]}],
    "properties": {
        "blockType": {"const": "DomainService"},
        "title": {"type": "string",
                  "x-prompt-write": "このブロックの見出しを書いてください（例: 業務サービス）。",
                  "x-prompt-query": "このブロックが何を語っているかの見出しです。"},
        "serviceName": {
            "type": "string",
            "x-prompt-write": "実装がこの業務サービスを名乗るときの名前を書いてください。"
                              "実装側の呼び名と完全に一致させます（突き合わせの鍵になります）。",
            "x-prompt-query": "実装のどれがこの業務サービスかを指す名前です。"
                              "実物と一致しているかは機械が確かめます。"},
        "group": {
            "type": "string",
            "x-prompt-write": "この業務サービスの実装を置くファイルの束を書いてください。"
                              "関連する複数の業務サービスが同じファイルに同居することがあるため、"
                              "1つの束を複数の業務サービスが共有してかまいません。",
            "x-prompt-query": "実装ファイルの場所を導くための束です。"
                              "同じ束を共有する業務サービスは同じファイルに在ります。"},
        "responsibility": {
            "type": "string",
            "x-prompt-write": "この業務サービスが引き受けている判断や計算を、業務語彙で1〜2文で書いてください。"
                              "満たすべきことは受け入れ基準のほうに書くので、ここには書きません。",
            "x-prompt-query": "この業務サービスが何を引き受けているかを読みます。"},
    },
    "required": ["blockType", "title", "serviceName", "group", "responsibility"],
}

DS_CONTENT = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"$ref": "#/$defs/TitleBlock"},
        "description": {"$ref": "#/$defs/SummaryBlock"},
        "domainService": {"$ref": "#/$defs/DomainServiceBlock"},
        "acceptanceCriteria": {"$ref": "#/$defs/AcceptanceCriteriaBlock"},
        "acceptanceScenarios": {"$ref": "#/$defs/AcceptanceScenariosBlock"},
    },
    "required": ["title", "description", "domainService",
                 "acceptanceCriteria", "acceptanceScenarios"],
}

edits = [
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
    {"defName": "InvariantsBlock", "fieldPath": "properties.items.items.properties.id",
     "value": {"type": "string", "x-prompt-write": ID_PROMPT, "x-prompt-query": ID_QUERY}},
    {"defName": "InvariantsBlock", "fieldPath": "properties.items.items.properties.rule",
     "value": {"type": "string", "x-prompt-write": RULE_PROMPT}},
    {"defName": "InvariantsBlock", "fieldPath": "properties.items.items.required",
     "value": ["id", "rule", "rationale"]},
    {"defName": None, "fieldPath": "$defs.DomainServiceBlock", "value": DS_BLOCK},
    {"defName": None, "fieldPath": "$defs.DomainServiceContent", "value": DS_CONTENT},
]
for d in ("AcceptanceScenariosBlock", "GuaranteeScenariosBlock",
          "InvariantScenariosBlock", "DomainServiceScenariosBlock"):
    edits.append({"defName": d, "fieldPath": "properties.scenarios.items.properties.satisfies",
                  "value": satisfies})

TARGET.unlink(missing_ok=True)
print("版を起こす :", run("patch-schema", "--schemaRef", REF, "--operation", "create_version",
                      "--params", json.dumps({"fromSchemaRef": "DomainSpecSchema/v8",
                                              "edits": edits}, ensure_ascii=False))[:110])

print("守り方の欄を落とす :",
      patch("remove_field", {"defName": "InvariantsBlock",
                             "fieldPath": "properties.items.items.properties.enforcement"}))
for d in ("AcceptanceScenariosBlock", "GuaranteeScenariosBlock",
          "InvariantScenariosBlock", "DomainServiceScenariosBlock"):
    patch("remove_field", {"defName": d, "fieldPath": "properties.scenarios.items.properties.covers"})
print("対応の自由文を落とす : ok")

print("自分の版を指す :",
      patch("set_field", {"defName": None, "fieldPath": "properties.schemaRef.const",
                          "value": "DomainSpecSchema/v9"}))
print("基準を表にする :",
      patch("set_field", {"defName": "AcceptanceCriteriaBlock", "fieldPath": "x-render.0",
                          "value": {"as": "table", "from": "items",
                                    "columns": [{"field": "id", "header": "符号"},
                                                {"field": "text", "header": "基準"}]}}))
print("不変条件を表にする :",
      patch("set_field", {"defName": "InvariantsBlock", "fieldPath": "x-render.0.columns",
                          "value": [{"field": "id", "header": "符号"},
                                    {"field": "rule", "header": "ルール"},
                                    {"field": "rationale", "header": "根拠"}]}))
for d in ("AcceptanceScenariosBlock", "GuaranteeScenariosBlock",
          "InvariantScenariosBlock", "DomainServiceScenariosBlock"):
    patch("set_field", {"defName": d, "fieldPath": "x-render.1.each.0.columns",
                        "value": [{"field": "category", "header": "分類"},
                                  {"field": "viewpoint", "header": "観点"},
                                  {"field": "satisfies", "header": "満たす基準"}]})
print("満たす基準の列 : ok")

print("種別を足す :", patch("add_kind_branch", {
    "discriminatorField": "specKind", "kindValue": "domain-service",
    "contentDefName": "DomainServiceContent"}))
for b in ("domainServices", "domainServiceScenarios"):
    print(f"文脈から外す [{b}] :",
          patch("remove_block", {"contentDefName": "BoundedContextContent", "propName": b}))

print("指示の契約 :", run("check-prompt-contract", "--schemaRef", REF)[:140])
