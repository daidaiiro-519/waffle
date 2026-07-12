# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{タイトル}}` | 「業務エキスパートが理解できる日本語の説明：識別子」の形式で設定してください。説明部分はこのSpecが何であるかを業務語彙で簡潔に表す句（documentIdやクラス名をそのまま繰り返さない）。specKindがbounded-context/subdomain/aggregateの場合は、説明の末尾にその種別を表す語（bounded-contextなら「〜を行う境界づけられたコンテキスト」、subdomainなら「〜を担うサブドメイン」、aggregateなら「〜を守る集約」）を含め、読んだだけでこのSpecがDDDのどの構成要素かがわかるようにしてください（usecaseの場合はこの種別語を付けない）。識別子部分はspecKindに応じて設定する: usecaseの場合はcontent.name.operationNameと同じ値、aggregateの場合はcontent.aggregateRoot.nameと同じ値、bounded-context/subdomainの場合はdocumentIdをそのまま使う（識別子は既に別の構造化フィールドが正であり、ここでは表示のためだけに引用する。実装と乖離しても他のフィールドのように機械的ドリフト検知の対象にならないため、識別子以外の実装レベルの詳細をここに書き込まない）。（JSON上のフィールド: content.title.title） |
| `{{概要.論点1}}` | 論点ごとに列挙する（1〜2項目が目安）。この文脈/業務領域/集約/ユースケースが何かを1〜2文で（ドメイン語彙のみ・技術用語禁止）。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.summary.items[]） |
| `{{集約ルート.ルート名}}` | ルートエンティティ名（ドメイン語彙）。例: Order（JSON上のフィールド: content.aggregateRoot.name） |
| `{{集約ルート.外部参照1}}` | ID で参照する他集約を列挙（オブジェクトは内部に持たない・図6-4）。例: Customer, Product。無ければ空。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.aggregateRoot.externalRefs[]） |
| `{{エンティティ.項目1.名前}}` | エンティティ名。例: Order / OrderLine（JSON上のフィールド: content.entities.items[].name） |
| `{{エンティティ.項目1.役割}}` | このエンティティが集約内で担う役割を1文で。例: 注文全体の整合性を保つ集約ルート（JSON上のフィールド: content.entities.items[].role） |
| `{{エンティティ.項目1.ルート}}` | 集約ルートなら true（1つだけ）。（JSON上のフィールド: content.entities.items[].isRoot） |
| `{{エンティティ.項目1.属性1.属性}}` | 属性名。例: status / orderId（JSON上のフィールド: content.entities.items[].attributes[].name） |
| `{{エンティティ.項目1.属性1.型}}` | 型（値オブジェクト名・他エンティティ・ID）。例: OrderStatus / OrderLine[] / customerId（JSON上のフィールド: content.entities.items[].attributes[].type） |
| `{{エンティティ.項目1.属性1.識別子}}` | この属性が識別子なら true（エンティティに1つ）。（JSON上のフィールド: content.entities.items[].attributes[].isId） |
| `{{値オブジェクト.項目1.名前}}` | 値オブジェクト名。例: Money（任意ブロック：エンティティ属性の型となる値オブジェクトが無ければvalueObjectsブロック自体を省略してよい）（JSON上のフィールド: content.valueObjects.items[].name） |
| `{{値オブジェクト.項目1.表す値}}` | 何を表すか。例: 通貨つきの金額（JSON上のフィールド: content.valueObjects.items[].represents） |
| `{{値オブジェクト.項目1.振る舞い}}` | 振る舞い・制約・等価判定。例: 不変。加算は同一通貨のみ。負値不可。（JSON上のフィールド: content.valueObjects.items[].behavior） |
| `{{不変条件.項目1.ルール}}` | 不変条件（「〜は常に〜」の形）。例: 注文明細の数量は常に1以上である（JSON上のフィールド: content.invariants.items[].rule） |
| `{{不変条件.項目1.守り方}}` | 静的(値/構造)=schema が守る / 動的(状態遷移など)=guard が守る。（JSON上のフィールド: content.invariants.items[].enforcement） |
| `{{不変条件.項目1.根拠}}` | その不変条件が必要な業務上の根拠を短く。例: 在庫を超えて注文できると出荷不能になるため（JSON上のフィールド: content.invariants.items[].rationale） |
| `{{ライフサイクル.状態1}}` | 取りうる状態を列挙。例: PLACED, PAID, SHIPPED。状態を持たない集約なら空。（配列。この形式の行を必要な数だけ繰り返す）（任意ブロック：状態を持たない集約であればlifecycleブロック自体を省略してよい）（JSON上のフィールド: content.lifecycle.states[]） |
| `{{ライフサイクル.遷移1.from}}` | 遷移元の状態。statesで宣言済みの値の中から選ぶ。集約インスタンスがまだ存在しない新規生成コマンドの場合のみ、開始疑似状態を表す"[*]"を使う。例: CREATED（JSON上のフィールド: content.lifecycle.transitions[].from） |
| `{{ライフサイクル.遷移1.to}}` | 遷移先の状態。statesで宣言済みの値の中から選ぶ。例: VALIDATED（JSON上のフィールド: content.lifecycle.transitions[].to） |
| `{{ライフサイクル.遷移1.command}}` | この遷移を起こすコマンド。commandsで宣言済みのコマンド名の中から選ぶ（新しいコマンド名をここで作らない）。例: validate（JSON上のフィールド: content.lifecycle.transitions[].command） |
| `{{ライフサイクル.遷移1.条件}}` | 遷移の追加条件があれば。無ければ空。（JSON上のフィールド: content.lifecycle.transitions[].condition） |
| `{{コマンド.項目1.名前}}` | コマンド名（命令形）。例: place / 確定する（JSON上のフィールド: content.commands.items[].name） |
| `{{コマンド.項目1.説明}}` | 何をするか・どの不変条件を守るかを1文で（実装手順は書かない）。（JSON上のフィールド: content.commands.items[].description） |
| `{{コマンド.項目1.前提}}` | 実行に必要な前提状態。集約インスタンスがまだ存在しない新規生成コマンドの場合は null（曖昧な文字列プレースホルダーは使わない）。（JSON上のフィールド: content.commands.items[].requiresState） |
| `{{コマンド.項目1.後}}` | 成功後の状態。この集約のlifecycle.statesで宣言済みの値の中から選ぶ（新しい状態名をここで作らない）。例: VALIDATED（JSON上のフィールド: content.commands.items[].postState） |
| `{{コマンド.項目1.引数1.引数}}` | 引数名。ドメイン語彙で。例: quantity（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.commands.items[].params[].name） |
| `{{コマンド.項目1.引数1.意味}}` | この引数が何を表すかを1文で。例: 注文する数量（JSON上のフィールド: content.commands.items[].params[].meaning） |
| `{{コマンド.項目1.発行イベント1}}` | 発行するドメインイベント名（過去形）。無ければ空。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.commands.items[].emits[]） |
| `{{ドメインイベント.イベント1.名前}}` | イベント名（必ず過去形）。例: OrderPlaced（任意ブロック：発行するドメインイベントが無ければdomainEventsブロック自体を省略してよい）（JSON上のフィールド: content.domainEvents.items[].name） |
| `{{ドメインイベント.イベント1.発行契機}}` | どのコマンド/契機で発行されるか。commandsで宣言済みのコマンド名の中から選ぶ。例: place（JSON上のフィールド: content.domainEvents.items[].raisedBy） |
| `{{ドメインイベント.イベント1.ペイロード1.項目}}` | ペイロード項目名。例: quantity（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.domainEvents.items[].payload[].name） |
| `{{ドメインイベント.イベント1.ペイロード1.意味}}` | このペイロード項目が何を表すかを1文で。例: 確定した数量（JSON上のフィールド: content.domainEvents.items[].payload[].meaning） |
| `{{不変条件シナリオ.背景}}` | 複数シナリオ共通の前提（Gherkin Background 相当）。無ければ空文字。（任意ブロック：無ければinvariantScenariosブロック自体を省略してよい）（JSON上のフィールド: content.invariantScenarios.background） |
| `{{不変条件シナリオ.シナリオ1.シナリオ名}}` | シナリオ名（概要）。（JSON上のフィールド: content.invariantScenarios.scenarios[].name） |
| `{{不変条件シナリオ.シナリオ1.分類}}` | 分類: 正常系 / 異常系 / 境界値。（JSON上のフィールド: content.invariantScenarios.scenarios[].category） |
| `{{不変条件シナリオ.シナリオ1.観点}}` | 観点: 側面（状態遷移/計算整合/事前条件 等）＋検証の狙い。（JSON上のフィールド: content.invariantScenarios.scenarios[].viewpoint） |
| `{{不変条件シナリオ.シナリオ1.本文}}` | このシナリオの Given/When/Then（Scenario: 1つ・実行可能なテストとして書き起こせる形）。ドメイン語彙で書き、実装詳細（クラス名/API/SQL/UI 操作）は書かない。（JSON上のフィールド: content.invariantScenarios.scenarios[].gherkin） |
| `{{不変条件シナリオ.シナリオ1.参照}}` | 検証する不変条件への参照（任意・トレーサビリティ）。（JSON上のフィールド: content.invariantScenarios.scenarios[].covers） |

---

# {{タイトル}}

---

## 概要

- {{概要.論点1}}

---

## 集約ルート

{{集約ルート.ルート名}}

### 外部参照（ID）

- {{集約ルート.外部参照1}}

---

## エンティティ

### {{エンティティ.項目1.名前}}（集約ルート）

{{エンティティ.項目1.役割}}

| 属性 | 型 |
|---|---|
| **{{エンティティ.項目1.属性1.属性}}**（識別子） | {{エンティティ.項目1.属性1.型}} |

---

## 値オブジェクト

### {{値オブジェクト.項目1.名前}}

| 表す値 | 振る舞い |
|---|---|
| {{値オブジェクト.項目1.表す値}} | {{値オブジェクト.項目1.振る舞い}} |

---

## 不変条件

| ルール | 守り方 | 根拠 |
|---|---|---|
| {{不変条件.項目1.ルール}} | {{不変条件.項目1.守り方}} | {{不変条件.項目1.根拠}} |

---

## ライフサイクル

```mermaid
stateDiagram-v2
    {{ライフサイクル.遷移1.from}} --> {{ライフサイクル.遷移1.to}}: {{ライフサイクル.遷移1.command}}
```

### 遷移

| from | to | command | 条件 |
|---|---|---|---|
| {{ライフサイクル.遷移1.from}} | {{ライフサイクル.遷移1.to}} | {{ライフサイクル.遷移1.command}} | {{ライフサイクル.遷移1.条件}} |

---

## コマンド

### {{コマンド.項目1.名前}}

{{コマンド.項目1.説明}}

| 前提 | 後 | 発行イベント |
|---|---|---|
| {{コマンド.項目1.前提}} | {{コマンド.項目1.後}} | {{コマンド.項目1.発行イベント1}} |

| 引数 | 意味 |
|---|---|
| {{コマンド.項目1.引数1.引数}} | {{コマンド.項目1.引数1.意味}} |

---

## ドメインイベント

### {{ドメインイベント.イベント1.名前}}

#### 発行契機

{{ドメインイベント.イベント1.発行契機}}

#### ペイロード

| 項目 | 意味 |
|---|---|
| {{ドメインイベント.イベント1.ペイロード1.項目}} | {{ドメインイベント.イベント1.ペイロード1.意味}} |

---

## 不変条件シナリオ

### 背景

{{不変条件シナリオ.背景}}

### {{不変条件シナリオ.シナリオ1.シナリオ名}}

| 分類 | 観点 |
|---|---|
| {{不変条件シナリオ.シナリオ1.分類}} | {{不変条件シナリオ.シナリオ1.観点}} |

```gherkin
{{不変条件シナリオ.シナリオ1.本文}}
```
