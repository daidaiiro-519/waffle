# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{タイトル}}` | documentId をそのまま設定してください。（JSON上のフィールド: content.title.title） |
| `{{概要}}` | このコンポーネント/領域の概要を1〜2文で。（JSON上のフィールド: content.summary.text） |
| `{{クエリ性能目標.見出し}}` | このブロックの見出し。「クエリ性能目標」など具体的な名称を記入。（JSON上のフィールド: content.queryPerformanceTargets.title） |
| `{{クエリ性能目標.項目1.指標}}` | 指標・目標値・根拠を列挙。IaCコードから導出できる情報(具体的な設定値の羅列)ではなく、その目標値がなぜ必要かという事業/業務側の根拠を書く。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.queryPerformanceTargets.items[].metric） |
| `{{クエリ性能目標.項目1.目標値}}` | 目標値。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.queryPerformanceTargets.items[].target） |
| `{{クエリ性能目標.項目1.根拠}}` | 根拠。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.queryPerformanceTargets.items[].rationale） |
| `{{保持方針.項目1.データ種別}}` | データ種別・保持期間・根拠を列挙。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.retention.items[].dataType） |
| `{{保持方針.項目1.保持期間}}` | 保持期間。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.retention.items[].retentionPeriod） |
| `{{保持方針.項目1.根拠}}` | 根拠。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.retention.items[].rationale） |
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

## {{クエリ性能目標.見出し}}

| 指標 | 目標値 | 根拠 |
|---|---|---|
| {{クエリ性能目標.項目1.指標}} | {{クエリ性能目標.項目1.目標値}} | {{クエリ性能目標.項目1.根拠}} |

---

## 保持方針

| データ種別 | 保持期間 | 根拠 |
|---|---|---|
| {{保持方針.項目1.データ種別}} | {{保持方針.項目1.保持期間}} | {{保持方針.項目1.根拠}} |

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
