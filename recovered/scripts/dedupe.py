"""uc-scaffold-document から、業務サービスが持つ意味論を抜く。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/"
     "usecase/uc-scaffold-document." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(block, expr="@"):
    return json.loads(run("query", "--operation", "query_path", "--path", P,
                          "--blockKey", block, "--expression", expr))["value"]


crit = q("acceptanceCriteria", "items")
by_id = {c["id"]: c for c in crit}

# 文言から ds の意味論を抜き、uc にしか言えないことだけを残す
by_id["element-add"]["text"] = (
    "When 鍵を宣言した配列へ add_element で要素が与えられたとき、"
    "システムは既存の要素を一度も読み込ませることなく、その要素を加える shall"
    "（読み出して組み立て直す手順を挟まないことが、この操作の目的そのもの）。")

by_id["element-retire"]["text"] = (
    "When 鍵を宣言した配列へ retire_element で鍵が与えられたとき、システムは"
    "宣言された参照をたどってその鍵が指されていないことを確かめてから、取り下げを適用する shall。")

by_id["element-add-fills-const"]["text"] = (
    "When 要素を加えるとき、システムは schema がその要素に宣言する固定値を集めて渡し、"
    "書き込んだ結果が schema に適合する状態にする shall。")

by_id["element-ops-are-atomic"]["text"] = (
    "If 複数の要素操作のうち1つでも受け付けられないとき、システムはどの操作も適用せず、"
    "Document へ何も保存しない shall"
    "（配列の中で起きる失敗だけでなく、順序配列の拒否・丸ごと置き換えの拒否・"
    "宣言の誤りなど、配列の外で起きる失敗も含む）。")

by_id["unknown-element-key-fails"]["text"] = (
    "If 要素操作が、指定された鍵を持つ要素が無いために適用できなかったとき、"
    "システムは UNKNOWN_ELEMENT_KEY を返す shall。")

# element-edit は uc にしか言えない部分を持たないので落とす
crit = [c for c in crit if c["id"] != "element-edit"]

# 落とすと主張が消える「保存されること」を、uc 固有の基準として起こす
crit.append({
    "id": "element-ops-are-persisted",
    "text": "When 要素操作がすべて受け付けられたとき、システムは書き換えた配列を Document へ保存し、"
            "その配列の道を written に記録する shall。"})

# シナリオ：element-edit のものを落とし、保存の筋書きを起こす
scen = [s for s in q("acceptanceScenarios", "scenarios")
        if "element-edit" not in (s.get("satisfies") or [])]
scen.append({
    "name": "受け付けられた要素操作は Document に残る",
    "category": "正常系",
    "viewpoint": "保存：書き換えた配列が、実際に Document へ書き戻されるか",
    "satisfies": ["element-ops-are-persisted"],
    "gherkin": "Scenario: 受け付けられた要素操作は Document に残る\n"
               "  Given 鍵を宣言した配列を持つ Document\n"
               "  When 要素を1件 add_element する\n"
               "  Then 再び読み込んでもその要素が残っており、"
               "written にその配列の道が記録されている"})

print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps({"content.acceptanceCriteria.items": crit,
                                  "content.acceptanceScenarios.scenarios": scen},
                                 ensure_ascii=False))[:200])
print(run("validate", "--path", P)[:250])
print(f"基準 {len(crit)} / シナリオ {len(scen)}")
