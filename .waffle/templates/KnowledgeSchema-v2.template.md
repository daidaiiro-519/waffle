# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | documentId をそのまま設定してください。 |
| `{{overview.questions[1]}}` | この概念を知ることで答えられるようになる、利用者の具体的な問いを列挙してください。「〜べきか」「〜はどう判断するか」の形で。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{overview.text}}` | この概念が何であるかを1〜2文で要約してください。 |
| `{{principles.items[1]}}` | この概念の原則を、独立した主張ごとに1要素で列挙してください（例: 定義・成立根拠・優先順位・副次的効果は、それぞれ別要素に分ける）。1要素は1〜2文とし、他の要素の主張と混在させない。出典の一般原則に基づいて記述してください。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{classifications.items[1].name}}` | 分類名。例: core / supporting / generic（配列。この形式の行を必要な数だけ繰り返す） |
| `{{classifications.items[1].description}}` | その分類の特徴を1文で。例: 競争優位を生む中核的な業務領域 |
| `{{classifications.emptyReason}}` | itemsが空の場合、この概念に分類軸が無い理由を書いてください。itemsに中身がある場合は空文字でよい。 |
| `{{decisionCriteria.stages[1].id}}` | ノードの識別子。例: q1（配列。この形式の行を必要な数だけ繰り返す） |
| `{{decisionCriteria.stages[1].label}}` | 問いや帰結の短い文言。例: 複数集約にまたがるか？ |
| `{{decisionCriteria.transitions[1].from}}` | 遷移元ノードのid。stagesで宣言済みのidの中から選ぶ。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{decisionCriteria.transitions[1].to}}` | 遷移先ノードのid。stagesで宣言済みのidの中から選ぶ。 |
| `{{decisionCriteria.transitions[1].label}}` | 遷移条件（回答）の短い文言。例: はい / いいえ |
| `{{decisionCriteria.emptyReason}}` | stages/transitionsが空の場合、この概念に判断の分岐点が無い理由を書いてください。中身がある場合は空文字でよい。 |
| `{{examples.text}}` | 架空の題材を使い、この概念を具体的に当てはめた実例を記述してください。特定の実在企業名は避けてください。 |
| `{{antiPatterns.items[1].name}}` | アンチパターン名。何が誤りかが分かる短い名詞句で。例: 貧血ドメインモデル（配列。この形式の行を必要な数だけ繰り返す） |
| `{{antiPatterns.items[1].problem}}` | その誤りが引き起こす具体的な問題を1文で。 |
| `{{antiPatterns.emptyReason}}` | itemsが空の場合、この概念によくある誤りが無い理由を書いてください。itemsに中身がある場合は空文字でよい。 |
| `{{provenance.source}}` | 内容の出典（著者名・書籍/論文名・年等）と、要約/再構成であり直接引用でないことを明記してください。 |
| `{{provenance.caveats}}` | 調査・検証の過程でまだ確証が得られていない留保事項があれば書いてください（例: 特定の定式化が検証で却下された等）。無ければ空文字。 |
| `{{relatedConcepts.items[1].conceptId}}` | 関連するKnowledge documentのdocumentId。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{relatedConcepts.items[1].note}}` | どう関連するかを1文で。例: この概念の前提となる基礎概念 |
| `{{relatedConcepts.emptyReason}}` | itemsが空の場合、この概念に関連する他のKnowledgeが無い理由を書いてください。itemsに中身がある場合は空文字でよい。 |

---

# {{title.title}}

---

## 概要

### この概念が答える判断

- {{overview.questions[1]}}

{{overview.text}}

---

## 原則

- {{principles.items[1]}}

---

## 分類

| 分類 | 特徴 |
|---|---|
| {{classifications.items[1].name}} | {{classifications.items[1].description}} |

{{classifications.emptyReason}}

---

## 判断基準

```mermaid
flowchart LR
    {{decisionCriteria.stages[1].id}}[{{decisionCriteria.stages[1].label}}]
    {{decisionCriteria.transitions[1].from}} -->|{{decisionCriteria.transitions[1].label}}| {{decisionCriteria.transitions[1].to}}
```

{{decisionCriteria.emptyReason}}

---

## 実例

{{examples.text}}

---

## アンチパターン

| アンチパターン | 問題点 |
|---|---|
| {{antiPatterns.items[1].name}} | {{antiPatterns.items[1].problem}} |

{{antiPatterns.emptyReason}}

---

## 出典・根拠の透明性

{{provenance.source}}

### 留保事項

{{provenance.caveats}}

---

## 関連概念

| 関連概念 | 関係 |
|---|---|
| {{relatedConcepts.items[1].conceptId}} | {{relatedConcepts.items[1].note}} |

{{relatedConcepts.emptyReason}}
