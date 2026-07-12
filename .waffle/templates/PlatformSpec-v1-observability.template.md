# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | documentId をそのまま設定してください。 |
| `{{summary.text}}` | このコンポーネント/領域の概要を1〜2文で。 |
| `{{monitoring.items[1].target}}` | 監視対象・閾値・重大度を列挙。 |
| `{{monitoring.items[1].threshold}}` | 閾値。 |
| `{{monitoring.items[1].severity}}` | 重大度。 |
| `{{retention.items[1].dataType}}` | データ種別・保持期間・根拠を列挙。 |
| `{{retention.items[1].retentionPeriod}}` | 保持期間。 |
| `{{retention.items[1].rationale}}` | 根拠。 |
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

## 監視対象と閾値

| 監視対象 | 閾値 | 重大度 |
|---|---|---|
| {{monitoring.items[1].target}} | {{monitoring.items[1].threshold}} | {{monitoring.items[1].severity}} |

---

## 保持方針

| データ種別 | 保持期間 | 根拠 |
|---|---|---|
| {{retention.items[1].dataType}} | {{retention.items[1].retentionPeriod}} | {{retention.items[1].rationale}} |

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
