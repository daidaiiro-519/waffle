"""受け入れ条件の被覆を確かめる検査のユースケース仕様を起こす。

決定（ADR）で定めた4つの結果と、未記入の扱いを仕様として書き下ろす。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
DOC = "uc-check-criteria-coverage"
PATH = f".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/usecase/{DOC}.json"


def run(*args: str) -> str:
    r = subprocess.run(["uv", "run", "waffle", *args],
                       capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


print(run("scaffold", "--operation", "create", "--schemaRef", "DomainSpecSchema",
          "--discriminator", "specKind=usecase", "--documentId", DOC,
          "--contextRef", "bc-waffle", "--subdomainRef", "sd-reconciliation")[:120])

values = {
    "status": "DRAFT",
    "subdomainRef": "sd-reconciliation",
    "tags": ["framework:waffle", "topic:traceability"],
    "content.title.title": "受け入れ条件の被覆を確かめる：uc-check-criteria-coverage",
    "content.usecase.operationName": "CheckCriteriaCoverage",
    "content.actorIntent.actor": "Orchestrator（HarnessAgent）",
    "content.actorIntent.intent":
        "受け入れ条件のうち、どの振る舞いのシナリオからも指されていないものを知りたい",
    "content.usecaseRationale.items": [
        "受け入れ条件と振る舞いのシナリオは対で担保を成す。対応が宣言されていないと、"
        "ある条件がどのシナリオからも覆われていないことを機械が言えず、"
        "件数の差までしか分からない。どの条件が欠けているかは人が読んで数えるしかなかった。",

        "シナリオが実装へ転写されて照合されることは既に担保されているが、"
        "その手前——条件とシナリオが結び付いているか——には突き合わせが無い。"
        "末端が実装に届いていても、そもそも誰も担当していない条件は素通りする。",
    ],
    "content.description.items": [
        "仕様文書の中で、受け入れ条件と、それを満たすと宣言された振る舞いのシナリオを突き合わせ、"
        "結び付いていない側を両方向で報告する。",
        "報告するのは結び付きの有無だけで、シナリオが実際にその条件を確かめているかは判定しない。",
    ],
    "content.externalActors.items": [],
    "content.preconditions.items": [
        "対象の仕様文書が、受け入れ条件に識別子を持つ形で書かれていること",
    ],
    "content.inputs.items": [
        {"name": "path",
         "description": "確かめる対象の仕様文書。1件だけを見るときに指定する"},
        {"name": "documentsRoot",
         "description": "仕様側の走査範囲。配下の仕様文書をまとめて確かめるときに指定する"},
    ],
    "content.mainFlow.participants": [
        {"id": "Orchestrator", "kind": "actor"},
        {"id": "被覆の検査", "kind": "participant"},
        {"id": "仕様文書", "kind": "participant"},
    ],
    "content.mainFlow.steps": [
        {"from": "Orchestrator", "to": "被覆の検査",
         "message": "受け入れ条件の被覆を確かめる", "kind": "command"},
        {"from": "被覆の検査", "to": "仕様文書",
         "message": "受け入れ条件と振る舞いのシナリオを読む", "kind": "command"},
        {"from": "被覆の検査", "to": "被覆の検査",
         "message": "宣言された識別子の集合と、シナリオが指した識別子の集合を突き合わせる",
         "kind": "self"},
        {"from": "被覆の検査", "to": "Orchestrator",
         "message": "結び付いていない側を両方向で返す", "kind": "return"},
    ],
    "content.postconditions.items": [
        "返り値は unreferenced（どのシナリオからも指されていない受け入れ条件）を持つ",
        "返り値は dangling（実在しない識別子を指しているシナリオと、その識別子）を持つ",
        "返り値は duplicate_ids（同一文書内で重複している識別子）を持つ",
        "返り値は unlinked_scenarios（満たす条件を1件も挙げていないシナリオ）を持つ",
        "返り値は uncovered_by_omission（満たす条件の欄そのものが未記入のシナリオ）を持つ。"
        "未記入を黙って対象から外すと、宣言の欠落と検査に通ったことが同じ見た目になる",
        "結び付きの有無だけを判定し、シナリオが指した条件を実際に確かめているかは判定しない",
    ],
    "content.acceptanceCriteria.items": [
        "When ある受け入れ条件がどの振る舞いのシナリオからも指されていないとき、"
        "システムはその条件を unreferenced に含める shall。",

        "When 振る舞いのシナリオが同一文書内に実在しない識別子を指しているとき、"
        "システムはその組を dangling に含める shall。",

        "When 同一文書内で受け入れ条件の識別子が重複しているとき、"
        "システムはその識別子を duplicate_ids に含める shall。",

        "When 振る舞いのシナリオが満たす条件を1件も挙げていないとき、"
        "システムはそのシナリオを unlinked_scenarios に含める shall。",

        "When 振る舞いのシナリオが満たす条件の欄そのものを持たないとき、"
        "システムはそのシナリオを uncovered_by_omission に含める shall。",

        "While すべての受け入れ条件がいずれかの振る舞いのシナリオから指されているとき、"
        "システムは unreferenced を空配列で返す shall。",

        "While 走査範囲が指定されたとき、システムは配下のすべての仕様文書を対象にする shall。",
    ],
    "content.errors.items": [
        {"code": "INVALID_PATH",
         "condition": ["対象のパスが存在しない、またはパストラバーサルを含む"]},
    ],
    "content.acceptanceScenarios.background": "",
    "content.acceptanceScenarios.scenarios": [
        {"name": "どのシナリオからも指されていない条件を挙げる",
         "category": "異常系",
         "viewpoint": "宣言の突き合わせ：条件側から見た欠けを検出できるか",
         "gherkin": "Scenario: どのシナリオからも指されていない条件を挙げる\n"
                    "  Given 受け入れ条件を3件持ち、そのうち2件だけを指すシナリオを持つ仕様文書\n"
                    "  When 受け入れ条件の被覆を確かめる\n"
                    "  Then 指されていない1件が unreferenced に現れる",
         "covers": ""},

        {"name": "実在しない識別子を指しているシナリオを挙げる",
         "category": "異常系",
         "viewpoint": "参照の健全性：指す先が在るかを確かめられるか",
         "gherkin": "Scenario: 実在しない識別子を指しているシナリオを挙げる\n"
                    "  Given 同一文書内に無い識別子を指すシナリオを持つ仕様文書\n"
                    "  When 受け入れ条件の被覆を確かめる\n"
                    "  Then そのシナリオと識別子の組が dangling に現れる",
         "covers": ""},

        {"name": "重複した識別子を挙げる",
         "category": "異常系",
         "viewpoint": "参照の健全性：指す先が一意に定まるか",
         "gherkin": "Scenario: 重複した識別子を挙げる\n"
                    "  Given 同じ識別子を持つ受け入れ条件を2件持つ仕様文書\n"
                    "  When 受け入れ条件の被覆を確かめる\n"
                    "  Then その識別子が duplicate_ids に現れる",
         "covers": ""},

        {"name": "どの条件も挙げていないシナリオを挙げる",
         "category": "異常系",
         "viewpoint": "宣言の突き合わせ：シナリオ側から見た欠けを検出できるか",
         "gherkin": "Scenario: どの条件も挙げていないシナリオを挙げる\n"
                    "  Given 満たす条件を空で宣言したシナリオを持つ仕様文書\n"
                    "  When 受け入れ条件の被覆を確かめる\n"
                    "  Then そのシナリオが unlinked_scenarios に現れる",
         "covers": ""},

        {"name": "満たす条件の欄を持たないシナリオを挙げる",
         "category": "境界値",
         "viewpoint": "欠落と合格の区別：未記入を黙って対象外にしないか",
         "gherkin": "Scenario: 満たす条件の欄を持たないシナリオを挙げる\n"
                    "  Given 満たす条件の欄そのものを持たないシナリオを持つ仕様文書\n"
                    "  When 受け入れ条件の被覆を確かめる\n"
                    "  Then そのシナリオが uncovered_by_omission に現れる\n"
                    "  And unreferenced には現れない",
         "covers": ""},

        {"name": "すべて指されているときは欠けなしと判定する",
         "category": "正常系",
         "viewpoint": "宣言の突き合わせ：整合しているときに空で返るか",
         "gherkin": "Scenario: すべて指されているときは欠けなしと判定する\n"
                    "  Given すべての受け入れ条件がいずれかのシナリオから指されている仕様文書\n"
                    "  When 受け入れ条件の被覆を確かめる\n"
                    "  Then unreferenced が空で返る\n"
                    "  And dangling が空で返る",
         "covers": ""},

        {"name": "走査範囲を指定すると配下をまとめて確かめる",
         "category": "正常系",
         "viewpoint": "走査の範囲：複数の仕様文書を一度に対象にできるか",
         "gherkin": "Scenario: 走査範囲を指定すると配下をまとめて確かめる\n"
                    "  Given 指されていない条件を持つ仕様文書が2件ある走査範囲\n"
                    "  When その走査範囲で受け入れ条件の被覆を確かめる\n"
                    "  Then 2件とも unreferenced に現れる",
         "covers": ""},
    ],
    "content.operationGuarantees.items": [
        "When 対象のパスが存在しないとき、システムは INVALID_PATH エラーを返す shall"
        "（対象を特定し取得する解決プロセス自体の契約であり、複数のusecaseに共通する）。",
    ],
    "content.guaranteeScenarios.background": "",
    "content.guaranteeScenarios.scenarios": [
        {"name": "存在しないパスは受け付けない",
         "category": "異常系",
         "viewpoint": "解決プロセスの契約：対象を取得できないときの扱い",
         "gherkin": "Scenario: 存在しないパスは受け付けない\n"
                    "  Given 存在しないパス\n"
                    "  When 受け入れ条件の被覆を確かめる\n"
                    "  Then INVALID_PATH エラーが返る",
         "covers": ""},
    ],
    "content.operationIndex.items": [],
}

r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill",
                    "--path", PATH, "--values", json.dumps(values, ensure_ascii=False)],
                   capture_output=True, text=True, cwd=CWD)
print((r.stdout or r.stderr).strip()[:600])
print(run("validate", "--path", PATH)[:400])
