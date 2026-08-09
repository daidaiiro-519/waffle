---
id: "uc-check-verification-gate"
type: "usecase"
title: "実装完了→検証フェーズへ進んでよいかを機械的に判定する：CheckVerificationGate"
description: "対象usecase specのacceptanceScenariosと実装済みテストの対応関係、および渡されたテスト実行結果から、検証フェーズへ進んでよいか（ready/blocked/needs_human）を判定する。"
schemaRef: "DomainSpecSchema/v8"
---

# 実装完了→検証フェーズへ進んでよいかを機械的に判定する：CheckVerificationGate

## 概要

- 対象usecase specのacceptanceScenariosと実装済みテストの対応関係、および渡されたテスト実行結果から、検証フェーズへ進んでよいか（ready/blocked/needs_human）を判定する。

---

## 存在意義

- spec-first+TDDというWaffle自身の開発プロセスでは、「テストを書いた」ことと「specの受け入れシナリオを実際に満たすテストを書いた」ことは同じではない。この区別を人間の目視確認に委ねると見落としが起き、フェーズを次に進めてよいかの判断が属人化する。
- 既存のcheck_scenario_drift（spec⇄テストの対応関係の検知）は差分を検出するだけで、「だから次に進んでよいか」という判断までは行わない。判断まで含めて機械化する経路が無いと、Orchestratorは毎回同じ判断ロジックを即興で組み立てることになり、判定基準がセッションごとにぶれる。

---

## 主アクターと意図

### 主アクター

Orchestrator（HarnessAgent）

### 意図

対象usecase specについて、実装完了フェーズから検証フェーズへ進んでよいかを判定したい

---

## 事前条件

- 対象usecase specのpathが要望テキストで与えられている
- 対象specに対応するネイティブテストファイルのpathが要望テキストで与えられている
- 通ったテストと落ちたテストを記録した実行結果のファイルのpathが要望テキストで与えられている。ここに並ぶのはテスト実行環境が報告する識別子（テストの名前）であって、シナリオ名ではない。両者は別の語彙であり、対応づけはspec⇄テストの照合結果が持つ対で行う

---

## 入力

| 入力 | 説明 |
|---|---|
| `specPath` | 検査の対象とする仕様のパス |
| `testPath` | 対応するテストファイルのパス |
| `testResultsPath` | 通ったテストと落ちたテストを記録した、実行結果のパス |
| `architectureRef` | シナリオ照合の規約を引くarchitecture documentのdocumentId |

---

## 基本フロー

```mermaid
sequenceDiagram
    actor Orchestrator
    Orchestrator->>VerificationGate: specPath, testFilePath, testResultsPathを指定して判定を依頼する
    VerificationGate->>VerificationGate: spec⇄テストの対応関係を照合し、差分（未実装・孤立・文言不一致・宣言行の重複・spec内の宣言行の食い違い）と、対応が取れた組（シナリオ名とテスト名の対）を得る
    VerificationGate->>VerificationGate: 対応が取れた組のテスト名側と、実行結果のfailedを交差させる。交差が空でも、failedに未知の識別子が並んでいれば識別子の不整合として扱い、readyへ進まない
    VerificationGate-->>Orchestrator: status（ready/blocked/needs_human）と、シナリオ名で表したreasonsを返す
```

---

## 事後条件

- 判定結果がstatus（ready/blocked/needs_human）として返る
- statusの根拠がreasonsとして返る（人間が理由を確認できる）
- 実行結果との突き合わせはテスト名で行い、人間へ返す根拠はシナリオ名で表す。2つの語彙を1つの文字列に兼ねさせない
- 本usecaseはテストを実行しない・specやテストファイルを書き換えない（読み取り専用・副作用なし）

---

## 受け入れ基準

- When specのacceptanceScenariosに対応するテストが1件以上未実装（missing_in_tests）のとき、システムはstatus blocked を返す shall。
- When 実装済みテストのうちspecに存在しないもの（orphaned_in_tests）、Gherkinと内容が一致しないもの（gherkin_mismatches）、同じ宣言行を複数のテストが名乗っているもの（duplicate_declarations）、spec自身の宣言行が名前と食い違うもの（spec_declaration_mismatches）が1件以上あるとき、システムはstatus needs_human を返す shall（意図的な追加か更新漏れかを機械的に判別できないため）。
- When spec⇄テストの対応関係に差分が無いが、対応するテストの実行結果に1件以上failedが含まれるとき、システムはstatus blocked を返す shall。ここでの突き合わせは、照合結果が持つ対のテスト名側と実行結果のfailedを交差させて行う shall（シナリオ名と交差させると、両者が別の語彙であるため常に空集合になり、全テストが落ちていてもreadyを返す）。
- When 実行結果のfailedに、照合結果のどの対のテスト名とも一致しない識別子だけが含まれるとき、システムはreadyを返さず、識別子の不整合をreasonsに含めて needs_human を返す shall（交差が空であることを、落ちたテストが無いことと同一視しない）。
- When spec⇄テストの対応関係に差分が無く、対応する全テストがpassedであるとき、システムはstatus ready を返す shall。
- While 複数の条件に同時に該当するとき、システムはblocked/needs_human/readyの優先順位（missing_in_tests最優先、次にorphaned/mismatch/duplicate/spec_declaration_mismatch、次にfailed、最後にready）で単一のstatusを決定する shall。
- When statusを返すとき、システムはその根拠をreasonsに含める shall。reasonsにはシナリオ名を用いる shall（人間が読む面はspecの語彙で表す）。
- If specPathが存在しないとき、システムはINVALID_PATHエラーを返す shall。
- If testFilePathが存在しないとき、システムはINVALID_PATHエラーを返す shall。
- If testResultsPathが存在しない、またはJSONとして解釈できないとき、システムはINVALID_TEST_RESULTSエラーを返す shall。

---

## 操作保証

- While 同一の入力で複数回実行しても、システムは同じstatusを返す shall（副作用の無い読み取り専用操作）。
- When 判定を行うとき、システムはテスト自体を実行しない shall（既に生成済みのtestResultsPathを読むのみ。実行はOrchestrator側の責務）。

---

## エラー

| コード | 条件 |
|---|---|
| `INVALID_PATH` | - specPathまたはtestFilePathが存在しない |
| `INVALID_TEST_RESULTS` | - testResultsPathが存在しない、またはJSONとして解釈できない |

---

## 受け入れシナリオ

### 未実装のシナリオがあるときはblockedを返す

| 分類 | 観点 |
|---|---|
| 正常系 | 判定：missing_in_testsが1件以上あればblocked |

```gherkin
Scenario: 未実装のシナリオがあるときはblockedを返す
  Given specのacceptanceScenariosに対して未実装のシナリオを1件含む対象
  When CheckVerificationGateを実行する
  Then statusはblockedであり、reasonsに未実装のシナリオが含まれる
```

### 意図不明なズレがあるときはneeds_humanを返す

| 分類 | 観点 |
|---|---|
| 正常系 | 判定：orphaned_in_tests/gherkin_mismatchesが1件以上あればneeds_human |

```gherkin
Scenario: 意図不明なズレがあるときはneeds_humanを返す
  Given specに無いテスト（orphaned_in_tests）を1件含む対象
  When CheckVerificationGateを実行する
  Then statusはneeds_humanであり、reasonsにそのズレが含まれる
```

### 対応関係に差分は無いがテストが失敗しているときはblockedを返す

| 分類 | 観点 |
|---|---|
| 正常系 | 判定：spec⇄テストの対応は取れているがfailedが1件以上あればblocked |

```gherkin
Scenario: 対応関係に差分は無いがテストが失敗しているときはblockedを返す
  Given spec⇄テストの対応関係に差分が無く、1件failedを含むテスト実行結果
  When CheckVerificationGateを実行する
  Then statusはblockedであり、reasonsに失敗したテスト名が含まれる
```

### 対応関係に差分が無く全テストが成功しているときはreadyを返す

| 分類 | 観点 |
|---|---|
| 正常系 | 判定：差分無し・全passedならready |

```gherkin
Scenario: 対応関係に差分が無く全テストが成功しているときはreadyを返す
  Given spec⇄テストの対応関係に差分が無く、全てpassedのテスト実行結果
  When CheckVerificationGateを実行する
  Then statusはreadyである
```

### 複数条件に該当するときは優先順位に従い単一のstatusを返す

| 分類 | 観点 |
|---|---|
| 境界値 | 優先順位：missing_in_tests > orphaned/mismatch > failed > ready |

```gherkin
Scenario: 複数条件に該当するときは優先順位に従い単一のstatusを返す
  Given missing_in_testsとorphaned_in_testsを同時に含む対象
  When CheckVerificationGateを実行する
  Then statusはblockedである（missing_in_testsが最優先）
```

### 存在しないspecPathはエラーを返す

| 分類 | 観点 |
|---|---|
| 異常系 | エラー：specPathが存在しないときはINVALID_PATH |

```gherkin
Scenario: 存在しないspecPathはエラーを返す
  Given 実在しないspecPath
  When CheckVerificationGateを実行する
  Then INVALID_PATH エラーが返る
```

### 存在しないtestFilePathはエラーを返す

| 分類 | 観点 |
|---|---|
| 異常系 | エラー：testFilePathが存在しないときはINVALID_PATH |

```gherkin
Scenario: 存在しないtestFilePathはエラーを返す
  Given 実在しないtestFilePath
  When CheckVerificationGateを実行する
  Then INVALID_PATH エラーが返る
```

### 不正なtestResultsPathはエラーを返す

| 分類 | 観点 |
|---|---|
| 異常系 | エラー：testResultsPathが存在しない、またはJSONとして不正なときはINVALID_TEST_RESULTS |

```gherkin
Scenario: 不正なtestResultsPathはエラーを返す
  Given 存在しない、またはJSONとして不正なtestResultsPath
  When CheckVerificationGateを実行する
  Then INVALID_TEST_RESULTS エラーが返る
```

### 落ちたテストはテスト名で突き合わせて検出する

| 分類 | 観点 |
|---|---|
| 境界値 | 計算整合: 実行結果はテスト名、specはシナリオ名という別の語彙。対応が取れた組のテスト名側で交差しないと、交差は常に空になる |

```gherkin
Scenario: 落ちたテストはテスト名で突き合わせて検出する
  Given 対応関係に差分が無く、シナリオ名とは異なる名前のテストが1件failedである実行結果
  When 検証ゲートの判定を実行する
  Then status blocked が返る
  And reasonsにそのシナリオ名が含まれる
```

### 実行結果の識別子が対応表と噛み合わないときreadyを返さない

| 分類 | 観点 |
|---|---|
| 異常系 | 事前条件: 交差が空であることを、落ちたテストが無いことと同一視すると、全テストが落ちていてもreadyになる |

```gherkin
Scenario: 実行結果の識別子が対応表と噛み合わないときreadyを返さない
  Given 対応関係に差分が無く、failedにどの対のテスト名とも一致しない識別子だけが並ぶ実行結果
  When 検証ゲートの判定を実行する
  Then status ready は返らない
  And reasonsに識別子の不整合が含まれる
```

### 同じ宣言行を複数のテストが名乗っているときneeds_humanを返す

| 分類 | 観点 |
|---|---|
| 異常系 | ドリフト: どのテストがそのシナリオを検証しているかが決まらない状態を、通過させない |

```gherkin
Scenario: 同じ宣言行を複数のテストが名乗っているときneeds_humanを返す
  Given 同一の宣言行を2件のテストが名乗っている状態
  When 検証ゲートの判定を実行する
  Then status needs_human が返る
```

---

## 操作保証シナリオ

### 同一入力での再実行はべき等である

| 分類 | 観点 |
|---|---|
| 正常系 | べき等性：同一のspecPath/testFilePath/testResultsPathを2回実行しても結果が一致する |

```gherkin
Scenario: 同一入力での再実行はべき等である
  Given CheckVerificationGate システム と同一の入力
  When 2回連続で実行する
  Then 2回の結果は完全に一致する
```
