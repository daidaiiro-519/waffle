# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | documentId をそのまま設定してください。 |
| `{{summary.text}}` | このコンポーネント/領域の概要を1〜2文で。 |
| `{{servingTargets.title}}` | このブロックの見出し。「サービング要件」など具体的な名称を記入。 |
| `{{servingTargets.items[1].metric}}` | 指標・目標値・根拠を列挙。IaCコードから導出できる情報(具体的な設定値の羅列)ではなく、その目標値がなぜ必要かという事業/業務側の根拠を書く。 |
| `{{servingTargets.items[1].target}}` | 目標値。 |
| `{{servingTargets.items[1].rationale}}` | 根拠。 |
| `{{trainingDataGovernance.items[1].dataClassification}}` | 学習データのデータ分類・利用境界・要件を列挙。 |
| `{{trainingDataGovernance.items[1].usageBoundary}}` | 利用境界。 |
| `{{trainingDataGovernance.items[1].requirement}}` | 要件。 |
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

## {{servingTargets.title}}

| 指標 | 目標値 | 根拠 |
|---|---|---|
| {{servingTargets.items[1].metric}} | {{servingTargets.items[1].target}} | {{servingTargets.items[1].rationale}} |

---

## 学習データガバナンス

| データ分類 | 利用境界 | 要件 |
|---|---|---|
| {{trainingDataGovernance.items[1].dataClassification}} | {{trainingDataGovernance.items[1].usageBoundary}} | {{trainingDataGovernance.items[1].requirement}} |

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
