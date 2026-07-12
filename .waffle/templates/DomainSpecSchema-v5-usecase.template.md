# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | 「業務エキスパートが理解できる日本語の説明：識別子」の形式で設定してください。説明部分はこのSpecが何であるかを業務語彙で簡潔に表す句（documentIdやクラス名をそのまま繰り返さない）。specKindがbounded-context/subdomain/aggregateの場合は、説明の末尾にその種別を表す語（bounded-contextなら「〜を行う境界づけられたコンテキスト」、subdomainなら「〜を担うサブドメイン」、aggregateなら「〜を守る集約」）を含め、読んだだけでこのSpecがDDDのどの構成要素かがわかるようにしてください（usecaseの場合はこの種別語を付けない）。識別子部分はspecKindに応じて設定する: usecaseの場合はcontent.name.operationNameと同じ値、aggregateの場合はcontent.aggregateRoot.nameと同じ値、bounded-context/subdomainの場合はdocumentIdをそのまま使う（識別子は既に別の構造化フィールドが正であり、ここでは表示のためだけに引用する。実装と乖離しても他のフィールドのように機械的ドリフト検知の対象にならないため、識別子以外の実装レベルの詳細をここに書き込まない）。 |
| `{{summary.items[1]}}` | 論点ごとに列挙する（1〜2項目が目安）。この文脈/業務領域/集約/ユースケースが何かを1〜2文で（ドメイン語彙のみ・技術用語禁止）。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{name.operationName}}` | このusecaseの操作名をPascalCaseで一意に。例: CheckScenarioDrift。この名前は対応する実装クラス名としてそのまま使われる（coding-standardのusecase実装クラス命名規約を参照）。summary/actorIntentが日本語で説明する操作を、ユビキタス言語の識別子として1語に凝縮したもの。（本文には描画されない。title.titleの識別子部分として引用される） |
| `{{usecaseRationale.items[1]}}` | 存在しなかった場合に起きる問題・防いでいるリスクを、独立した論点ごとに列挙する。このusecaseが存在しなかった場合に起きる問題、または防いでいるリスクを1〜2文で。メカニズム（何をするか）ではなく目的（なぜ必要か）を書く。actorIntent.intentが「何を達成したいか」を書く場所であるのに対し、ここは「それがなぜ業務上重要か」を書く場所（両者を混同しない）。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{actorIntent.actor}}` | 主アクター（業務上の役割）。例: 顧客 |
| `{{actorIntent.intent}}` | 何を達成したいか（1文）。例: カートの商品を注文として確定する |
| `{{externalActors.items[1]}}` | 関与する副アクター・隣接コンテキストを列挙（同じ外部システム＝業務領域の境界）。無ければ空。（配列。この形式の行を必要な数だけ繰り返す）（任意ブロック：無ければexternalActorsブロック自体を省略してよい） |
| `{{operationIndex.items[1].operation}}` | 操作の識別子（例: get_block）。実装のoperation分岐の文字列と完全一致させる。（任意ブロック：operation引数で分岐する複数の操作を持たない単一操作のusecaseでは省略する） |
| `{{operationIndex.items[1].summary}}` | この操作が何をするかの一文説明（業務語彙で）。 |
| `{{preconditions.items[1]}}` | 操作開始前に成立している必要がある条件を列挙。無ければ空。（配列。この形式の行を必要な数だけ繰り返す）（任意ブロック：無ければpreconditionsブロック自体を省略してよい） |
| `{{mainFlow.participants[1].id}}` | 識別子。stepsのfrom/toと同じ表記に揃える。 |
| `{{mainFlow.participants[1].kind}}` | 人間/主アクターなら actor、集約等のシステム側なら participant。 |
| `{{mainFlow.steps[1].from}}` | 送り手（ドメインの役者）。 |
| `{{mainFlow.steps[1].to}}` | 受け手（ドメインの役者）。event の場合は空でよい。 |
| `{{mainFlow.steps[1].message}}` | メッセージ（コマンド/返り値/イベント名）。 |
| `{{mainFlow.steps[1].kind}}` | command=呼び出し / self=自分への処理 / return=返り値 / event=イベント発行。 |
| `{{postconditions.items[1]}}` | 成功時に成立する結果（集約の状態変化・発行イベント）を列挙。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{acceptanceCriteria.items[1]}}` | 受け入れ条件を EARS で列挙（When/While/If … shall …）。一意・検証可能・ドメイン語彙のみ。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{operationGuarantees.items[1]}}` | 保証をEARSで列挙（When/While/If … shall …）。書いてよいのは『何を保証するか』だけ（べき等性・一貫性・提供チャネルの一貫性等）。『どう実現するか』（具体的なDB技法・ロック機構・実装技術）は書かない（CodingSchemaのcode-templateの領分）。判定基準（このusecaseに書くか、集約のinvariantsに書くか）: 同じ資源を操作する複数usecaseの間で、この保証内容が重複するか？ 重複するなら集約（agg-*.json）のinvariants/invariantScenariosに書く。このusecase固有の業務理由でのみ必要な保証だけをここに書く。性能の生数値（応答時間・スループット等）は書かない（CodingSchemaのtestTypes: non-functional-performanceの領分）。（配列。この形式の行を必要な数だけ繰り返す）（任意ブロック：無ければoperationGuaranteesブロック自体を省略してよい） |
| `{{errors.items[1].code}}` | エラーコード。例: OUT_OF_STOCK（任意ブロック：無ければerrorsブロック自体を省略してよい） |
| `{{errors.items[1].condition}}` | そのエラーコードが返る具体的な条件を1文で。例: 対象ファイルが存在しない |
| `{{acceptanceScenarios.background}}` | 複数シナリオ共通の前提（Gherkin Background 相当）。無ければ空文字。 |
| `{{acceptanceScenarios.scenarios[1].name}}` | シナリオ名（概要）。 |
| `{{acceptanceScenarios.scenarios[1].category}}` | 分類: 正常系 / 異常系 / 境界値。 |
| `{{acceptanceScenarios.scenarios[1].viewpoint}}` | 観点: 側面（状態遷移/計算整合/事前条件 等）＋検証の狙い。 |
| `{{acceptanceScenarios.scenarios[1].gherkin}}` | このシナリオの Given/When/Then（Scenario: 1つ・実行可能なテストとして書き起こせる形）。ドメイン語彙で書き、実装詳細（クラス名/API/SQL/UI 操作）は書かない。 |
| `{{acceptanceScenarios.scenarios[1].covers}}` | 検証する受け入れ基準への参照（任意・トレーサビリティ）。 |
| `{{acceptanceScenarios.scenarios[1].operation}}` | このシナリオが検証する操作の識別子（任意）。usecaseの実装がoperation引数で複数の操作を分岐する場合のみ設定し、その操作を指す文字列そのものを設定する（例: get_block）。check-operation-driftが実装コードのoperation分岐と機械的に突き合わせるため、gherkin本文に埋め込む代わりにここへ構造化して書く。単一操作のusecaseでは省略する。（本文には描画されない。operationIndexと対になる構造化メタデータ） |
| `{{guaranteeScenarios.background}}` | 複数シナリオ共通の前提。無ければ空文字。（任意ブロック：operationGuaranteesが無ければguaranteeScenariosブロック自体を省略してよい） |
| `{{guaranteeScenarios.scenarios[1].name}}` | シナリオ名（概要）。 |
| `{{guaranteeScenarios.scenarios[1].category}}` | 分類: 正常系 / 異常系 / 境界値。 |
| `{{guaranteeScenarios.scenarios[1].viewpoint}}` | 観点: べき等性/一貫性/提供チャネルの一貫性 等＋検証の狙い。 |
| `{{guaranteeScenarios.scenarios[1].gherkin}}` | Given/When/Then。ドメイン語彙で書き、実装詳細は書かない。 |
| `{{guaranteeScenarios.scenarios[1].covers}}` | 対応するOperationGuaranteesの項目への参照。 |

---

# {{title.title}}

---

## 概要

- {{summary.items[1]}}

---

## 存在意義

- {{usecaseRationale.items[1]}}

---

## 主アクターと意図

- **主アクター**: {{actorIntent.actor}}
- **意図**: {{actorIntent.intent}}

---

## 関与する外部

- {{externalActors.items[1]}}

---

## 操作一覧

| 操作 | 概要 |
|---|---|
| `{{operationIndex.items[1].operation}}` | {{operationIndex.items[1].summary}} |

---

## 事前条件

- {{preconditions.items[1]}}

---

## 基本フロー

```mermaid
sequenceDiagram
    {{mainFlow.participants[1].kind}} {{mainFlow.participants[1].id}}
    {{mainFlow.steps[1].from}}->>{{mainFlow.steps[1].to}}: {{mainFlow.steps[1].message}}
```

---

## 事後条件

- {{postconditions.items[1]}}

---

## 受け入れ基準

- {{acceptanceCriteria.items[1]}}

---

## 操作保証

- {{operationGuarantees.items[1]}}

---

## エラー

| コード | 条件 |
|---|---|
| `{{errors.items[1].code}}` | {{errors.items[1].condition}} |

---

## 受け入れシナリオ

### 背景

{{acceptanceScenarios.background}}

### {{acceptanceScenarios.scenarios[1].name}}

| 分類 | 観点 |
|---|---|
| {{acceptanceScenarios.scenarios[1].category}} | {{acceptanceScenarios.scenarios[1].viewpoint}} |

```gherkin
{{acceptanceScenarios.scenarios[1].gherkin}}
```

---

## 操作保証シナリオ

### 背景

{{guaranteeScenarios.background}}

### {{guaranteeScenarios.scenarios[1].name}}

| 分類 | 観点 |
|---|---|
| {{guaranteeScenarios.scenarios[1].category}} | {{guaranteeScenarios.scenarios[1].viewpoint}} |

```gherkin
{{guaranteeScenarios.scenarios[1].gherkin}}
```
