---
id: "coding-standard-typescript-hexagonal"
type: "coding-standard"
title: "TypeScript/ヘキサゴナル構成のコーディング規約を定めるCoding Standard：coding-standard-typescript-hexagonal"
description: "TypeScript/ヘキサゴナル構成のコーディング規約（命名・スタイル）を定める。"
schemaRef: "CodingSchema/v7"
---

# TypeScript/ヘキサゴナル構成のコーディング規約を定めるCoding Standard：coding-standard-typescript-hexagonal

## 概要

TypeScript/ヘキサゴナル構成のコーディング規約（命名・スタイル）を定める。

---

## 命名

### ファイル名

- **由来**: type
- **変換**: pascal-to-kebab
- **拡張子**: .ts

### 表記

| 対象 | 可視性 | 表記 | 接頭辞 |
|---|---|---|---|
| `type` |  | pascal |  |
| `function` |  | camel |  |
| `field` |  | camel |  |
| `constant` |  | upper-snake |  |

### 規範

| 適用先 | 規範 |
|---|---|
| 語彙 | 仕様のユビキタス言語に一致させる（実装都合の言い換えをしない） |
| domain | ユビキタス言語のみで命名し、技術的接尾辞（Impl/DTO/Manager/Helper等）をつけない |
| outbound adapter | 使用する技術を明示してよい。例: SqliteOrderRepository, DrizzleOrderRepository |
| application | 動詞＋目的語の業務操作名で命名する。例: RequestPickup, RegisterOrder |
| レイヤー境界を越えるDTO | 境界を越えるための入れ物であると分かる名前にする。例: OrderStatusResponse, RegisterOrderCommand |

---

## スタイル

| 種別 | 規約 |
|---|---|
| 必須 | any型を使わない。型が未確定な場合はunknownを使い、使用箇所で型を絞り込む |
| 必須 | 関数は1つの責務のみを持つ。複数の判断軸を1関数に混ぜない |
| 禁止 | 循環import（相互にimportし合うモジュール） |
| 推奨 | 公開APIの引数・戻り値には明示的な型注釈を付ける（推論に任せない） |
| 必須 | importは標準/組み込みモジュール・サードパーティ・ローカル（自プロジェクト）の3グループに分け、グループ間を空行で区切る。グループ内はアルファベット順。自動整形ツール（eslint-plugin-import等）の設定をこの規約のSSOTとし、手動での並べ替えはしない |

---

## docstring

- **スタイル**: TSDoc
- **構文の種類**: tagged
- **パラメータ**: @param
- **戻り値**: @returns
- **例外**: @throws

### 必須とする対象

| 対象 | 可視性 | 必須 |
|---|---|---|
| `type` | public | ✓ |
| `function` | public | ✓ |
| `type` | private | - |
| `function` | private | - |

### 要約行の書き方

要約行（1行目）は、ソースを開かずに検索・判断できるよう「何をするか・いつ使うか」が分かる語で書く

```
/**
 * 注文の合計金額を計算する。割引適用後の金額を返す。
 *
 * @param order - 対象の注文
 * @returns 割引適用後の合計金額
 */
function calculateTotal(order: Order): Money { /* ... */ }
```

---

## 決定ルール

| 種別 | 規約 |
|---|---|
| 必須 | docstringは公開要素のみ必須とする |
| 禁止 | コードから自明に導出できる情報（型そのものの説明等）だけをdocstringに書く |
