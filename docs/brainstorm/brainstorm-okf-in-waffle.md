# ブレインストーミング: OKF（tags/relationsグラフ）をWaffle自身のコンセプト機能として取り込む

## ★クローズ（2026-07-21）

このブレストが動機だった「documentをグラフとして紐づけて閲覧したい」というニーズは、
別途確立した`document-graph` Skill（`docs/brainstorm/brainstorm-document-graph-skill.md`）
が満たしている。document-graphが実際に要求する契約は`id`/`type`/`title`/
`description`/`tags`の5項目のみで、これは全schemaへのx-frontmatter展開
（commit `6655d95`）で満たし済み。

本文書が個別に合意していた`resource`フィールド追加・論点4のx-render経由
リンクフラグ機構は、document-graph経由の解決とは別の実装方針（Skill側の
ベアテキストIDスキャン）に置き換わったため、本文書のまま次アクションとして
残すと「まだ何か作業が残っている」という誤解を招く。着手しない、という結論
でクローズする。将来OKF準拠自体（Waffle外部への標準準拠）が独立した動機として
再浮上した場合は、新しいブレストとして起こすこと（本文書を再開しない）。

**作成日:** 2026-07-14
**目的:** 元々has-udd側で構想されていたOKF（frontmatter駆動のtags/relations
グラフ）を、「Waffle＋has-uddのセット利用」前提から「Waffle自身が提供する
機能」へ路線変更したことを受け、Waffleの実際のdocument型・既存ref フィールド
に当てはめ直し、Waffleのコンセプトレベルの機能として設計する。
**モード:** アイデア発散

**経緯:** `docs/brainstorm/brainstorm-query-usecase-redesign.md`の議論中、
「タグによる索引検索」の是非を検討していたところ、元々has-udd側に
`docs/brainstorm/brainstorm-okf-frontmatter-relations.md`という先行ブレスト
（tags＝分類・relations＝有向エッジという役割分担、relationsは既存の構造化
refフィールドから機械生成し手書きしない、という設計）が存在することが判明。
ユーザーの方針転換（Waffle自体がこの機能を持つ）を受け、Waffleの実際の
document型に当てはめて再設計する。

## ★訂正（2026-07-15）: 論点1・2はOKFの誤解に基づいており無効

論点1・2は、`brainstorm-okf-frontmatter-relations.md`（has-udd内部の独自
拡張構想）を「OKF」そのものだと誤認して進めていた。実際のOKFは
Google Cloudが公開する外部の実在仕様（[SPEC](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)、[FAQ](https://okf.md/faq/)）で、
以下の通りはるかに最小限だと判明した:

- **必須フィールドは`type`のみ**（自由記述・中央登録なし）
- **推奨フィールド**: `title`/`description`/`resource`（対象を一意に指す
  URI）/`tags`（横断分類のYAMLリスト）/`timestamp`（ISO 8601）
- **文書間の関連性は、専用の構造化フィールド（`relations:`等）ではなく、
  本文中の標準Markdownリンクで表現する。関係の種別（親子・参照・結合等）は
  リンク自体ではなく周囲の文章（prose）で伝える**
- 予約ファイル: `index.md`（ディレクトリ内容の列挙）、`log.md`（更新履歴）。
  概念文書自体には使わない
- ディレクトリ構成は自由（規約なし）

つまり、`x-relation`という新しいschema annotationを作り、参照フィールドを
機械的にグラフ化する、という論点1・2の設計方向は不要だった。関連性は
**render済みの本文に、既存の言及がMarkdownリンクとして現れていれば
それで足りる**。論点1・2の内容はこのセッションの学びの記録として残すが、
以降の設計はこの訂正を前提に、論点3から再開する。

---

## 前提: has-udd側の先行ブレストからの継承事項

`brainstorm-okf-frontmatter-relations.md`で既に合意されていた設計原則は、
Waffleへ適用してもそのまま有効だと考えられる（今日のquery-usecase-redesign
の結論とも一致するため）:

1. **tagsとrelationsは別物**: tags＝属性による分類（無向・多対多、フィルタ用）、
   relations＝特定の相手文書を名指しする有向リンク（グラフのエッジ）
2. **relationsの源泉は既存の構造化refフィールドのみ**: frontmatterや別の場所に
   relationsを手書きしない。既存ref（後述の表）から**都度・機械的に生成**する
   ことで、正典との二重管理・driftを防ぐ（Harness原則：関係はengineが持つ）
3. **カテゴリ（所属）も別軸で可視化対象にする**: type（documentType/schemaRef
   discriminator）で色分け、所属関係（bounded-context等）でクラスタリング

これらはWaffleの「正典はdocument.json、派生物は都度計算」という今日の結論と
矛盾せず、そのまま土台にできる。

---

## Waffleの実際のdocument型が持つref フィールド（第一稿・要確認）

| document型 | 既存ref（エッジの素） | 向き先 | 備考 |
|---|---|---|---|
| DomainSpecSchema (bounded-context) | `members.items[].{kind, id}` | bc → subdomain/aggregate/usecase | kindがedgeの種別を兼ねる |
| DomainSpecSchema (bounded-context) | `contextMap.items[]` | bc → 外部bounded-context | パートナー関係等 |
| SkillSchema (advisor) | `knowledgeRefs.items[].path` | skill → knowledge | 既存ubiquitous-language等と同型 |
| AgentSchema (subagent) | `skillPreloads.items[]` | agent → skill | documentId参照 |
| CodingSchema | `stack`（グルーピングキー） | coding document同士（同一stack） | 有向エッジというより同値グルーピング |
| CodingSchema (architecture) | `thicknessBySubdomain.items[].category` | architecture → subdomainのcategory値 | 値の参照であり、document自体への直接リンクではない可能性 |
| PresentationSpecSchema (flow) | `participants.items[]` | flow → 業務ユースケース/アクター | 要確認 |

**要確認事項**: 上記は今セッション中に断片的に確認した情報からの第一稿であり、
全schemaを横断した網羅的な調査はまだ行っていない。着手前に、全8schema
（Agent/Coding/DomainSpec/Knowledge/Platform/Presentation/Skill/Template）を
CLI経由で確認し、ref フィールドの一覧を正確に洗い出す必要がある。

---

## アイデアダンプ

1. relations生成をrenderパイプラインの一部として実装し、`.md`出力の
   frontmatterに`relations:`を機械的に埋め込む
2. relations生成を独立したquery操作（例: `query --operation get_relations`）
   として実装し、render経由でなくてもグラフ構造を取得できるようにする
3. tags/relationsグラフの可視化は、has-udd側のPoC（`okf-prototype.html`、
   Cytoscapeベース）をWaffle向けに移植する
4. 可視化はWaffleの責務に含めず、relations/tagsを機械可読な形で出力する
   ところまでをWaffleの責務とし、可視化は呼び出し側（Claude Code等）に委ねる
5. どのフィールドが「relationsの源泉」かを、schema側で`x-relation`のような
   新しいannotationとして宣言する（`x-prompt-write`と同じパターンを踏襲）
6. 型（documentType/schemaRef discriminator）をグラフのノード色、
   bounded-context等の所属をクラスタリングの単位とする
7. relations生成は今日合意したパターンD（参照解決）の一般化として実装する
   （1つのrefをたどるD → 宣言された全refフィールドを辿ってグラフ全体を
   組み立てる操作、という関係）
8. まずは可視化を伴わない、relations/tagsのJSON出力（グラフのノード・エッジ
   一覧）だけを先に作り、可視化は別スコープとして完全に切り離す

**絞り込み候補:** 5(x-relation宣言)＋7(パターンDの一般化)＋4/8(可視化は
スコープ外、機械可読な出力までがWaffleの責務)が本命。まずrelationsフィールド
の宣言方式と、それを都度計算する操作の設計から詰める。

---

## 論点 1: どのフィールドが「relationsの源泉」かを、schemaはどう宣言すべきか

### AI 初期見解
**見解:** 既存の`x-prompt-write`/`x-prompt-query`と同じパターンを踏襲し、
フィールド定義に`x-relation`（例: `{"targetDocumentType": "Knowledge"}`）を
付与する形が一貫性が高いと考える。

**根拠:**
- Waffle既存のx-プレフィックス annotation群（`x-prompt-write`/`x-prompt-query`/
  `x-render`/`x-render-target`等）は、いずれも「schemaがフィールドの意味・
  扱われ方を宣言し、engineがそれを機械的に解釈する」という一貫した設計に
  なっている。relationsの宣言もこの延長に置くのが自然
- has-udd側の先行ブレストが既に「x-frontmatterが型ごとにどのフィールドが
  relationsかを宣言する」という同型の結論に達しており（論点2）、車輪の
  再発明を避けられる
- ただし対象フィールドの型が、単純な文字列参照（`knowledgeRefs.items[].path`）
  から、種別付きの配列（`members.items[].{kind, id}`）まで多様なため、
  `x-relation`の宣言形式は単一パターンでは足りない可能性がある。ここが
  詳細設計の本体になる

### ユーザー見解
> 補助的なアノテーション（命名規則で拾えるものは省略）という中途半端な形は
> 避けたい。やるなら「命名規則で拾う」か「アノテーションで拾う」かのどちらか
> に統一したい。

### AI 再考見解
**見解:** 全ての参照フィールドに例外なく`x-relation`を明示的に宣言する方式
（命名規則からの推測は一切行わない）を推奨する。
**根拠:**
- Waffle自身の既存のx-プレフィックス群（`x-prompt-write`/`x-prompt-query`/
  `x-render`/`x-render-target`）は、いずれも「意味は必ずschemaが明示的に
  宣言し、engineは命名規則から推測しない」という一貫した思想を持っており、
  命名規則ベースの推測はこの設計思想とズレる
- 命名規則方式は、`members.items[].id`のような命名規則に乗らない参照
  フィールドが増えるたびに例外リストを継ぎ足すことになり、「命名規則＋
  例外」という中途半端な状態に近づいていく
- 宣言漏れという欠点は、「実際にRef形状を持つフィールドにx-relationの
  宣言が漏れていないか」を検証する`check-*`系usecaseで機械的に検知できる
  ——これはWaffleが既に得意とする「宣言と実態の対応を保証する」領域その
  ものであり、新しい種類のリスクではない

### 合意決定
**決定:** 参照フィールドの検出は、命名規則からの推測を一切行わず、
全ての参照フィールドに`x-relation`アノテーションを明示的に宣言する方式に
統一する。
**理由:** Waffleの既存設計思想（意味は必ず明示的に宣言する）との一貫性を
優先し、命名規則との併用による中途半端さを避けるため。宣言漏れのリスクは
既存のdrift検知パターンで相殺できる。
**次のアクション:** `x-relation`の具体的な宣言形式（単純な文字列参照、
種別付き配列、動的な参照先型の表現方法等）を次の論点で詰める。宣言漏れを
検知する新usecaseの要否も併せて検討する。

---

## 論点 2: x-relationの具体的な宣言形式

### AI 初期見解
**見解:** 基本形は「参照先のdocumentType」を宣言するシンプルなオブジェクト
（`{"targetDocumentType": "Skill"}`）とし、参照先の型が兄弟フィールドで
変わるケース（`members.items[].{kind, id}`）には`fromSibling`のような拡張
表現を用意する。

### ユーザー見解
> かなり複雑になりそうだけど大丈夫か。

### AI 再考見解（1回目）
**見解:** `members.items[].{kind, id}`は、`kind`の値（subdomain/aggregate/
usecase）に関わらず参照先は常に同一のDomainSpecSchema（specKind
discriminatorで区別されるだけ）であり、動的な型解決は実は不要だった。
`fromSibling`のような拡張は、実例0件のまま一般化しようとしていた
（evidence-based-scopeの誤適用）ため設計から外す。残る複雑さは
`knowledgeRefs.items[].path`が documentId ではなくレンダリング後のファイル
パスを値に持っている点のみとし、`valueFormat`のような分岐フラグで吸収する
案を出した。

### ユーザー見解（2回目）
> なぜその値（valueFormat）が必要なのか説明してほしい。多段階のネストのような
> 複雑な参照解決の仕組みは用意したくない。そもそもそんなに複雑なクエリを
> 要求するdocument構造にすべきではない。documentIdはもはやエイリアス的な
> 一意識別子であり、ファイルパスを別途保持する必要は無いはず。

### AI 再考見解（2回目・最終）
**見解:** `valueFormat`のような分岐も撤回する。x-relationが宣言する値は、
**例外なく常に「直接のdocumentId」1本**とする。参照解決の仕組み側に
多段階の変換・分岐ロジックを一切持たせない。`knowledgeRefs.items[].path`が
ファイルパスを保持している状態自体が、「参照はdocumentId一本であるべき」
という原則に反するschema側の歪みであり、参照解決の仕組みで吸収するのでは
なく、**schema側（`knowledgeRefs`のフィールド定義）を修正する**ことで
直す。documentIdは`x-render-target`のパステンプレート機構により、いつでも
ファイルパスへ機械的に導出できる一意なエイリアスとして機能する設計に既に
なっており、documentId以外の識別子（ファイルパス等）を別途参照値として
保持する理由が無い。
**根拠:**
- 参照解決の仕組みを複雑にするのではなく、そもそも複雑な解決を要求しない
  document構造にする、という原則の方が筋が良い
- documentId→ファイルパスの導出は、`x-render-target`の`path`テンプレート
  機構が既に担っており、この機構を参照値の解決にも一貫して使える
- 動的型解決（論点2再考1回目参照）に続き、これも「実例1件のために機構を
  一般化しようとしていた」典型例であり、機構ではなくデータ側を直す判断を
  優先すべきという、本セッションで繰り返し確認されたパターンに合致する

### 合意決定
**決定:** `x-relation`アノテーションの値は、常に単純な
`{"targetDocumentType": "<DocumentType名>"}`の形のみとし、値のフォーマット
分岐・動的型解決・多段階変換ロジックは一切持たせない。参照フィールドの値は
例外なくdocumentIdでなければならない。`knowledgeRefs.items[].path`のように
現状これに従っていないフィールドは、x-relation機構の実装に着手する際に
併せてスキーマ修正する。
**理由:** 「参照解決の仕組みを複雑にする」のではなく「複雑な解決を要求
しないdocument構造にする」という原則を優先した。documentIdは
`x-render-target`により常にファイルパスへ導出可能な一意のエイリアスであり、
別形式の識別子を参照値として持たせる必要が無い。
**次のアクション:** `knowledgeRefs`（SkillSchema）のフィールド定義を
documentId直接参照に修正する対応を、x-relation機構本体の実装と併せて
spec-firstで計画する。

---

## 論点 3: OKFフロントマターの各フィールドを、Waffleの既存フィールドにどうマッピングするか

### AI 初期見解
**見解:** OKFの6フィールドのうち5つは、Waffleの既存フィールドへほぼ
そのまま対応させられる。残る`type`と`resource`だけ、具体的な値の決め方を
詰める必要がある。

| OKFフィールド | Waffleでの対応 | 備考 |
|---|---|---|
| `type`（必須） | schemaの discriminator 値（`codingKind`/`specKind`/`skillKind`/`agentKind`等）。discriminatorを持たないschema（Knowledge/Template）は`documentType`をそのまま使う | OKFは「descriptive and self-explanatory」を求めており、粗い`documentType`より粒度が細かいdiscriminatorの方が適合する |
| `title` | `title.title`（TitleBlock、全schema共通） | そのまま |
| `description` | 各schemaのOverview/Summaryブロックの`text`/`items` | ブロック名がschemaごとに異なるため、render側でマッピング表が要る |
| `resource` | document.jsonの正典パス（またはgitリモートURL＋パス） | 具体形は要検討 |
| `tags` | 既存の`tags`フィールド | そのまま |
| `timestamp` | `updatedAt`（既にISO 8601形式） | そのまま |

**根拠:**
- `title`/`tags`/`timestamp`は既存フィールドの直接転記で済み、新しい設計判断は不要
- `type`はdiscriminatorがある場合とない場合で扱いが分かれるが、OKFのtypeが
  自由記述・中央未登録である以上、Waffle側で厳密なenumを新設する必要は無い
- `description`は各schemaのOverview/Summaryブロックの構造がバラバラなため、
  render側で「このschemaのどのブロックがdescriptionに当たるか」という
  対応表を持つ必要がある——ここが実装上の主な作業になりそう
- `resource`は、documentIdから`x-render-target`経由で導出可能なパスで足りる
  可能性が高いが、「URIとして一意に指す」という要件を満たすには、リポジトリ
  内相対パスで十分か、gitリモートURLまで含めるべきかの判断が要る

### ユーザー見解
> 合意。

### AI 再考見解
**見解:** `resource`はgitリモートURLまでは持たせず、リポジトリ内相対パス
（document.jsonのパス）のみとする。Waffle自身が「自己完結・git subtree
split可能」という性質を大事にしている以上、外部URLへの依存よりリポジトリ内
で完結する形の方が一貫する。

### 合意決定
**決定:** OKFフロントマター6項目は全てWaffleの既存フィールドの転記または
軽い導出で賄う。`type`＝schemaのdiscriminator値（無ければdocumentType）、
`resource`＝リポジトリ内相対パス（document.jsonのパス）、`title`/`tags`/
`timestamp`は既存フィールドをそのまま転記、`description`のみ各schemaの
Overview/Summaryブロックとの対応表をrender側に持たせる。新しいschema
annotationも新しいCLI操作も不要。
**理由:** OKFの必須要件は`type`のみで残りは推奨に過ぎず、Waffleが既に持つ
情報で全項目を無理なく満たせる。関連性（relations）は論点訂正の通り本文中の
Markdownリンクで表現するため、本論点の対象外。
**次のアクション:** `waffle render`のusecase spec（`uc-render-document`）に、
OKFフロントマター出力を追加する変更を、spec-first厳守で計画する。
`description`のブロック対応表を8schema分洗い出す。

---

## 論点 4: 本文中の関連性を、実際にどうMarkdownリンクにするか

### AI 初期見解
**見解:** 既存の`x-render`設定に、参照であることを示す軽いフラグ
（例: `"link": true`）を追加する方式を推奨する。documentIdから実際の
render済みパスへの変換は`x-render-target`が既に機械的に担っており、新しい
解決ロジックは不要。論点1・2で否定した`x-relation`（参照先の型を宣言する
大きな仕組み）とは異なり、これは既存のx-render機構が持つ「値をどう描画
するか」という責務の延長に過ぎない。

### ユーザー見解
> この方式なら、documentIdが動的に解決される（新しいdocumentが増えても
> renderのたびに正しく解決し直される）点が良い。

### 合意決定
**決定:** `x-render`のcolumns/pairs等の宣言に軽量なリンクフラグを追加し、
該当フィールドの値（documentId）を、render時に`x-render-target`のpath
テンプレートを使って実際の相対パスへ解決し、Markdownリンクとして出力する。
新しいschema annotation（x-relation等）は作らない。
**理由:** documentId→パスの解決は`x-render-target`で既に機械的に可能であり、
新しい解決ロジックを増やさずに済む。動的解決のため、document構成が変化
しても常に正しいリンクを保てる。
**次のアクション:** どのschemaのどのx-render設定にリンクフラグを追加すべきか
（委譲先テーブル、SkillFollowUpのtemplate、集約メンバー一覧等）を洗い出し、
論点3のfrontmatter対応と併せてspec-firstで計画する。

---

## セッションまとめ

### 合意事項一覧
1. 論点1・2は「OKF」の誤認（has-udd内部構想を実仕様と誤認）に基づいており
   無効。実際のOKFはGoogle Cloud公開の外部仕様で、必須フィールドは`type`
   のみ、関連性は本文中の標準Markdownリンクで表現する最小限の規約
2. 論点3: OKFフロントマター6項目は全てWaffleの既存フィールドの転記・軽い
   導出で賄う。新しいschema annotationもCLI操作も不要
3. 論点4: 本文中の関連性リンク化は、既存`x-render`設定への軽量な
   リンクフラグ追加で実現する。documentId→パス解決は`x-render-target`が
   既に担う

### 次のアクション一覧
- `uc-render-document`にOKFフロントマター出力を追加する変更をspec-firstで
  計画する（`description`のブロック対応表を8schema分洗い出す）
- `x-render`へのリンクフラグ追加対象（委譲先テーブル・SkillFollowUp・
  集約メンバー一覧等）を洗い出し、同usecase内で併せて計画する

### 保留・未解決の論点
なし（4論点とも合意済み、うち1・2は訂正により無効化）。実装はいずれも
spec-first手続きを経てから。

---
