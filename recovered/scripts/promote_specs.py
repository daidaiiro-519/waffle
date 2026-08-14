"""検証だけが守っていた振る舞いを、仕様の宣言へ引き上げる。

ddd-advisor の判定に従う。基準を足さずにシナリオだけ足すと、紐づけ先の無い
筋書きになる——既に1件その形が壊れている（下の FIX）。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
UC = ".waffle/documents/specs/bc-artifact-share/subdomain/sd-artifact-sharing/usecase"


def q(path: str, block: str, expr: str = "@"):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", path, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


def fill(path: str, values: dict) -> None:
    r = subprocess.run(
        ["uv", "run", "waffle", "scaffold", "--operation", "fill",
         "--path", path, "--values", json.dumps(values, ensure_ascii=False)],
        capture_output=True, text=True, cwd=CWD)
    out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {"raw": r.stdout}
    name = path.rsplit("/", 1)[-1]
    print(f"  {name}: {out.get('written', out)}")
    if r.stderr.strip():
        print("   STDERR:", r.stderr[:200])


def add(path: str, block: str, key: str, items: list) -> None:
    """宣言の並びへ足す。現在値を取ってから丸ごと置き換える。"""
    current = q(path, block, key)
    fill(path, {f"content.{block}.{key}": current + items})


print("── コメントの読み出し ──")
P = f"{UC}/uc-read-comments.json"
add(P, "acceptanceCriteria", "items", [
    "管理者が求めたとき、自分が投稿者でない共有アーティファクトのコメントも返すこと",
    "If 読めない記録があるとき、それを飛ばして残りを返し、飛ばした件数を添えること",
])
add(P, "acceptanceScenarios", "scenarios", [
    {"name": "管理者は他人のものも読める", "category": "正常系",
     "viewpoint": "事前条件: 読める範囲が、管理者にだけ自分のもの以外へ広がることを確かめる。拒む側の筋書きは既にあるが、許す側が無かった",
     "gherkin": "Scenario: 管理者は他人のものも読める\n  Given Aの投稿者はXである\n  When 管理者がAのコメントを読み出す\n  Then 寄せられたコメントが返る",
     "covers": "管理者が求めたとき、自分が投稿者でない共有アーティファクトのコメントも返すこと"},
    {"name": "読めない記録があっても残りが返る", "category": "異常系",
     "viewpoint": "部分的な失敗。1件の不具合でその共有アーティファクトの反応がすべて見えなくなることを避ける。黙って落とすと、投稿者は『これで全部だ』と思い込む",
     "gherkin": "Scenario: 読めない記録があっても残りが返る\n  Given Aに3件の記録があり、うち1件が読めない状態になっている\n  When Xが読み出しを求める\n  Then 読める2件が返る\n  And 読めなかった件数が1と伝わる",
     "covers": "If 読めない記録があるとき、それを飛ばして残りを返し、飛ばした件数を添えること"},
])

print("── プロジェクトへの出し入れ ──")
P = f"{UC}/uc-assign-to-project.json"
add(P, "acceptanceCriteria", "items", [
    "入れられる単位の数が上限に達しているとき、それ以上入れないこと",
])
add(P, "errors", "items", [
    {"code": "TOO_MANY_PROJECTS",
     "condition": ["入れられる単位の数が上限に達している"]},
])
add(P, "acceptanceScenarios", "scenarios", [
    {"name": "上限を超えてプロジェクトへ加えられない", "category": "境界値",
     "viewpoint": "境界値: 上限は書き手の側だけが守る。閲覧の面は先頭から決まった数しか見ないため、超過を許すと投稿者には成功が返り、閲覧者だけが開けない状態になる",
     "gherkin": "Scenario: 上限を超えてプロジェクトへ加えられない\n  Given 共有アーティファクトAが上限の数だけプロジェクトに入っている\n  When Aをもう1つのプロジェクトへ加えようとする\n  Then TOO_MANY_PROJECTS として拒まれる",
     "covers": "入れられる単位の数が上限に達しているとき、それ以上入れないこと"},
])

print("── 中身の差し替え ──")
P = f"{UC}/uc-replace-content.json"
add(P, "acceptanceCriteria", "items", [
    "If 差し替えようとする中身が空であるとき、差し替えないこと",
])
add(P, "acceptanceScenarios", "scenarios", [
    {"name": "空の中身には差し替えられない", "category": "異常系",
     "viewpoint": "事前条件: 中身が空のまま差し替わると、渡した相手には何も無いものが見える。公開のときと同じ扱いにする",
     "gherkin": "Scenario: 空の中身には差し替えられない\n  Given 共有アーティファクトAが公開されている\n  When 空の中身で差し替えようとする\n  Then EMPTY_CONTENT として拒まれる\n  And それまでの中身は変わらない",
     "covers": "If 差し替えようとする中身が空であるとき、差し替えないこと"},
])

print("── プロジェクトを作る ──")
P = f"{UC}/uc-create-project.json"
add(P, "acceptanceCriteria", "items", [
    "If 想定していない出し入れの範囲が示されたとき、作らないこと",
])
add(P, "acceptanceScenarios", "scenarios", [
    {"name": "想定外の共有の別では作らない", "category": "異常系",
     "viewpoint": "事前条件: 出し入れの範囲は作るときにしか決められない。想定外の値のまま作ると、誰が出し入れしてよいかが決まらないまま渡ってしまう",
     "gherkin": "Scenario: 想定外の共有の別では作らない\n  Given 個人でも共有でもない範囲が示されている\n  When プロジェクトを作ろうとする\n  Then SCOPE_REQUIRED として拒まれる",
     "covers": "If 想定していない出し入れの範囲が示されたとき、作らないこと"},
])

print("── 投稿者を招く ──")
P = f"{UC}/uc-invite-publisher.json"
add(P, "operationGuarantees", "items", [
    "招いた人を指す識別子が、名簿の一覧が返すものと同じであること",
])
add(P, "guaranteeScenarios", "scenarios", [
    {"name": "招待が返す識別子は一覧のものと揃っている", "category": "正常系",
     "viewpoint": "同一性: 招くことと見渡すことは別の操作だが、同じ人を同じ識別子で指す。揃っていないと、招いた直後にその人を引き継ぎ先として指せない",
     "gherkin": "Scenario: 招待が返す識別子は一覧のものと揃っている\n  Given 管理者がある宛先の人を招く\n  When 続けて招かれている人を見渡す\n  Then 招待が返した識別子と、一覧に並ぶその人の識別子が一致する"},
])

print("── 自分のものを見渡す ──")
P = f"{UC}/uc-list-my-artifacts.json"
add(P, "acceptanceCriteria", "items", [
    "管理者に返すとき、それぞれを公開した人が分かる形で返すこと",
])
add(P, "acceptanceScenarios", "scenarios", [
    {"name": "差し替えの区切りはコメントの件数に数えない", "category": "境界値",
     "viewpoint": "境界値: 区切りは反応と同じ並びに載るが、反応そのものではない。同じものが2つの操作で逆の扱いを受けるので、その違いを宣言に残す",
     "gherkin": "Scenario: 差し替えの区切りはコメントの件数に数えない\n  Given 共有アーティファクトAに2件のコメントがあり、一度差し替えられている\n  When 投稿者Xが見渡しを求める\n  Then 添えられる反応の件数は2である",
     "covers": "各共有アーティファクトに寄せられた反応の件数を添えること"},
])

print("── 既に壊れている紐づけを直す ──")
P = f"{UC}/uc-publish-artifact.json"
scenarios = q(P, "acceptanceScenarios", "scenarios")
hit = [s for s in scenarios if s["name"] == "空の文書は公開できない"]
if hit:
    print("   直す前の covers:", hit[0]["covers"])
    hit[0]["covers"] = "If 渡された文書が空であるとき、公開しないこと"
    criteria = q(P, "acceptanceCriteria", "items")
    if hit[0]["covers"] not in criteria:
        fill(P, {"content.acceptanceCriteria.items": criteria + [hit[0]["covers"]]})
    fill(P, {"content.acceptanceScenarios.scenarios": scenarios})
else:
    print("   『空の文書は公開できない』が見つかりません")
