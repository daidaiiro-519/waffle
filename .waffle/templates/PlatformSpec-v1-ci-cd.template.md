# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | documentId をそのまま設定してください。 |
| `{{summary.text}}` | このコンポーネント/領域の概要を1〜2文で。 |
| `{{deploymentTargets.title}}` | このブロックの見出し。「デプロイ先要件」など具体的な名称を記入。 |
| `{{deploymentTargets.items[1].metric}}` | 指標・目標値・根拠を列挙。IaCコードから導出できる情報(具体的な設定値の羅列)ではなく、その目標値がなぜ必要かという事業/業務側の根拠を書く。 |
| `{{deploymentTargets.items[1].target}}` | 目標値。 |
| `{{deploymentTargets.items[1].rationale}}` | 根拠。 |
| `{{releasePolicy.items[1].environment}}` | 環境ごとの昇格基準・承認要件を列挙。各環境の詳細な昇格基準を記述する(パイプライン図の各段階に対応)。 |
| `{{releasePolicy.items[1].promotionCriteria}}` | 昇格基準。 |
| `{{releasePolicy.items[1].approvalRequirement}}` | 承認要件。 |
| `{{releasePipeline.stages[1].id}}` | 環境の段階(id)を列挙。例: dev（配列。この形式の行を必要な数だけ繰り返す） |
| `{{releasePipeline.stages[1].label}}` | 環境の段階(label)。例: 開発環境 |
| `{{releasePipeline.transitions[1].from}}` | 段階間の遷移の遷移元(from)。stagesで宣言済みのidを使う。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{releasePipeline.transitions[1].to}}` | 段階間の遷移の遷移先(to)。stagesで宣言済みのidを使う。 |
| `{{releasePipeline.transitions[1].label}}` | 昇格条件の要約(label)。 |
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

## {{deploymentTargets.title}}

| 指標 | 目標値 | 根拠 |
|---|---|---|
| {{deploymentTargets.items[1].metric}} | {{deploymentTargets.items[1].target}} | {{deploymentTargets.items[1].rationale}} |

---

## リリース/環境昇格方針

| 環境 | 昇格基準 | 承認要件 |
|---|---|---|
| {{releasePolicy.items[1].environment}} | {{releasePolicy.items[1].promotionCriteria}} | {{releasePolicy.items[1].approvalRequirement}} |

---

## リリースパイプライン

```mermaid
flowchart LR
    {{releasePipeline.stages[1].id}}[{{releasePipeline.stages[1].label}}]
    {{releasePipeline.transitions[1].from}} -->|{{releasePipeline.transitions[1].label}}| {{releasePipeline.transitions[1].to}}
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
