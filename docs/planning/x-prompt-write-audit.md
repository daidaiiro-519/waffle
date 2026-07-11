# x-prompt-write 全schema棚卸し

**作成日:** 2026-07-11
**目的:** 全schemaの`x-prompt-write`（AIが値を埋める際に読む執筆指示）の薄さ・
使い回しを棚卸しし、schemaごとにフェーズを分けて丁寧に修正する。
再現性・べき等性の担保は、document.json個々の値ではなく、その値を生む
`x-prompt-write`自体の記述品質にかかっている、という認識に基づく。

**進め方:** 1schemaずつフェーズを区切り、このドキュメントの該当セクションを
チェックしながら修正する。一気に全部やると漏れが生じるため、必ず
スキーマ単位で完結させてから次に進む。各schemaの修正が終わったら
「ステータス」を「完了」に更新し、次のschemaへ進む。

## フェーズ順序（提案）

| 順 | Schema | 理由 |
|---|---|---|
| 1 | DomainSpecSchema/v4 | 既にNameBlock.operationName等の修正内容が合意済み（A1〜A5）。仕掛かり中のため最初に完了させる |
| 2 | CodingSchema/v2 | 重複テキスト「規約の内容。」が4ブロックにまたがる、最も深刻な使い回し |
| 3 | KnowledgeSchema/v1 | 総数に対する薄いフィールドの比率が高い（22件中10件） |
| 4 | PresentationSpecSchema/v1 | 同上（30件中9件） |
| 5 | AgentSchema/v1 | 薄い箇所は少ないが「why」等、根拠を書かせる重要フィールドが含まれる |
| 6 | SkillSchema/v1 | 薄い箇所が最も少ない |
| 7 | PlatformSpec/v1 | 総数が少なく影響範囲が小さい |

RenderMetaSchema/v1・DocstringSchema/v1は`x-prompt-write`を持つフィールドが0件のため対象外。

---

## DomainSpecSchema/v4

**総フィールド数:** 107件　**20字未満:** 30件　**重複テキスト:** 8種

**ステータス:** 完了（2026-07-11）

**対応内容:** 15フィールドのx-prompt-writeを強化（NameBlock.operationName・
CommandsBlock.postState/params.name/params.meaning・LifecycleBlock.
transitions.from/to/command・DomainServicesBlock.name・DomainEventsBlock.
raisedBy/payload.name/payload.meaning・EntitiesBlock.role・MembersBlock.kind・
ErrorsBlock.condition・ContextMapBlock.content・InvariantsBlock.rule/rationale）。
主眼は「他ブロックで宣言済みの値を再利用すべき箇所に、その旨を明記する」
（例: postState/transitions.from/toはlifecycle.statesの値を再利用すべきなのに
指示が無かった）ことと、他の兄弟フィールドと非対称に例が欠けていた箇所への
例示追加。

**そのまま残した重複テキスト（意図的）:** `*ScenariosBlock.scenarios[].name`
（4箇所, "シナリオ名（概要）。"）・`.category`（4箇所, "分類: 正常系/異常系/
境界値。"）・`.background`（2ペア）は、CodingSchemaの「rule」のような
「同じ言葉で意味が変わる」問題ではなく、**文脈が違っても本当に同じ意味**
（シナリオ名はシナリオ名、正常系/異常系/境界値という分類軸も4ブロック共通）
のため、無理に書き分けなかった。coding-standard側にも1件追加
（`architecture-python-hexagonal.json`の`rules`に「usecase実装クラス名は
対応するusecase specの操作名とそのまま一致させる」を追加）。

### 重複テキスト（同じ指示文が複数の別フィールドで使い回されている）

- `意味を1文で。` が 2箇所で使用:
  - `CommandsBlock.properties.items.items.properties.params.items.properties.meaning`
  - `DomainEventsBlock.properties.items.items.properties.payload.items.properties.meaning`
- `シナリオ名（概要）。` が 4箇所で使用:
  - `InvariantScenariosBlock.properties.scenarios.items.properties.name`
  - `AcceptanceScenariosBlock.properties.scenarios.items.properties.name`
  - `GuaranteeScenariosBlock.properties.scenarios.items.properties.name`
  - `DomainServiceScenariosBlock.properties.scenarios.items.properties.name`
- `分類: 正常系 / 異常系 / 境界値。` が 4箇所で使用:
  - `InvariantScenariosBlock.properties.scenarios.items.properties.category`
  - `AcceptanceScenariosBlock.properties.scenarios.items.properties.category`
  - `GuaranteeScenariosBlock.properties.scenarios.items.properties.category`
  - `DomainServiceScenariosBlock.properties.scenarios.items.properties.category`
- `複数シナリオ共通の前提。無ければ空文字。` が 2箇所で使用:
  - `GuaranteeScenariosBlock.properties.background`
  - `DomainServiceScenariosBlock.properties.background`
- `観点: 側面（状態遷移/計算整合/事前条件 等）＋検証の狙い。` が 2箇所で使用:
  - `InvariantScenariosBlock.properties.scenarios.items.properties.viewpoint`
  - `AcceptanceScenariosBlock.properties.scenarios.items.properties.viewpoint`
- `Given/When/Then。ドメイン語彙で書き、実装詳細は書かない。` が 2箇所で使用:
  - `GuaranteeScenariosBlock.properties.scenarios.items.properties.gherkin`
  - `DomainServiceScenariosBlock.properties.scenarios.items.properties.gherkin`
- `複数シナリオ共通の前提（Gherkin Background 相当）。無ければ空文字。` が 2箇所で使用:
  - `InvariantScenariosBlock.properties.background`
  - `AcceptanceScenariosBlock.properties.background`
- `このシナリオの Given/When/Then（Scenario: 1つ・実行可能なテストとして書き起こせる形）。ドメイン語彙で書き、実装詳細（クラス名/API/SQL/UI 操作）は書かない。` が 2箇所で使用:
  - `InvariantScenariosBlock.properties.scenarios.items.properties.gherkin`
  - `AcceptanceScenariosBlock.properties.scenarios.items.properties.gherkin`

### 薄いフィールド（20字未満、要見直し）

| フィールド | 現在の指示文 |
|---|---|
| `CommandsBlock.properties.items.items.properties.params.items.properties.name` | 引数名。 |
| `DomainEventsBlock.properties.items.items.properties.payload.items.properties.name` | 項目名。 |
| `EntitiesBlock.properties.items.items.properties.role` | 役割を1文で。 |
| `LifecycleBlock.properties.transitions.items.properties.from` | 遷移元の状態。 |
| `LifecycleBlock.properties.transitions.items.properties.to` | 遷移先の状態。 |
| `CommandsBlock.properties.items.items.properties.postState` | 成功後の状態。 |
| `CommandsBlock.properties.items.items.properties.params.items.properties.meaning` | 意味を1文で。 |
| `DomainEventsBlock.properties.items.items.properties.payload.items.properties.meaning` | 意味を1文で。 |
| `MembersBlock.properties.items.items.properties.kind` | メンバーの種別。 |
| `DomainServicesBlock.properties.items.items.properties.name` | 業務サービス名。 |
| `InvariantScenariosBlock.properties.scenarios.items.properties.name` | シナリオ名（概要）。 |
| `AcceptanceScenariosBlock.properties.scenarios.items.properties.name` | シナリオ名（概要）。 |
| `GuaranteeScenariosBlock.properties.scenarios.items.properties.name` | シナリオ名（概要）。 |
| `DomainServiceScenariosBlock.properties.scenarios.items.properties.name` | シナリオ名（概要）。 |
| `LifecycleBlock.properties.transitions.items.properties.command` | 遷移を起こすコマンド。 |
| `ErrorsBlock.properties.items.items.properties.condition` | その失敗が起きる条件。 |
| `ContextMapBlock.properties.items.items.properties.content` | 何を連係するかを1文で。 |
| `MainFlowBlock.properties.steps.items.properties.from` | 送り手（ドメインの役者）。 |
| `UbiquitousLanguageBlock.properties.items.items.properties.term` | 用語（この文脈での呼び名）。 |
| `UbiquitousLanguageBlock.properties.items.items.properties.definition` | その用語が指すものを1文で。 |
| `InvariantsBlock.properties.items.items.properties.rationale` | そのルールが要る根拠を短く。 |
| `ValueObjectsBlock.properties.items.items.properties.represents` | 何を表すか。例: 通貨つきの金額 |
| `InvariantsBlock.properties.items.items.properties.rule` | 不変条件（「〜は常に〜」の形）。 |
| `ValueObjectsBlock.properties.items.items.properties.name` | 値オブジェクト名。例: Money |
| `DomainEventsBlock.properties.items.items.properties.raisedBy` | どのコマンド/契機で発行されるか。 |
| `DomainEventsBlock.properties.items.items.properties.payload` | イベントが運ぶデータ。無ければ空。 |
| `LifecycleBlock.properties.transitions.items.properties.condition` | 遷移の追加条件があれば。無ければ空。 |
| `CommandsBlock.properties.items.items.properties.params` | 引数（ドメインデータ）。無ければ空。 |
| `EntitiesBlock.properties.items.items.properties.isRoot` | 集約ルートなら true（1つだけ）。 |
| `ActorIntentBlock.properties.actor` | 主アクター（業務上の役割）。例: 顧客 |

---

## CodingSchema/v2

**総フィールド数:** 77件　**20字未満:** 21件　**重複テキスト:** 1種

**ステータス:** 未着手

### 重複テキスト（同じ指示文が複数の別フィールドで使い回されている）

- `規約の内容。` が 4箇所で使用:
  - `StyleBlock.properties.items.items.properties.rule`
  - `CodingRulesBlock.properties.items.items.properties.rule`
  - `ScenarioBindingBlock.properties.items.items.properties.rule`
  - `TestRulesBlock.properties.items.items.properties.rule`

### 薄いフィールド（20字未満、要見直し）

| フィールド | 現在の指示文 |
|---|---|
| `TestPlanBlock.properties.items.items.properties.value` | 内容。 |
| `PolicyBlock.properties.items.items.properties.rule` | 方針の内容。 |
| `StyleBlock.properties.items.items.properties.rule` | 規約の内容。 |
| `CodingRulesBlock.properties.items.items.properties.rule` | 規約の内容。 |
| `ScenarioBindingBlock.properties.items.items.properties.rule` | 規約の内容。 |
| `TestRulesBlock.properties.items.items.properties.rule` | 規約の内容。 |
| `ArchitectureRulesBlock.properties.items.items.properties.rule` | ルールの内容。 |
| `PolicyBlock.properties.items` | 依存追加の規律を列挙。 |
| `ScenarioBindingBlock.properties.items.items.properties.item` | 項目名。例: 対応関係 |
| `PlacementByTargetBlock.properties.items.items.properties.testKind` | テスト種別。例: 単体 |
| `MiddlewareBlock.properties.items.items.properties.role` | ミドルウェアの役割分類。 |
| `ThicknessBySubdomainBlock.properties.items.items.properties.thickness` | 実装の厚み方針を1文で。 |
| `IdentityBlock.properties.tier` | このスタックが担うティア。 |
| `LibrariesBlock.properties.items.items.properties.version` | バージョン。固定不要なら空。 |
| `LayersBlock.properties.items.items.properties.responsibility` | このレイヤーの責務を1文で。 |
| `NamingBlock.properties.items.items.properties.convention` | 命名規約。例: スネークケース |
| `TestTypesBlock.properties.items.items.properties.tool` | 使用ツール。例: pytest |
| `PlacementByTargetBlock.properties.items.items.properties.target` | テスト対象。例: domain |
| `TestPlanBlock.properties.items.items.properties.item` | 計画項目名。例: 実行タイミング |
| `TestTypesBlock.properties.items.items.properties.testType` | 共通カタログの固定語彙から選ぶ。 |
| `TestFrameworkBlock.properties.unit` | 単体テストFW。例: pytest |

---

## SkillSchema/v1

**総フィールド数:** 34件　**20字未満:** 2件　**重複テキスト:** 0種

**ステータス:** 未着手

### 薄いフィールド（20字未満、要見直し）

| フィールド | 現在の指示文 |
|---|---|
| `ReferencesBlock.properties.items` | 参照リソースを列挙してください。 |
| `KnowledgeRefsBlock.properties.items.items.properties.description` | このファイルが何を扱うかを1文で。 |

---

## AgentSchema/v1

**総フィールド数:** 34件　**20字未満:** 4件　**重複テキスト:** 0種

**ステータス:** 未着手

### 薄いフィールド（20字未満、要見直し）

| フィールド | 現在の指示文 |
|---|---|
| `KeyCommandsBlock.properties.items.items.properties.command` | 実行するコマンド。 |
| `KeyCommandsBlock.properties.items.items.properties.purpose` | 何のためのコマンドかを1文で。 |
| `OperatingRulesBlock.properties.items.items.properties.why` | なぜこのルールが必要か（根拠）。 |
| `SkillFollowUpBlock.properties.items.items.properties.why` | なぜこのフォローアップが必要か。 |

---

## KnowledgeSchema/v1

**総フィールド数:** 22件　**20字未満:** 10件　**重複テキスト:** 0種

**ステータス:** 未着手

### 薄いフィールド（20字未満、要見直し）

| フィールド | 現在の指示文 |
|---|---|
| `ClassificationsBlock.properties.items.items.properties.name` | 分類名。 |
| `ClassificationsBlock.properties.items.items.properties.description` | その分類の特徴。 |
| `AntiPatternsBlock.properties.items.items.properties.name` | アンチパターン名。 |
| `AntiPatternsBlock.properties.items.items.properties.problem` | 何が問題かの説明。 |
| `DecisionCriteriaBlock.properties.transitions.items.properties.from` | 遷移元ノードのid。 |
| `DecisionCriteriaBlock.properties.transitions.items.properties.to` | 遷移先ノードのid。 |
| `DecisionCriteriaBlock.properties.stages.items.properties.label` | 問いや帰結の短い文言。 |
| `DecisionCriteriaBlock.properties.stages.items.properties.id` | ノードの識別子。例: q1 |
| `RelatedConceptsBlock.properties.items.items.properties.note` | どう関連するかの短い説明。 |
| `DecisionCriteriaBlock.properties.transitions.items.properties.label` | 遷移条件（回答）の短い文言。 |

---

## PresentationSpecSchema/v1

**総フィールド数:** 30件　**20字未満:** 9件　**重複テキスト:** 0種

**ステータス:** 未着手

### 薄いフィールド（20字未満、要見直し）

| フィールド | 現在の指示文 |
|---|---|
| `ActionsBlock.properties.items.items.properties.description` | 何をするかを1文で。 |
| `AcceptanceScenariosBlock.properties.scenarios.items.properties.name` | シナリオ名（概要）。 |
| `VisualRefBlock.properties.url` | Figma等のURL。 |
| `FieldsBlock.properties.items.items.properties.required` | 入力必須なら true。 |
| `ActionsBlock.properties.items.items.properties.name` | 操作名。例: 注文を確定する |
| `FieldsBlock.properties.items.items.properties.name` | 項目名。例: パスワード（確認） |
| `ActionsBlock.properties.items` | 画面上の操作を列挙。無ければ空。 |
| `ActionsBlock.properties.items.items.properties.trigger` | 操作の契機。例: 「確定」ボタン押下 |
| `UsecaseSequenceBlock.properties.participants.items.properties.label` | 表示名（任意・省略時はidそのまま）。 |

---

## PlatformSpec/v1

**総フィールド数:** 12件　**20字未満:** 4件　**重複テキスト:** 0種

**ステータス:** 未着手

### 薄いフィールド（20字未満、要見直し）

| フィールド | 現在の指示文 |
|---|---|
| `PlatformGuaranteeScenariosBlock.properties.scenarios.items.properties.name` | シナリオ名（概要）。 |
| `PlatformGuaranteeScenariosBlock.properties.scenarios.items.properties.covers` | 対応する保証項目への参照。 |
| `PlatformGuaranteeScenariosBlock.properties.scenarios.items.properties.viewpoint` | 観点: 何を保証するか＋検証の狙い。 |
| `ReleasePipelineBlock.properties.stages` | 環境の段階(id/label)を列挙。 |

---
