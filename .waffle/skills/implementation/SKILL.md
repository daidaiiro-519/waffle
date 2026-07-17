---
name: "implementation"
description: "VALIDATED以上のspec、および必要に応じてHandoffに記録された設計観点・実装観点をもとに、実際のソースコードを実装する必要があるときに使う。TDD（Red→Green→必要ならRefactor）で進める。"
---

# implementation

## 目的

VALIDATED以上のspec、および必要に応じてHandoffに記録された設計観点・実装観点をもとに、実際のソースコードを実装する必要があるときに使う。TDD（Red→Green→必要ならRefactor）で進める。

---

## 役割

- 対象specおよび受け取った設計観点・実装観点を根拠に、実装方針を立てる
- TDDでネイティブテストを先に書き、実装する
- 受け取った判断材料（設計観点・実装観点）に反する実装をしない

---

## 処理対象と成果物

### 処理対象

VALIDATED以上のspecと、必要に応じて既に確定しているHandoffの設計観点・実装観点。

### 成果物

specのacceptanceScenarios/acceptanceCriteriaを満たすソースコード（実装とネイティブテスト）。document.jsonではない。

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| 対象spec（specRef） | VALIDATED以上のstatusを持つspecであることを前提とする。明示されなければ呼び出し元に確認する。 |
| Handoffに記録された設計観点・実装観点（あれば） | 既に呼び出し元から与えられているものとして受け取る。無い場合はspecのacceptanceScenarios/acceptanceCriteriaのみを根拠に進める。 |

---

## 実行手順

### Step 1: 対象specの受け入れ基準を確認する

対象specのacceptanceScenarios/acceptanceCriteriaを確認し、実装すべき振る舞いを把握する。

### Step 2: テストを先に書く（Red）

acceptanceScenariosのGherkinをもとに、対応するネイティブテストを先に書く。まだ実装が無いため失敗することを確認する。

### Step 3: 実装する（Green）

テストが通る最小限の実装を行う。

### Step 4: 必要に応じて整理する（Refactor）

テストが通った状態を保ったまま、重複や分かりにくさを整理する。

---

## 出力形式

変更したファイルの一覧と、テスト実行結果を報告する。

---

## ガードレール

- VALIDATED未満のstatusのspecを根拠に実装しない
- テストより先に実装を書かない（Red→Green→必要ならRefactorの順を守る）
- 受け取った設計観点・実装観点に反する実装をしない。矛盾する場合は実装を進めず呼び出し元に確認する
- このSkillはCodingSchema等のドキュメント作成ではなく、実際のソースコード実装そのものを指す
