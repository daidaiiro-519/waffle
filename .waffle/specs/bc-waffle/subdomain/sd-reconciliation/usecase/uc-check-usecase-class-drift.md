---
id: "uc-check-usecase-class-drift"
type: "usecase"
title: "操作名と実装クラス名の一致を検証する：CheckUsecaseClassDrift"
description: "usecase specが宣言する操作名(operationName)と、対応する実装クラスが実際に持つクラス名が一致しているかを機械的に検証する。宣言と実装クラスの対応関係という、他のどのreconcile usecaseも見ていない盲点を検出する。"
schemaRef: "DomainSpecSchema/v8"
---

# 操作名と実装クラス名の一致を検証する：CheckUsecaseClassDrift

## 概要

- usecase specが宣言する操作名(operationName)と、対応する実装クラスが実際に持つクラス名が一致しているかを機械的に検証する。宣言と実装クラスの対応関係という、他のどのreconcile usecaseも見ていない盲点を検出する。

---

## 存在意義

- usecase specのoperationNameと実装クラス名が乖離したまま放置されると、specが実装から乖離した「違うモデル」を宣言し続けることになり、DDDのモデル駆動設計（モデルはコードに宿る）の前提が崩れる。この検知が無ければ、リネームの片方だけ反映し忘れる、といった典型的なドリフトに誰も気づけない。

---

## 主アクターと意図

### 主アクター

Orchestrator（HarnessAgent）

### 意図

usecase specの操作名と実装クラス名が一致しているかを確認したい

---

## 事前条件

- Document集約の実インスタンス群を走査する対象ディレクトリ（documents_root）が与えられている
- usecase実装クラスの配置ルートディレクトリ（src_root）が与えられている
- 実装言語（language）が与えられている。省略時はpython

---

## 入力

| 入力 | 説明 |
|---|---|
| `documentsRoot` | 仕様側の走査範囲。未指定なら architectureRef が受け持つコンテキストから決まる |
| `srcRoot` | usecase実装クラスの配置ルートディレクトリ（明示指定時は--architectureRefより優先） |
| `architectureRef` | srcRoot未指定時に参照するarchitecture documentのdocumentId（例: architecture-waffle） |
| `language` | 実装言語（python/java/typescript/javascript） |

---

## 基本フロー

```mermaid
sequenceDiagram
    Orchestrator->>UsecaseClassTree: documents_root/src_rootを指定してクラス名ドリフト検査を依頼する
    UsecaseClassTree->>UsecaseClassTree: documents_root配下のusecase document(specKind=usecase)を走査し、各documentのcontent.name.operationNameを集める
    UsecaseClassTree->>UsecaseClassTree: 各operationNameをsnake_caseに変換し、対応する実装ファイル（src_root配下）が実在するかを確認する
    UsecaseClassTree->>UsecaseClassTree: 実在するファイルをASTで解析してクラス定義名を抽出し、operationNameと一致するクラスが含まれるか確認する
    UsecaseClassTree-->>Orchestrator: missing_implementation_file・class_name_mismatchの2つのオブジェクト配列を返す
```

---

## 事後条件

- 返り値は次の2フィールドを持つ: missing_implementation_file（operationNameから導出したファイルパスが実在しないusecaseの組）・class_name_mismatch（実装ファイルは実在するが、operationNameと一致するクラス定義が含まれていないusecaseの組）
- ファイルパスの導出は、operationNameをsnake_caseに変換し（例: CheckScenarioDrift→check_scenario_drift）、src_root配下に{name}.pyとして配置されている前提で行う
- クラス名の抽出はASTのみで行い、実行や意味理解はしない（宣言された名前と、実装ファイル内に存在するクラス定義名の機械的な突き合わせのみ）
- missing_implementation_file・class_name_mismatchの両方が空配列であれば、全usecaseの操作名と実装クラスが一致している（正常系）

---

## 受け入れ基準

- When usecase specのoperationNameから導出したファイルパスが実在しないとき、システムはその組をmissing_implementation_fileに含める shall。
- When 実装ファイルは実在するが、operationNameと一致するクラス定義がそのファイル内に見つからないとき、システムはその組をclass_name_mismatchに含める shall。
- While 全usecaseの操作名と実装クラスが一致しているとき、システムはmissing_implementation_file・missing_implementation_in_scope・class_name_mismatchの3つ全てを空配列で返す shall。
- If 対象のdocuments_rootまたはsrc_rootが存在しないとき、システムはINVALID_PATHエラーを返す shall。
- If languageがサポート対象外のとき、システムはUNSUPPORTED_LANGUAGEエラーを返す shall。
- While languageが指定されないとき、システムはpythonとして扱う shall。
- When 概念ごとの探索範囲を決めるとき、システムはarchitectureのlayout.granularityがその概念にperFileを宣言していればファイル単位、宣言していなければconceptPlacementが与える配置ディレクトリ単位とする shall（配置を決める権限はarchitectureにあり、この操作は宣言を読むだけで独自の規則を持たない）。
- When 操作がディレクトリ単位で探すと宣言されていて、操作名と一致するクラス定義がその配置ディレクトリのどこにも見つからないとき、システムはその組をmissing_implementation_in_scopeに含める shall（探した範囲を伝えるため、1つの道を指すexpectedPathではなくsearchedRootを持たせる）。
- While 操作がファイル単位で探すと宣言されているとき、システムは操作名から導出したファイルパスの不在のみをmissing_implementation_fileに含め、ディレクトリ単位の報告を行わない shall（2つの探し方の結果を同じ器に入れると、受け手が同じキーから読むべき意味を決められなくなるため）。
- While granularityがその概念にperFileを宣言していないとき、システムは検査を中断せず、ディレクトリ単位の探索を続ける shall（宣言が無いことは引数の誤りではなく、そのプロジェクトがまだ決めていないという事実であり、報告して先へ進む）。

---

## 操作保証

- When 対象のdocuments_rootまたはsrc_rootが存在しないとき、システムは INVALID_PATH エラーを返す shall（対象を特定し取得する解決プロセス自体の契約であり、複数のusecaseに共通する）。

---

## エラー

| コード | 条件 |
|---|---|
| `INVALID_PATH` | - documents_rootまたはsrc_rootが存在しない、またはパストラバーサルを含む |
| `UNSUPPORTED_LANGUAGE` | - languageがサポート対象外（python/java/typescript/javascript以外） |

---

## 受け入れシナリオ

### 全usecaseの操作名と実装クラスが一致するとき差分なしと判定する

| 分類 | 観点 |
|---|---|
| 正常系 | 整合：全operationNameが対応する実装ファイル内の同名クラスと一致するとき正常系（空配列） |

```gherkin
Scenario: 全usecaseの操作名と実装クラスが一致するとき差分なしと判定する
  Given 全usecaseのoperationNameが、対応する実装ファイル内の同名クラスと一致するspecツリー
  When クラス名ドリフト検査を実行する
  Then missing_implementation_file・class_name_mismatch両方が空配列で返る
```

### 実装ファイルが存在しないusecaseを検出する

| 分類 | 観点 |
|---|---|
| 異常系 | ドリフト：operationNameから導出したファイルが実在しない |

```gherkin
Scenario: 実装ファイルが存在しないusecaseを検出する
  Given operationNameから導出したファイルパスに対応する実装ファイルが実在しないusecase document
  When クラス名ドリフト検査を実行する
  Then missing_implementation_fileにその組が含まれる
```

### クラス名が一致しないusecaseを検出する

| 分類 | 観点 |
|---|---|
| 異常系 | ドリフト：実装ファイルは実在するがoperationNameと一致するクラスが無い |

```gherkin
Scenario: クラス名が一致しないusecaseを検出する
  Given 実装ファイルは実在するが、operationNameと一致するクラス定義を持たないusecase document
  When クラス名ドリフト検査を実行する
  Then class_name_mismatchにその組が含まれる
```

### Java実装に対してもクラス名ドリフトを検知できる

| 分類 | 観点 |
|---|---|
| 正常系 | 計算整合: 検知が対象言語に依らず成立すること |

```gherkin
Scenario: Java実装に対してもクラス名ドリフトを検知できる
Given languageにjavaを指定し、operationNameと一致するJavaクラスを持つ実装ファイル
When クラス名ドリフト検査を実行する
Then 対象言語に依らず正しく一致と判定される
```

### 宣言がなければ配置ディレクトリのどこにも無いことを報告する

| 分類 | 観点 |
|---|---|
| 正常系 | 宣言に従う：探し方が変われば報告の器も変わる |

```gherkin
Scenario: 宣言がなければ配置ディレクトリのどこにも無いことを報告する
  Given granularityがusecaseにperFileを宣言していないarchitecture
  And 操作名と一致するクラスが配置ディレクトリのどこにも無い
  When 操作と実装の食い違いを調べる
  Then その組がmissing_implementation_in_scopeに現れる
  And 探した配置ディレクトリがsearchedRootとして添えられている
  And missing_implementation_fileは空のままである
```

### 宣言があればファイルの不在だけを報告する

| 分類 | 観点 |
|---|---|
| 正常系 | 宣言に従う：2つの探し方の結果を混ぜない |

```gherkin
Scenario: 宣言があればファイルの不在だけを報告する
  Given granularityがusecaseにperFile 1を宣言しているarchitecture
  And 操作名から導出したファイルが存在しない
  When 操作と実装の食い違いを調べる
  Then その組がmissing_implementation_fileに現れる
  And missing_implementation_in_scopeは空のままである
```

---

## 操作保証シナリオ

### 存在しないdocuments_rootはINVALID_PATH

| 分類 | 観点 |
|---|---|
| 異常系 | エラー：走査起点の不在 |

```gherkin
Scenario: 存在しないdocuments_rootはINVALID_PATH
  When 存在しないdocuments_rootでクラス名ドリフト検査を実行する
  Then INVALID_PATHエラーが返る
```
