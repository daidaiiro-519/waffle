# アーティファクトシェア — 設計資料

作った文書に、URLひとつで反応が返ってくる共有ツールの設計一式。
**見るのは不特定多数、上げるのは招待された人だけ**という非対称を、自前のAWS環境だけで成立させる。

まず [overview.html](overview.html) を開く。以下すべてへのリンクが張ってある。

## 構成

| 場所 | 内容 |
|---|---|
| `overview.html` | 全体まとめ。構想・構成・画面・テンプレート・決定事項・実装順序 |
| `design/architecture.html` | 中身の由来を問わない配信ラッパーの位置づけ。design-share＝POCという経緯 |
| `design/boundary-and-auth.html` | アクター定義、招待制に至る比較、Cognito対IIC、オリジン分離、metaスキーマ |
| `design/requirements.html` | SKILL.md要件・インフラ要件。流用／新規／変更の切り分けと移行手順 |
| `ui/main.html` | メイン画面。アップロードと自分の一覧 |
| `ui/project.html` | プロジェクト画面。一覧と詳細 |
| `ui/viewer.html` | 閲覧者の画面。トークン入力から共有された一覧まで |
| `ui/viewing.html` | 開いた画面。文書本体＋コメント欄 |
| `templates/` | 既定4種の空テンプレート（`{{...}}` に執筆ガイダンス入り） |
| `examples/` | 同じ4種の記入例 |

動作確認用のサンプルHTMLは [`../samples/artifact-share/`](../samples/artifact-share/) にある。
`ui/main.html` へドロップすると、metaタグの有無による分岐をそのまま確認できる。

## UIモックについて

`ui/` 配下はすべてブラウザで開けば実際に動く。外部依存はゼロ。

- `main.html` — HTMLをドロップすると `<head>` を解析し、document-graph契約のmetaタグがあれば入力欄を出さずに公開できる。ないときは表示名だけ尋ねる
- コメント件数を押すと、本体を開かずコメントだけを読むダイアログが出る
- 行の `⋯` から差し替え・トークン再発行・エクスポート・無効化のダイアログを確認できる

## 経緯

- 設計判断に至るまでのやり取りは [`../brainstorm/brainstorm-artifact-share-concept.md`](../brainstorm/brainstorm-artifact-share-concept.md)（8論点の合意記録）
- design-share は本構想を先に確かめたPOC。配信基盤の側を本体として据え直し、design-share は UIモックという対象物とその作り方の専門知識だけを持つ子スキルになる
