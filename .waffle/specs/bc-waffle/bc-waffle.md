# スキーマ駆動でDocumentを検証・生成・描画する境界づけられたコンテキスト：bc-waffle

## 概要

- waffle の中核機能群が属する文脈。document.json を唯一の正とし、AI が構造を推論せず システムが機械的に読み書き・生成・描画する（Harness 原則）。

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
| `reconcile` | スペックが嘘をつかないよう、7種類のドリフト（スペック内部の参照整合性・スペックとテストシナリオの対応関係・Document集約とSchema版の対応関係・usecase操作名と実装クラス名の対応関係・集約仕様と実装Entity/ValueObjectの対応関係・usecase operationの宣言と実装分岐の対応関係・業務サービスのgroupと実装ファイルの対応関係）を機械的に検知し続けること。docstring の構造化抽出・規約適合検証（uc-scan-source-code/uc-lint-docstring）はreconcileが使う部品であり、reconcile本体ではない。 |

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

- uc-scaffold-document
- uc-query-document
- uc-query-document-collection
- uc-validate-document
- uc-render-document
- uc-scan-source-code
- uc-lint-docstring
- uc-check-spec-integrity
- uc-check-scenario-drift
- uc-check-schema-version-drift
- uc-check-usecase-class-drift
- uc-patch-schema
- uc-check-operation-drift
- uc-check-aggregate-class-drift
- uc-check-domain-service-drift
- uc-render-blank-template
- uc-check-verification-gate
- uc-check-query-precedes-array-fill

---

## ドメインサービス

| 業務サービス | 責務 |
|---|---|
| パステンプレート解決 | x-source-target/x-render-target のパステンプレートを document の値で解決(resolve)し、逆に実パスからテンプレート変数を復元(reverse-parse)する。scaffold/render/query の複数usecaseが共通して依存する（特定の集約に属さない）。 |
| 整形描画 | x-render宣言(Schema集約の値オブジェクト)とDocument集約のcontent dataの両方を参照してMarkdownへ整形する。RenderMetaSchemaが定義する部品種別(paragraph/list/table/keyvalue/section/kvtable/sequence/statediagram/architecture/flowchart)ごとに決定的な整形規則を持つ。特定の集約に属さない（Schema集約とDocument集約にまたがる計算）。 |
| discriminatorキー抽出 | schemaのallOf if/then構造から、どのフィールド（specKind/codingKind/skillKind等）がkindのdiscriminatorとして機能しているかを機械的に取り出す。scaffold/renderの複数usecaseが共通して依存する（特定の集約に属さない・Schema集約の構造そのものを読むがSchema集約の外から呼ばれる編成ロジック）。 |
| 後方互換チェック | 変更前後のschema(dict)の差分を計算し、公開済みkindのrequired配列への追加等、既存instanceを壊しうる変更を検出する。特定の集約に属さない純粋な差分計算ロジック。 |
| 契約整形 | schemaファイルの物理的な整形をagg-schemaが定める契約（json.dumps(indent=2, ensure_ascii=False)+改行）に一意に揃える。Schema集約の不変条件を実際に適用する。 |

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
Scenario: paragraph/listが正しく整形される
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
Scenario: sequenceはactor/participantを区別する
  Given kind:actor/participantを含む参加者宣言
  When renderする
  Then actor/participantそれぞれの宣言がMermaid構文で区別される
```

### sequenceはloop・altを入れ子で表現する

| 分類 | 観点 |
|---|---|
| 正常系 | sequenceのloop/alt入れ子保証 |

```gherkin
Scenario: sequenceはloop/altを入れ子で表現する
  Given loop/alt種別のstepを含むsteps配列
  When renderする
  Then loop/altブロックが正しく入れ子のMermaid構文になる
```

### sequenceはactivate・deactivateを表現する

| 分類 | 観点 |
|---|---|
| 境界値 | sequenceのactivate/deactivate保証 |

```gherkin
Scenario: sequenceはactivate/deactivateを表現する
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

### requiredへの追加は後方互換違反として検出される

| 分類 | 観点 |
|---|---|
| 異常系 | 後方互換チェック：公開済みkindのContent defのrequired配列に新規エントリを追加する変更を検出する |

```gherkin
Scenario: requiredへの追加は後方互換違反として検出される
  Given 公開済みのschemaと、あるContent defのrequired配列に新規エントリを追加した変更後schema
  When 後方互換チェックを実行する
  Then 違反として検出される
```

### optionalプロパティの追加は後方互換違反にならない

| 分類 | 観点 |
|---|---|
| 正常系 | 後方互換チェック：requiredに含まれない新規プロパティの追加は既存instanceを壊さない |

```gherkin
Scenario: optionalプロパティの追加は後方互換違反にならない
  Given 公開済みのschemaと、requiredに含めずに新規プロパティのみ追加した変更後schema
  When 後方互換チェックを実行する
  Then 違反として検出されない
```

### 契約整形はjson.dumpsの出力と完全一致する

| 分類 | 観点 |
|---|---|
| 正常系 | 契約整形：schemaファイルの物理整形がagg-schemaの不変条件と一致する |

```gherkin
Scenario: 契約整形はjson.dumpsの出力と完全一致する
  Given 任意の整形が施されたschema(dict)
  When 契約整形を適用する
  Then 出力はjson.dumps(schema, indent=2, ensure_ascii=False)+改行と完全一致する
```
