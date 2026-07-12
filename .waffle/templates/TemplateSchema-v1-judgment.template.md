# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | documentId をそのまま設定してください。 |
| `{{trigger.text}}` | この骨格がいつ使われるべきかを一文で書いてください（例:「『このコードはどこに置くべきか』等の配置・依存方向に関する判断を求める相談」）。実際の相談文ではなく、発動条件の説明であることに注意。 |
| `{{trigger.openingLine}}` | 判断フローに入る前に相談対象を一文でスコープする文を{{}}プレースホルダー込みで書いてください（例:「{{対象（ユーザーが提示したシステム・機能・設計）}}について判断します。」）。 |
| `{{contextBlocks.items[1].title}}` | 前置きセクションの見出し。例: サブドメイン分類（配列。この形式の行を必要な数だけ繰り返す。判断フローに入る前に確認させたい前提〔分類・階層等〕が無ければ items を空配列にし、このセクション自体を本文から省略する） |
| `{{contextBlocks.items[1].guidance}}` | そのセクションに何を書くべきかの指示文（{{}}プレースホルダーを使う）。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{diagnosticFlow.title}}` | このセクションの見出しを書いてください。骨格の性質に応じて『判断フロー』『診断フロー』『計画フロー』等、文脈に合った語を選んでよい（見出し語自体は骨格ごとに変わってよいが、直後のitemsの構造は共通）。 |
| `{{diagnosticFlow.items[1].question}}` | 問い文（{{}}プレースホルダーを含む）。例:「{{判断の起点となる問い}}」（配列。この形式の行を必要な数だけ繰り返す） |
| `{{diagnosticFlow.items[1].branches[1].condition}}` | 分岐条件（例: YESの条件、NOの条件）。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{diagnosticFlow.items[1].branches[1].then}}` | その条件のときどうなるか（次の問いへ進む旨、または結論そのもの）。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{verdict.guidance}}` | 判定結果をどう提示すべきかの指示を{{}}プレースホルダー込みで書いてください。判定理由（バックボーンの定義・原則に基づく根拠）を必ず示すよう指示に含めること。 |
| `{{recommendedAction.guidance}}` | 推奨アクションをどう提示すべきかの指示を{{}}プレースホルダー込みで書いてください。動詞で始まる具体的な行動を示すよう指示に含めること。 |
| `{{extraSections.items[1].title}}` | 追加セクションの見出し。例: 診断的差し戻し（該当する場合のみ）（配列。この形式の行を必要な数だけ繰り返す。判定・推奨アクションの後に必要な追加セクションが無ければ items を空配列にし、このセクション自体を本文から省略する） |
| `{{extraSections.items[1].guidance}}` | そのセクションに何を書くべきかの指示文（{{}}プレースホルダーを使う）。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{antiPatternNote.guidance}}` | アンチパターンに該当する場合に何を書くべきかの指示を{{}}プレースホルダー込みで書いてください。該当するアンチパターン名とリスクをセットで示すよう指示に含めること。 |

（`contextBlocks.emptyReason` / `extraSections.emptyReason` はitemsが空配列のときにその理由を記録するデータ専用フィールドで、本文には描画されない。items=[]にする場合は必ずこの理由も埋めること。`diagnosticFlow.items[1].questionId`〔例: q1〕も本文には描画されない内部識別子。）

---

# {{title.title}}

---

## 使用条件

{{trigger.text}}

{{trigger.openingLine}}

---

## 前置きセクション

### {{contextBlocks.items[1].title}}

{{contextBlocks.items[1].guidance}}

---

## {{diagnosticFlow.title}}

### {{diagnosticFlow.items[1].question}}

| 条件 | 結果 |
|---|---|
| {{diagnosticFlow.items[1].branches[1].condition}} | {{diagnosticFlow.items[1].branches[1].then}} |

---

## 判定

{{verdict.guidance}}

---

## 推奨アクション

{{recommendedAction.guidance}}

---

## 追加セクション

### {{extraSections.items[1].title}}

{{extraSections.items[1].guidance}}

---

## 注意（アンチパターンに該当する場合のみ）

{{antiPatternNote.guidance}}
