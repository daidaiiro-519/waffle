## 概要

drift-check系4usecaseがWaffle自身のパスをハードコードしていた問題を、architecture文書のsourceRoot/conceptPlacementから動的解決する仕組みの実装引き継ぎ。ddd-advisor/tech-lead-advisorの敵対的検証結果を反映する。

---

 

---

# drift-check系usecaseの動的パス解決の実装引き継ぎ：handoff-concept-source-root-resolution

## 引き継ぎ元spec

bc-waffle

---

## 完成イメージ

---

## 使われ方（実際の呼び出し例）

---

## 設計観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| ddd-advisor | sourceRootと既存フィールドの役割分担 | layout.tree（人間可読な正典ツリー、自由記述）から機械的にパースする案は、人間可読性のための自由度と機械可読な厳密パースという異質な関心事を混在させる脆い実装になるため不採用。conceptPlacement.placementが既に「treeの一部を構造化データとして切り出す」先例であり、sourceRootはその延長として独立フィールドに持たせるのが一貫している。ただしtreeとsourceRootが将来ズレる（二重の正典化）リスクがあるため、tree側のx-prompt-writeに『先頭行はsourceRootと一致させること』を明記して対応済み（CodingSchema/v4）。 |
| ddd-advisor | sourceRoot/placementを1フィールドに統合しない | sourceRoot（言語・スタックごとに決まる技術規約、1architecture文書に1つ）とplacement（DDD概念ごとの配置、9概念×配列）は変更理由も粒度も異なる別軸であり、統合すると9箇所全てに同じroot文字列を重複させることになりDRY違反になる。分離設計を維持する。 |
| ddd-advisor | {package}等のトークンをinit時に解決しない | architecture-waffle.jsonの実データで、layout.treeが現時点でも{package}を未解決のまま保持していることを確認済み。sourceRootだけこの前例を破ってinit時に解決すると非対称な変更になるため、sourceRootもtreeと同じ扱い（未解決のまま複製、解決は利用時＝drift-check実行時）にする。 |
| tech-lead-advisor | 実装場所は共有ドメインサービス | 4つのdrift-check usecaseで同一パターン（sourceRoot+placementをpath_template.resolveへ渡す）が重複するため、architecture-evidence-based-scope（複数実例からの一般化＝2件以上）の基準を満たす。各usecase個別実装ではなく、domain/services配下の共有ヘルパーとして切り出す（bc-waffle.jsonのdomainServicesにResolveConceptSourceRoot/ConceptSourceRootとして宣言済み）。 |
| tech-lead-advisor | packageの導出方法 | 新規フィールド・新規CLIオプションは追加しない。architectureRef（documentId、例: architecture-waffle）から"{codingKind}-"プレフィックスを剥がすだけでpackage名（waffle）を復元できることを実データで確認済み（init_coding_preset.pyのdocument_id = f"{kind}-{product_name}"という既存命名規約から論理的に必然する値）。 |
| tech-lead-advisor | CLIオプション設計 | 既存--srcRootは残し明示指定時はそちらを優先（後方互換）。新設--architectureRefは未指定時のみ使う。ただしWaffle自身のパスへの暗黙フォールバックは廃止し、両方未指定ならエラーにする（今回の欠陥の温床を残さないため）。 |

---

## 実装観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | 共有ヘルパーのシグネチャ | resolve_source_root(layout: dict, concept_placement_items: list[dict], concept: str, **variables) -> str \| None。sourceRootが無い/conceptが見つからない場合はNoneを返し、呼び出し側（CLI）がフォールバック（エラー）を判断する。既存path_template.resolve()を内部で呼ぶ（改変せず合成利用）。 |
| tech-lead-advisor | path_template.resolveのKeyError挙動に注意 | resolve()はstr.format(**variables)の薄いラッパーで、テンプレートに{package}があるのにpackage変数を渡し忘れるとKeyErrorで例外送出する（素通りしない）。python版sourceRoot("src/{package}")では必ずpackage変数を渡す実装にすること。ts版("src"、プレースホルダ無し)はpackage変数が無くても安全に動く。 |
| tech-lead-advisor | 4つのusecase自体は無改修 | check_usecase_class_drift.py等application層のrun(documents_root, src_root, ...)シグネチャは変更不要。CLI（inbound adapter）がarchitectureRefを解決してsrc_rootの生文字列に変換してから渡すだけで、application層は変換後の結果を受け取るのみ（依存方向の原則に合致）。 |

---

## 既知の制約・トレードオフ

- 複数言語混在プロジェクト（同一プロジェクトにPython実装のusecaseとTypeScript実装のusecaseが混在する場合）は今回のスコープ外。1回の呼び出しで1つのarchitecture文書のみ参照するMVPとし、必要になった時点で再設計する
- productNameとpackage実体名が乖離するケース（kebab-case変換が必要になる等）も今回のスコープ外。実例が無いうちに先回りしない（evidence-based-scope）
