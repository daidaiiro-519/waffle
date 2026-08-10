---
id: "bc-waffle"
type: "bounded-context"
title: "スキーマ駆動でDocumentを検証・生成・描画する境界づけられたコンテキスト：bc-waffle"
description: "決められた型を持つ文書を扱う文脈。型どおりに書かれているかを確かめ、型から値の入っていない雛形を起こし、人が読める形へ書き起こすところまでを内側に含む。加えて、書かれた内容と実際の作られたものが食い違っていないかを突き合わせることも、この文脈が担う。 文書を誰にどこまで見せるか、受け取った相手からどんな意見が返るかは、この文脈の外側にある。ここで扱うのは、書かれたものが型を満たしているか、型から何を起こせるか、型と実物が食い違っていないかの3つだけであり、文書が述べている業務そのものの当否は扱わない。"
tags: ["context:waffle"]
schemaRef: "DomainSpecSchema/v8"
---

# スキーマ駆動でDocumentを検証・生成・描画する境界づけられたコンテキスト：bc-waffle

## 名前

スキーマ駆動Document基盤

---

## 概要

- 決められた型を持つ文書を扱う文脈。型どおりに書かれているかを確かめ、型から値の入っていない雛形を起こし、人が読める形へ書き起こすところまでを内側に含む。加えて、書かれた内容と実際の作られたものが食い違っていないかを突き合わせることも、この文脈が担う。
- 文書を誰にどこまで見せるか、受け取った相手からどんな意見が返るかは、この文脈の外側にある。ここで扱うのは、書かれたものが型を満たしているか、型から何を起こせるか、型と実物が食い違っていないかの3つだけであり、文書が述べている業務そのものの当否は扱わない。

---

## ユビキタス言語

| 用語 | 定義 |
|---|---|
| `Document` | schema で構造を定義された JSON の成果物単位（spec / skill / coding 等）。 |
| `Schema` | Document の構造・描画(x-render)・記入/読取指示(x-prompt)を定義する JSON Schema。 |
| `Harness原則` | AI はファイルを直接読まず値だけを埋め、システムが一切の構造アクセス・生成を担う原則。 |
| `意味単位` | ブロック / フィールド / 条件一致 / 全階層など、Document の意味のある取得単位。 |
| `prompt(読み方指針)` | 取得した value をどう解釈するかの指針。schema の x-prompt-query 由来。 |
| `骨格(scaffold)` | schema を機械走査して生成した、値が空の schema 準拠 Document の雛形。 |
| `UDD ループ` | Spec を正本とし、検証・描画・受け入れテストを通じて仕様と実装の整合を保つ開発サイクル。 |
| `不変条件` | 集約が常に満たす業務ルール。static は schema、dynamic は guard が守る。 |
| `reconcile` | スペックが嘘をつかないよう、宣言と実装の対応が食い違っていないかを機械的に検知し続けること。docstring の構造化抽出や規約への適合判定は、この検知が使う部品であって、reconcile 自体ではない。 |

---

## 構成要素

### サブドメイン

- sd-document-management
- sd-validation
- sd-source-code
- sd-docstring-linting
- sd-reconciliation
- sd-schema-management
- sd-flow-gate

### 集約

- agg-document
- agg-schema

### 業務ユースケース

- uc-check-aggregate-class-drift
- uc-check-domain-service-drift
- uc-check-layer-drift
- uc-check-operation-drift
- uc-check-path-is-projection
- uc-check-prompt-contract
- uc-check-query-precedes-array-fill
- uc-check-scenario-drift
- uc-check-schema-version-drift
- uc-check-spec-integrity
- uc-check-surface-drift
- uc-check-usecase-class-drift
- uc-check-verification-gate
- uc-export-skill-bundle
- uc-init-coding-preset
- uc-lint-docstring
- uc-patch-schema
- uc-query-document
- uc-query-document-collection
- uc-render-blank-template
- uc-render-document
- uc-render-document-viewer
- uc-render-handoff-template
- uc-scaffold-document
- uc-scan-source-code
- uc-update-coding-preset
- uc-validate-document

---

## ドメインサービス

| 業務サービス | 責務 |
|---|---|
| パステンプレート解決 | Schema集約が宣言するパステンプレート（成果物と原本の置き場所）と、Document集約が持つ値の両方を読んで実際のパスへ解決し、逆に実パスからテンプレート変数を復元する。Schema集約とDocument集約にまたがる計算。 |
| 整形描画 | Schema集約の値オブジェクトが宣言する描画の指定と、Document集約のcontentの両方を参照してMarkdownへ整形する。部品の種別ごとに決定的な整形規則を持つ。Schema集約とDocument集約にまたがる計算。 |
| discriminatorキー抽出 | schemaの分岐構造から、どのフィールドが種別の判別子として働いているかを取り出す。Schema集約1つに閉じるが、その集約は識別子・版・種別ごとの輪郭だけを持ち、schemaの構造そのものを保持していないため、構造を読むこの計算を集約の中に置けない。 |
| ソースルート解決 | 規約が宣言する実装の置き場所（ソースルートと概念ごとの配置）から、指定した概念の実装ファイルの置き場所を導く。規約を表す集約がこの境界づけられたコンテキストにまだ宣言されていないため、いずれの集約にも属せない状態でここに居る。その集約を宣言した時点で、そちらへ戻すかどうかを判断し直す。 |

---

## 業務サービスシナリオ

### パステンプレートは変数を解決する

| 分類 | 観点 |
|---|---|
| 正常系 | パステンプレート解決：{var}形式のプレースホルダを実際の値に置き換える |

```gherkin
Scenario: パステンプレートは変数を解決する
  Given 変数を含むパステンプレートと解決に必要な値
  When resolve する
  Then 全ての変数が値に置き換わった実パスが返る
```

### 逆解析は実パスからテンプレート変数を復元する

| 分類 | 観点 |
|---|---|
| 正常系 | パステンプレート解決：reverse-parseはresolveの逆写像として変数を一意に復元する |

```gherkin
Scenario: 逆解析は実パスからテンプレート変数を復元する
  Given パステンプレートと、そのテンプレートから解決された実パス
  When reverse-parse する
  Then resolve時に使った値と同じ変数が復元される
```

### テンプレートと一致しないパスは復元できない

| 分類 | 観点 |
|---|---|
| 異常系 | パステンプレート解決：構造が一致しない実パスはreverse-parse不能として扱う |

```gherkin
Scenario: テンプレートと一致しないパスは復元できない
  Given テンプレートの区切り構造と一致しない実パス
  When reverse-parse する
  Then 復元は失敗する
```

### paragraph・listが正しく整形される

| 分類 | 観点 |
|---|---|
| 正常系 | paragraph/listの整形保証 |

```gherkin
Scenario: paragraph・listが正しく整形される
  Given paragraph/listを宣言するx-render
  When renderする
  Then paragraphは地の文、listは箇条書きとして整形される
```

### tableはパイプ文字をエスケープしboolを整形する

| 分類 | 観点 |
|---|---|
| 境界値 | tableのセルエスケープ・bool整形保証 |

```gherkin
Scenario: tableはパイプ文字をエスケープしboolを整形する
  Given パイプ文字やbool値を含む行データ
  When tableとしてrenderする
  Then パイプ文字はエスケープされ、boolは✓/-に整形される
```

### sectionは入れ子とitemLabelを整形する

| 分類 | 観点 |
|---|---|
| 正常系 | sectionの入れ子・itemLabel整形保証 |

```gherkin
Scenario: sectionは入れ子とitemLabelを整形する
  Given itemLabelを持つsection宣言と入れ子のeach部品
  When renderする
  Then 各itemの見出しにitemLabelが付与され、入れ子の部品も正しく描画される
```

### keyvalueが正しく整形される

| 分類 | 観点 |
|---|---|
| 正常系 | keyvalueの整形保証 |

```gherkin
Scenario: keyvalueが正しく整形される
  Given keyvalueを宣言するx-render
  When renderする
  Then ラベルと値の組が箇条書きとして整形される
```

### sectionはbadgeで条件付き強調を付与する

| 分類 | 観点 |
|---|---|
| 境界値 | sectionのbadge（条件付き強調）保証 |

```gherkin
Scenario: sectionはbadgeで条件付き強調を付与する
  Given badge条件を満たすitemを含むsection宣言
  When renderする
  Then 条件を満たすitemの見出しにのみ強調語が付与される
```

### tableはmarkFieldで識別子を太字強調する

| 分類 | 観点 |
|---|---|
| 境界値 | tableのmarkField（識別子強調）保証 |

```gherkin
Scenario: tableはmarkFieldで識別子を太字強調する
  Given markFieldが真の行を含むtable宣言
  When renderする
  Then 該当セルが太字＋markSuffixで強調される
```

### statediagramが正しいMermaid構文になる

| 分類 | 観点 |
|---|---|
| 正常系 | statediagramのMermaid構文生成保証 |

```gherkin
Scenario: statediagramが正しいMermaid構文になる
  Given 状態遷移の配列を宣言するx-render
  When renderする
  Then stateDiagram-v2として正しいMermaid構文が生成される
```

### statediagramは疑似状態を表現する

| 分類 | 観点 |
|---|---|
| 境界値 | statediagramの疑似状態（choice/fork/join）保証 |

```gherkin
Scenario: statediagramは疑似状態を表現する
  Given pseudoStatesFromで疑似状態を宣言するx-render
  When renderする
  Then choice/fork/joinの疑似状態宣言がMermaid構文の先頭に出力される
```

### sequenceはactor・participantを区別する

| 分類 | 観点 |
|---|---|
| 境界値 | sequenceのactor/participant区別保証 |

```gherkin
Scenario: sequenceはactor・participantを区別する
  Given kind:actor/participantを含む参加者宣言
  When renderする
  Then actor/participantそれぞれの宣言がMermaid構文で区別される
```

### sequenceはloop・altを入れ子で表現する

| 分類 | 観点 |
|---|---|
| 正常系 | sequenceのloop/alt入れ子保証 |

```gherkin
Scenario: sequenceはloop・altを入れ子で表現する
  Given loop/alt種別のstepを含むsteps配列
  When renderする
  Then loop/altブロックが正しく入れ子のMermaid構文になる
```

### sequenceはactivate・deactivateを表現する

| 分類 | 観点 |
|---|---|
| 境界値 | sequenceのactivate/deactivate保証 |

```gherkin
Scenario: sequenceはactivate・deactivateを表現する
  Given activate/deactivateフラグを持つstep
  When renderする
  Then Mermaidのアクティベーション記法(+/-)が正しく付与される
```

### architectureが正しいMermaid構文になる

| 分類 | 観点 |
|---|---|
| 正常系 | architectureのMermaid構文生成保証 |

```gherkin
Scenario: architectureが正しいMermaid構文になる
  Given zones/connectionsを宣言するx-render
  When renderする
  Then architecture-betaとして正しいMermaid構文が生成される
```

### flowchartが正しいMermaid構文になる

| 分類 | 観点 |
|---|---|
| 正常系 | flowchartのMermaid構文生成保証 |

```gherkin
Scenario: flowchartが正しいMermaid構文になる
  Given stages/transitionsを宣言するx-render
  When renderする
  Then flowchart LRとして正しいMermaid構文が生成される
```

### kvtableは単一行として整形される

| 分類 | 観点 |
|---|---|
| 境界値 | kvtableの単一行整形保証 |

```gherkin
Scenario: kvtableは単一行として整形される
  Given kvtableを宣言するx-render
  When renderする
  Then block自身の値が1行のtableとして整形される
```

### tableはjoin指定で配列セルを結合整形する

| 分類 | 観点 |
|---|---|
| 境界値 | tableのjoin（配列セル結合）保証 |

```gherkin
Scenario: tableはjoin指定で配列セルを結合整形する
  Given join/sepを指定したcolumns宣言と配列値を持つセル
  When renderする
  Then 配列の各要素がjoinテンプレートで整形されsepで連結される
```

### schemaのif直下からdiscriminatorキーを取り出す

| 分類 | 観点 |
|---|---|
| 正常系 | discriminatorキー抽出：トップレベルのif.propertiesの最初のキーを返す |

```gherkin
Scenario: schemaのif直下からdiscriminatorキーを取り出す
  Given トップレベルにif.properties.specKindを持つschema
  When discriminatorキーを抽出する
  Then specKindが返る
```

### schemaのallOf内のifからdiscriminatorキーを取り出す

| 分類 | 観点 |
|---|---|
| 正常系 | discriminatorキー抽出：allOfの各要素のif.propertiesを走査し最初に見つかったキーを返す |

```gherkin
Scenario: schemaのallOf内のifからdiscriminatorキーを取り出す
  Given トップレベルにはifを持たないが、allOf内の要素にif.properties.codingKindを持つschema
  When discriminatorキーを抽出する
  Then codingKindが返る
```

### discriminatorが無いschemaはNoneを返す

| 分類 | 観点 |
|---|---|
| 境界値 | discriminatorキー抽出：ifもallOf内のifも持たないschemaは分岐を持たない |

```gherkin
Scenario: discriminatorが無いschemaはNoneを返す
  Given ifもallOfも持たないschema
  When discriminatorキーを抽出する
  Then Noneが返る
```

### 実装の置き場所は、ソースルートと概念の配置を結合して決まる

| 分類 | 観点 |
|---|---|
| 正常系 | 計算整合: 宣言だけから実装の置き場所を導く（推測しない） |

```gherkin
Scenario: 実装の置き場所は、ソースルートと概念の配置を結合して決まる
  Given {package}トークンを含むsourceRootと、usecase概念のplacement
  When resolve_source_rootをpackage変数付きで実行する
  Then sourceRoot/placementの形に解決される
```

### ソースルートに変数が無ければ、渡された値は無視される

| 分類 | 観点 |
|---|---|
| 境界値 | 計算整合: 宣言だけから実装の置き場所を導く（推測しない） |

```gherkin
Scenario: ソースルートに変数が無ければ、渡された値は無視される
  Given プレースホルダを含まないsourceRoot（TypeScript版の慣習）
  When package変数を渡してresolve_source_rootを実行する
  Then package変数は無視され、sourceRoot/placementがそのまま結合される
```

### ソースルートが宣言されていなければ解決しない

| 分類 | 観点 |
|---|---|
| 境界値 | 計算整合: 宣言だけから実装の置き場所を導く（推測しない） |

```gherkin
Scenario: ソースルートが宣言されていなければ解決しない
  Given sourceRootフィールドを持たないlayout
  When resolve_source_rootを実行する
  Then Noneが返る
```

### 宣言に無い概念は解決しない

| 分類 | 観点 |
|---|---|
| 境界値 | 計算整合: 宣言だけから実装の置き場所を導く（推測しない） |

```gherkin
Scenario: 宣言に無い概念は解決しない
  Given conceptPlacementに存在しないconcept名
  When resolve_source_rootを実行する
  Then Noneが返る
```

### 規約の識別子から製品名を取り出す

| 分類 | 観点 |
|---|---|
| 正常系 | 計算整合: 宣言だけから実装の置き場所を導く（推測しない） |

```gherkin
Scenario: 規約の識別子から製品名を取り出す
  Given "architecture-waffle"のようなarchitectureRef（documentId）とcodingKind
  When package_name_from_referenceを実行する
  Then "architecture-"接頭辞を剥がしたproduct名が返る
```

### 識別子の種別が食い違えば製品名を取り出さない

| 分類 | 観点 |
|---|---|
| 境界値 | 境界: 取り出せる場合と取り出せない場合の対 |

```gherkin
Scenario: 識別子の種別が食い違えば製品名を取り出さない
  Given codingKindのプレフィックスと一致しないarchitectureRef
  When package_name_from_referenceを実行する
  Then Noneが返る
```
