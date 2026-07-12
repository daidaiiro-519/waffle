# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{タイトル}}` | documentId をそのまま設定してください。（JSON上のフィールド: content.title.title） |
| `{{概要}}` | このコンポーネント/領域の概要を1〜2文で。（JSON上のフィールド: content.summary.text） |
| `{{デプロイ対象.見出し}}` | このブロックの見出し。「デプロイ先要件」など具体的な名称を記入。（JSON上のフィールド: content.deploymentTargets.title） |
| `{{デプロイ対象.項目1.指標}}` | 指標・目標値・根拠を列挙。IaCコードから導出できる情報(具体的な設定値の羅列)ではなく、その目標値がなぜ必要かという事業/業務側の根拠を書く。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.deploymentTargets.items[].metric） |
| `{{デプロイ対象.項目1.目標値}}` | 目標値。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.deploymentTargets.items[].target） |
| `{{デプロイ対象.項目1.根拠}}` | 根拠。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.deploymentTargets.items[].rationale） |
| `{{リリース昇格方針.項目1.環境}}` | 環境ごとの昇格基準・承認要件を列挙。各環境の詳細な昇格基準を記述する(パイプライン図の各段階に対応)。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.releasePolicy.items[].environment） |
| `{{リリース昇格方針.項目1.昇格基準}}` | 昇格基準。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.releasePolicy.items[].promotionCriteria） |
| `{{リリース昇格方針.項目1.承認要件}}` | 承認要件。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.releasePolicy.items[].approvalRequirement） |
| `{{リリースパイプライン.段階1.ID}}` | 環境の段階(id)を列挙。例: dev（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.releasePipeline.stages[].id） |
| `{{リリースパイプライン.段階1.ラベル}}` | 環境の段階(label)。例: 開発環境（JSON上のフィールド: content.releasePipeline.stages[].label） |
| `{{リリースパイプライン.遷移1.遷移元}}` | 段階間の遷移の遷移元(from)。stagesで宣言済みのidを使う。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.releasePipeline.transitions[].from） |
| `{{リリースパイプライン.遷移1.遷移先}}` | 段階間の遷移の遷移先(to)。stagesで宣言済みのidを使う。（JSON上のフィールド: content.releasePipeline.transitions[].to） |
| `{{リリースパイプライン.遷移1.昇格条件}}` | 昇格条件の要約(label)。（JSON上のフィールド: content.releasePipeline.transitions[].label） |
| `{{保証シナリオ.背景}}` | 複数シナリオ共通の前提。無ければ空文字。（JSON上のフィールド: content.guaranteeScenarios.background） |
| `{{保証シナリオ.シナリオ1.シナリオ名}}` | シナリオ名（概要）。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.guaranteeScenarios.scenarios[].name） |
| `{{保証シナリオ.シナリオ1.分類}}` | 分類: 正常系 / 異常系 / 境界値。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.guaranteeScenarios.scenarios[].category） |
| `{{保証シナリオ.シナリオ1.観点}}` | 観点: 何を保証するか＋検証の狙い。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.guaranteeScenarios.scenarios[].viewpoint） |
| `{{保証シナリオ.シナリオ1.シナリオ本文}}` | Given/When/Then。ドメイン語彙で書き、IaCの実装詳細は書かない。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.guaranteeScenarios.scenarios[].gherkin） |
| `{{保証シナリオ.シナリオ1.対応項目}}` | 対応する保証項目への参照。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.guaranteeScenarios.scenarios[].covers） |

---

# {{タイトル}}

---

## 概要

{{概要}}

---

## {{デプロイ対象.見出し}}

| 指標 | 目標値 | 根拠 |
|---|---|---|
| {{デプロイ対象.項目1.指標}} | {{デプロイ対象.項目1.目標値}} | {{デプロイ対象.項目1.根拠}} |

---

## リリース/環境昇格方針

| 環境 | 昇格基準 | 承認要件 |
|---|---|---|
| {{リリース昇格方針.項目1.環境}} | {{リリース昇格方針.項目1.昇格基準}} | {{リリース昇格方針.項目1.承認要件}} |

---

## リリースパイプライン

```mermaid
flowchart LR
    {{リリースパイプライン.段階1.ID}}[{{リリースパイプライン.段階1.ラベル}}]
    {{リリースパイプライン.遷移1.遷移元}} -->|{{リリースパイプライン.遷移1.昇格条件}}| {{リリースパイプライン.遷移1.遷移先}}
```

---

## プラットフォーム操作保証シナリオ

### 背景

{{保証シナリオ.背景}}

### {{保証シナリオ.シナリオ1.シナリオ名}}

| 分類 | 観点 |
|---|---|
| {{保証シナリオ.シナリオ1.分類}} | {{保証シナリオ.シナリオ1.観点}} |

```gherkin
{{保証シナリオ.シナリオ1.シナリオ本文}}
```
