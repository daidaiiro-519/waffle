# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{タイトル}}` | documentId をそのまま設定してください。（JSON上のフィールド: content.title.title） |
| `{{命名.項目1.対象}}` | 命名の対象。例: モジュール / ファイル（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.naming.items[].target） |
| `{{命名.項目1.規約}}` | 命名規約。例: スネークケース（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.naming.items[].convention） |
| `{{スタイル.項目1.種別}}` | 種別。必須 / 禁止 / 推奨のいずれか。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.style.items[].level） |
| `{{スタイル.項目1.規約}}` | 型注釈・関数の責務範囲・import規律等、コードスタイルに関する規約の内容。例: 全ての公開関数に型注釈を付ける（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.style.items[].rule） |
| `{{docstring.スタイル}}` | 言語標準の docstring スタイル。例: Google スタイル docstring（JSON上のフィールド: content.docstring.style） |
| `{{docstring.要約行の書き方}}` | 要約行（1行目）の書き方の指針。「何をするか・いつ使うか」を検索と判断に効く語で、の旨。（JSON上のフィールド: content.docstring.summaryGuidance） |
| `{{docstring.対象}}` | docstring を必須にする対象。例: 公開要素（module / 公開 class / 公開 function）。private は任意。（JSON上のフィールド: content.docstring.target） |
| `{{docstring.コード例}}` | このスタイルに従った docstring のコード例（要約行＋本文＋Args/Returns 等・カスタムタグなし）。（JSON上のフィールド: content.docstring.example） |
| `{{決定ルール.項目1.種別}}` | 種別。必須 / 禁止 / 推奨のいずれか。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.rules.items[].level） |
| `{{決定ルール.項目1.規約}}` | docstring必須の範囲・コードから導出できる情報を書かない・仕様と異なる語彙で命名しない等、docstring/コメントに関する規約の内容。例: 公開関数のdocstringは要約行＋Args/Returnsを持つ（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.rules.items[].rule） |

---

# {{タイトル}}

---

## 命名

| 対象 | 規約 |
|---|---|
| {{命名.項目1.対象}} | {{命名.項目1.規約}} |

---

## スタイル

| 種別 | 規約 |
|---|---|
| {{スタイル.項目1.種別}} | {{スタイル.項目1.規約}} |

---

## docstring

- **スタイル**: {{docstring.スタイル}}
- **対象**: {{docstring.対象}}

### 要約行の書き方

{{docstring.要約行の書き方}}

```
{{docstring.コード例}}
```

---

## 決定ルール

| 種別 | 規約 |
|---|---|
| {{決定ルール.項目1.種別}} | {{決定ルール.項目1.規約}} |
