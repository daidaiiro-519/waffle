---
name: "document-graph"
description: "MD/HTMLファイル群の間の関連性をtreemap・カテゴリ一覧・紐づき先ツリーで可視化したいときに使う。Waffleのdocument.jsonに一切依存せず、MD frontmatter／HTML <meta>タグ＋本文リンクという契約だけを前提に動くので、任意のマークダウン・HTMLフォルダに対して使える。「documentどうしの関係を見せて」「ナレッジベースの全体像を俯瞰したい」と言われたときに使う。"
disable-model-invocation: true
---

# MD/HTMLの契約に基づきdocument間の関係をtreemapで可視化するSkill：document-graph

## 目的

MD/HTMLファイル群の間の関連性をtreemap・カテゴリ一覧・紐づき先ツリーで可視化したいときに使う。Waffleのdocument.jsonに一切依存せず、MD frontmatter／HTML <meta>タグ＋本文リンクという契約だけを前提に動くので、任意のマークダウン・HTMLフォルダに対して使える。「documentどうしの関係を見せて」「ナレッジベースの全体像を俯瞰したい」と言われたときに使う。

---

## 役割

- MD frontmatter／HTML <meta>タグ＋本文リンクという契約に沿ってnode/edgeを抽出する
- 抽出したグラフをtreemap・カテゴリ一覧・関連ツリーとして可視化するローカルサーバーを提供する
- config.json（表示したいソースの宣言）とsources/配下のシムリンクをCLI経由で管理する
- MD→HTML変換等の生成ロジックは持たず、契約に従った既存のMD/HTMLを表示するだけに徹する

---

## 処理対象と成果物

### 処理対象

契約（id=ファイル名幹、type/title/description/tagsをfrontmatterまたは<meta>で宣言し、本文中の標準リンクで関連を表す）を満たすMD/HTMLファイル群を格納したフォルダ、またはCLIで登録済みのソース一覧。

### 成果物

typeごとの規模感を示すtreemap・カテゴリ一覧・documentごとの紐づき先ツリーを備えた自己完結HTMLを、ローカルサーバー（127.0.0.1限定）で配信する。

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| 可視化したいMD/HTMLフォルダのパス | 明示されなければユーザーに確認する。相対パスは実行時のカレントディレクトリを基準に絶対パスへ解決する。 |
| フォルダのalias・format | 指定がなければフォルダ名から自動生成・配下拡張子の多数決で自動推定する（`document-graph add`が行う）。 |
| サーバーのポート番号 | 指定がなければ既定の4173を使う。 |

---

## 実行手順

### Step 1: ソースフォルダをconfig.jsonへ登録する

対象のMD/HTMLフォルダを`document-graph add <path>`で登録する。alias自動生成・format自動推定・sources/配下へのシムリンク同期・契約チェック（frontmatter/meta未検出件数）が1コマンドで行われる。

### Step 2: 登録済みソースを確認する

`document-graph list`で現在登録されているソースの一覧（alias/format/path）を確認する。

### Step 3: ローカルサーバーを起動しグラフを閲覧する

`document-graph serve [--port 4173]`でローカルサーバーを起動し、ブラウザで開く。GETのたびにsources/配下を再スキャンして最新のグラフを返すので、ファイルを追記・保存した後はページ再読み込みだけで反映される。

### Step 4: 不要になったソースを削除する

`document-graph remove <alias>`で登録とシムリンクを解除する。

---

## 出力形式

`add`はalias／format／symlink同期結果／契約チェック結果（frontmatter・meta未検出件数、重複ファイル名の警告があれば併記）を箇条書きで報告する。`list`はalias・format・pathをタブ区切りで一覧する。`serve`は起動したURLを1行で表示する。

---

## ガードレール

- 動作要件はpython3（標準ライブラリのみ）で完結し、PyYAML等の外部パッケージを追加しない
- サーバーは127.0.0.1限定で待受け、外部公開しない
- Skill自身はMD→HTML変換等の生成ロジックを持たない。契約（frontmatter/meta＋本文リンク）を満たすMD/HTMLを表示するだけに徹する
- config.jsonは手作業で編集せず、必ずadd/list/removeコマンド経由で変更する
- 全ソースを通じてファイル名（拡張子除く）は一意という契約を前提とする。重複が検出された場合は警告として画面に表示されるので、ファイル名を調整して解消する
- sources/配下のシムリンクはSkillが自動管理する統制フォルダなので、手動でファイルを追加・編集しない

---

## 参照

- `scripts/config.py`: config.jsonの読み書きとsources/配下のシムリンク差分同期
- `scripts/graph_index.py`: frontmatter/meta＋本文リンクの契約パーサーとnode/edge抽出、カテゴリ集計
- `scripts/treemap_layout.py`: squarified treemapの矩形分割を計算する純粋関数
- `scripts/graph_viewer_html_template.py`: treemap・カテゴリ一覧・関連ツリーを描画する自己完結HTMLテンプレート
- `scripts/server.py`: 127.0.0.1限定のローカルサーバー。GETのたびに最新のグラフHTMLを返す
- `scripts/cli.py`: add/list/remove/serveサブコマンドを持つCLIエントリポイント
- `scripts/dg.sh`: CLIラッパースクリプト（design-shareのds.shと同じ立て付け）
