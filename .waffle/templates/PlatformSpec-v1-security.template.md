# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | documentId をそのまま設定してください。 |
| `{{summary.text}}` | このコンポーネント/領域の概要を1〜2文で。 |
| `{{compliance.items[1].framework}}` | コンプライアンスフレームワークの名称・対象範囲・要件を列挙。例: SOC2, PCI-DSS, GDPR |
| `{{compliance.items[1].scope}}` | 対象範囲。 |
| `{{compliance.items[1].requirement}}` | 要件。 |
| `{{accessPolicy.items[1].principal}}` | アクセス制御の主体・許可される操作・条件を列挙。例: 特定ロール、サービスアカウント |
| `{{accessPolicy.items[1].allowedActions}}` | 許可される操作。 |
| `{{accessPolicy.items[1].condition}}` | 条件。無ければ空。 |
| `{{dataBoundary.items[1].classification}}` | データ分類ごとの境界・要件を列挙。 |
| `{{dataBoundary.items[1].boundary}}` | 境界。 |
| `{{dataBoundary.items[1].requirement}}` | 要件。 |
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

## コンプライアンス要件

| フレームワーク | 対象範囲 | 要件 |
|---|---|---|
| {{compliance.items[1].framework}} | {{compliance.items[1].scope}} | {{compliance.items[1].requirement}} |

---

## アクセス制御方針

| 主体 | 許可される操作 | 条件 |
|---|---|---|
| {{accessPolicy.items[1].principal}} | {{accessPolicy.items[1].allowedActions}} | {{accessPolicy.items[1].condition}} |

---

## データ分類ごとの境界

| データ分類 | 境界 | 要件 |
|---|---|---|
| {{dataBoundary.items[1].classification}} | {{dataBoundary.items[1].boundary}} | {{dataBoundary.items[1].requirement}} |

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
