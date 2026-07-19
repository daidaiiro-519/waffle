## 概要

Handoffを固定HTMLテンプレートへ描画するusecaseの設計判断を実装へ引き継ぐ。

---

# Handoffを固定HTMLテンプレートへ描画する実装引き継ぎ：handoff-uc-render-handoff-template

## 引き継ぎ元spec

uc-render-handoff-template

---

## 完成イメージ

---

## 使われ方（実際の呼び出し例）

---

## 設計観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | 別usecaseとして新設し、既存RenderDocumentは変更しない | RenderDocumentのソース中に既に「HTML は将来 viewer が担うため engine は MD のみ描画」という注記があり、MD生成と人間向けHTML成果物は設計時点で切り分け済み。固定テンプレート適用は別種の変更理由を持つため、同一usecaseに条件分岐で混ぜると責務が混在する。 |
| ddd-advisor | HTML生成はDocument集約の外側の別関心事（CQRS的投影） | document.json（AI向け正本）が唯一の真実源、HTMLはそこから導出される読み取りモデル（投影）。Document集約はvalidate/fillの整合性のみを保証し、HTML生成という out-of-band な処理を集約自身の責務に含めない。 |
| ddd-advisor | sd-document-management配下への配置は妥当だが、中核分類根拠との緊張関係に注意する | 当該サブドメインの中核分類根拠は「x-render宣言に従った機械描画」だが、本usecaseはこの語彙で表現できないため自前の決定的コードで書く。usecaseRationaleにevidence-based-scopeの限定条件（2件目の実例が出るまで汎用化しない）を明記することで整合させた。 |

---

## 実装観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | 固定テンプレート実体はsrc/waffle配下のコード内定数として持つ | 固定テンプレートは実行時に差し替える対象ではなく、コンパイル時に固定される資産。schema側に技術詳細（HTML/CSS）を持たせると依存方向が逆転するため、新規ポート（TemplateRepository等）は不要。 |
| tech-lead-advisor | 座標計算ロジックはusecase自身でなくdomain/services配下の純粋関数へ切り出す | 既存のpart_renderer（宣言的部品描画をdomain/servicesに切り出している前例）と同型のパターンに従う。usecase内に直接書くとアプリケーション層に業務ロジックの詳細判定を書きすぎるアンチパターンに該当し、座標計算だけを独立してテストできなくなる。 |
| ddd-advisor | 読み取り専用の投影として実装し、Handoff集約の状態は変更しない | 誤って集約のトランザクション境界を書き換えないよう、postconditionsに「Handoff集約自身の状態・内容は変更しない」ことを明記した。 |

---

## 既知の制約・トレードオフ

- schemaRef不一致・completionImage欠如は暗黙にスキップせず、明示的なエラー（WRONG_SCHEMA_REF・MISSING_COMPLETION_IMAGE）として扱う。
- 2件目の実例（Backend集約構造図等）が具体的に発生するまで、テンプレートエンジンの汎用フレームワーク化は行わない（evidence-based-scope）。
