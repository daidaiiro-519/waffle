# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | documentId をそのまま設定してください。 |
| `{{summary.text}}` | このコンポーネント/領域の概要を1〜2文で。 |
| `{{capacity.title}}` | このブロックの見出し。「容量・性能要件」など具体的な名称を記入。 |
| `{{capacity.items[1].metric}}` | 指標・目標値・根拠を列挙。IaCコードから導出できる情報(具体的な設定値の羅列)ではなく、その目標値がなぜ必要かという事業/業務側の根拠を書く。 |
| `{{capacity.items[1].target}}` | 目標値。 |
| `{{capacity.items[1].rationale}}` | 根拠。 |
| `{{resilience.items[1].metric}}` | 耐障害性の指標・目標値・根拠を列挙。 |
| `{{resilience.items[1].target}}` | 目標値。 |
| `{{resilience.items[1].rationale}}` | 根拠。 |
| `{{security.items[1].boundary}}` | このコンポーネント固有のセキュリティ境界を列挙(プロダクト全体を横断するコンプライアンス/アクセス方針はsecurity specKindの責務であり、ここには書かない)。 |
| `{{security.items[1].requirement}}` | 要件。 |
| `{{layout.zones[1].id}}` | ゾーンのid。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{layout.zones[1].label}}` | ゾーンのlabel。 |
| `{{layout.zones[1].contains[1].id}}` | そのゾーンに含まれるコンポーネントのid。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{layout.zones[1].contains[1].label}}` | そのゾーンに含まれるコンポーネントのlabel。 |
| `{{layout.connections[1].from}}` | コンポーネント間の接続元(from)。containsで宣言したidを使う。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{layout.connections[1].to}}` | コンポーネント間の接続先(to)。containsで宣言したidを使う。 |
| `{{guaranteeScenarios.background}}` | 複数シナリオ共通の前提。無ければ空文字。 |
| `{{guaranteeScenarios.scenarios[1].name}}` | シナリオ名（概要）。 |
| `{{guaranteeScenarios.scenarios[1].category}}` | 分類: 正常系 / 異常系 / 境界値。 |
| `{{guaranteeScenarios.scenarios[1].viewpoint}}` | 観点: 何を保証するか＋検証の狙い。 |
| `{{guaranteeScenarios.scenarios[1].gherkin}}` | Given/When/Then。ドメイン語彙で書き、IaCの実装詳細は書かない。 |
| `{{guaranteeScenarios.scenarios[1].covers}}` | 対応する保証項目への参照。 |

---

# {{title.title}}

---

## 概要

{{summary.text}}

---

## {{capacity.title}}

| 指標 | 目標値 | 根拠 |
|---|---|---|
| {{capacity.items[1].metric}} | {{capacity.items[1].target}} | {{capacity.items[1].rationale}} |

---

## 耐障害性要件

| 指標 | 目標値 | 根拠 |
|---|---|---|
| {{resilience.items[1].metric}} | {{resilience.items[1].target}} | {{resilience.items[1].rationale}} |

---

## このコンポーネント固有のセキュリティ境界

| 境界 | 要件 |
|---|---|
| {{security.items[1].boundary}} | {{security.items[1].requirement}} |

---

## ネットワーク構成図

```mermaid
architecture-beta
    group {{layout.zones[1].id}}(cloud)["{{layout.zones[1].label}}"]
        service {{layout.zones[1].contains[1].id}}(server)["{{layout.zones[1].contains[1].label}}"] in {{layout.zones[1].id}}

    {{layout.connections[1].from}}:R --> L:{{layout.connections[1].to}}
```

---

## プラットフォーム操作保証シナリオ

### 背景

{{guaranteeScenarios.background}}

### {{guaranteeScenarios.scenarios[1].name}}

| 分類 | 観点 |
|---|---|
| {{guaranteeScenarios.scenarios[1].category}} | {{guaranteeScenarios.scenarios[1].viewpoint}} |

```gherkin
{{guaranteeScenarios.scenarios[1].gherkin}}
```
