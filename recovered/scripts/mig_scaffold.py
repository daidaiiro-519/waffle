"""uc-scaffold-document を v9 へ移し、要素単位の編集の基準を足す。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/"
     "usecase/uc-scaffold-document." + "json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


# 既存14件（順序は現行のまま）＋ 移設で表に出た欠け4件 ＋ 要素単位の編集9件
CRITERIA = [
    ("skeleton-conforms-to-schema",
     "When schemaRef と documentId が与えられたとき、システムは schema に適合する骨格を生成する shall（status=schema の enum 先頭）。"),
    ("fill-writes-declared-fields-only",
     "When fill で値が与えられたとき、システムは宣言済み値フィールドにのみ書き込む shall。"),
    ("rejects-structure-changing-values",
     "If 構造を変える値や const / discriminator が与えられたとき、システムは拒否し skipped に記録する shall。"),
    ("missing-discriminator",
     "If 分岐のある schema で discriminator が無いとき、システムは MISSING_DISCRIMINATOR を返し候補を案内する shall。"),
    ("invalid-discriminator",
     "If 分岐のある schema で discriminator の値が候補enumに存在しないとき、システムは INVALID_DISCRIMINATOR を返し候補を案内する shall。"),
    ("clear-field-removes",
     "When clear_fieldでdocumentPath・fieldPathが与えられたとき、システムはその値フィールドをdocumentから削除する shall。"),
    ("clear-field-idempotent",
     "While 削除対象のフィールドが既に存在しないとき、clear_fieldは無変更で成功する shall。"),
    ("clear-field-protects-required",
     "If clear_fieldの削除対象が必須フィールドであるとき、システムはREQUIRED_FIELDエラーを返し削除を拒否する shall。"),
    ("migrate-rewrites-schema-ref",
     "When migrate_schemaでdocumentPath・schemaRef（移行先）が与えられたとき、システムはDocumentのschemaRefをその値へ書き換える shall。"),
    ("migrate-idempotent",
     "While Documentのschemaが既に目的のschemaRefであるとき、migrate_schemaは無変更で成功する shall。"),
    ("migrate-invalid-schema-ref",
     "If migrate_schemaの移行先schemaRefが解決できないとき、システムはINVALID_SCHEMA_REFエラーを返し書き換えを拒否する shall。"),
    ("create-resolves-latest-version",
     "When createで版を含まないschemaRefが与えられたとき、システムはその名前の最新の版へ解決して骨格を生成する shall（指示や手順に版を書かせないため。書かれた版はschemaが上がった瞬間から古い版を指す）。"),
    ("create-rejects-outdated-version",
     "If createで最新でない版のschemaRefが明示されたとき、システムはOUTDATED_SCHEMA_REFエラーを返し骨格を生成しない shall（最新以外の版で新しいdocumentを作る用途を持たないため）。"),
    ("migrate-accepts-any-version",
     "While migrate_schemaに移行先のschemaRefが与えられたとき、システムはその版が最新かどうかを問わず書き換える shall（既存documentを段階的に運ぶ操作であり、createの制限をここへ持ち込むと移行の道が塞がるため）。"),

    # ── 移設で表に出た、シナリオが指していたのに存在しなかった基準 ──
    ("reports-actual-write-result",
     "When 書き込みを終えたとき、システムは実際に書き込んだ欄だけを written に、書き込まなかった欄を skipped に記録する shall（書き込み結果を偽らない）。"),
    ("create-persists-skeleton",
     "When create が骨格を生成したとき、システムは schema が宣言する置き場所へ骨格を書き出し、create に渡された参照パラメータを document 本体にも書き込む shall。"),
    ("fill-template-carries-guidance",
     "When create が骨格を生成したとき、システムは記入対象の道とその執筆ガイダンスを fillTemplate として返す shall（content の外にあるトップレベルの欄も含む）。"),
    ("creates-missing-block-kind",
     "When まだ存在しないブロックの中の欄へ書き込むとき、システムはそのブロックの種別も一緒に作り、書き込んだ結果が schema に適合する状態にする shall。"),

    # ── ここから、配列の要素単位の編集 ──
    ("element-add",
     "When 鍵を宣言した配列へ add_element で要素が与えられたとき、システムは既存の要素を読み込ませることなく、その要素を配列の末尾へ加える shall。"),
    ("element-edit",
     "When 鍵を宣言した配列へ edit_element で鍵と欄の値が与えられたとき、システムはその鍵を持つ要素の指定された欄だけを書き換え、鍵は変えない shall。"),
    ("element-retire",
     "When 鍵を宣言した配列へ retire_element で鍵が与えられ、その鍵を指す参照がどこにも残っていないとき、システムはその要素を配列から取り除く shall。"),
    ("retire-blocked-by-reference",
     "If retire_element の対象の鍵を指す参照が Document の中に残っているとき、システムは PRECONDITION_NOT_MET を返し、参照している場所を示して取り除かない shall。"),
    ("unknown-element-key-fails",
     "If 指定された鍵を持つ要素が配列に存在しないとき、システムは UNKNOWN_ELEMENT_KEY を返し、要素を新たに作らない shall。"),
    ("rejects-wholesale-replace-on-declared-array",
     "If 鍵を宣言した配列に対して fill で配列全体が与えられたとき、システムは WHOLESALE_REPLACE_NOT_ALLOWED を返し、使うべき要素操作を案内して書き込まない shall。"),
    ("element-ops-are-atomic",
     "If 複数の要素操作のうち1つでも受け付けられないとき、システムはどの操作も適用せずに返す shall。"),
    ("element-add-fills-const",
     "When 要素を加えるとき、システムは schema がその要素に宣言する固定値を補って、書き込んだ結果が schema に適合する状態にする shall。"),
    ("ordered-array-rejects-element-ops",
     "If 順序そのものが意味を持つと宣言された配列へ要素操作が与えられたとき、システムは ELEMENT_OPS_NOT_APPLICABLE を返し、その配列は丸ごと置き換えて書き換えるものだと案内する shall。"),
    ("undeclared-array-keeps-wholesale",
     "While 配列が鍵も順序も宣言していないとき、システムは従来どおり fill による丸ごとの置き換えを受け付ける shall。"),
]

# 既存27シナリオ → 満たす基準
MAP = {
    "生成した骨格は自分の schema で valid": ["skeleton-conforms-to-schema"],
    "構造を変える値は拒否される": ["rejects-structure-changing-values"],
    "宣言済みの値フィールドに書き込まれる": ["fill-writes-declared-fields-only"],
    "discriminator が無いと候補を案内する": ["missing-discriminator"],
    "createはadvisor_skillの骨格を生成する": ["skeleton-conforms-to-schema"],
    "createはx_source_targetに骨格を書き出す": ["create-persists-skeleton"],
    "fillTemplateは値フィールドのpathとprompt_x_prompt_writeを持つ": ["fill-template-carries-guidance"],
    "customはadvisorと構成が異なる": ["skeleton-conforms-to-schema"],
    "宣言済みの値フィールドを削除する": ["clear-field-removes"],
    "既に存在しないフィールドのclear_fieldは無変更で成功する": ["clear-field-idempotent"],
    "必須フィールドのclear_fieldはREQUIRED_FIELDとして拒否される": ["clear-field-protects-required"],
    "不正なdiscriminator値はINVALID_DISCRIMINATOR": ["invalid-discriminator"],
    "migrate_schemaはschemaRefを新版へ書き換える": ["migrate-rewrites-schema-ref"],
    "migrate_schemaは同じ版への書き換えに対して冪等である": ["migrate-idempotent"],
    "migrate_schemaは解決できないschemaRefをINVALID_SCHEMA_REFとして拒否する": ["migrate-invalid-schema-ref"],
    "constフィールドは現行schemaの宣言値と完全一致する場合のみ再同期できる": ["rejects-structure-changing-values"],
    "createに渡した参照パラメータはdocument本体にも書き込まれる": ["create-persists-skeleton"],
    "fillTemplateにはcontent外のトップレベルのx-prompt-writeフィールドも含まれる": ["fill-template-carries-guidance"],
    "fillはcontent外のトップレベルのx-prompt-writeフィールドにも書き込める": ["fill-writes-declared-fields-only"],
    "fillはdocumentIdとdiscriminatorキーへの書き込みを拒否する": ["rejects-structure-changing-values"],
    "schema版が変わった後に新設された任意ブロックも既存documentへ書き込める": ["fill-writes-declared-fields-only"],
    "書き込み単位でない欄を指すと何も書き込まない": ["reports-actual-write-result"],
    "宣言に無い欄を指すと何も書き込まない": ["reports-actual-write-result"],
    "ブロックがまだ無い欄へ書くと種別も一緒に作られる": ["creates-missing-block-kind"],
    "版を省けば最新の版で作られる": ["create-resolves-latest-version"],
    "古い版を明示したら作らせない": ["create-rejects-outdated-version"],
    "必須ブロックの中にある必須でない欄は削除できる": ["clear-field-removes"],
}


def sc(name, cat, view, sat, given, when, then):
    return {"name": name, "category": cat, "viewpoint": view, "satisfies": sat,
            "gherkin": f"Scenario: {name}\n  Given {given}\n  When {when}\n  Then {then}"}


NEW = [
    sc("要素を1件足すのに既存を読み込ませない", "正常系",
       "要素の同一性：足す操作が、配列全体を経由せずに済むか",
       ["element-add"],
       "受け入れ基準を3件持つ Document", "基準を1件 add_element で加える",
       "配列は4件になり、既存の3件はそのまま残る"),
    sc("要素の欄を直しても鍵は変わらない", "正常系",
       "要素の同一性：直すことと別物に置き換えることを取り違えないか",
       ["element-edit"],
       "鍵 conformant-is-validated を持つ要素がある Document",
       "その鍵を指して text だけを edit_element で書き換える",
       "text だけが変わり、鍵と他の要素は変わらない"),
    sc("参照が残っていない要素は取り下げられる", "正常系",
       "取り下げの前提：参照が外れていれば通るか",
       ["element-retire"],
       "どのシナリオからも指されていない受け入れ基準",
       "その鍵を指して retire_element する",
       "その要素が配列から取り除かれる"),
    sc("参照が残っている要素は取り下げられない", "異常系",
       "取り下げの前提：宣言された参照関係から可否が導かれるか",
       ["retire-blocked-by-reference"],
       "あるシナリオの satisfies から指されている受け入れ基準",
       "その鍵を指して retire_element する",
       "PRECONDITION_NOT_MET が返り、参照しているシナリオが示され、要素は残る"),
    sc("存在しない鍵を指すと失敗する", "異常系",
       "要素の同一性：指し間違いを、黙って足すことで埋めないか",
       ["unknown-element-key-fails"],
       "その鍵を持つ要素が無い配列", "その鍵を指して edit_element する",
       "UNKNOWN_ELEMENT_KEY が返り、要素は増えない"),
    sc("鍵を宣言した配列は丸ごと置き換えられない", "異常系",
       "取りこぼしの遮断：取りこぼす手順そのものへ入れないか",
       ["rejects-wholesale-replace-on-declared-array"],
       "鍵を宣言した受け入れ基準の配列",
       "fill でその配列へ要素の並びを丸ごと渡す",
       "WHOLESALE_REPLACE_NOT_ALLOWED が返り、使うべき要素操作が案内され、何も書き込まれない"),
    sc("1つでも受け付けられない要素操作があれば何も適用しない", "異常系",
       "原子性：途中まで適用された状態を残さないか",
       ["element-ops-are-atomic"],
       "3件の要素操作のうち1件が存在しない鍵を指している",
       "3件をまとめて適用する",
       "どの操作も適用されず、配列は操作前のまま"),
    sc("要素を足すと固定値も補われる", "正常系",
       "適合の保持：書き込みが成功と報告されて不適合が残ることを防げるか",
       ["element-add-fills-const"],
       "要素に固定値の欄を宣言している配列",
       "固定値の欄を含めずに要素を add_element で加える",
       "固定値が補われ、書き込んだ結果が schema に適合する"),
    sc("順序が意味を持つ配列に要素操作は使えない", "異常系",
       "並びの扱い：並び全体が1つの値である配列を、要素へ分解させないか",
       ["ordered-array-rejects-element-ops"],
       "順序そのものが意味を持つと宣言された手順の配列",
       "その配列へ add_element する",
       "ELEMENT_OPS_NOT_APPLICABLE が返り、丸ごと置き換えて書き換えるものだと案内される"),
    sc("何も宣言していない配列は今までどおり書き換えられる", "境界値",
       "並びの扱い：宣言していない配列の書き換え方を変えていないか",
       ["undeclared-array-keeps-wholesale"],
       "鍵も順序も宣言していない配列",
       "fill でその配列へ並びを丸ごと渡す",
       "従来どおり書き込まれる"),
]

GUARANTEES = [
    ("create-idempotent-structure",
     "When 同じ documentId で create を複数回実行したとき、システム の生成する構造（schema由来の骨格の形）は常にべき等である shall。"),
    ("create-preserves-existing-values",
     "While document.json が既に存在するとき、create を再実行しても、fill で書き込まれた既存の values は保持され、破壊されない shall（values 自体の再現性はシステムの管轄外・呼び出し側の責務）。"),
    ("path-not-found",
     "When 対象パスが存在しないとき、システムは INVALID_PATH エラーを返す shall（対象を特定し取得する解決プロセス自体の契約であり、複数のusecaseに共通する）。"),
    ("schema-ref-unresolvable",
     "When 対象のschemaRefを解決できないとき、システムは INVALID_SCHEMA_REF エラーを返す shall（schemaを特定し取得する解決プロセス自体の契約であり、複数のusecaseに共通する）。"),
    ("clear-field-idempotent-op",
     "When 同じclear_field操作を複数回実行したとき、システムの生成する結果は常にべき等である shall。"),
    ("element-ops-target-document",
     "When 要素操作が与えられたとき、システムは常に Document 全体を対象として読み書きし、要素だけを切り離して指させない shall。"),
]

print(run("scaffold", "--operation", "migrate_schema", "--path", P,
          "--schemaRef", "DomainSpecSchema/v9")[:200])

cur = json.loads(run("query", "--operation", "query_path", "--path", P,
                     "--blockKey", "acceptanceScenarios",
                     "--expression", "scenarios"))["value"]
out = []
missing = []
for s in cur:
    s = dict(s)
    ids = MAP.get(s["name"])
    if not ids:
        missing.append(s["name"])
        continue
    s.pop("covers", None)
    s["satisfies"] = ids
    out.append(s)
if missing:
    print("  対応づけできないシナリオ:", missing)
out.extend(NEW)

vals = {
    "content.acceptanceCriteria.items": [{"id": i, "text": t} for i, t in CRITERIA],
    "content.acceptanceScenarios.scenarios": out,
    "content.operationGuarantees.items": [{"id": i, "text": t} for i, t in GUARANTEES],
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:300])
print(run("validate", "--path", P)[:400])
print(f"基準 {len(CRITERIA)} / シナリオ {len(out)}")
