# handoff-uc-query-document

## 引き継ぎ元spec

uc-query-document

---

## 設計観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| ddd-advisor | resolve_refはQueryDocument内に残してよい（既存16操作と同じ粒度） | resolve_refは単一documentのref解決という点操作であり、既存16操作（単一document・単一block・単一配列フィールド）と同じ責務の粒度に属する。「参照先のpathだけを返し、中身は取得しない」という設計は、外部集約をIDで参照し直接オブジェクトとして保持しない（eager-loadしない）という原則を体現しており、参照（reference）と実体取得（dereference）の境界を呼び出し側の意図として明示させる点で健全。 |
| tech-lead-advisor | resolve_refがdomain/services/path_template.pyを呼ぶ依存方向（application→domain）は適切 | path_template.resolve/reverse_parseは既にDBやフレームワークを知らない純粋ロジックとしてdomain層に実装済みであり、「参照解決の規則」というドメインルールに該当する。application層のquery_document.pyからdomain層のこのロジックを呼ぶことは、依存が常に外側（application）から内側（domain）へ向かうという原則に合致する。逆方向（domainがapplicationを知る）ではない点を実装時に崩さないこと。 |

---

## 実装観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | resolve_refはexisting _dispatchのGroup相当として追加し、run本体を肥大化させない | 既存実装は_dispatch内でget_meta/index_scan/find_all等をGroup単位に整理し、末尾に純粋ヘルパ関数群（_block_prompt/_find_by_id等）を分離している。resolve_refも同じ構成（dispatchの1分岐＋末尾の純粋ヘルパ）に沿って実装し、クラス構造自体を変えない。 |

---

## 既知の制約・トレードオフ

- resolve_refはテンプレート変数を解決できない場合MISSING_TEMPLATE_VARを返す。対象documentがtargetSchemaRefのx-source-targetテンプレートが要求する変数（contextRef等）を持たない場合に発生する。実装時はpath_template.resolveの失敗をこのエラーコードにマッピングすること。
