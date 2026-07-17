---
name: "spec-authoring"
description: "既存のspec schema（DomainSpecSchema・CodingSchema・PlatformSpec・PresentationSpecSchema等）に沿ってspec document.jsonを新規作成・更新する必要があるときに使う。schemaRefに基づいて骨格を生成し、既に確定している判断材料をもとに値を埋め、validate・renderまで行う。"
---

# spec-authoring

## 目的

既存のspec schema（DomainSpecSchema・CodingSchema・PlatformSpec・PresentationSpecSchema等）に沿ってspec document.jsonを新規作成・更新する必要があるときに使う。schemaRefに基づいて骨格を生成し、既に確定している判断材料をもとに値を埋め、validate・renderまで行う。

---

## 役割

- 対象schemaRefのscaffold create/fillを使い、spec document.jsonを作成・更新する
- x-prompt-write宣言と、既に与えられている判断材料に従い、必要な値を埋める
- validate→renderまで通し、成果物を確定させる

---

## 処理対象と成果物

### 処理対象

対象spec schemaのdocumentId・schemaRefと、そのcontentを埋めるための判断材料（設計判断・アーキテクチャ判断等、既に確定している見解）。

### 成果物

validate・render済みのspec document.json（および対応するMarkdown）。

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| 対象schemaRef・documentId | 明示されなければ呼び出し元に確認する。 |
| contentを埋めるための判断材料（設計判断・アーキテクチャ判断等、既に確定している見解） | 既に呼び出し元から与えられているものとして受け取る。与えられていない場合、このSkill自身では判断材料を収集しない。それはこのSkillの責務ではないため、呼び出し元に確認する。 |

---

## 実行手順

### Step 1: 対象schemaRefの骨格を生成する

対象spec document.jsonの骨格を生成する。既存document.jsonの更新の場合はこの手順を省略する。

### Step 2: 受け取った判断材料をもとに値を埋める

x-prompt-write宣言に従い、既に与えられている判断材料を使ってcontentの各値を埋める。配列は現在値を取得してから組み立て直し、丸ごと置き換える。

### Step 3: validateする

schemaへの適合を検証する。エラーがあれば該当箇所を修正して再度validateする。

### Step 4: renderする

validate済みのdocumentを成果物へ描画する。

---

## 出力形式

作成・更新したdocument.jsonのパスと、validate/renderの結果を報告する。

---

## ガードレール

- document.jsonの操作は必ずCLI/MCP経由で行う（直接Read/Edit/Writeしない）
- 既存document.jsonはscaffold fillで編集する。配列はqueryで現在値を取得してから組み立て直し、丸ごと置き換える
- 設計判断・アーキテクチャ判断が必要な箇所を、判断材料が与えられていないまま自分で埋めない。判断材料が不足している場合は呼び出し元に確認する
- schemaに新規必須トップレベルキーが追加されている場合のみ、check-schema-version-driftで検知した上でEdit/Writeを許容する
