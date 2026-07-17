# ブレインストーミング: uc-query-document（Query Use Case）の再設計

**作成日:** 2026-07-14
**目的:** 現行の`uc-query-document`（16のセマンティック操作）が、個別の必要に応じて
その場しのぎで追加されてきた「エイヤーな仕様」になっている問題を見直し、
JSONPath/JMESPathのような枯れたJSON問い合わせ技術と、DynamoDBのQuery/GSI
（グローバルセカンダリインデックス）に着想を得た、柔軟で拡張性のあるクエリ
仕様を再設計する。
**モード:** アイデア発散

**経緯:** `docs/brainstorm/brainstorm-waffle-process-reliability.md`のブレスト中、
ddd-advisorへの相談が「複数document.jsonを横断してパターン検索する」操作が
CLIに存在しないことが原因で約30分かかった（詳細は同文書の「副次的な発見」
セクション）。当初は`grep_documents`という単一操作を追加する軽い対応案を
出したが、そもそも既存の16操作自体（`get_block`/`get_field`/`get_items`/
`get_item_field`/`get_items_slice`/`filter_items`/`filter_exists`/
`filter_pattern`/`get_by_id`/`get_nested_items`/`get_children`等）が、
単一document・単一block・単一配列フィールドを対象にした点操作の寄せ集めで
あり、後付けの一操作追加ではなく設計全体を見直すべき、という指摘を受けた。

---

## 現状把握: `uc-query-document`の16操作

`src/waffle/application/usecases/query_document.py`を確認した実際の一覧:

| 系統 | 操作 | 対象範囲 |
|---|---|---|
| ファイル単位 | `scan` | 単一ファイルの生テキスト |
| ディレクトリ単位 | `index_scan_dir` | 配下の全document.jsonの「ブロック索引＋tags」のみ（コンテンツ本体は含まない） |
| メタ | `get_meta` | 単一documentのメタフィールド |
| メタ | `index_scan` | 単一documentのブロック索引 |
| 全階層検索 | `find_all` | 単一document内を再帰探索（所属blockの文脈は失われる） |
| ブロック単位 | `get_block` / `get_field` | 単一document・単一blockの取得 |
| 配列単位 | `get_items` / `get_item_field` / `get_items_slice` / `filter_items` / `filter_exists` / `filter_pattern` / `get_by_id` / `get_nested_items` / `get_children` | 単一document・単一block・単一配列フィールドに対する取得・絞り込み |

**観察**: 9個が「単一document・単一block・単一配列フィールド」というほぼ同じ
対象範囲に対する、微妙に違う絞り込み方法（フィルタ条件・スライス・ID検索・
ネスト展開）のバリエーションになっている。これはJSONPath/JMESPathのような
汎用パス式言語があれば、ほぼ全て1つの操作に集約できる種類の重複。また
「複数documentを横断して、内容に基づいて検索する」という操作は現状ゼロ
（`index_scan_dir`はブロック*索引*のみで本文検索不可、`scan`はディレクトリ非対応）。

一方で、他のJSON問い合わせツールに無い、Waffle独自の価値もある: 各操作が
返す`{prompt, value}`という形——`prompt`にはschemaの`x-prompt-query`/
`x-prompt-interpret`から動的算出した「この値をどう読むべきか」というAI向け
ガイダンスが必ず付随する。素のJSONPath/jqにはこの概念が無い。

---

## アイデアダンプ

1. JSONPath式を受け取る汎用`jsonpath`操作を新設し、`get_block`/`get_field`/
   `get_items`/`get_item_field`/`get_items_slice`/`get_by_id`/
   `get_nested_items`/`get_children`/`filter_items`/`filter_exists`/
   `filter_pattern`の11操作を実質的に代替する
2. JSONPathではなくJMESPath（AWS CLI/boto3が採用する、`?`によるフィルタ式等
   JSONPathより読みやすいとされる問い合わせ言語）を採用する
3. 既存16操作は後方互換のため段階的に残しつつ、新しい汎用操作を追加のみ
   導入する（破壊的変更を避ける）
4. 既存16操作を廃止し新操作に一本化する（破壊的だが仕様が単純になる）
5. マッチしたノードの所属blockを逆引きし、対応する`x-prompt-query`/
   `x-prompt-interpret`を結果に付随させる仕組みを、JSONPath/JMESPath化した
   後も維持する（Waffle独自価値の保持）
6. DynamoDBのGSI（グローバルセカンダリインデックス）に着想を得て、
   `tags`/`schemaRef`/`documentType`等の属性ごとに「属性値→documentパス一覧」
   を持つインデックスを生成・維持する
7. インデックスの再構築を、`brainstorm-waffle-process-reliability.md`論点3で
   合意したHooks拡張（fill/patch後の自動処理）にフックし、常に最新の状態を
   保つ
8. 属性インデックスに加え、全文検索寄りのインデックス（転置インデックス・
   trigram等）を持ち、パターン検索（`grep_documents`相当）も高速化する
9. DynamoDBのQuery API的に、インデックスを条件式で絞り込む操作
   （例: `query --operation index_query --index tags --keyCondition
   "contains(tags, 'repo:has-udd')"`）を新設する
10. インデックスが対象外・未整備のケース用に、DynamoDBのScanに相当する
    「全document横断の生検索」フォールバック操作（`grep_documents`）も別途
    用意する
11. 複数document.jsonを跨いだJOIN的なクエリ（例:「あるusecaseが参照する
    subdomainのcategoryも一緒に取得する」）まで見据える
12. クエリ結果のページネーション（DynamoDBの`LastEvaluatedKey`相当）を
    設計段階から組み込む
13. インデックス自体をdocument.json化し、Waffle自身のschema/CLI経由で
    メンテナンスできるようにする（インデックスもWaffleでdogfoodする）
14. インデックスはWaffle管理外の内部実装詳細（例: SQLite等）に留め、AIからは
    query操作のインターフェースのみ見せる（構造の露出を最小化する既存方針
    「AIは値だけ、構造はengineが組む」との一貫性）

**絞り込み候補（既存の`{prompt, value}`という独自価値を壊さず、実現性が高いものを優先）:**
- 案1（JSONPath化）＋案5（prompt付随の維持）: 単一document内の点操作群を
  汎用化する本命。既存の「読み方の指針を必ず付ける」というWaffleの設計哲学を
  維持したまま、操作の種類だけを削減できる
- 案6＋案7＋案9（GSI的インデックス＋Hooks連携での自動更新＋条件検索操作）:
  複数document横断の効率的な検索を実現する本命。論点3のHooks拡張と自然に
  接続する
- 案10（Scanフォールバック）: インデックス未整備な検索軸のための保険として
  併設が妥当
- 案2（JMESPath）/案4（破壊的一本化）/案11（JOIN）/案12（ページネーション）は、
  今回の主題（横断検索の欠如・点操作の重複）に対して必須ではなく、別途検討
  または将来スコープとして保留候補

---

## 追記: LoomDBという既存の自作DBを土台にできないか（2026-07-14）

ユーザーから、以前に自作したローカル埋め込みDB「LoomDB」（`/home/daidaiiro/workspace/loomdb`。
`waffle/vendor/loomdb`としてこのリポジトリにも既に取り込まれている）を今回の
検討に活かせないか、という指摘があった。実物（README・`docs/01-spec.md`・
`loom-py`のテストコード）を確認したところ、想定していた「GSI的インデックス」
「JSONPath的な構造アクセス」のアイデアの多くが、**既に実装・テスト済みの
機能として存在する**ことが分かった。

### LoomDBの実際の姿

- DynamoDBのデータモデル・API（Query/Scan・KeyCondition/FilterExpression・
  UpdateExpression・ProjectionExpression・GSI/LSI・TTL・batch/transact）を
  再現した、**組込み型のローカルNoSQL**（redb＝pure RustのACID KVストアが土台）
- DynamoDBには無い**JOIN**（inner/left outer・Nテーブル多段・自己結合）を
  独自拡張として持つ
- GSIは**常に強整合**（同一トランザクションで主データと索引を同時更新する
  ため、DynamoDBの結果整合より上位互換）。`update_table`でGSIを後付け追加
  でき、追加時に既存データを自動バックフィルする
- `ProjectionExpression`はネストパス（`addr.city`・`tags[0]`）を指定でき、
  今回検討していたJSONPathの「単一document内の構造アクセスを汎用化する」
  というニーズをかなりの部分カバーする
- **`loom-py`（PyPI名`loomdb`予定、PyO3実装）というPythonバインディングが
  既に実装・テスト済み**（`from loomdb import LoomDB; db = LoomDB("data.loom")`）。
  Waffle自身がPython実装のため、追加のFFI層を書かずに直接呼べる
- ステータス表を見る限り、Query/GSI/JOIN/Projection/TTL/batch・transactは
  いずれも実テスト（Rust側property test・Python側unittest）で緑。未了なのは
  npm/PyPIへの配布パッケージング（⏳）のみで、機能自体は完成している

### この発見がuc-query-document再設計に与える影響

当初のアイデアダンプで挙げていた「案6: GSI的インデックス」「案9: Query API的な
条件検索操作」「案10: Scanフォールバック」「案11: JOIN（将来スコープとして
保留していた）」は、いずれも**LoomDBが標準機能として既に持っている**。
つまり、これらを自前でゼロから設計・実装する代わりに、**LoomDBをWaffleの
クエリ/インデックス実装基盤として採用できないか**、という、当初の論点1
（JSONPath化）より一段階手前の、より大きな論点が浮上した。

想定される形: document.json自体（1ファイル＝1つの正典）は今まで通りWaffleの
ソース・オブ・トゥルースとしてディスク上に残し、Hooksによる自動処理
（`brainstorm-waffle-process-reliability.md`論点3で合意した、fill/patch-schema
後の自動処理の拡張）でLoomDBの表へ都度ミラーリングする。`uc-query-document`の
内部実装が、素のPython辞書探索の代わりにLoomDBのQuery/Filter/Projection/GSI/
JOINを呼ぶようになり、AI向けのインターフェース（`{prompt, value}`を返す
`waffle query`操作）自体は変えない、あるいは今よりも大幅に強化する。
LoomDBという実装詳細はAIからは見えない内部最適化として隠蔽する（アイデア
ダンプの案14と一致）。

---

## 論点 1: uc-query-documentの内部実装を、LoomDBを土台にしたクエリ/インデックス基盤へ置き換えるべきか

### AI 初期見解
**見解:** 置き換える方向で検討を進める価値が高いと考える。ただし
「置き換えるかどうか」の是非よりも先に、「document.jsonという1ファイル＝1
正典というWaffleの根幹設計と、LoomDBというテーブル/項目モデルをどう
橋渡しするか」という設計を詰める必要がある。

**根拠:**
- 当初アイデアダンプの本命候補（JSONPath化・GSI的インデックス・Hooks連携
  での自動更新・Scanフォールバック）を自前でゼロから設計・実装するのは
  相応の工数がかかるが、LoomDBはこれらの大半を**既に実装・テスト済みの
  機能として持っている**。しかもJOINという当初「将来スコープ」としていた
  機能まで無償で手に入る
- `loom-py`という動作確認済みのPythonバインディングが既にあり、Waffle
  （Python実装）から直接呼べる。新たにFFI層やパーサを自作する必要が無い
- ただし、document.jsonは「1 documentType・1ファイル＝1正典」という、
  人間・AIがCLI経由で直接読み書きする単位である一方、LoomDBは「テーブル・
  項目」という別のデータモデルを持つ。ドキュメントの`content`ブロック
  構造（ネストしたオブジェクト・配列・schemaごとに異なる形）を、LoomDBの
  項目（属性の集合）としてどう表現するか（ブロックごとに属性化するのか、
  contentを丸ごと1つのネスト属性として格納しProjectionで掘るのか）の
  マッピング設計が、この論点の実質的な本体になる
- LoomDBはまだnpm/PyPIに公開されておらず、`waffle/vendor/loomdb`という
  vendor取り込みへの直接依存になる。ビルド・バージョン管理・両リポジトリ間の
  変更の同期方法（vendorをどう更新するか）も設計対象に含める必要がある

### ユーザー見解
> LoomDBを土台にする方向で、tech-lead-advisor・platform-advisorに総合評価を依頼。
> platform-advisorが「redbは単一プロセス前提（ファイルロックで多重オープンを
> 拒否）」という致命的な不適合を指摘。redb本家メンテナ(cberner)のGitHub issue
> #376/#932を直接確認し、読み取り専用でも2プロセス目は`Err(DatabaseAlreadyOpen)`
> になること、メンテナ自身の回避策も「LMDBに乗り換える」「IPC/サーバ層を挟む」
> の2択であることを確認。サーバ層を挟む案はLoomDBの「サーバ不要・組込み」という
> 存在意義を壊すため却下。ただし、Waffleには既に`waffle serve`というMCPサーバ
> （単一常駐プロセス）があり、そこにLoomDBを組み込めば「新しくサーバを作る」
> のではなく「既存の正当な経路にLoomDBを埋め込む」形になり、この却下理由には
> 該当しない、という道が見つかった。ただしCLI直接呼び出し（今日の実運用）は
> 相変わらず対象外になる。
>
> 一方で、そもそも「なぜDBが要るか」を掘り下げたところ、当初の動機（30分ロス）
> は状態を持たない`grep_documents`的な単純操作1つで解決でき、DB/ミラーは
> 過剰装備だと一度結論しかけた。しかしユーザーの本来の狙いは検索速度ではなく
> **JOIN・複雑クエリという構造化されたクエリ能力**（DynamoDBが持たずLoomDBが
> 持つ差別化機能）であり、これは`ThicknessBySubdomainBlock`のcategory突き合わせや
> `subdomainRef`/`contextRef`追跡のような、既にWaffle内に存在する「手作業JOIN」を
> 解消しうる、実例の伴う需要だと判明した。
>
> さらに議論を進める中で、今の素朴なファイル書き込み（`fill`）には保護が無く、
> 同一document.jsonへの同時書き込みが「エラーにすらならず後勝ちで静かに壊れる」
> という、redbの`DatabaseAlreadyOpen`（大声で失敗する）より悪い脆弱性があることが
> 判明。「いっそLoomDBを正典にすれば安全では」という案も出たが、document.jsonを
> gitで直接管理する（diff・blame・3-way merge・特定ツールへの非依存）ことの価値
> ——Terraform/Kubernetesマニフェストのような「Content as Code」としての性質——は
> 手放せないと判断し、正典はdocument.json（git管理のプレーンJSON）のまま、
> という結論で合意した。

### AI 再考見解
**見解:** 論点1（当初「単一document内の構造アクセスをJSONPath化すべきか」
「LoomDBを土台にすべきか」として立てた論点）を、実際の議論の帰結に合わせて
2つに分離する。
1. **即応すべき軽量な穴**: 複数document横断のパターン検索が無いという当初の
   ギャップは、状態を持たない`grep_documents`的な単純操作の追加で解決する。
   永続インデックス・DBは不要（evidence-based-scopeの実例1件で正当化できる
   範囲は、この最小実装まで）。
2. **書き込みの安全性**: 今回の議論で新たに判明した、より優先度の高い問題。
   `brainstorm-waffle-process-reliability.md`論点3のHooks拡張（fill前の
   query確認、原子的な書き込み等）で対処する。LoomDB/DBへの正典移行は不要。
3. **JOIN・複雑クエリという構造化ニーズ**: 実例の伴う本物の需要ではあるが、
   LoomDBを使うには「MCPサーバという単一常駐プロセスへの埋め込み」が前提
   条件になり、CLI直接呼び出し（今日の主な運用）はその恩恵を受けられない。
   正典はdocument.jsonのまま、LoomDBは都度再構築可能な派生ミラーとしてのみ
   位置づけられる。これは今回のスコープを超える規模の投資（MCPサーバアーキ
   テクチャの整備＋LoomDBのビルド環境確保＋効果測定）であり、独立した将来
   検討として切り出す。

**根拠:** tech-lead-advisor・platform-advisorの評価、redbメンテナ本人の一次
情報（GitHub issue）、および「正典はgit管理されたJSONであるべき」という
議論の帰結を総合すると、今すぐ着手すべき最小実装（1・2）と、条件が整って
から着手すべき将来投資（3）は、明確に別物として扱うべきだと判断した。

### 合意決定
**決定:** 論点1は2つの独立した対応に分割する。(a) `grep_documents`相当の
状態を持たない横断検索操作を`uc-query-document`に追加する。(b) 書き込みの
安全性は`brainstorm-waffle-process-reliability.md`論点3のHooks拡張に一本化し、
本ブレストでは重複対応しない。LoomDBを用いたJOIN/複雑クエリ基盤（MCPサーバ
組み込み前提）は、正典をdocument.jsonに保つという前提の上で、独立した将来
検討（論点2以降、または別ブレスト）として切り出す。
**理由:** 即応すべき実務的なギャップ（検索・書き込み安全性）と、条件付きの
大きな将来投資（LoomDB統合）を同じ論点で扱うと、evidence-based-scopeが
正しく適用できなくなる（小さな実例1件を理由に、大きな投資まで一緒に正当化
してしまう）。
**次のアクション:** (a)(b)はそれぞれのbrainstormの次のアクション通りに
spec-firstで進める。LoomDB統合は、MCPサーバアーキテクチャの成熟度・
ビルド環境の確保状況を見て、別途着手判断する。

---

## 論点 2: それでもなお、LoomDBを活用する価値はどこにあるか（将来検討）

### AI 初期見解
**見解:** 前提（正典はdocument.json、LoomDBは派生ミラー）を踏まえると、LoomDB
の価値は検索速度ではなく**JOINという構造化されたクエリ能力**に集約される。
`ThicknessBySubdomainBlock`のcategory突き合わせ、usecase specの
`subdomainRef`/`contextRef`追跡といった、AIが複数回`query`を呼んで手作業で
つなぎ合わせている実例が既にある。将来のコーパス規模拡大への備え、LoomDB
自身の実運用検証という別目的も副次的な価値としてある。ただしコスト
（Rust/PyO3依存・MCPサーバ中心運用への移行）を考えると、今すぐ着手する
緊急性は無く、条件が整うまで様子を見る対象。

### ユーザー見解
> 「Waffleとしてどうあるべきか」という問いへのAIの回答（軽量・自己完結・
> git-nativeなドキュメントエンジンというアイデンティティを守り、LoomDBは
> コアが一切依存しない、完全に切り離せる任意のアクセラレータとしてのみ
> 検討する）に同意する。

### AI 再考見解
**見解:** LoomDB活用の価値（JOIN等）自体は否定しないが、Waffleの
プロダクトアイデンティティ（CLAUDE.mdが自ら宣言する「自己完結ディレクトリ・
git subtree split可能」という軽量・独立性）を判断基準の最上位に置く。
価値とコストの天秤ではなく、**「Waffleのコアがそれに依存してよいか」を
先に問い、依存させない設計でしか採用しない**、という制約を先に固定する
方が、今後の判断がぶれない。

### 合意決定
**決定:** LoomDBは将来的に検討する場合も、Waffleのコア機能から完全に
独立した任意のアクセラレータとしてのみ位置づける。LoomDBが無い、または
ビルドできない環境でもWaffleは既存機能100%で動作し続けることを、採用の
絶対条件とする。中核の設計・アーキテクチャ判断には組み込まない。
**理由:** Waffle自身がCLAUDE.mdで「自己完結ディレクトリ（git subtree split
で独立可能）」と宣言しており、この軽量・独立性というアイデンティティを、
JOIN等の便益と引き換えに崩すべきではないと判断した。
**次のアクション:** 現時点で具体的な実装アクションは無し（着手条件が
整うまで保留）。JOIN需要が具体的に積み上がった場合、またはMCPサーバ中心の
運用への移行が別の理由で決まった場合に、改めて「切り離し可能な任意拡張」
としての設計を検討する。

---

## セッションまとめ

### 合意事項一覧
1. 単一document構造アクセスの点操作11個はJSONPath/JMESPath的な汎用式へ
   一本化する方向（詳細設計は未着手）
2. 複数document横断のニーズ（検索・フィルタ・参照解決/JOIN）は、状態を
   持たない4パターン（A: 構造アクセス、B: パターン検索`grep_documents`、
   C: 横断フィルタ・属性抽出、D: 参照解決）として実装する。永続インデックス・
   ミラーDB（LoomDB/SQLite等）はコアに導入しない
3. LoomDBは将来検討する場合も、コアが一切依存しない切り離し可能な任意
   アクセラレータとしてのみ位置づける（正典はdocument.json＝git管理の
   プレーンJSONのまま）
4. 書き込みの安全性（fillの後勝ち上書きリスク）は本ブレストでは対応せず、
   `brainstorm-waffle-process-reliability.md`論点3のHooks拡張に一本化する
5. パターンC・Dは、`tags`によるフィルタと、各document型が持つ構造化ref
   フィールド（`subdomainRef`/`contextRef`/`knowledgeRefs`等）をたどる
   参照解決を前提に設計する——後続のOKF-in-Waffle（tags/relationsグラフ）
   ブレストが、この2パターンを土台として利用する

### 次のアクション一覧
- パターンA〜Dをspec-first厳守で、`sd-document-management`または適切な
  subdomain配下のusecase specとして起こす
- OKF-in-Waffle（tags/relationsのグラフ化）は独立した新規ブレストとして
  別途着手する（本セッションで継続）

### 保留・未解決の論点
LoomDB統合（JOIN・GSI相当）は、MCPサーバアーキテクチャの成熟・具体的な
JOIN需要の積み上げを待つ形で保留。永続索引（GSI/LSI相当）の設計は、
実測でボトルネックが判明してから着手する（現時点では設計しない）。

---
