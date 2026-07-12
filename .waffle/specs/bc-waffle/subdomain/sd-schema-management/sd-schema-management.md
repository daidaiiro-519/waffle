# Schema定義ファイル自体の作成・部分編集を担うサブドメイン：sd-schema-management

## 概要

- AIに構造を推論させず、システムが決定的にSchema定義ファイル自体を作成・部分編集（ブロック追加・リネーム等）する業務領域。Documentの値ではなくDocumentの型定義そのものを対象とする点でsd-document-managementと責務が異なる（agg-document/agg-schemaが既に別集約であるのと同型の区別）。

---

## サブドメイン分類

### 分類

中核

### 根拠

- Waffleの差別化の源泉であるHarness原則（AIに構造を推論させずシステムが構造を守る）を、Document生成だけでなくSchema自体の生成・編集にも適用する
- Schema編集の安全性（冪等性・後方互換性・最小diff）は既製品のJSON編集ツールでは代替できない、waffle固有の価値

---

## 業務ユースケース一覧

- uc-patch-schema

---

## 詳細設計ガイド

- Schema編集はDocument編集より一段リスクが高い（既存Documentの適合性を左右するため）
- 物理的な整形はagg-schemaが定める契約（json.dumps(indent=2, ensure_ascii=False)相当）に一意に従わせる
- 部分編集は素のdict操作＋契約整形で最小diffを保証する
- 後方互換チェック（既存instanceを壊しうる変更の検出）を書き込み前に必ず通す

---

## ドメインサービス

| 業務サービス | 責務 |
|---|---|
| 後方互換チェック | 変更前後のschema(dict)の差分を計算し、公開済みkindのrequired配列への追加等、既存instanceを壊しうる変更を検出する。特定の集約に属さない純粋な差分計算ロジック。 |
| 契約整形 | schemaファイルの物理的な整形をagg-schemaが定める契約（json.dumps(indent=2, ensure_ascii=False)+改行）に一意に揃える。Schema集約の不変条件を実際に適用する。 |

---

## 業務サービスシナリオ

### requiredへの追加は後方互換違反として検出される

| 分類 | 観点 |
|---|---|
| 異常系 | 後方互換チェック：公開済みkindのContent defのrequired配列に新規エントリを追加する変更を検出する |

```gherkin
Scenario: requiredへの追加は後方互換違反として検出される
  Given 公開済みのschemaと、あるContent defのrequired配列に新規エントリを追加した変更後schema
  When 後方互換チェックを実行する
  Then 違反として検出される
```

### optionalプロパティの追加は後方互換違反にならない

| 分類 | 観点 |
|---|---|
| 正常系 | 後方互換チェック：requiredに含まれない新規プロパティの追加は既存instanceを壊さない |

```gherkin
Scenario: optionalプロパティの追加は後方互換違反にならない
  Given 公開済みのschemaと、requiredに含めずに新規プロパティのみ追加した変更後schema
  When 後方互換チェックを実行する
  Then 違反として検出されない
```

### 契約整形はjson.dumpsの出力と完全一致する

| 分類 | 観点 |
|---|---|
| 正常系 | 契約整形：schemaファイルの物理整形がagg-schemaの不変条件と一致する |

```gherkin
Scenario: 契約整形はjson.dumpsの出力と完全一致する
  Given 任意の整形が施されたschema(dict)
  When 契約整形を適用する
  Then 出力はjson.dumps(schema, indent=2, ensure_ascii=False)+改行と完全一致する
```
