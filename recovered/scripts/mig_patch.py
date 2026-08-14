"""uc-patch-schema を v9 へ移し、enum 除去の互換検査と kind の取り消しを足す。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-schema-management/"
     "usecase/uc-patch-schema." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


# 既存31件へ、現行の並び順のまま識別子を与える
IDS = [
    "add-block", "add-block-idempotent", "rename-block", "rename-block-idempotent",
    "backward-incompatible-rejected", "invalid-schema-structure-rejected",
    "untouched-parts-unchanged", "set-field", "set-field-idempotent",
    "set-field-block-not-found", "write-error", "remove-block", "remove-block-idempotent",
    "remove-block-required-rejected", "add-def", "add-def-idempotent", "add-kind-branch",
    "add-kind-branch-normalizes-dispatch", "add-kind-branch-idempotent",
    "add-kind-branch-unsupported-shape", "create-version", "create-version-already-exists",
    "create-version-skips-compat-check", "set-kind-render-target",
    "set-kind-render-target-idempotent", "set-kind-render-target-unsupported-shape",
    "set-field-root-scope", "remove-field", "remove-field-idempotent",
    "remove-field-block-not-found", "remove-field-root-scope",
]

NEW_CRITERIA = [
    # 移設で表に出た欠け
    ("unknown-operation-rejected",
     "If 未知の operation が与えられたとき、システムは INVALID_OPERATION を返し書き込みを拒否する shall。"),
    # 互換検査の穴
    ("enum-value-removal-is-incompatible",
     "If 変更が種別の候補値（enum）の除去を含むとき、システムは BACKWARD_INCOMPATIBLE エラーを返し書き込みを拒否する shall"
     "（その候補値を指す既存Documentを壊しうるため。意図した破壊は create_version で新版として行う）。"),
    ("def-removal-is-incompatible",
     "If 変更が $defs エントリの除去を含み、そのエントリがどこかから参照されているとき、"
     "システムは BACKWARD_INCOMPATIBLE エラーを返し書き込みを拒否する shall。"),
    # 種別の取り消し
    ("remove-kind-branch",
     "When remove_kind_branch で discriminator フィールド名と kind 値が与えられたとき、システムは"
     "ルート直下の該当ブランチ・その enum 値・x-render-target のその kind のエントリを、"
     "ひとつの操作としてまとめて取り除く shall（半端に整合しない Schema を残さないため）。"),
    ("remove-kind-branch-idempotent",
     "While 対象の kind 値がどこにも存在しないとき、remove_kind_branch は無変更で成功する shall。"),
    ("remove-kind-branch-partial-not-left",
     "If remove_kind_branch の途中でいずれかの箇所を取り除けないとき、"
     "システムはどの箇所も取り除かずに返す shall。"),
]

SCEN_IDS = [
    ["add-block"], ["add-block-idempotent"], ["rename-block"], ["rename-block-idempotent"],
    ["backward-incompatible-rejected"], ["invalid-schema-structure-rejected"],
    ["untouched-parts-unchanged"], ["schema-ref-unresolvable"], ["unknown-operation-rejected"],
    ["set-field"], ["set-field-idempotent"], ["set-field-block-not-found"], ["write-error"],
    ["backward-incompatible-rejected"], ["backward-incompatible-rejected"],
    ["remove-block"], ["remove-block-idempotent"], ["remove-block-required-rejected"],
    ["add-def"], ["add-def-idempotent"], ["add-kind-branch-normalizes-dispatch"],
    ["add-kind-branch"], ["add-kind-branch-idempotent"], ["add-kind-branch-unsupported-shape"],
    ["create-version"], ["create-version-skips-compat-check"], ["create-version-already-exists"],
    ["set-kind-render-target"], ["set-kind-render-target-idempotent"],
    ["set-kind-render-target-unsupported-shape"], ["set-field-root-scope"],
    ["remove-field"], ["remove-field-idempotent"], ["remove-field-block-not-found"],
    ["remove-field-root-scope"],
]


def sc(name, cat, view, sat, given, when, then):
    return {"name": name, "category": cat, "viewpoint": view, "satisfies": sat,
            "gherkin": f"Scenario: {name}\n  Given {given}\n  When {when}\n  Then {then}"}


NEW_SCEN = [
    sc("種別の候補値の除去は後方互換を壊すものとして拒まれる", "異常系",
       "互換の検査：候補値の除去が検査を素通りしないか",
       ["enum-value-removal-is-incompatible"],
       "3つの候補値を持つ種別の欄", "remove_field でその候補値のうち1つを取り除く",
       "BACKWARD_INCOMPATIBLE が返り、Schema は変わらない"),
    sc("参照されている定義の除去は後方互換を壊すものとして拒まれる", "異常系",
       "互換の検査：参照されたまま定義が消えないか",
       ["def-removal-is-incompatible"],
       "どこかから参照されている $defs エントリ", "remove_field でそのエントリを取り除く",
       "BACKWARD_INCOMPATIBLE が返り、Schema は変わらない"),
    sc("種別の取り消しは分岐と候補値と描画先を同時に取り除く", "正常系",
       "取り消しの原子性：整合したまま消せるか",
       ["remove-kind-branch"],
       "分岐・候補値・描画先の3箇所に現れている kind 値",
       "その kind を remove_kind_branch する",
       "3箇所すべてから取り除かれ、残った Schema は構文的にも整合している"),
    sc("既に無い種別の取り消しは無変更で成功する", "境界値",
       "取り消しの原子性：繰り返しても結果が変わらないか",
       ["remove-kind-branch-idempotent"],
       "どこにも存在しない kind 値", "その kind を remove_kind_branch する",
       "無変更で成功する"),
    sc("一部を取り除けないときは何も取り除かない", "異常系",
       "取り消しの原子性：半端に整合しない Schema を残さないか",
       ["remove-kind-branch-partial-not-left"],
       "分岐と候補値には現れるが、描画先の形が既知でない Schema",
       "その kind を remove_kind_branch する",
       "エラーが返り、分岐も候補値も取り除かれていない"),
    sc("新版を作るときは候補値を取り除ける", "境界値",
       "互換の検査：意図した破壊の道が塞がっていないか",
       ["create-version-skips-compat-check"],
       "候補値の除去を含む edits", "create_version で新しい版を作る",
       "BACKWARD_INCOMPATIBLE にならず、新版が書き出される"),
]

GUARANTEES = [
    ("add-block-idempotent-op", "When 同じadd_block操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("rename-block-idempotent-op", "When 同じrename_block操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("set-field-idempotent-op", "When 同じset_field操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("remove-block-idempotent-op", "When 同じremove_block操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("add-def-idempotent-op", "When 同じadd_def操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("add-kind-branch-idempotent-op", "When 同じadd_kind_branch操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("set-kind-render-target-idempotent-op", "When 同じset_kind_render_target操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("minimal-diff", "While 対象外の箇所が既に整形契約に従っているとき、書き込み後もその箇所は一切変更されない shall（最小diff）。"),
    ("remove-field-idempotent-op", "When 同じremove_field操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("remove-kind-branch-idempotent-op", "When 同じremove_kind_branch操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("schema-ref-unresolvable", "When 対象のschemaRefを解決できないとき、システムは INVALID_SCHEMA_REF エラーを返す shall（schemaを特定し取得する解決プロセス自体の契約であり、複数のusecaseに共通する）。"),
]

print(run("scaffold", "--operation", "migrate_schema", "--path", P,
          "--schemaRef", "DomainSpecSchema/v9")[:160])

old_c = json.loads(run("query", "--operation", "query_path", "--path", P,
                       "--blockKey", "acceptanceCriteria", "--expression", "items"))["value"]
assert len(old_c) == len(IDS), (len(old_c), len(IDS))
criteria = [{"id": i, "text": t} for i, t in zip(IDS, old_c)]
criteria += [{"id": i, "text": t} for i, t in NEW_CRITERIA]

cur = json.loads(run("query", "--operation", "query_path", "--path", P,
                     "--blockKey", "acceptanceScenarios", "--expression", "scenarios"))["value"]
assert len(cur) == len(SCEN_IDS), (len(cur), len(SCEN_IDS))
out = []
for s, ids in zip(cur, SCEN_IDS):
    s = dict(s)
    s.pop("covers", None)
    s["satisfies"] = ids
    out.append(s)
out.extend(NEW_SCEN)

vals = {
    "content.acceptanceCriteria.items": criteria,
    "content.acceptanceScenarios.scenarios": out,
    "content.operationGuarantees.items": [{"id": i, "text": t} for i, t in GUARANTEES],
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:300])
print(run("validate", "--path", P)[:400])
print(f"基準 {len(criteria)} / シナリオ {len(out)}")
