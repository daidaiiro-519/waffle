---
id: "uc-validate-document"
type: "usecase"
title: "Documentがschemaに適合するか検証する：ValidateDocument"
description: "Document の content が schema に適合するかを検証し、適合可否と違反詳細を返す（副作用なし）。"
tags: ["context:waffle"]
schemaRef: "DomainSpecSchema/v9"
---

# Documentがschemaに適合するか検証する：ValidateDocument

## 概要

- Document の content が schema に適合するかを検証し、適合可否と違反詳細を返す（副作用なし）。

---

## 存在意義

- schemaへの適合が機械チェックされなければ、DocumentをCREATEDからVALIDATEDへ進めてよいかの判断が人手のレビュー頼みになり、構造的に壊れた文書がrender・reconcile等の後続処理に渡ってしまう。他の全usecase（render/query/reconcile系）はDocumentがschemaに適合していることを前提に動くため、この検証ゲートが無ければそれらの前提が保証されない。

---

## 主アクターと意図

### 主アクター

Orchestrator（HarnessAgent）

### 意図

対象 Document が schema に適合するかを判定し、進められるか確かめる

---

## 事前条件

- 対象 Document が存在する

---

## 入力

| 入力 | 説明 |
|---|---|
| `path` | 適合を確かめる対象のdocumentの置き場所 |

---

## 基本フロー

```mermaid
sequenceDiagram
    actor Orchestrator
    Orchestrator->>Document: validate する
    Document->>Document: content を schema と照合
    Note over Document: DocumentValidated（適合時）
    Document-->>Orchestrator: 適合可否と違反詳細を返す
```

---

## 事後条件

- 適合し、状態遷移も可能なとき、判定されたstatus（例: VALIDATED）が実際にdocumentへ書き込まれる
- 適合時は DocumentValidated が発行される
- schemaがこのdocument種別で"validate"を状態遷移コマンドと定義していない場合（例: SkillSchema/CodingSchemaのmaturityLifecycleにはx-lifecycle自体が無い）、statusは変更しない

---

## 受け入れ基準

| 基準 |
|---|
| When 適合する Document が与えられたとき、システムは VALIDATED 判定を返す shall。 |
| When 不適合のとき、システムは違反詳細つきで失敗を返す shall。 |
| If schemaRef が無いとき、システムは MISSING_SCHEMA_REF を返す shall。 |
| When 適合し状態遷移も可能なとき、システムは判定したstatusを実際にDocumentへ書き込む shall。 |
| If 対象ファイルが JSON として解釈できないとき、システムは INVALID_JSON を返す shall。 |
| If Document が終端の状態にあるとき、システムは INVALID_TRANSITION を返し、状態を変えない shall。 |
| If 鍵を宣言した配列の中に、同じ鍵を持つ要素が2つ以上あるとき、システムは不適合として、その配列と重複した鍵を違反詳細に含めて返す shall。 |
| If 鍵を宣言した配列が、参照関係の宣言を持たないとき、システムは不適合としてその配列を違反詳細に含めて返す shall（どこからも指されないことが正しいなら、指されない旨を宣言させるため。宣言の欠けを『指されていない』と読むと、取り下げの規律が黙って効かなくなる）。 |

---

## 操作保証

| 保証 |
|---|
| When 対象パスが存在しないとき、システムは INVALID_PATH エラーを返す shall（対象を特定し取得する解決プロセス自体の契約であり、複数のusecaseに共通する）。 |
| When 対象のschemaRefを解決できないとき、システムは INVALID_SCHEMA_REF エラーを返す shall（schemaを特定し取得する解決プロセス自体の契約であり、複数のusecaseに共通する）。 |

---

## 受け入れシナリオ

### 適合する Document は VALIDATED 判定になる

| 分類 | 観点 |
|---|---|
| 正常系 | 適合判定：適合する Document は VALIDATED |

```gherkin
Scenario: 適合する Document は VALIDATED 判定になる
  Given schema に適合する Document
  When validate する
  Then VALIDATED 判定が返る
```

### 不適合は違反詳細つきで失敗する

| 分類 | 観点 |
|---|---|
| 異常系 | 適合判定：不適合は違反詳細つきで失敗 |

```gherkin
Scenario: 不適合は違反詳細つきで失敗する
  Given schema に適合しない Document
  When validate する
  Then 違反詳細つきで失敗する
```

### schemaRef を持たない Document は検証できない

| 分類 | 観点 |
|---|---|
| 異常系 | エラー：schemaRef 欠如は MISSING_SCHEMA_REF |

```gherkin
Scenario: schemaRef を持たない Document は検証できない
  Given schemaRef の無い Document
  When validate する
  Then MISSING_SCHEMA_REF エラーが返る
```

### 既存documentはschemaに適合する

| 分類 | 観点 |
|---|---|
| 正常系 | dogfood：waffle自身が持つ全document(skill/coding/spec)がそれぞれのschemaに適合し、正しいstatusになる(dogfood横断regression) |

```gherkin
Scenario Outline: 既存documentはschemaに適合する
  Given waffle自身のdocument
  When validateする
  Then 成功し、schemaのlifecycleに応じた正しいstatusになる
```

### SUPERSEDEDは終端でありvalidateを受け付けない

| 分類 | 観点 |
|---|---|
| 異常系 | 終端状態：SUPERSEDED状態のDocumentへのvalidateはINVALID_TRANSITIONとして拒否される |

```gherkin
Scenario: SUPERSEDEDは終端でありvalidateを受け付けない
  Given SUPERSEDED状態のDocument
  When validateする
  Then INVALID_TRANSITIONエラーが返る
```

### 不正なJSONはINVALID_JSON

| 分類 | 観点 |
|---|---|
| 異常系 | エラー：対象ファイルがJSONとして解釈できないときの失敗 |

```gherkin
Scenario: 不正なJSONはINVALID_JSON
  Given 不正なJSONの対象ファイル
  When validateする
  Then INVALID_JSONエラーが返る
```

### 適合判定は実際にstatusをdocumentへ書き込む

| 分類 | 観点 |
|---|---|
| 正常系 | 永続化：適合し状態遷移も可能なとき、判定結果を実際にdocumentへ書き込む |

```gherkin
Scenario: 適合判定は実際にstatusをdocumentへ書き込む
  Given CREATED状態の、schemaに適合するDocument
  When validateする
  Then 判定結果のstatusが実際にdocument.jsonへ書き込まれる（再読込しても反映されている）
```

### 鍵が重複した配列は不適合になる

| 分類 | 観点 |
|---|---|
| 異常系 | 要素の同一性：鍵が要素を一意に指すという前提が崩れていないか |

```gherkin
Scenario: 鍵が重複した配列は不適合になる
  Given 鍵を宣言した配列に、同じ鍵を持つ要素が2つある Document
  When 適合を検証する
  Then 不適合となり、違反詳細にその配列と重複した鍵が含まれる
```

### 鍵を宣言していない配列は値が重なっていても適合する

| 分類 | 観点 |
|---|---|
| 境界値 | 要素の同一性：一意性の要求が、宣言した配列にだけ及んでいるか |

```gherkin
Scenario: 鍵を宣言していない配列は値が重なっていても適合する
  Given 鍵を宣言していない配列に、同じ値の要素が2つある Document
  When 適合を検証する
  Then 適合と判定される
```

### 鍵を宣言して参照関係を宣言していない配列は不適合になる

| 分類 | 観点 |
|---|---|
| 異常系 | 宣言の完全性：宣言の欠けが、規律の沈黙にならないか |

```gherkin
Scenario: 鍵を宣言して参照関係を宣言していない配列は不適合になる
  Given 鍵は宣言しているが参照関係を宣言していない配列を持つ Schema と、それに従う Document
  When 適合を検証する
  Then 不適合となり、違反詳細にその配列が含まれる
```

### 指されないことを宣言した配列は適合する

| 分類 | 観点 |
|---|---|
| 境界値 | 宣言の完全性：指されない配列を書けなくしていないか |

```gherkin
Scenario: 指されないことを宣言した配列は適合する
  Given 鍵を宣言し、どこからも指されない旨を宣言した配列
  When 適合を検証する
  Then 適合と判定される
```

---

## 操作保証シナリオ

### 存在しないパスはINVALID_PATH

| 分類 | 観点 |
|---|---|
| 異常系 | 解決契約：対象パスが実在しないとき、パスの解決に失敗しINVALID_PATHになる |

```gherkin
Scenario: 存在しないパスはINVALID_PATH
  Given 実在しない対象パス
  When 本usecaseを実行する
  Then INVALID_PATHエラーが返る
```

### 解決できないschemaRefはINVALID_SCHEMA_REF

| 分類 | 観点 |
|---|---|
| 異常系 | 解決契約：schemaRefを解決できないとき、schemaの解決に失敗しINVALID_SCHEMA_REFになる |

```gherkin
Scenario: 解決できないschemaRefはINVALID_SCHEMA_REF
  Given 解決できないschemaRef
  When 本usecaseを実行する
  Then INVALID_SCHEMA_REFエラーが返る
```
