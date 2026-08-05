---
id: "test-standard-artifact-share"
type: "test-standard"
title: "artifact-shareのテスト方針を定めるTest Standard：test-standard-artifact-share"
description: "artifact-shareのテスト方針・配置・シナリオの束ね方を定める。2つのランタイムが同じ業務ルールを守るため、実装は分かれても同じシナリオへ紐づける。"
tags: ["tier:backend"]
schemaRef: "CodingSchema/v5"
---

# artifact-shareのテスト方針を定めるTest Standard：test-standard-artifact-share

## 概要

artifact-shareのテスト方針・配置・シナリオの束ね方を定める。2つのランタイムが同じ業務ルールを守るため、実装は分かれても同じシナリオへ紐づける。

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

公開と閲覧の可否がこの製品の中核であり、その判断はドメインモデルで表す。実際のAWSに触れる検証は費用と実行時間が乗るため、境界の契約テストで代える。

---

## テスト計画

| 項目 | 値 |
|---|---|
| 実行タイミング | すべての変更（コミット前ローカル・PR で CI） |
| ゲート | 対応するシナリオのネイティブテストが緑であることをマージ必須条件にする |
| 対象外 | 実際のAWS環境に対する自動テスト（上げた直後の自己点検は手動で行う） |

---

## テストタイプ

| テストタイプ | ツール | 対象 | 補足 |
|---|---|---|---|
| `unit` | pytest | domain / application |  |
| `integration` | pytest | outbound adapter |  |
| `acceptance` | pytest | application | 仕様のシナリオを見て直接執筆する |
| `contract` | pytest | ports / inbound adapter | 本物の実装と偽実装の両方が同じスイートを満たすことを確かめる。ランタイムをまたぐデータの形もここで確かめる |

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
| 突き合わせのキーは文書コメントに置いた宣言行。テスト関数の名前は突き合わせに使わない。仕様の語彙をそのまま識別子にできる言語でしか成立しないため |
| テスト関数の命名は対象言語の慣習に従う（PythonならASCIIのsnake_case） |
| 仕様のシナリオに紐づかないテストは、シナリオ対応テストとは別のファイルへ置く。混ぜると常に孤立として報告され続け、警報が意味を失う |
| 2つのランタイムが同じシナリオを実装する場合、両方のテストが同じ宣言行を持つ。どちらか一方しか無い状態を、実装が揃っていることと取り違えない |
| エッジランタイムの振る舞いは、配る形そのものに対して確かめる。手元のコードだけを確かめても、実行環境の制約で落ちる差分を捕まえられない |

---

## シナリオdocstring

- **スタイル**: テスト関数の文書コメント（docstring）内に、先頭の宣言行「Scenario: {シナリオ名}」と、続くGiven/When/Thenをそのまま記載する
- **対象**: usecase specのacceptanceScenarios/guaranteeScenarios、aggregate specのinvariantScenariosに対応する全テスト関数

### 転記の指針

文書コメントには、対応する仕様のシナリオの宣言行とGiven/When/Thenを、言い換えず一字一句そのまま転記する。宣言行は突き合わせのキーそのもの、本文はシナリオ文言の事後編集への追従を検知する材料であり、役割が異なる。

```
def test_suspended_artifact_cannot_be_viewed():
    """
    Scenario: 公開を止めると閲覧トークンで開けない
    Given 公開されているアーティファクト
    When 公開を止める
    Then 閲覧トークンで開けない
    """
```

---

## テスト対象別の配置

- **置き方**: layer-first

| レイヤー | テスト種別 | 配置 | 置き方（個別） | 接尾辞 | 補足 |
|---|---|---|---|---|---|
| domain | `unit` | `.waffle/skills/artifact-share/tests/domain/unit/` |  |  | 配置はリポジトリ直下からの道で書く。検査はここをそのまま探すので、根を別に渡して補う仕組みは無い |
| application | `unit` | `.waffle/skills/artifact-share/tests/application/unit/` |  |  |  |
| application | `acceptance` | `.waffle/skills/artifact-share/tests/application/acceptance/` |  |  |  |
| application | `integration` | `.waffle/skills/artifact-share/tests/application/integration/` |  |  |  |
| application | `contract` | `.waffle/skills/artifact-share/tests/application/contract/` |  |  | port は層ではなく application が所有する要素なので、その契約テストも application の下に置く。同じ契約スイートを本物と偽実装の両方に対して実行する |
| inbound adapter | `contract` | `.waffle/skills/artifact-share/tests/adapters/inbound/contract/` |  |  | 閲覧ゲートの振る舞いもここで確かめる。エッジランタイムは層を持たないため、入口としてまとめて扱う |
| outbound adapter | `integration` | `.waffle/skills/artifact-share/tests/adapters/outbound/integration/` |  |  |  |

---

## 決定ルール

| 種別 | 規約 |
|---|---|
| 禁止 | 単体テストが実物のAWSサービスに依存する |
| 推奨 | 不変条件はテストダブルなしで検証する |
| 必須 | テストファイル名は test_{対応するspecのdocumentIdをsnake_case化したもの}.py で統一する |
| 必須 | tests/ 配下は architecture が宣言するレイヤーを第一階層とし、テスト種別を第二階層とする |
| 必須 | port の契約テストは、本物の実装とテスト用の偽実装の両方が同じテストスイートを満たすことを確認する |
| 禁止 | 同じ port の偽実装を複数のテストファイルに分けて定義する。少しずつ食い違い、実物なら失敗する場面で偽実装が成功してテストが緑になる |
| 必須 | 時刻・乱数・ID生成のような非決定的な値は、テストダブルで決定的な値に固定する |
| 禁止 | 仕様の記述に、テスト層・アーキテクチャ層の内部語彙を持ち込む |
