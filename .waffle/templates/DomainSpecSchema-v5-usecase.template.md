# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{タイトル}}` | 「業務エキスパートが理解できる日本語の説明：識別子」の形式で設定してください。説明部分はこのSpecが何であるかを業務語彙で簡潔に表す句（documentIdやクラス名をそのまま繰り返さない）。specKindがbounded-context/subdomain/aggregateの場合は、説明の末尾にその種別を表す語（bounded-contextなら「〜を行う境界づけられたコンテキスト」、subdomainなら「〜を担うサブドメイン」、aggregateなら「〜を守る集約」）を含め、読んだだけでこのSpecがDDDのどの構成要素かがわかるようにしてください（usecaseの場合はこの種別語を付けない）。識別子部分はspecKindに応じて設定する: usecaseの場合はcontent.name.operationNameと同じ値、aggregateの場合はcontent.aggregateRoot.nameと同じ値、bounded-context/subdomainの場合はdocumentIdをそのまま使う（識別子は既に別の構造化フィールドが正であり、ここでは表示のためだけに引用する。実装と乖離しても他のフィールドのように機械的ドリフト検知の対象にならないため、識別子以外の実装レベルの詳細をここに書き込まない）。（JSON上のフィールド: content.title.title） |
| `{{概要.論点1}}` | 論点ごとに列挙する（1〜2項目が目安）。この文脈/業務領域/集約/ユースケースが何かを1〜2文で（ドメイン語彙のみ・技術用語禁止）。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.summary.items[]） |
| `{{名前}}` | このusecaseの操作名をPascalCaseで一意に。例: CheckScenarioDrift。この名前は対応する実装クラス名としてそのまま使われる（coding-standardのusecase実装クラス命名規約を参照）。summary/actorIntentが日本語で説明する操作を、ユビキタス言語の識別子として1語に凝縮したもの。（本文には描画されない。title.titleの識別子部分として引用される）（JSON上のフィールド: content.name.operationName） |
| `{{存在意義.理由1}}` | 存在しなかった場合に起きる問題・防いでいるリスクを、独立した論点ごとに列挙する。このusecaseが存在しなかった場合に起きる問題、または防いでいるリスクを1〜2文で。メカニズム（何をするか）ではなく目的（なぜ必要か）を書く。actorIntent.intentが「何を達成したいか」を書く場所であるのに対し、ここは「それがなぜ業務上重要か」を書く場所（両者を混同しない）。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.usecaseRationale.items[]） |
| `{{主アクターと意図.主アクター}}` | 主アクター（業務上の役割）。例: 顧客（JSON上のフィールド: content.actorIntent.actor） |
| `{{主アクターと意図.意図}}` | 何を達成したいか（1文）。例: カートの商品を注文として確定する（JSON上のフィールド: content.actorIntent.intent） |
| `{{関与する外部.副アクター1}}` | 関与する副アクター・隣接コンテキストを列挙（同じ外部システム＝業務領域の境界）。無ければ空。（配列。この形式の行を必要な数だけ繰り返す）（任意ブロック：無ければexternalActorsブロック自体を省略してよい）（JSON上のフィールド: content.externalActors.items[]） |
| `{{操作一覧.項目1.操作}}` | 操作の識別子（例: get_block）。実装のoperation分岐の文字列と完全一致させる。（任意ブロック：operation引数で分岐する複数の操作を持たない単一操作のusecaseでは省略する）（JSON上のフィールド: content.operationIndex.items[].operation） |
| `{{操作一覧.項目1.概要}}` | この操作が何をするかの一文説明（業務語彙で）。（JSON上のフィールド: content.operationIndex.items[].summary） |
| `{{事前条件.条件1}}` | 操作開始前に成立している必要がある条件を列挙。無ければ空。（配列。この形式の行を必要な数だけ繰り返す）（任意ブロック：無ければpreconditionsブロック自体を省略してよい）（JSON上のフィールド: content.preconditions.items[]） |
| `{{基本フロー.登場人物1.識別子}}` | 識別子。stepsのfrom/toと同じ表記に揃える。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.mainFlow.participants[].id） |
| `{{基本フロー.登場人物1.種別}}` | 人間/主アクターなら actor、集約等のシステム側なら participant。（JSON上のフィールド: content.mainFlow.participants[].kind） |
| `{{基本フロー.ステップ1.送り手}}` | 送り手（ドメインの役者）。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.mainFlow.steps[].from） |
| `{{基本フロー.ステップ1.受け手}}` | 受け手（ドメインの役者）。event の場合は空でよい。（JSON上のフィールド: content.mainFlow.steps[].to） |
| `{{基本フロー.ステップ1.メッセージ}}` | メッセージ（コマンド/返り値/イベント名）。（JSON上のフィールド: content.mainFlow.steps[].message） |
| `{{基本フロー.ステップ1.種別}}` | command=呼び出し / self=自分への処理 / return=返り値 / event=イベント発行。（JSON上のフィールド: content.mainFlow.steps[].kind） |
| `{{事後条件.結果1}}` | 成功時に成立する結果（集約の状態変化・発行イベント）を列挙。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.postconditions.items[]） |
| `{{受け入れ基準.条件1}}` | 受け入れ条件を EARS で列挙（When/While/If … shall …）。一意・検証可能・ドメイン語彙のみ。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.acceptanceCriteria.items[]） |
| `{{操作保証.保証1}}` | 保証をEARSで列挙（When/While/If … shall …）。書いてよいのは『何を保証するか』だけ（べき等性・一貫性・提供チャネルの一貫性等）。『どう実現するか』（具体的なDB技法・ロック機構・実装技術）は書かない（CodingSchemaのcode-templateの領分）。判定基準（このusecaseに書くか、集約のinvariantsに書くか）: 同じ資源を操作する複数usecaseの間で、この保証内容が重複するか？ 重複するなら集約（agg-*.json）のinvariants/invariantScenariosに書く。このusecase固有の業務理由でのみ必要な保証だけをここに書く。性能の生数値（応答時間・スループット等）は書かない（CodingSchemaのtestTypes: non-functional-performanceの領分）。（配列。この形式の行を必要な数だけ繰り返す）（任意ブロック：無ければoperationGuaranteesブロック自体を省略してよい）（JSON上のフィールド: content.operationGuarantees.items[]） |
| `{{エラー.項目1.コード}}` | エラーコード。例: OUT_OF_STOCK（任意ブロック：無ければerrorsブロック自体を省略してよい）（JSON上のフィールド: content.errors.items[].code） |
| `{{エラー.項目1.条件}}` | そのエラーコードが返る具体的な条件を1文で。例: 対象ファイルが存在しない（JSON上のフィールド: content.errors.items[].condition） |
| `{{受け入れシナリオ.背景}}` | 複数シナリオ共通の前提（Gherkin Background 相当）。無ければ空文字。（JSON上のフィールド: content.acceptanceScenarios.background） |
| `{{受け入れシナリオ.シナリオ1.シナリオ名}}` | シナリオ名（概要）。（JSON上のフィールド: content.acceptanceScenarios.scenarios[].name） |
| `{{受け入れシナリオ.シナリオ1.分類}}` | 分類: 正常系 / 異常系 / 境界値。（JSON上のフィールド: content.acceptanceScenarios.scenarios[].category） |
| `{{受け入れシナリオ.シナリオ1.観点}}` | 観点: 側面（状態遷移/計算整合/事前条件 等）＋検証の狙い。（JSON上のフィールド: content.acceptanceScenarios.scenarios[].viewpoint） |
| `{{受け入れシナリオ.シナリオ1.本文}}` | このシナリオの Given/When/Then（Scenario: 1つ・実行可能なテストとして書き起こせる形）。ドメイン語彙で書き、実装詳細（クラス名/API/SQL/UI 操作）は書かない。（JSON上のフィールド: content.acceptanceScenarios.scenarios[].gherkin） |
| `{{受け入れシナリオ.シナリオ1.参照}}` | 検証する受け入れ基準への参照（任意・トレーサビリティ）。（JSON上のフィールド: content.acceptanceScenarios.scenarios[].covers） |
| `{{受け入れシナリオ.シナリオ1.操作}}` | このシナリオが検証する操作の識別子（任意）。usecaseの実装がoperation引数で複数の操作を分岐する場合のみ設定し、その操作を指す文字列そのものを設定する（例: get_block）。check-operation-driftが実装コードのoperation分岐と機械的に突き合わせるため、gherkin本文に埋め込む代わりにここへ構造化して書く。単一操作のusecaseでは省略する。（本文には描画されない。operationIndexと対になる構造化メタデータ）（JSON上のフィールド: content.acceptanceScenarios.scenarios[].operation） |
| `{{操作保証シナリオ.背景}}` | 複数シナリオ共通の前提。無ければ空文字。（任意ブロック：operationGuaranteesが無ければguaranteeScenariosブロック自体を省略してよい）（JSON上のフィールド: content.guaranteeScenarios.background） |
| `{{操作保証シナリオ.シナリオ1.シナリオ名}}` | シナリオ名（概要）。（JSON上のフィールド: content.guaranteeScenarios.scenarios[].name） |
| `{{操作保証シナリオ.シナリオ1.分類}}` | 分類: 正常系 / 異常系 / 境界値。（JSON上のフィールド: content.guaranteeScenarios.scenarios[].category） |
| `{{操作保証シナリオ.シナリオ1.観点}}` | 観点: べき等性/一貫性/提供チャネルの一貫性 等＋検証の狙い。（JSON上のフィールド: content.guaranteeScenarios.scenarios[].viewpoint） |
| `{{操作保証シナリオ.シナリオ1.本文}}` | Given/When/Then。ドメイン語彙で書き、実装詳細は書かない。（JSON上のフィールド: content.guaranteeScenarios.scenarios[].gherkin） |
| `{{操作保証シナリオ.シナリオ1.参照}}` | 対応するOperationGuaranteesの項目への参照。（JSON上のフィールド: content.guaranteeScenarios.scenarios[].covers） |

---

# {{タイトル}}

---

## 概要

- {{概要.論点1}}

---

## 存在意義

- {{存在意義.理由1}}

---

## 主アクターと意図

- **主アクター**: {{主アクターと意図.主アクター}}
- **意図**: {{主アクターと意図.意図}}

---

## 関与する外部

- {{関与する外部.副アクター1}}

---

## 操作一覧

| 操作 | 概要 |
|---|---|
| `{{操作一覧.項目1.操作}}` | {{操作一覧.項目1.概要}} |

---

## 事前条件

- {{事前条件.条件1}}

---

## 基本フロー

```mermaid
sequenceDiagram
    {{基本フロー.登場人物1.種別}} {{基本フロー.登場人物1.識別子}}
    {{基本フロー.ステップ1.送り手}}->>{{基本フロー.ステップ1.受け手}}: {{基本フロー.ステップ1.メッセージ}}
```

---

## 事後条件

- {{事後条件.結果1}}

---

## 受け入れ基準

- {{受け入れ基準.条件1}}

---

## 操作保証

- {{操作保証.保証1}}

---

## エラー

| コード | 条件 |
|---|---|
| `{{エラー.項目1.コード}}` | {{エラー.項目1.条件}} |

---

## 受け入れシナリオ

### 背景

{{受け入れシナリオ.背景}}

### {{受け入れシナリオ.シナリオ1.シナリオ名}}

| 分類 | 観点 |
|---|---|
| {{受け入れシナリオ.シナリオ1.分類}} | {{受け入れシナリオ.シナリオ1.観点}} |

```gherkin
{{受け入れシナリオ.シナリオ1.本文}}
```

---

## 操作保証シナリオ

### 背景

{{操作保証シナリオ.背景}}

### {{操作保証シナリオ.シナリオ1.シナリオ名}}

| 分類 | 観点 |
|---|---|
| {{操作保証シナリオ.シナリオ1.分類}} | {{操作保証シナリオ.シナリオ1.観点}} |

```gherkin
{{操作保証シナリオ.シナリオ1.本文}}
```
