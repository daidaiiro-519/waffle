---
name: project_domain_folder_unit_is_kind_based
description: ドメイン層のフォルダは種類単位（entities/ と value_objects/）で確定。集約単位は採らない
metadata:
  type: project
---

ドメイン層のフォルダ単位は**種類単位**で確定した（2026-08-07）。`entities/` に集約ルートと非ルートentity、`value_objects/` に値オブジェクトを置く。集約単位（`domain/document/` のように一貫性の境界ごとに切る）は採らない。commit f007d14（値オブジェクトの切り出し）は維持する。

ddd-advisor は集約単位への差し戻しを勧めたが、その要の根拠「`granularity: aggregate perFile 1` に違反している」は宣言の文言と照らして崩れた。文言は「1ファイルに集約1つ」であり、「集約の仕様に属する全要素が1ファイル」ではない。

**Why:** 決め手は共有される値オブジェクトの実測。`ViewTokenId` / `ViewTokenExpiry` / `ViewTokenStatus` の3つを agg-project と agg-shared-artifact が両方とも宣言しており、集約単位にすると置き場所の3択がすべてドリフト検知を悪化させる——どちらかへ置けば他方が誤検知、`shared/` を作れば種類単位が復活、複製すれば `ambiguous_value_object` が常時発火する。種類単位なら `conceptPlacement` が concept→1ディレクトリの全単射になり、既存の `resolve_source_root` がそのまま使える。集約単位はパステンプレートと集約名の表記規則という宣言を2つ増やす。

**How to apply:** この論点が再び挙がったら、上の実測（ViewToken の3つが2集約から宣言されている）を先に確認する。ddd-advisor が同じ主張を繰り返す場合、`granularity` の文言解釈が争点なので `waffle query --expression 'granularity'` で実物を出して裁く。集約単位が優る唯一の点（集約をまたぐimportが相対パスで表面化する）は、`check-layer-drift` が層単位でしか見ておらず回収する仕組みが無いため、現時点では効かない。関連する候補は [[knowledge-cand-declaration-text-arbitrates-violation-claims]] と [[knowledge-cand-avoidable-friction-is-not-detection]] として下書き記録済み。

未了として残っている実害（フォルダ単位とは別件）:
- `check_aggregate_class_drift.py:113` / `check_usecase_class_drift.py:56` の `expected_path` が `granularity` を読まず決め打っている。宣言が無い場合の報告種別（`missing_implementation_file` → `missing_class`）が変わるため、直行レーンでは直せずフルサイクルが要る
- `resolve_directory_scoped_root` が4つの状態（perFile宣言あり／architectureRef無し／document見つからず／解決できず）をすべて `None` に潰している
- 非ルートentityは属性も存在も一切検査されていない（`_declared_attributes` が `name == root_name` のみ）。`ArtifactViewToken = ViewToken` の別名共有はこの穴の内側にあるため、別名対応だけしても検知は1件も増えない
- python-hexagonal プリセットの `tree`（`domain/model/`）と `conceptPlacement`（`domain/entities`・`domain/value_objects`）が食い違っている。直すのは `tree` 側（`layout` の x-prompt が「食い違いを見つけたら図を直す」と定めている）
- `lint-docstring` が coding-standard の `docstring` ブロックを読んでいない。`LintDocstring.run(target_path, kind)` は `kind="google"` という文字列を受け取るだけで、`tagParams`/`tagReturns`/`tagRaises`/`syntaxKind`/`proseMustStartWith`/`required`（可視性の表）は `src/waffle` に文字列として存在しない。タグ検査自体は port 経由の外部lintツールが行っており、たまたま google 既定と一致しているだけ。規約側でタグ名を変えても追随しない。`expected_path` が `granularity` を読まない件と同じ型の欠陥で、「検査は宣言を読む」という1つのspecにまとめるのが筋
- `agg-project` 不変条件7（閲覧トークンに期限を設けないことを許す）に、invariantScenario もテストも無い。シナリオ追加はspec変更なので別サイクル
- artifact-share の docstring 違反は domain だけで59件（2026-08-08時点、内訳 MISSING_DOC_COMMENT 11 / MISSING_ARGS_SECTION 15 / ARGS_MISMATCH 15 / MISSING_RETURNS_SECTION 18）。application 35・adapters 28 は未再測
