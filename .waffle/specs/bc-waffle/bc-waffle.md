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
| `ドメイン駆動設計` | 業務の言葉でモデルを作り、その言葉のまま実装へ運ぶ設計の考え方。この文脈では土台として置く。 |
| `境界づけられたコンテキスト` | ある言葉が一貫した意味を持ち続けられる範囲であり、そのモデルが実装として独立している範囲。 |
| `業務領域（サブドメイン）` | 事業活動を細分化した業務活動の単位。自社で作り込むか既製品に任せるかを判断するための分類を持つ。 |
| `集約` | まとめて一貫していなければならない範囲。状態を変える経路を自分の操作だけに絞る。 |
| `エンティティ` | 同一性を持ち、状態が移り変わっても同じものだと言える構成要素。 |
| `値オブジェクト` | 同一性を持たず、持つ値だけで等しさが決まる構成要素。 |
| `業務サービス` | 集約の内側に置けない業務上の計算や判断。状態を持たない。 |
| `業務ユースケース` | 誰かが目的を持って行う一連の業務。呼び出せる操作を持つ。 |
| `不変条件` | 集約が操作をまたいで常に満たす業務上の主張。構造の宣言が言えることは、ここへ重ねて書かない。 |
| `ユビキタス言語` | 境界の内側で、業務に詳しい人と作る人が同じ意味で使う言葉。 |
| `腐敗防止層` | 外の文脈のモデルをそのまま取り込まず、こちらの言葉へ翻訳して受け取る仕組み。 |
| `受け入れ基準` | その要素が満たすべきことを1つの主張として述べたもの。 |
| `シナリオ` | 受け入れ基準を満たしていると言える、システムを1回通した筋書き。実装へ転写される単位。 |
| `転写` | 仕様に書かれたシナリオの文言を、そのまま実装側の検証へ写すこと。 |
| `照合` | 写した文言が食い違っていないかを機械が突き合わせること。 |
| `意味的整合` | 振る舞いが仕様どおりであること。受け入れ基準とシナリオの転写と照合で担保する。 |
| `構造的整合` | 在るべきものが在るべき形で在ること。構造の宣言と実物の突き合わせで担保する。 |
| `所属` | ある文脈にどの要素が属するかという宣言。欠けと余りを両方向で確かめる。 |
| `ドリフト` | 宣言と実物が食い違っている状態。食い違っていないかを機械が検知し続ける。 |
| `Document` | Schema で構造を定義された JSON の成果物単位。 |
| `Schema` | Document の構造・描画・記入と読取の指示を定義するもの。 |
| `版` | Schema の世代。一度作った版は遡って構造を変えない。 |
| `ブロック` | Document の内容を構成する、意味のまとまりを持つ単位。 |
| `意味単位` | ブロック・フィールド・条件一致・全階層など、Document の意味のある取得単位。 |
| `骨格(scaffold)` | Schema を機械走査して生成した、値が空の Schema 準拠 Document の雛形。 |
| `x-prompt` | Schema に埋め込まれた、書くときと読むときの指針。 |
| `描画` | Document を読み手向けの成果物へ整形すること。整形の仕方も Schema が宣言する。 |
| `DomainSpecSchema` | 業務領域の仕様を定義するもの。文脈・業務領域・業務ユースケース・集約・業務サービスの種別を持つ。 |
| `CodingSchema` | 実装の在り方を定義するもの。技術構成・概念の配置・層・試験方針を宣言する。 |
| `CodingPresets` | 実装の在り方の宣言に使う、既定の組み合わせ。 |
| `PlatformSpec` | 動かす土台の仕様を定義するもの。 |
| `PresentationSpecSchema` | 画面の設計を定義するもの。 |
| `SkillSchema` | Skill を定義するもの。 |
| `AgentSchema` | 働き手を定義するもの。段取りを担う役と、委ねられる役の両方を扱う。 |
| `KnowledgeSchema` | 判断の背景となる原則を定義するもの。 |
| `HandoffSchema` | 決めたことを作る側へ渡す記録を定義するもの。 |
| `HookSchema` | 自動で割り込む仕掛けを定義するもの。 |
| `TemplateSchema` | 他へ持ち出すための雛形を定義するもの。 |
| `規約` | 実装がどう在るべきかの宣言。置き場所・依存の向き・検証の置き方を定める。 |
| `概念の配置` | 業務領域の構成要素それぞれを、実装のどこに置くかの宣言。 |
| `層` | 実装を役割で分けた区分。どの層がどの層に依存してよいかを規約が定める。 |
| `ポート` | 業務の側が定め、外側が実装する境目。 |
| `試験方針` | どの層に、どの種類の検証を、どこへ置くかの宣言。 |
| `宣言行` | 実装側の検証に置かれる、どのシナリオを担うかを名乗る一行。照合の鍵になる。 |
| `CLI` | 人と道具が、命令を打って Waffle を使う入口。 |
| `MCP` | AI の道具として Waffle を使う入口。CLI と同じことができる。 |
| `コマンド` | 入口から呼べる操作の単位。検証・描画・取得・骨格生成・検知など。 |
| `Hooks` | 作業の流れの中で、決められた場面に自動で割り込んで働く仕掛け。 |
| `Harness` | AI がファイルを直接読まず値だけを埋め、構造への出入りと生成をシステムが担う仕組み。 |
| `業務ユースケース駆動設計（UDD）` | 業務ユースケースの仕様を正本に置き、そこから実装と検証を導く進め方。 |
| `UDDループ` | 調べる・決める・引き継ぐ・作るを1周する進め方。どこまで踏むかはその都度判断する。 |
| `Orchestrator` | 作業の段取りを判断し、専門役へ委ねる役。 |
| `Subagent` | Orchestrator が独立した文脈で走らせる働き手。 |
| `Skill` | ある作業のやり方を、手順と受け入れ基準の形で持たせたもの。 |
| `実務Skill` | 調べる・決める・引き継ぐ・作るのそれぞれを担う Skill。 |
| `アドバイザーSkill` | ある観点の専門として、判断を敵対的に検証する Skill。 |
| `ddd-advisor` | ドメイン駆動設計の観点から検証する役。 |
| `tech-lead-advisor` | 依存の向き・層の配置・検知の実効性の観点から検証する役。 |
| `qa-advisor` | 検証の十分さの観点から検証する役。 |
| `ux-advisor` | 使い手の体験の観点から検証する役。 |
| `platform-advisor` | 動かす土台の観点から検証する役。 |
| `skill-router` | どの実務Skill にどのアドバイザーSkill を組み合わせるかを振り分ける役。 |
| `Human on the Loop` | 人が担うのは意思決定だけで、それ以外は AI が考え作るという分担。 |
| `Knowledge` | 判断の背景として繰り返し参照される、採用済みの原則。 |
| `ADR` | ある決定について、選択肢と根拠と代償を残した記録。 |
| `引き継ぎ` | 決めたことを作る側へ渡すための記録。完成の姿と、未解決の論点を含む。 |
| `パス` | Document や成果物が置かれている位置。 |
| `パステンプレート` | Schema が宣言する、パス変数を含んだ置き場所の型。 |
| `実パス` | パス変数がすべて値で埋まった、ひとつに定まるパス。 |
| `原本` | 値を保持している Document そのもの。 |
| `成果物` | Document を描画して得られる、読み手向けの出力。 |
| `解決` | パステンプレートとパス変数の値から実パスを導くこと。 |
| `逆解析` | 実パスとパステンプレートから、パス変数の値を取り出すこと。解決の逆。 |
| `パス変数` | パステンプレートの中で、値で埋める箇所。 |
| `配り先` | 成果物を、原本の置き場所とは別に届ける先。 |

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
- uc-check-criteria-coverage
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
| ソースルート解決 | 規約の architecture 文書が宣言するソースルートと概念ごとの配置から、指定した概念の実装ファイルの置き場所を導く。規約の宣言は物差しとして受け取るだけで、測る対象は集約の外にあるため、いずれの集約もこの計算を持てない。（測る対象は実装ファイルの置き場所） |
| 表記の適用 | 規約の coding-standard 文書が宣言する表記に従って、識別子の綴りを変換する。規約の宣言は物差しとして受け取るだけで、測る対象は集約の外にあるため、いずれの集約もこの計算を持てない。（測る対象は実装上の識別子） |
| 実装ファイル名の導出 | 規約の coding-standard 文書が宣言する変換と末尾から、型の名前を実装ファイルの名前へ導く。規約の宣言は物差しとして受け取るだけで、測る対象は集約の外にあるため、いずれの集約もこの計算を持てない。（測る対象は実装ファイルの名前） |
| 層の割り当て | 規約の architecture 文書が宣言する層とその置き場所から、あるファイルがどの層に属するかを決める。規約の宣言は物差しとして受け取るだけで、測る対象は集約の外にあるため、いずれの集約もこの計算を持てない。（測る対象はソースファイルの位置） |
| 実装の棚卸し | 規約が宣言した配置に実在するファイルと、仕様が名指しした実装ファイルを突き合わせ、名指しされていないものを返す。規約の宣言は物差しとして受け取るだけで、測る対象は集約の外にあるため、いずれの集約もこの計算を持てない。（測る対象は実在するファイル） |
| シナリオの突き合わせ | 仕様が宣言するシナリオと、テストの文書コメントに置かれた宣言行を突き合わせる。規約の test-standard 文書（シナリオの束ね方・テストの配置・テストファイルの名づけ）と coding-standard 文書（表記）と、対象の仕様文書の3つを横断して読むため、複数の集約にまたがる計算。 |

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
