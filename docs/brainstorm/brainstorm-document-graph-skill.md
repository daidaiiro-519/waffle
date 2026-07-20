# ブレインストーミング: document-graphをWaffle非依存のSkillとして作り直す

**目的:** 今回のセッションで作り込んだdocument-graph（treemap＋カテゴリ一覧＋紐づき先ツリー＋ローカルサーバー）を、design-shareと同じ設計思想（動作ロジック自体がWaffleに依存しない、マークダウン/HTMLの「契約」だけを前提に動く）のSkillとして作り直す方針を決める。既存実装をどこまで転用できるか、契約をどう定義するか、config.jsonの設計を含めて検討する。
**モード:** アイデア発散

---

## アイデアダンプ

1. MDフロントマターにYAMLで title/tags/description/relatedTo（配列）を書く契約にする
2. 関連性（エッジ）は本文中の標準Markdownリンクから解析する契約にする（OKF方式）
3. HTML側は`<meta name="...">`タグに構造化データを埋め込む契約にする
4. HTML側は`<script type="application/json">`でノード情報を埋め込む契約にする（今のgraph.htmlに近い）
5. config.jsonに「対象フォルダのリスト」を持たせ、複数プロジェクトを横断できるようにする
6. config.jsonに除外パターン（globなど）を持たせる
7. 既存のtreemap計算・カテゴリ分類描画・紐づき先ツリー・タブ切り替えJSは、契約さえ満たせばほぼそのまま転用できる可能性が高い（Waffle依存はデータ取得層だけ）
8. データ取得層を差し替え可能なアダプタパターンにする（Waffle document.json用アダプタ／汎用MD+frontmatter用アダプタを両方持たせる）
9. Skill内に`ds.sh`のようなCLIラッパースクリプトを持つ
10. ローカルサーバーもSkill内に持ち、design-shareの`console_server.py`と同じ立て付けにする
11. Waffle側は「契約に沿ったMD/HTMLを出力する」責務だけ持てばよく、Skill側の実装を一切知らなくてよい（疎結合）
12. 契約のバージョニング（v1契約など）を最初から持たせて将来の拡張に備える

**絞り込み候補:**
- 契約はOKF準拠（フロントマター＝メタ情報、エッジ＝本文リンク）にする（アイデア1・2）— 車輪の再発明を避け、Markdownエコシステム全体の慣習とも合う
- 既存の可視化ロジック（treemap・カテゴリ描画・紐づき先ツリー）は層分離した上で転用する（アイデア7・8）— ゼロから作り直すコストを避けられる
- config.jsonで複数フォルダ・MD/HTML両対応にする（アイデア5）— 「任意のマークダウンを格納したフォルダやHTMLを置いたフォルダを指定すれば」という要望に直接対応
- Skillは表示専任に徹し、MD→HTML変換ロジックは持たない（アイデア11）— 疎結合を保つ

---

## 論点 1: マークダウン/HTMLの「契約」をどう定義するか

### AI 初期見解
**見解:** フロントマターにはtitle/tags/description等のメタ情報だけを持たせ、関連性（エッジ）は本文中の標準Markdownリンクから解析する、というOKF準拠の方式を採用すべき。

**根拠:**
- 本セッションで既にOKFの実物（reference実装）を調査済みで、「エッジは本文リンクから解決、フロントマタータグは検索/フィルタ用」という設計原則が確定している。独自拡張より先にOKF準拠を検討すべき
- フロントマターに関連性まで詰め込むと、汎用マークダウンとしての可搬性が下がる（他のMarkdownツールとの互換性が薄れる）
- 本文リンクからのエッジ抽出は、Obsidian等のMarkdownエコシステム全体で採用されている一般的なパターンであり、汎用性が高い

### ユーザー見解
> ✏️ まず、今現状動いている仕組みから必要な属性はわかるはずなので、そこから整理するのがいい。それをフロントマターに移せれば同じ動きになるし、HTMLもフロントマター相当のメタ情報を書ける個所を決めれば、どちらでも同じ抽出ができる。
>
> （紐づきツリー機能との両立を確認した上で）であれば話が早い。**リンクはファイル名をIDとして解決する**仕組みがいいと思う。これは既存のWaffleでやっていること。相対パスは結構問題になる。解決策として、フォルダ階層がおかしくならないよう、Skillが解決できる指定の場所へシムリンクを張るのがいいかも。ユーザーがconfig.jsonで表示したいdocumentを指定し、そのフォルダ配下にシムリンクしたdocument/フォルダが並ぶ形にできれば柔軟。逆にSkillが実フォルダの場所へシムリンクを張る方式だと、フォルダ構成がバラバラになるので却下。ファイル名で解決する以外に方法はないと思う。一般的に推奨される方法でやるのが一番いい。ソースコードはこのSkillsフォルダに同梱する形で実装すれば済みそう。

### AI 再考見解
現在稼働中のWaffle実装（`graph_index.py`/`compute_categories`）が実際に要求している属性を棚卸しすると：

| Waffle内部での実体 | 契約での置き場所（MD） | 契約での置き場所（HTML） |
|---|---|---|
| `documentId`（グラフのnodeキー、かつリンク解決キー） | ファイル名（拡張子除く） | ファイル名（拡張子除く） |
| `type`/`specKind`（カテゴリ分類ラベル） | frontmatter: `type` | `<meta name="type">` |
| `title` | frontmatter: `title`（無ければMDの最初の`# 見出し`にフォールバック可） | `<title>`または`<meta name="title">` |
| `description` | frontmatter: `description` | `<meta name="description">` |
| `tags` | frontmatter: `tags` | `<meta name="tags">` |
| `related`（双方向edge） | 本文中の`[text](path)`リンクを全文スキャン | 本文中の`<a href>`を全文スキャン |

この棚卸しの上で、ファイル名IDによるリンク解決は理にかなっている。根拠は2つ：

1. **Waffle自身がすでにこの方式**。`graph_index.py`は`content.members.items[].members`等から得た参照文字列を、相対パスではなく`documentId`という平坦なキーとして扱い、全ドキュメントを走査して一致するnodeを探している（`document_graph_server.py`の`_find_document`もdocumentIdの全件走査で一致検索）。相対パス解決を今回新規導入すると、むしろWaffle本体とは異なる挙動を持ち込むことになり、契約としての一貫性が崩れる。
2. **Obsidian等のMarkdownエコシステムの実績**。Obsidianの`[[wikilink]]`はvault内のどこにあってもファイル名（拡張子除く）で解決される「shortest path resolution」を採用しており、フォルダ階層は解決に関与しない。これは「本文リンクからエッジを抽出する」という論点1の合意済み前提（OKF準拠）とも自然に噛み合う——リンクの書式は標準的な`[text](target)`のままで、`target`の解釈規則だけを「相対パスとして辿る」から「ファイル名IDとして全体から探す」に変えるだけで済む。

シムリンクの向き（Skillが持つ`sources/`のような統制下フォルダへ外部の実document/フォルダを**持ち込む**方向）にも同意する。理由：
- Skill本体の走査ロジックが「自分のフォルダ配下を`**/*.md`・`**/*.html`で再帰スキャンするだけ」という単一ルートの単純な実装で済み、外部の任意の絶対パスをコード側で扱う必要がなくなる。
- config.jsonの役割が「表示したいソース（フォルダやファイル）の一覧を宣言する」ことに限定され、「その宣言からシムリンクを実際に張る」という同期処理（setup/sync的な一手順）に分離できる——design-shareが正本を1箇所に集約して配信する思想と同型。
- 逆方向（Skillが実フォルダへシムリンクを張る）は、ユーザーの言う通りconfig.jsonごとに参照先フォルダ構成が変わり、Skillの前提が不安定になる。

一点、決めておくべき派生論点がある：ファイル名ID解決は**「全ソースを通じてファイル名が一意である」ことが前提**になる。これはWaffle自身も`documentId`のリポジトリ全体一意性をすでに要求しているのと同じ制約なので、新規に持ち込む負担ではなく、単に契約として明文化すればよいはず（重複ファイル名が見つかった場合はスキャン時にエラー/警告として検出する）。

### 合意決定
- **contract定義（node属性）**：`id`=ファイル名（拡張子除く）、`type`（MD frontmatter `type` / HTML `<meta name="type">`）、`title`、`description`、`tags`の4属性をfrontmatter⇄`<meta>`の対称マッピングとする。
- **edge解決**：本文リンク（MD `[text](target)` / HTML `<a href>`）の`target`を、相対パスとしてではなく**ファイル名（拡張子除く）をID**として全ソース走査から一致検索する。Waffleの`documentId`解決方式・Obsidianのwikilink解決方式の両方と整合する。
- **一意性制約**：契約として「全ソースを通じてファイル名は一意」を明文化し、重複はスキャン時にエラー/警告として検出する。
- **フォルダ正規化**：config.jsonは表示したいソース（フォルダ/ファイル）の宣言のみを担い、実際の配置はSkill配下の統制フォルダへ**外部から持ち込む向き**のシムリンクで正規化する（Skill側が実フォルダへ出向く向きは採用しない）。具体的なsync手順・フォルダ名規則は論点2（config.jsonの設計）で詰める。
- **配置**：Skillのソースコードは当該Skillフォルダに同梱する。

---

## 論点 2: config.jsonの設計

### AI 初期見解（論点1の合意を踏まえて改訂）
**見解:** config.jsonの役割は「表示したいソースの宣言」のみに限定する。実体は`sources`という配列で、各要素は`{ "alias": "waffle-specs", "path": "/abs/or/relative/path", "format": "md" | "html" }`のような最小構造を持つ。`alias`はシムリンク先フォルダ名（Skill配下の統制フォルダ、例: `sources/{alias}/`）に使う。`format`はそのフォルダ配下をMD契約として読むかHTML契約として読むかを明示する。

同期（宣言→実際のシムリンク作成）は、Skillの起動時（グラフ表示コマンド実行時）に毎回差分チェックして自動で追従させる（設定ファイルを変更しても別途「sync」コマンドを覚えておく必要がない）。alias単位でシムリンクするので、`sources/{alias}/`配下はソースフォルダそのものへの1本のシムリンク（あるいはOS非対応時はディレクトリコピーへのフォールバック）で足り、ファイル単位でシムリンクを量産する必要はない。

**根拠:**
- 「任意のマークダウンを格納したフォルダやHTMLを置いたフォルダを指定すれば」という要望自体が、MD用・HTML用の2種類の入力ソースを想定している
- 論点1で「ファイル名は全ソースを通じて一意」という制約に合意した。この一意性はスキャン時（起動時）に検証すればよく、config.json自体に重複回避の仕組みを持たせる必要はない——構造をシンプルに保てる
- ただしevidence-based-scopeの観点では、実例が今はWaffle自身1件しかない段階で複数フォルダ対応まで作り込むのは時期尚早かもしれない——単一ソースだけを想定した最小構造から始め、2件目の実例（Waffle以外のドキュメント群）が出てから拡張する方が安全。ただし`sources`を配列にしておくこと自体はコストが低く、後から要素を増やすだけで拡張できるので、最初から配列型にしておいて良い

### ユーザー見解
> ✏️ これがよさそうですね（config.jsonを手作業で書かせず、`document-graph add <path>` のような1コマンドで完結させる案に賛成）。ただし確認したいのは、この`alias`はグラフ画面側の表示に出てくるものなのか？

### AI 再考見解
config.jsonの「作成体験」も設計対象に含めるべきだった。手作業でのJSON編集を前提にすると、alias命名・format判定・シムリンク作成・契約チェックのすべてをユーザーが頭の中でやってからJSONへ書き起こす必要があり、論点1で決めた仕組みの複雑さがそのままUXの重さに転嫁してしまう。これを避けるため、config.jsonを「人間が直接編集するファイル」ではなく「CLIの操作結果として生成される状態ファイル」と位置づけ直す：

- `document-graph add <path>` — フォルダ名からalias自動生成（衝突時のみ確認）、配下拡張子の多数決でformatを自動推定、追加と同時にシムリンク同期＋契約チェック（frontmatter/meta未検出件数の一覧）まで実行する。
- `document-graph list` / `document-graph remove <alias>` — 対称コマンドとして持たせる。
- design-shareの`ds.sh`と同じく、Skill同梱のCLIラッパー（論点4の「配置・実行形態」とも整合）として実装する。GUIウィザードのような重い仕組みは、実例が増えて必要性が具体的に見えてから検討する（evidence-based-scope）。

alias表示可否について：**aliasは画面には一切出てこない**。グラフ画面（treemap・カテゴリ一覧・関連ツリー）のカテゴリ分類軸は契約の`type`（frontmatter/meta由来）であり、どのsourceから来たかではないため、aliasはsources/フォルダ名とconfig.json内の識別子としてのみ使われる、完全に裏方の概念になる。異なるsourceの同じ`type`のドキュメントは、画面上は区別なく同じカテゴリに混在する。「sourceごとに画面で区別したい」という要望が今後具体的に出れば、それは別途「表示軸にsourceを加える」という拡張として扱う（現時点では要望なしのため作らない）。

### 合意決定
- **config.jsonの作成主体**：手作業でのJSON編集を前提にせず、`document-graph add/list/remove`というSkill同梱CLIで作成・変更する。config.jsonは「CLI操作の結果として生成される状態ファイル」と位置づける。
- **add時の自動化**：alias はフォルダ名から自動生成（衝突時のみ確認）、format は配下拡張子の多数決で自動推定、追加と同時にシムリンク同期＋契約チェック結果の表示まで行う。
- **alias の表示範囲**：グラフ画面（treemap・カテゴリ・関連ツリー）には一切表示しない。sources/フォルダ名とconfig.json内の識別子としてのみ使う裏方の概念。カテゴリ分類軸はあくまで契約の`type`。source軸での表示・フィルタは現時点ではスコープ外（要望が具体的に出てから検討）。
- **GUIウィザードは今は作らない**：CLIのみで完結させ、必要性が実例ベースで見えてからローカルサーバー側への拡張を検討する。

---

## 論点 3: 既存Waffle実装をどこまで転用できるか

### AI 初期見解（論点1・2の合意を踏まえて改訂）
**見解:** 転用できる層／作り直す層の境界は変わらないが、論点1・2の合意で「作り直す層」の中身がより具体的になった。

**転用できる（ほぼそのまま）:**
- `treemap_layout.py`（squarify）: 完全に汎用的な純粋関数で無変更のまま使える
- `render_graph_html()`: node/edgeのdict構造だけを受け取る設計なので、node属性が論点1で決めた`{id, type, title, description, tags}`＋`related`の形に収まっていれば、document.jsonの存在を知らないこのままの形で移植できる（`specKind`/`schemaRef`はcontractに無いので参照箇所があれば剥がす）
- タブ切り替えJS・関連ツリーの折りたたみJS・検索フィルタJS: すべてDOM/文字列操作でWaffle非依存

**作り直しが必要（論点1・2で輪郭が明確になった）:**
- `graph_index.py`の`_extract_refs`（content.membersやspecRefを読む部分）→ frontmatter/meta パーサー＋本文リンクの全文スキャン＋**ファイル名IDでのedge解決**（論点1）に置き換え
- `render_document_graph.py`のDocumentRepository依存部分 → `sources/`配下の再帰ファイルスキャナに置き換え
- 新規: config.json読み込み・シムリンク差分同期・`document-graph add/list/remove`CLI（論点2）— Waffle側に対応物がないので完全新規

**根拠:**
- 論点1で決めたnode属性（4項目＋related）は、既存`compute_categories`が生成しているdict構造のスーパーセットではなく、`specKind`/`schemaRef`を含まない小さめの部分集合なので、描画層は「情報が減った版」として問題なく動くはず
- 影響範囲は「データ取得層＋config/シムリンク管理」に限定でき、描画層（treemap・カテゴリ・関連ツリー・タブ）はゼロから作り直すよりリスクが低い、という結論自体は変わらない

### ユーザー見解
> ✏️ 活用できるところは活用しましょうか。

### AI 再考見解
描画層（treemap・カテゴリ描画・関連ツリー・タブ切り替え）は移植前提で進める。移植作業そのものは論点1・2の合意が固まった今、実装フェーズでの機械的な切り出し作業（`graph_viewer_html_template.py`から`specKind`/`schemaRef`参照箇所を除去してcontractの4属性＋relatedだけを前提にする）になるので、ブレインストーミングとしてはこれ以上詰める論点は残っていない。

### 合意決定
- **転用する**: `treemap_layout.py`（無変更）、`render_graph_html()`とその周辺JS（タブ・関連ツリー・検索フィルタ）を移植する。移植時にnode属性を契約の`{id, type, title, description, tags}`＋`related`だけに絞り込む（`specKind`/`schemaRef`参照を除去）。
- **作り直す**: edge抽出（frontmatter/meta＋本文リンクスキャン＋ファイル名ID解決）、データ取得層（sources/配下の再帰スキャナ）、config.json/シムリンク同期/CLI一式。いずれも既存Waffle実装に対応物がない、またはdocument.json依存が強く転用不可のため新規実装とする。

---

## 論点 4: Skillとしての配置・実行形態

### AI 初期見解（論点1〜3の合意を踏まえて改訂）
**見解:** design-shareと同じ構造（SKILL.md＋scripts/配下にCLIラッパー・ローカルサーバー）を踏襲する。Skillは契約に従ったMD/HTMLを「表示するだけ」に徹し、MD→HTML変換ロジックは持たない（変換はWaffle側の責務のまま）。scripts/配下は最低限これだけの構成になる：

- `config.py` — config.json読み込み・`sources/`シムリンク差分同期・契約チェック
- `cli.py` — `document-graph add/list/remove`（論点2）のエントリポイント
- `graph_index.py`（移植・改修） — frontmatter/meta＋本文リンクスキャン→node/edge構築（論点1・3）
- `treemap_layout.py`（無変更移植）、`graph_viewer_html_template.py`（属性を絞り込んで移植）
- `server.py` — design-shareの`console_server.py`と同じ立て付けのローカルサーバー（127.0.0.1限定、GETのたびに再スキャン）

**根拠:**
- design-shareの`console_server.py`も標準ライブラリ＋最小限の依存で完結しており、既存の踏襲パターンとして一貫性がある
- Skillが自分でMD→HTML変換までしてしまうと、「HTML契約」と「MD契約」の境界が曖昧になり、疎結合が崩れる。表示専任にすることで、生成元（Waffleに限らず他のツール）を問わない汎用性を保てる
- ローカルサーバーの「ディスクにあれば読むだけ、無ければエラー」という設計は契約ベースでも有効——ただし今回Waffle内に作ったサーバーとは違い、Skill側は「その場で生成」機能を持たない（変換はWaffle側の責務のまま）。ただしSkill自身が持つのは「MD/HTML→表示用HTML」の変換であり、これはSkillの正当な責務（描画層の移植そのもの）なので混同しないよう明記する
- config.json・シムリンク・CLIをすべて`scripts/`配下に同梱することで、論点1で合意した「ソースコードはSkillフォルダに同梱する」を素直に満たす

### ユーザー見解
> ✏️ これで問題なく動作するならOKだと思います。

### AI 再考見解
「問題なく動作するか」は、この時点では設計レベルの整合性検証（論点1〜4の合意が矛盾なく1つの実装として成立するか）にとどまっており、実装・実データでの動作確認はまだしていない。ブレインストーミングとしてはここで合意事項が出揃ったので、次は実装フェーズで小さく検証しながら進める（例: Waffle自身のdocument.jsonから契約準拠のMD/HTMLを1〜2件書き出し→Skillのadd/list→表示、という最小の縦通しを最初に確認する）のが妥当。

### 合意決定
- 論点4のAI初期見解（design-share踏襲の`scripts/`構成: `config.py`/`cli.py`/`graph_index.py`/`treemap_layout.py`/`graph_viewer_html_template.py`/`server.py`）を採用する。
- 「問題なく動作するか」の確認は実装フェーズの最小縦通し検証（Waffle document.json→契約準拠MD/HTML 1〜2件→Skillのadd→表示、が通ること）で担保する。

---

## 未解決事項の決着：既存Waffle内部実装（uc-render-document-graph）の扱い

### ユーザー見解
> ✏️ 廃止の方がいい。そもそもSpecを作成せずに実装したものなので、実装の仕方自体が正しくない。ただし、Waffle側で修正が必要な点が2つある：(1) Handoffのレンダリング時に、今回の契約に合わせたメタデータをHTMLに設定してレンダリングできるようにすること (2) マークダウンのレンダリング時に、正しくフロントマターを設定できるようにすること。

### AI 再考見解
廃止の判断に同意する。理由はCLAUDE.mdの運用ルール（document-authoring系はまずskill-routerに問い合わせる等）以前の話で、そもそもUDD（spec-first）の原則自体に反して実装が先行した成果物であり、「実装として動くから残す」は正当化にならない。Waffleに残すべきなのは、Skillの契約を満たすための出力側の責務（下記2点）だけで、可視化ロジック自体はSkill側へ完全移管する。

Waffle側の修正2点は、論点1で確認した「(A) MD経由（`RenderDocumentViewer`等）」「(B) Handoff直接HTML（`RenderHandoffTemplate`）」という2つの描画経路の区分とちょうど一致する：

1. **Handoff（HTML直接生成経路）**: `render_handoff_template.py`/`handoff_html_template.py`が出力するHTMLに、契約の`<meta name="id/type/title/description/tags">`を埋め込む。今回Handoffのschema versionバグ（v1固定→v2実データで失敗）を発見・修正した箇所と同じファイル群であり、影響範囲は把握済み。
2. **MD経由（frontmatter経路）**: MDへレンダリングするusecase群（現状`x-frontmatter`を宣言しているのは`SkillSchema/v2`のみ、他スキーマは未対応と確認済み）が、契約の`title`/`description`/`tags`/`type`をYAML frontmatterとして正しく書き出すようにする。これは各DomainSpecSchema等のx-render機構またはMDレンダリングusecase側の改修になる。

この2点は「Skillが動くための前提条件」であり、Skill自体の実装より先にWaffle側で着手する必要がある（Skillは契約が満たされている前提でしか動かないため）。

### 合意決定
- **既存Waffle内部実装（`uc-render-document-graph`・`serve-document-graph`・関連ファイル一式）は廃止する。** そもそもspecを作らず実装が先行した成果物であり、実装方式自体が誤りだったため「動くから残す」は採らない。
- **Waffle側の対応が2点、Skill実装の前提条件として必要**：
  1. Handoff HTML直接生成経路（`render_handoff_template.py`）に契約準拠の`<meta>`出力を追加する。
  2. MD frontmatter経路（現状`SkillSchema/v2`以外は`x-frontmatter`未対応）に、契約準拠のfrontmatter出力を追加する。
- 実装順序：Waffle側2点の対応 → Skillの最小縦通し検証 → Skill本体実装、という順で進める。

---
