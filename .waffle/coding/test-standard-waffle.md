---
id: "test-standard-waffle"
type: "test-standard"
title: "Waffle自身のテスト方針（4層テスト構成）を定めるTest Standard：test-standard-waffle"
description: "Waffle自身のunit/integration/acceptance/contractという4層テスト構成の方針を定める。"
schemaRef: "CodingSchema/v5"
---

# Waffle自身のテスト方針（4層テスト構成）を定めるTest Standard：test-standard-waffle

## 概要

Waffle自身のunit/integration/acceptance/contractという4層テスト構成の方針を定める。

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

業務ロジックの実装方法＝ドメインモデル。Waffleはspec(DomainSpecSchema)のTestScenariosを実行可能テストへ機械的に束ねるUDD(Usage-Driven Development)ループを持ち、この対応関係の詳細規約はscenarioBindingで定める。

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

| テストタイプ | ツール | 対象 | 補足 |
|---|---|---|---|
| `unit` | pytest | domain / application |  |
| `integration` | pytest | application / outbound adapter |  |
| `acceptance` | pytest | application | 要件のシナリオを見てAIが直接執筆する |
| `contract` | pytest | ports / inbound adapter | インターフェース定義との差分検査 |

---

## フレームワーク

- **単体テスト**: pytest
- **受け入れテスト**: pytest

---

## シナリオの束ね方

### 突き合わせのキー

- **宣言行**: Scenario: {シナリオ名}
- **一意の範囲**: ['layer', 'spec', 'scenario']
- **ファイル名の由来**: spec-document-id

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
| テストの文書コメント（Pythonならdocstring）の先頭に置いた宣言行「Scenario: {シナリオ名}」で、specのシナリオと突き合わせる。テスト関数名は突き合わせに使わない。関数名をキーにすると、仕様の語彙をそのまま識別子にできる言語でしか成立せず（シナリオ名は日本語、Pythonの識別子慣習はASCII）、識別子へ変換する過程で句読点や空白が潰れて別のシナリオと衝突しうるため |
| 対象言語の命名慣習に従う（PythonならASCIIのsnake_case）。シナリオ名を識別子にしない。どのシナリオに対応するかは宣言行が持つ |
| 宣言行⇔シナリオ名の突き合わせで機械検出（check-scenario-drift）。未実装（specにあってテストが無い）と孤立（テストにあってspecに無い）を検出し、中身の妥当性はAIが評価する |
| specのGuaranteeScenarios/AcceptanceScenarios/InvariantScenarios/DomainServiceScenariosに対応するテストは、対応するgherkinの宣言行とGiven/When/Thenをそのまま転記する。宣言行は突き合わせのキーそのもの、本文はシナリオ文言の事後編集への追従を検知する材料であり、役割が異なる |
| specのシナリオに対応しない補助的なテストは、シナリオ対応テストとは別のファイルへ置く。同じファイルへ混ぜると、そのテストが常に孤立として報告され続け、警報が意味を失う。ドリフト検知はspecとテストファイルの組に対して行うため、specと組にならないファイルは検査対象にならない |
| 文書コメントの取り出しは言語ごとのadapterが担い、コアは言語の構文解析技術を知らない。Pythonの文書コメントは関数の内側にあるため構造的に対応づくが、Java/TypeScript/JavaScriptでは関数の直前に置かれるため近接でしか対応づかない。言語によって対応づけの確実さが異なることを前提にする |

---

## シナリオdocstring

- **スタイル**: 対象言語の文書コメント構文に、先頭の宣言行「Scenario: {シナリオ名}」と、続くGiven/When/Thenをそのまま記載する（Pythonならpytestの三重引用符docstring内）。文書コメントの位置は言語で異なり、Pythonは関数の内側、Java/TypeScript/JavaScriptは関数の直前に置く
- **対象**: usecase specのacceptanceScenarios/guaranteeScenarios、aggregate specのinvariantScenarios、bounded-context specのdomainServiceScenariosに対応する全テスト関数

### 転記の指針

文書コメントには、対応するspecのシナリオの宣言行とGiven/When/Thenを、人間が言い換えず一字一句そのまま転記する。転記が要るのは2つの役割を兼ねるため。宣言行はspecとテストを突き合わせるキーそのものであり、これを持たないテストはどのシナリオにも対応しないものとして扱われる。本文は、シナリオ文言の事後編集への追従を検知する材料になる（キーの一致だけでは文言の編集を検知できない）

```
def test_suspend_blocks_viewing():
    """
    Scenario: 止めると開けなくなる
    Given 共有アーティファクトAが公開されている
    When 共有アーティファクトAの公開を止める
    Then 共有アーティファクトAの閲覧トークンで開けない
    """
    ...
```

---

## テスト対象別の配置

- **置き方**: layer-first

| レイヤー | テスト種別 | 配置 | 置き方（個別） | 接尾辞 | 補足 |
|---|---|---|---|---|---|
| domain | `unit` | `tests/domain/unit/` |  |  |  |
| application | `acceptance` | `tests/application/acceptance/` |  |  |  |
| application | `integration` | `tests/application/integration/` |  |  |  |
| application | `unit` | `tests/application/unit/` |  |  | port経由の編成ロジック自身が独自の分岐/判定を持つ場合のみ追加する |
| application | `contract` | `tests/application/contract/` |  |  | port は層ではなく application が所有する要素なので、その契約テストも application の下に置く。同じ契約テストスイートを、本物のadapterとテスト用の偽実装の両方に対して実行する |
| inbound adapter | `contract` | `tests/adapters/inbound/contract/` |  |  |  |
| outbound adapter | `integration` | `tests/adapters/outbound/integration/` |  |  |  |

---

## 決定ルール

| 種別 | 規約 |
|---|---|
| 禁止 | 単体テストが実物の DB・外部サービスに依存する |
| 推奨 | 不変条件はテストダブルなしで検証する |
| 必須 | テストファイル名は test_{対応するspecのdocumentIdをsnake_case化したもの}.py で統一する（仕様のシナリオに対応する全テストに適用。実装モジュール名を由来にした命名は禁止） |
| 必須 | tests/ 配下は architecture が宣言するレイヤーを第一階層とし、テスト種別（unit/integration/acceptance/contract）を第二階層とする。第一階層のレイヤー名は architecture の layers が宣言するものをそのまま使い、ここで別途定義しない。テスト種別を第一階層にすると、レイヤーごとに取りうる種別が違うこと（domain に contract は無い、ports に unit は無い等）を構造で表せず、あり得ない組み合わせを禁止規則で塞ぐことになる（実際に「tests/unit/adapters/ に置かない」という禁止規則が必要になり、かつ守られていなかった） |
| 推奨 | application層のport経由コードは、tests/application/integration（実アダプタを差した検証）で既に検証済みの保証を、fakeに差し替えて再検証するためだけの単体テストを追加しない。追加するのは、そのコード自身が独自の分岐/判定ロジックを持ち、かつどの既存シナリオにも対応しない場合のみ（テストカバレッジは目標ではなく診断ツール） |
| 必須 | アダプターの契約テストは、ポートのインターフェースに対して書き、本物の実装とテスト用の偽実装の両方が同じテストスイートを満たすことを確認する |
| 禁止 | 仕様(要件)の記述に、テスト層・アーキテクチャ層の内部語彙（unit/integration/adapter・具体的なクラス名等）を持ち込む。仕様は常に業務語彙のみで書き、「どう検証するか」はこの規約（コーディング側）にのみ書く |
| 必須 | 値オブジェクトのテストは、値が等しければ等価であること・不変であること（状態を変更するメソッドが存在しないこと）を検証する |
| 必須 | エンティティのテストは、同一性がidで決まること（フィールドの値が同じでもidが違えば別物として扱われること）を検証する |
| 必須 | 集約のテストは、不変条件が常にメソッド経由でしか変更できず、直接不変条件に違反した状態を作れないことを検証する（コンストラクタ・setter等での迂回が無いこと） |
| 必須 | 業務サービスのテストは、ステートレスであること（同じ入力に対して常に同じ結果を返し、呼び出し順序に依存しないこと）を検証する |
| 必須 | 時刻・乱数・ID生成のような非決定的な値は、テストダブル（固定クロック・シード固定・テスト用ID生成器）で決定的な値に固定する。本物のシステム時刻・乱数源に依存するアサーションを書かない |
| 必須 | テストには2つの出どころがある。仕様由来（specが宣言したシナリオを転記し、宣言行で突き合わせる）と、規約由来（portやアダプターが宣言した契約を確かめる）。この2つを同じディレクトリに混ぜると、ディレクトリを見てもどちらの保証なのか分からなくなるので、テスト種別で分ける——仕様由来は unit / acceptance と application の integration、規約由来は contract と adapters 配下の integration。この区別のために、層でない名前を第一階層に作らない（第一階層は常に architecture が宣言する層） |
