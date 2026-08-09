---
id: "test-standard-typescript-hexagonal"
type: "test-standard"
title: "TypeScript/ヘキサゴナル構成のテスト方針を定めるTest Standard：test-standard-typescript-hexagonal"
description: "TypeScript/ヘキサゴナル構成のテスト方針（テスト種別・層ごとの戦略）を定める。"
schemaRef: "CodingSchema/v6"
---

# TypeScript/ヘキサゴナル構成のテスト方針を定めるTest Standard：test-standard-typescript-hexagonal

## 概要

TypeScript/ヘキサゴナル構成のテスト方針（テスト種別・層ごとの戦略）を定める。

---

## テスト方針

- **重心**: pyramid

### 種別ごとの重心

| テスト種別 | 重心 |
|---|---|
| `unit` | high |
| `integration` | low |
| `acceptance` | medium |
| `contract` | medium |
| `e2e` | none |

### 根拠

業務ロジックの実装方法＝ドメインモデル

---

## テスト計画

| 項目 | 値 |
|---|---|
| 実行タイミング | すべての変更（コミット前ローカル・PRでCI） |
| CIトリガー | push / pull_request |
| ゲート | 対応するシナリオのテストが緑であることをマージ必須条件にする |
| 対象外 | パフォーマンステスト（中核だが性能要件なし） |

---

## テストタイプ

| テストタイプ | ツール | 対象 | 補足 |
|---|---|---|---|
| `unit` | Vitest | domain / application |  |
| `integration` | Vitest | outbound adapter |  |
| `acceptance` | Vitest | application | 要件のシナリオを見て人間またはAIが直接執筆する |
| `contract` | Vitest | ports / inbound adapter | インターフェース定義との差分検査 |

---

## フレームワーク

- **単体テスト**: Vitest
- **受け入れテスト**: Vitest

---

## シナリオの束ね方

### 突き合わせのキー

- **宣言行**: Scenario: {シナリオ名}
- **一意の範囲**: ['layer', 'spec', 'scenario']

### シナリオ種別とテストの対応

| シナリオ種別 | レイヤー | テスト種別 |
|---|---|---|
| `invariantScenarios` | domain | `unit` |
| `domainServiceScenarios` | domain | `unit` |
| `guaranteeScenarios` | application | `integration` |
| `acceptanceScenarios` | application | `acceptance` |

### 規範

| 規範 |
|---|
| 振る舞いはGiven/When/Then形式(Gherkin)のシナリオとして書く。1シナリオ＝1つの具体的な状況→操作→結果 |
| 書いたシナリオはそのまま放置せず、対応する実行可能なテスト関数を書く。シナリオの文章だけでは検証済みとみなさない |
| シナリオ名とテスト関数名を機械的に突き合わせ、対応するテストが無いシナリオ・対応するシナリオが無いテスト関数を検出する（中身の意味が正しいかどうかまでは自動判定しない） |

---

## シナリオdocstring

- **スタイル**: テスト関数(it/test)の直前に置くブロックコメント内にGiven/When/Thenをそのまま記載する
- **対象**: acceptanceScenarios/guaranteeScenarios/invariantScenarios/domainServiceScenariosに対応する全テスト関数

### 転記の指針

コメント本文には、対応するspec（usecase/aggregate/subdomain）のシナリオ（Given/When/Then）を一字一句そのまま転記する。関数名の一致だけでは、シナリオ文言の事後編集への追従を検知できないため。

```
/**
 * Given 在庫が1個の商品
 * When 2個注文する
 * Then 在庫不足エラーになる
 */
it("在庫不足なら失敗する", () => {
  // ...
});
```

---

## テスト対象別の配置

- **置き方**: colocated

| レイヤー | テスト種別 | 配置 | 置き方（個別） | 接尾辞 | 補足 |
|---|---|---|---|---|---|
| domain | `unit` |  |  | `.test.ts` | 実装ファイルと同じディレクトリに置く |
| application | `unit` |  |  | `.test.ts` | port経由の編成ロジック自身が独自の分岐/判定を持つ場合のみ追加する |
| outbound adapter | `integration` |  |  | `.test.ts` |  |
| application | `acceptance` | `tests/acceptance/` | type-first |  | 仕様のシナリオに対応するテストだけは、実装と分けて1か所へ集める |

---

## 決定ルール

| 種別 | 規約 |
|---|---|
| 禁止 | 単体テストが実物のDB・外部サービスに依存する |
| 推奨 | 不変条件はテストダブルなしで検証する |
| 必須 | テストファイル名は対応する仕様の識別子に対応させて統一する（実装モジュール名を由来にした命名は禁止） |
| 必須 | 値オブジェクトのテストは、値が等しければ等価であること・不変であることを検証する |
| 必須 | エンティティのテストは、同一性がidで決まることを検証する |
| 必須 | 集約のテストは、不変条件が常にメソッド経由でしか変更できないことを検証する |
| 必須 | 業務サービスのテストは、ステートレスであることを検証する |
| 必須 | アダプターの契約テストは、ポートのインターフェースに対して書き、本物の実装とテスト用の偽実装の両方が同じテストスイートを満たすことを確認する |
| 必須 | 時刻・乱数・ID生成のような非決定的な値は、テストダブル（固定クロック・シード固定・テスト用ID生成器）で決定的な値に固定する。本物のシステム時刻・乱数源に依存するアサーションを書かない |

---

## テストファイルの名づけ
