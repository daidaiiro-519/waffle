# artifact-share アップロード画面の動作確認用サンプル

アップロード画面が、HTMLの `<head>` を見て振る舞いを変える部分を確認するためのサンプル。
それぞれをアップロード画面へドラッグ＆ドロップすると、下表の分岐を再現できる。

| ファイル | document-graphのmetaタグ | 外部依存 | 期待する挙動 |
|---|---|---|---|
| `with-meta-decision-record.html` | あり（id/type/title/description/tags） | なし | 入力欄が1つも出ず、読み取った内容がそのまま表示される |
| `no-meta-plain.html` | なし | なし | 表示名の入力欄のみ。初期値に `<title>` が入る |
| `no-meta-external-deps.html` | なし | あり（フォント・画像） | 表示名の入力欄に加えて、外部依存の警告が件数付きで出る |

## 判定の基準

「どのツールが作ったか」でも「どの経路で入ってきたか」でもなく、
**HTMLからメタデータを取り出せるか否か**で分岐する。利用者に「これは外部で作ったHTMLですか？」とは尋ねない。

既定テンプレートで作った文書は以下を `<head>` に持つため、自動で読み取れる。

```html
<meta name="id" content="adr-search-backend-pg-trgm">
<meta name="type" content="DecisionRecord">
<meta name="title" content="検索基盤にPostgreSQLの全文検索を採用する">
<meta name="description" content="...">
<meta name="tags" content="backend, search, database, adr">
```

`no-meta-external-deps.html` が参照している外部URLは実在しない。
公開後はCSPにより読み込みが止まるため、この警告は「公開したら見た目が変わる」ことを事前に伝えるためのもの。
