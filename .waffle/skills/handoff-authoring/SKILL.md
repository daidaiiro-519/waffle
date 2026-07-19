---
name: "handoff-authoring"
description: "spec→実装の橋渡しとして、DDD設計判断・アーキテクチャ判断等のadvisor見解をHandoffSchema documentに記録する必要があるときに使う。VALIDATED以上のspecと、既に確定している判断材料をもとに、designViewpoints/implementationViewpointsを記録する。"
---

# spec→実装の橋渡しとなるHandoffドキュメントの作成を行うSkill：handoff-authoring

## 目的

spec→実装の橋渡しとして、DDD設計判断・アーキテクチャ判断等のadvisor見解をHandoffSchema documentに記録する必要があるときに使う。VALIDATED以上のspecと、既に確定している判断材料をもとに、designViewpoints/implementationViewpointsを記録する。

---

## 役割

- 対象specへの参照（specRef）を持つHandoff document.jsonを作成・更新する
- 受け取った判断材料を、designViewpoints/implementationViewpointsとして記録する
- validate→renderまで通し、成果物を確定させる

---

## 処理対象と成果物

### 処理対象

VALIDATED以上のspecへの参照と、記録する判断材料（設計観点・実装観点・制約等、既に確定している見解）。

### 成果物

validate・render済みのHandoff document.json（および対応するMarkdown）。

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| 対象spec（specRef） | VALIDATED以上のstatusを持つspecであることを前提とする。明示されなければ呼び出し元に確認する。 |
| 記録する判断材料（設計観点・実装観点等、既に確定している見解） | 既に呼び出し元から与えられているものとして受け取る。与えられていない場合、このSkill自身では判断材料を収集しない。それはこのSkillの責務ではないため、呼び出し元に確認する。 |

---

## 実行手順

### Step 1: 対象specとの対応を確認する

specRefが指すspecがVALIDATED以上のstatusであることを確認する。

### Step 2: 骨格を生成する

既存Handoff document.jsonが無ければ骨格を生成する。既存の更新の場合はこの手順を省略する。

### Step 3: 受け取った判断材料を記録する

既に与えられている判断材料を、designViewpoints/implementationViewpoints/constraintsの対応する配列に整理して記録する。配列は現在値を取得してから組み立て直し、丸ごと置き換える。

### Step 4: validateする

schemaへの適合を検証する。エラーがあれば該当箇所を修正して再度validateする。

### Step 5: renderする

validate済みのdocumentを成果物へ描画する。

---

## 出力形式

作成・更新したHandoff document.jsonのパス、記録したviewpoints件数、validate/renderの結果を報告する。

---

## ガードレール

- document.jsonの操作は必ずCLI/MCP経由で行う（直接Read/Edit/Writeしない）
- 既存document.jsonはscaffold fillで編集する。配列はqueryで現在値を取得してから組み立て直し、丸ごと置き換える
- VALIDATED未満のstatusのspecを対象にしない
- 判断材料が与えられていないまま自分で設計判断・アーキテクチャ判断を作り出さない。不足している場合は呼び出し元に確認する
- Handoffはあくまで助言記録であり、specの正式な状態遷移とは別物である（statusフィールドを持たない）
