"""業務サービスを、業務ユースケース・集約と同じく独自の文書種別にする。

3つとも受け入れ基準とシナリオを持ち、実装の成果物を持つ。つなぎ方が同じである以上、
宣言のされ方も同じでなければならない。文脈の文書の中の一項目のままにすると、
扱いだけが特例になる。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
REF = "DomainSpecSchema/v9"


def patch(op, params):
    r = subprocess.run(["uv", "run", "waffle", "patch-schema", "--schemaRef", REF,
                        "--operation", op, "--params", json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    out = (r.stdout or r.stderr).strip()
    return "ok" if '"changed"' in out else out[:170]


# ── 1. 業務サービス文書の中身を入れる器
print("器を作る :", patch("add_def", {
    "defName": "DomainServiceContent",
    "defDef": {"type": "object", "additionalProperties": False, "properties": {}, "required": []},
}))

# ── 2. 業務サービス自身を語るブロック
print("自身を語るブロック :", patch("add_block", {
    "blockName": "DomainServiceBlock",
    "contentDefName": "DomainServiceContent",
    "propName": "domainService",
    "required": True,
    "blockDef": {
        "type": "object",
        "additionalProperties": False,
        "x-render-order": 20,
        "x-render-level": 2,
        "x-render": [{"as": "kvtable",
                      "columns": [{"field": "serviceName", "header": "実装の名前"},
                                  {"field": "group", "header": "置き場所の束"}]}],
        "properties": {
            "blockType": {"const": "DomainService"},
            "title": {"type": "string",
                      "x-prompt-write": "このブロックの見出しを書いてください（例: 業務サービス）。",
                      "x-prompt-query": "このブロックが何を語っているかの見出しです。"},
            "serviceName": {
                "type": "string",
                "x-prompt-write":
                    "実装がこの業務サービスを名乗るときの名前を書いてください。"
                    "実装側の呼び名と完全に一致させます（突き合わせの鍵になります）。",
                "x-prompt-query":
                    "実装のどれがこの業務サービスかを指す名前です。実物と一致しているかは機械が確かめます。"},
            "group": {
                "type": "string",
                "x-prompt-write":
                    "この業務サービスの実装を置くファイルの束を書いてください。"
                    "関連する複数の業務サービスが同じファイルに同居することがあるため、"
                    "1つの束を複数の業務サービスが共有してかまいません。",
                "x-prompt-query":
                    "実装ファイルの場所を導くための束です。同じ束を共有する業務サービスは同じファイルに在ります。"},
            "responsibility": {
                "type": "string",
                "x-prompt-write":
                    "この業務サービスが引き受けている判断や計算を、業務語彙で1〜2文で書いてください。"
                    "満たすべきことは受け入れ基準のほうに書くので、ここには書きません。",
                "x-prompt-query": "この業務サービスが何を引き受けているかを読みます。"},
        },
        "required": ["blockType", "title", "serviceName", "group", "responsibility"],
    },
}))

# ── 3. 既にある定義を、そのまま参照する
for prop, block in (("title", "TitleBlock"),
                    ("description", "SummaryBlock"),
                    ("acceptanceCriteria", "AcceptanceCriteriaBlock"),
                    ("acceptanceScenarios", "AcceptanceScenariosBlock")):
    print(f"{prop} を参照 :", patch("set_field", {
        "defName": "DomainServiceContent",
        "fieldPath": f"properties.{prop}",
        "value": {"$ref": f"#/$defs/{block}"}}))

print("必須をそろえる :", patch("set_field", {
    "defName": "DomainServiceContent",
    "fieldPath": "required",
    "value": ["title", "description", "domainService",
              "acceptanceCriteria", "acceptanceScenarios"]}))

# ── 4. 種別として立てる
print("種別を足す :", patch("add_kind_branch", {
    "discriminatorField": "specKind",
    "kindValue": "domain-service",
    "contentDefName": "DomainServiceContent"}))
