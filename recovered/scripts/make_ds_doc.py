"""業務サービス「置き場所の導出」を、独自の文書として起こす。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
DOC = "ds-resolve-path-template"
P = f".waffle/documents/specs/bc-waffle/domain-service/{DOC}." + "json"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


print("器を作る :", run("scaffold", "--operation", "create", "--schemaRef", "DomainSpecSchema",
                     "--discriminator", "specKind=domain-service",
                     "--documentId", DOC, "--contextRef", "bc-waffle")[:90])

values = {
    "status": "CREATED",
    "tags": ["framework:waffle"],
    "content.title.title": "置き場所の宣言と値から実際の在り処を導く：ds-resolve-path-template",
    "content.description.items": [
        "置き場所のひな型と、そこへ入る値の両方を読んで、実際の在り処を導く。",
        "逆に、実際の在り処からひな型の変数を復元する向きも持つ。",
    ],
    "content.existenceRationale.title": "存在意義",
    "content.existenceRationale.items": [
        "ひな型を宣言しているのはスキーマで、そこへ入る値を持っているのは文書である。"
        "どちらか一方だけでは在り処が決まらないため、どちらの内側にも置けない。",
        "在り処を導く計算は、スキーマと文書のどちらの状態も変えない。"
        "読み取った時点の値で決まればよく、両者が同時に最新である必要が無いため、"
        "強い一貫性を要求しない。",
        "在り処が変わるのは、ひな型か値のどちらかが変わったときだけで、"
        "その変更はそれぞれの内側で完結する。またがるのは読み取りだけである。",
    ],
    "content.referencedAggregates.title": "参照する集約",
    "content.referencedAggregates.items": [
        {"aggregate": "agg-schema", "mode": "参照のみ",
         "reason": "置き場所のひな型と、そこに現れる変数の並びを読む。"},
        {"aggregate": "agg-document", "mode": "参照のみ",
         "reason": "ひな型の変数に入る値（識別子や所属の参照）を読む。"},
    ],
    "content.inputsOutputs.title": "入力と出力",
    "content.inputsOutputs.inputs": [
        {"name": "置き場所のひな型", "meaning": "変数を含んだ、在り処の書き方の型。"},
        {"name": "変数に入る値", "meaning": "ひな型の変数それぞれに対応する実際の値。"},
    ],
    "content.inputsOutputs.outputs": [
        {"name": "実際の在り処", "meaning": "ひな型の変数がすべて値に置き換わった、ひとつに定まる在り処。"},
        {"name": "復元された値", "meaning": "実際の在り処から読み取った、ひな型の変数それぞれの値。"},
    ],
    "content.inputsOutputs.undefinedInputs": [
        "ひな型が要求する変数のうち、値が与えられていないものがあるとき。",
        "復元しようとした在り処が、ひな型の区切り構造と一致しないとき。",
    ],
    "content.acceptanceCriteria.items": [
        {"id": "resolves-all-vars",
         "text": "When ひな型と、その変数すべてに対応する値が与えられたとき、"
                 "システムは変数を値に置き換えた在り処をひとつ返す shall。"},
        {"id": "reverse-recovers-vars",
         "text": "When ひな型と、そのひな型から導かれた在り処が与えられたとき、"
                 "システムは導出に使った値と同じ値を復元する shall。"},
        {"id": "reverse-rejects-mismatch",
         "text": "If 与えられた在り処がひな型の区切り構造と一致しないとき、"
                 "システムは復元を失敗として返す shall。"},
    ],
    "content.acceptanceScenarios.background": "",
    "content.acceptanceScenarios.scenarios": [
        {"name": "ひな型の変数を値に置き換える",
         "category": "正常系",
         "viewpoint": "導出：変数がすべて埋まるとき在り処がひとつに定まるか",
         "satisfies": ["resolves-all-vars"],
         "gherkin": "Scenario: ひな型の変数を値に置き換える\n"
                    "  Given 変数を含む置き場所のひな型と、その変数すべてに対応する値\n"
                    "  When 在り処を導く\n"
                    "  Then すべての変数が値に置き換わった在り処がひとつ返る"},
        {"name": "在り処から変数の値を復元する",
         "category": "正常系",
         "viewpoint": "逆向きの一意性：導出の逆として同じ値を取り出せるか",
         "satisfies": ["reverse-recovers-vars"],
         "gherkin": "Scenario: 在り処から変数の値を復元する\n"
                    "  Given 置き場所のひな型と、そのひな型から導かれた在り処\n"
                    "  When 変数の値を復元する\n"
                    "  Then 導出に使った値と同じ値が復元される"},
        {"name": "ひな型と構造の合わない在り処は復元できない",
         "category": "異常系",
         "viewpoint": "逆向きの健全性：構造の合わない入力を決められないものとして扱えるか",
         "satisfies": ["reverse-rejects-mismatch"],
         "gherkin": "Scenario: ひな型と構造の合わない在り処は復元できない\n"
                    "  Given ひな型の区切り構造と一致しない在り処\n"
                    "  When 変数の値を復元する\n"
                    "  Then 復元は失敗する"},
    ],
}
print("値を書く :", run("scaffold", "--operation", "fill", "--path", P,
                     "--values", json.dumps(values, ensure_ascii=False))[:120])
print("検証 :", run("validate", "--path", P)[:220])
