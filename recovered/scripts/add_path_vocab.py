"""置き場所まわりの語を宣言へ足し、業務サービスの文書をその語で書き直す。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
BC = ".waffle/documents/specs/bc-waffle/bc-waffle." + "json"
DS = (".waffle/documents/specs/bc-waffle/domain-service/"
      "ds-resolve-path-template." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(path, block, expr):
    return json.loads(run("query", "--operation", "query_path", "--path", path,
                          "--blockKey", block, "--expression", expr))["value"]


def fill(path, values):
    return run("scaffold", "--operation", "fill", "--path", path,
               "--values", json.dumps(values, ensure_ascii=False))[:140]


# ── 語彙を足す
NEW = [
    ("パス", "Document や成果物が置かれている位置。"),
    ("パステンプレート", "Schema が宣言する、パスの書き方の型。値で埋める変数を含む。"),
    ("実パス", "パステンプレートの変数がすべて値で埋まった、ひとつに定まるパス。"),
    ("原本", "値を保持している Document そのもの。"),
    ("成果物", "Document を描画して得られる、読み手向けの出力。"),
    ("解決", "パステンプレートと値から実パスを導くこと。"),
    ("逆解析", "実パスとパステンプレートから、変数の値を取り出すこと。"),
]
items = q(BC, "ubiquitousLanguage", "items")
have = {x["term"] for x in items}
items += [{"term": t, "definition": d} for t, d in NEW if t not in have]
print(f"語彙 {len(items)} 語 :", fill(BC, {"content.ubiquitousLanguage.items": items}))
print("  検証 :", run("validate", "--path", BC)[:120])
print("  描画 :", run("render", "--path", BC)[:90])

# ── 業務サービスの文書を、その語で書き直す
values = {
    "content.title.title": "パステンプレートと値から実パスを導く：ds-resolve-path-template",
    "content.description.items": [
        "Schema が宣言するパステンプレートと、Document が持つ値の両方を読んで、実パスへ解決する。",
        "逆に、実パスとパステンプレートから変数の値を取り出す逆解析も担う。",
    ],
    "content.existenceRationale.items": [
        "パステンプレートを宣言しているのは Schema 集約で、変数に入る値を持っているのは Document 集約である。"
        "どちらか一方だけでは実パスが定まらないため、どちらの内側にも置けない。",
        "解決も逆解析も、Schema 集約と Document 集約のどちらの状態も変えない。"
        "読み取った時点の値で決まればよく、両者が同時に最新である必要が無いため、強い一貫性を要求しない。",
        "実パスが変わるのは、パステンプレートか変数の値のどちらかが変わったときだけで、"
        "その変更はそれぞれの集約の内側で完結する。またがるのは読み取りだけである。",
    ],
    "content.referencedAggregates.items": [
        {"aggregate": "agg-schema", "mode": "参照のみ",
         "reason": "パステンプレートと、そこに現れる変数の並びを読む。"},
        {"aggregate": "agg-document", "mode": "参照のみ",
         "reason": "パステンプレートの変数に入る値を読む。"},
    ],
    "content.inputsOutputs.inputs": [
        {"name": "パステンプレート", "meaning": "値で埋める変数を含んだ、パスの書き方の型。"},
        {"name": "変数の値", "meaning": "パステンプレートの変数それぞれに対応する値。解決のときに与える。"},
        {"name": "実パス", "meaning": "変数がすべて埋まったパス。逆解析のときに与える。"},
    ],
    "content.inputsOutputs.outputs": [
        {"name": "実パス", "meaning": "解決の結果。変数がすべて値に置き換わり、ひとつに定まったパス。"},
        {"name": "変数の値", "meaning": "逆解析の結果。実パスから取り出した、変数それぞれの値。"},
    ],
    "content.inputsOutputs.undefinedInputs": [
        "パステンプレートが要求する変数のうち、値が与えられていないものがあるとき。",
        "逆解析しようとした実パスが、パステンプレートの区切り構造と一致しないとき。",
    ],
    "content.acceptanceCriteria.items": [
        {"id": "resolves-all-vars",
         "text": "When パステンプレートと、その変数すべてに対応する値が与えられたとき、"
                 "システムは変数を値に置き換えた実パスをひとつ返す shall。"},
        {"id": "reverse-recovers-vars",
         "text": "When パステンプレートと、そのパステンプレートから解決された実パスが与えられたとき、"
                 "システムは解決に使った値と同じ値を逆解析で返す shall。"},
        {"id": "reverse-rejects-mismatch",
         "text": "If 与えられた実パスがパステンプレートの区切り構造と一致しないとき、"
                 "システムは逆解析を失敗として返す shall。"},
    ],
    "content.acceptanceScenarios.scenarios": [
        {"name": "パステンプレートの変数を値に置き換える",
         "category": "正常系",
         "viewpoint": "解決：変数がすべて埋まるとき実パスがひとつに定まるか",
         "satisfies": ["resolves-all-vars"],
         "gherkin": "Scenario: パステンプレートの変数を値に置き換える\n"
                    "  Given 変数を含むパステンプレートと、その変数すべてに対応する値\n"
                    "  When 実パスへ解決する\n"
                    "  Then すべての変数が値に置き換わった実パスがひとつ返る"},
        {"name": "実パスから変数の値を取り出す",
         "category": "正常系",
         "viewpoint": "逆解析：解決の逆として同じ値を取り出せるか",
         "satisfies": ["reverse-recovers-vars"],
         "gherkin": "Scenario: 実パスから変数の値を取り出す\n"
                    "  Given パステンプレートと、そのパステンプレートから解決された実パス\n"
                    "  When 逆解析する\n"
                    "  Then 解決に使った値と同じ値が返る"},
        {"name": "区切り構造の合わない実パスは逆解析できない",
         "category": "異常系",
         "viewpoint": "逆解析：構造の合わない入力を決められないものとして扱えるか",
         "satisfies": ["reverse-rejects-mismatch"],
         "gherkin": "Scenario: 区切り構造の合わない実パスは逆解析できない\n"
                    "  Given パステンプレートの区切り構造と一致しない実パス\n"
                    "  When 逆解析する\n"
                    "  Then 逆解析は失敗する"},
    ],
}
print("\n業務サービス :", fill(DS, values))
print("  検証 :", run("validate", "--path", DS)[:140])
