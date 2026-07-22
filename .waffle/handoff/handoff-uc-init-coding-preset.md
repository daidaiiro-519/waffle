## 概要

CodingSchemaプリセット機構（uc-init-coding-preset）の実装引き継ぎ。プリセット/実規約の概念区分の設計背景と、新規port/adapter/usecaseの実装観点を伝える。

---

 

---

# CodingSchemaプリセット機構の実装引き継ぎ：handoff-uc-init-coding-preset

## 引き継ぎ元spec

uc-init-coding-preset

---

## 完成イメージ

---

## 使われ方（実際の呼び出し例）

---

## 設計観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| ddd-advisor | プリセット/実規約の概念区分 | 「プリセット（stack名でキーされる中立の種データ）」と「プロダクト固有の実規約（プロダクト名でキーされる、育っていくdocument）」を区別する設計はDDD原則上妥当。ubiquitous-languageの言う『同じ綴りの言葉が文脈で違う意味を隠し持っている』状態の解消であり、両者は対等な2コンテキストの連携ではなく、一方から他方が種を受け取って自分の言葉で育てる一方向の関係で十分（brainstorm-codingschema-preset-and-product-naming.md論点1参照）。 |
| tech-lead-advisor | プリセットの保存形式 | render_blank_templateの再利用は不可（空プレースホルダー生成であり、プリセットは既に決まった値を持つ静的データという別種のデータ）。schemaファイルと同格の場所（src/waffle/domain/model/CodingPresets/{presetName}.json）に、PackageSchemaRepositoryと同じimportlib.resources経由のアダプターで置くのが自然。 |
| tech-lead-advisor | usecase設計の単一責任 | 既存ScaffoldDocumentへのoperation追加は、単一document骨格生成と複数documentのプリセット複製という性質の異なる2責務を1クラスに混在させることになり、architecture-layer-boundaryの単一責任原則に反する。新規usecase（InitCodingPreset）として切り出す。 |

---

## 実装観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | stackフィールドの扱い | 生成されるproduct固有document(例: tech-stack-waffle)のstackフィールドは、プリセット名（例: python-hexagonal）のまま保持する。documentId(プロダクト名サフィックス)とstack値(プリセット系譜)を別軸にすることで、将来プリセットが改訂された際にどの実規約がそこから生まれたかを追跡できる（ユーザー合意）。 |
| tech-lead-advisor | 冪等性 | 既にdocumentIdが存在するkindはスキップし上書きしない（scaffold createの既存挙動と同じ設計原則）。 |

---

## 既知の制約・トレードオフ

- プリセットのライフサイクル（validate/render等のCLI操作の対象に含めるか）は今回のスコープ外。プリセットは静的データでありdocumentではないため、これらの操作対象にはならない
- 現時点でプリセットはpython-hexagonal/typescript-hexagonalの2種のみ。新しいプリセットの追加手段（CLIからの登録等）は今回の実装に含まれず、パッケージへの直接配置のみをサポートする
