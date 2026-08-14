"""検証で出た矛盾に沿って uc-patch-schema を直す。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-schema-management/"
     "usecase/uc-patch-schema." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(block, expr="@"):
    return json.loads(run("query", "--operation", "query_path", "--path", P,
                          "--blockKey", block, "--expression", expr))["value"]


crit = q("acceptanceCriteria", "items")
by_id = {c["id"]: c for c in crit}

# ── 矛盾の解消：互換の関門を通らない操作を明示列挙する ──
by_id["enum-value-removal-is-incompatible"]["text"] = (
    "If 互換の関門を通る操作の変更が、種別の候補値（enum）の除去を含むとき、"
    "システムは BACKWARD_INCOMPATIBLE エラーを返し書き込みを拒否する shall"
    "（その候補値を指す既存Documentを壊しうるため）。")

by_id["remove-kind-branch"]["text"] = (
    "When remove_kind_branch で discriminator フィールド名と kind 値が与えられたとき、システムは"
    "ルート直下の該当ブランチ・その enum 値・x-render-target のその kind のエントリを、"
    "ひとつの操作としてまとめて取り除く shall（半端に整合しない Schema を残さないため）。"
    "この操作は種別を捨てることそのものを目的とするため、互換の関門を通らない。")

# ── 免除の規律と、免除される操作が何を壊すのかを、基準として書く ──
NEW = [
    ("compat-gate-exemptions-are-enumerated",
     "While ある操作が互換の関門を通らないとき、システムはその操作を免除された操作として明示的に列挙し、"
     "その操作自身の基準で何を壊してよいかを述べる shall"
     "（免除が暗黙に増えると、関門があるという主張そのものが意味を失うため）。"),
    ("remove-kind-branch-breaks-existing-documents",
     "While remove_kind_branch が種別を取り除くとき、システムはその種別を指す既存Documentが"
     "壊れることを、この操作の結果として認める shall。"
     "実際にそのようなDocumentが残っていないかの確認は、schema版のドリフトを見る側の責務であり、"
     "この操作は行わない（Schemaを編集する操作にDocumentの走査を持ち込まないため）。"),
    ("remove-kind-branch-requires-normalized-dispatch",
     "If remove_kind_branch の対象のルート直下の分岐が if/then/else 形式であるとき、"
     "システムは UNSUPPORTED_ROOT_DISPATCH_SHAPE を返し取り除かない shall"
     "（片方を取り除くと残った else が全ての種別を受けてしまい、構造が壊れるため。"
     "先に add_kind_branch で allOf 形式へ正規化することを求める）。"),
    ("remove-kind-branch-keeps-allof-shape",
     "While remove_kind_branch のあと分岐が1つだけ残るとき、システムは allOf 形式のまま残す shall"
     "（if/then/else 形式へ戻すと、次の取り消しが上の基準で塞がるため）。"),
]
for i, t in NEW:
    crit.append({"id": i, "text": t})

# ── 原子性の失敗に、返る名を与える ──
by_id["remove-kind-branch-partial-not-left"]["text"] = (
    "If remove_kind_branch の途中でいずれかの箇所を取り除けないとき、"
    "システムはどの箇所も取り除かずに、その箇所に対応するエラー"
    "（描画先の形が既知でないときは UNSUPPORTED_RENDER_TARGET_SHAPE、"
    "ルート直下の分岐の形が既知でないときは UNSUPPORTED_ROOT_DISPATCH_SHAPE）を返す shall。")

# ── シナリオの手当て ──
scen = q("acceptanceScenarios", "scenarios")
by_name = {s["name"]: s for s in scen}


def gherkin(name, given, when, then):
    return f"Scenario: {name}\n  Given {given}\n  When {when}\n  Then {then}"


n = "一部を取り除けないときは何も取り除かない"
by_name[n]["gherkin"] = gherkin(
    n, "分岐と候補値には現れるが、描画先の形が既知でない Schema",
    "その kind を remove_kind_branch する",
    "UNSUPPORTED_RENDER_TARGET_SHAPE が返り、分岐も候補値も取り除かれていない")

n = "新版を作るときは候補値を取り除ける"
by_name[n]["gherkin"] = gherkin(
    n, "候補値を短くした enum を set_field で書き込む edits",
    "create_version で新しい版を作る",
    "BACKWARD_INCOMPATIBLE にならず、候補値の減った新版が書き出される")


def sc(name, cat, view, sat, given, when, then):
    return {"name": name, "category": cat, "viewpoint": view, "satisfies": sat,
            "gherkin": gherkin(name, given, when, then)}


scen += [
    sc("種別の取り消しは互換の関門を通らない", "境界値",
       "免除の規律：取り消しが自分の生んだ候補値の除去に自分で拒まれないか",
       ["remove-kind-branch", "compat-gate-exemptions-are-enumerated"],
       "allOf 形式の分岐を3つ持ち、そのうち1つを取り消す Schema",
       "remove_kind_branch する",
       "BACKWARD_INCOMPATIBLE にならず、3箇所から取り除かれる"),
    sc("取り消される種別を指す既存Documentは壊れる", "境界値",
       "免除の規律：免除された操作が何を壊すかが宣言されているか",
       ["remove-kind-branch-breaks-existing-documents"],
       "取り消す種別を指している既存Document",
       "その種別を remove_kind_branch する",
       "取り消しは成功し、そのDocumentが不適合になったことは"
       "schema版のドリフトを見る側で検知される"),
    sc("正規化されていない分岐からは取り消せない", "異常系",
       "分岐の形：残った else が全種別を受ける壊れ方を防げるか",
       ["remove-kind-branch-requires-normalized-dispatch"],
       "ルート直下が if/then/else 形式の Schema",
       "その kind を remove_kind_branch する",
       "UNSUPPORTED_ROOT_DISPATCH_SHAPE が返り、Schema は変わらない"),
    sc("分岐が1つだけ残っても allOf 形式のまま残る", "境界値",
       "分岐の形：次の取り消しの道を塞がないか",
       ["remove-kind-branch-keeps-allof-shape"],
       "allOf 形式の分岐を2つ持つ Schema",
       "片方を remove_kind_branch する",
       "残った1つは allOf 形式のまま置かれている"),
]

errors = q("errors", "items")
vals = {
    "content.acceptanceCriteria.items": crit,
    "content.acceptanceScenarios.scenarios": scen,
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:300])
print(run("validate", "--path", P)[:300])
print(f"基準 {len(crit)} / シナリオ {len(scen)}")
