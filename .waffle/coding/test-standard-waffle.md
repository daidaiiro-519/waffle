---
id: "test-standard-waffle"
type: "test-standard"
title: "Waffle自身のテスト方針（4層テスト構成）を定めるTest Standard：test-standard-waffle"
description: "Waffle自身のunit/integration/acceptance/contractという4層テスト構成の方針を定める。"
schemaRef: "CodingSchema/v3"
---

# Waffle自身のテスト方針（4層テスト構成）を定めるTest Standard：test-standard-waffle

## 概要

Waffle自身のunit/integration/acceptance/contractという4層テスト構成の方針を定める。

---

## テスト方針

- **方針**: ピラミッド形（単体テストを重視・統合はやや軽め・E2E は行わない）
- **根拠**: 業務ロジックの実装方法＝ドメインモデル。Waffleはspec(DomainSpecSchema)のTestScenariosを実行可能テストへ機械的に束ねるUDD(Usage-Driven Development)ループを持ち、この対応関係の詳細規約はscenarioBindingで定める。

---

## テスト計画

| 項目 | 値 |
|---|---|
| 実行タイミング | すべての変更（コミット前ローカル・PR で CI） |
| CI トリガー | push / pull_request |
| ゲート | 対応するシナリオのネイティブテストが緑であることをマージ必須条件にする |
| 対象外 | パフォーマンステスト（中核だが性能要件なし） |

---

## テストタイプ

| テストタイプ | ツール | 対象 |
|---|---|---|
| `unit` | pytest | domain / application |
| `integration` | pytest | adapters |
| `acceptance` | pytest（要件のシナリオを見てAIが直接執筆） | usecase |
| `contract` | pytest（インターフェース定義との差分検査） | 外部公開インターフェース（CLI/MCP） |

---

## フレームワーク

- **単体テスト**: pytest
- **受け入れテスト**: pytest

---

## シナリオの束ね方

| 項目 | 規約 |
|---|---|
| 対応関係 | 1 spec（DomainSpecSchemaのusecase）＝1 ネイティブテストファイル（AI執筆） |
| ネイティブテストの配置 | tests/acceptance/test_{documentId}.py（documentIdはspecのdocumentIdをそのままsnake_case化） |
| ドリフト検知 | シナリオ名⇔テスト関数名の名前突き合わせで機械検出（check-scenario-drift）。未実装/孤立を検出し、中身の妥当性はAIが評価する |
| シナリオブロック種別とテスト配置層の対応 | invariantScenarios(aggregate)→domain/unit、domainServiceScenarios(subdomain)→domain/unit、guaranteeScenarios(usecase・operationGuaranteesと対)→integration、acceptanceScenarios(usecase)→acceptance。コードの性質(純粋かport必須か)をケースバイケースで判定してはならない（ドリフト検知を非決定的にするため） |
| シナリオ文言の追従 | specのGuaranteeScenarios/AcceptanceScenarios/InvariantScenarios/DomainServiceScenariosに対応するテスト関数は、対応するgherkinのGiven/When/Thenをdocstringに転記する（関数名の一致だけでは、シナリオ文言の事後編集に対する追従を検知できないため） |

---

## シナリオdocstring

- **スタイル**: pytestの三重引用符docstring内にGiven/When/Thenをそのまま記載する
- **対象**: usecase specのacceptanceScenarios/guaranteeScenarios、aggregate specのinvariantScenarios、bounded-context specのdomainServiceScenariosに対応する全テスト関数

### 転記の指針

docstring本文は、対応するspec（DomainSpecSchemaのTestScenarios）のGiven/When/Thenを人間が言い換えず一字一句そのまま転記する。scenarioBindingが定める名前突き合わせ(check-scenario-drift)は関数名の有無しか見ないため、文言そのものの事後編集への追従はこの転記規約でのみ保証される。

```
def test_バックワード非互換なら書き込みを拒否する():
    """
    Given 公開済みkindのrequired配列にプロパティを追加するpatch_schema呼び出し
    When patch-schemaを実行する
    Then BACKWARD_INCOMPATIBLEエラーが返り、schemaファイルは書き換わらない
    """
    ...
```

---

## テスト対象別の配置

| 対象 | テスト種別 | 配置 |
|---|---|---|
| domain | unit | `tests/unit/domain/` |
| application | unit（port はテストダブル） | `tests/unit/application/（port経由の編成ロジック自身が独自の分岐/判定を持つ場合のみ追加する）` |
| adapters | integration（契約テスト） | `tests/integration/（同じ契約テストスイートを、本物のadapterとテスト用の偽実装の両方に対して実行できると、両者の振る舞いの一致を保証しやすい）` |
| usecase | acceptance（ネイティブ） | `tests/acceptance/` |
| システム全体の少数シナリオ | E2E | `tests/e2e/（コンポジションルートによる配線を含めて検証。件数は絞る）` |
| CLI / MCP の公開インターフェース | contract | `tests/contract/` |

---

## 決定ルール

| 種別 | 規約 |
|---|---|
| 禁止 | 単体テストが実物の DB・外部サービスに依存する |
| 推奨 | 不変条件はテストダブルなしで検証する |
| 必須 | テストファイル名は test_{対応するspecのdocumentIdをsnake_case化したもの}.py で統一する（domain/application/adapters(integration)/acceptanceの全層に適用。実装モジュール名を由来にした命名は禁止） |
| 必須 | tests/ 配下は testTypes（unit/integration/acceptance/contract/e2e）を第一階層とする。domain/applicationはunit/配下の第二階層（対象層の軸）。adaptersは単体テストではなく統合(integration)テストなので tests/unit/配下に置かず tests/integration/ を独立の第一階層にする |
| 推奨 | application層のport経由コードは、integration層(実アダプタ)で既に検証済みの保証を、fakeに差し替えて再検証するためだけの単体テストを追加しない。追加するのは、そのコード自身が独自の分岐/判定ロジックを持ち、かつどの既存シナリオにも対応しない場合のみ（テストカバレッジは目標ではなく診断ツール） |
| 必須 | アダプターの契約テストは、ポートのインターフェースに対して書き、本物の実装とテスト用の偽実装の両方が同じテストスイートを満たすことを確認する |
| 禁止 | 仕様(要件)の記述に、テスト層・アーキテクチャ層の内部語彙（unit/integration/adapter・具体的なクラス名等）を持ち込む。仕様は常に業務語彙のみで書き、「どう検証するか」はこの規約（コーディング側）にのみ書く |
| 必須 | 値オブジェクトのテストは、値が等しければ等価であること・不変であること（状態を変更するメソッドが存在しないこと）を検証する |
| 必須 | エンティティのテストは、同一性がidで決まること（フィールドの値が同じでもidが違えば別物として扱われること）を検証する |
| 必須 | 集約のテストは、不変条件が常にメソッド経由でしか変更できず、直接不変条件に違反した状態を作れないことを検証する（コンストラクタ・setter等での迂回が無いこと） |
| 必須 | 業務サービスのテストは、ステートレスであること（同じ入力に対して常に同じ結果を返し、呼び出し順序に依存しないこと）を検証する |
| 必須 | 時刻・乱数・ID生成のような非決定的な値は、テストダブル（固定クロック・シード固定・テスト用ID生成器）で決定的な値に固定する。本物のシステム時刻・乱数源に依存するアサーションを書かない |
