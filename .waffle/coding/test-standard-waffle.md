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

- **方針**: test-standard-python-hexagonalを前提とし、それに追加でWaffle固有のspec↔テスト対応規約を上乗せする
- **根拠**: Waffleはspec(DomainSpecSchema)のTestScenariosを実行可能テストへ機械的に束ねるUDD(Usage-Driven Development)ループを持つ。この対応関係はWaffle固有の仕組みであり、汎用のPython×Hexagonal規約(test-standard-python-hexagonal)には含めない。本文書はtest-standard-python-hexagonalを前提とし、frameworkやplacementByTargetの配置等、値が同一のフィールドは明示的に再掲した上で継承元を注記し、rules・testTypes等はWaffle固有の内容に絞って追加・簡略化している（機械的な差分継承ではなく、各フィールドの由来を平文で明示する方式を採る）

---

## テストタイプ

| テストタイプ | ツール | 対象 |
|---|---|---|
| `acceptance` | pytest（AIがspecのTestScenariosを見て執筆） | usecase |

---

## フレームワーク

- **単体テスト**: pytest（test-standard-python-hexagonalを継承）
- **受け入れテスト**: pytest（test-standard-python-hexagonalを継承）

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

- **スタイル**: pytestの三重引用符docstring内にGiven/When/Thenをそのまま記載する（test-standard-python-hexagonalを継承）
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
| domain | unit（配置はtest-standard-python-hexagonalを継承） | `tests/unit/domain/` |
| application | unit（port はテストダブル、配置はtest-standard-python-hexagonalを継承） | `tests/unit/application/` |
| adapters | integration（配置はtest-standard-python-hexagonalを継承） | `tests/integration/` |
| usecase | acceptance（ネイティブ、配置はtest-standard-python-hexagonalを継承） | `tests/acceptance/` |
| CLI / MCP の公開インターフェース | contract | `tests/contract/` |

---

## 決定ルール

| 種別 | 規約 |
|---|---|
| 必須 | テストファイル名は test_{対応するspecのdocumentIdをsnake_case化したもの}.py で統一する（domain/application/adapters(integration)/acceptanceの全層に適用。実装モジュール名を由来にした命名は禁止） |
| 必須 | DomainSpecSchemaのシナリオブロック種別とテスト配置層は機械的に対応する（scenarioBinding参照） |
| 禁止 | spec側(DomainSpecSchema等)のブロック名・シナリオの記述に、アーキテクチャ/テスト層の用語（unit/integration/adapter/render_engine等の内部コンポーネント名）を持ち込む。specは常にDDD/業務語彙のみで書く |
| 必須 | 時刻・乱数・ID生成のような非決定的な値は、テストダブル（固定クロック・シード固定・テスト用ID生成器）で決定的な値に固定する（test-standard-python-hexagonalを継承） |
