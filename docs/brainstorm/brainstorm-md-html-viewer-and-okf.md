# ブレインストーミング: MD正本を保ったままCSSが当たったHTMLで閲覧できる汎用viewer機構と、その消費者となるOKF frontmatter対応

**目的:** document.jsonの正本性（git diff/blame/レビュー向け）はMarkdownのまま保ちつつ、人間が実際に読むときはCSSの効いた見やすいHTMLで見られるようにする汎用viewer機構を設計し、あわせて[[brainstorm-okf-in-waffle]]で「消費者不在」を理由に保留していたOKF frontmatter対応（tags/type等）を、このviewerの実際の消費者として組み込むかどうかを検討する。
**モード:** アイデア発散

**経緯:** `uc-render-handoff-template`でHandoff専用の手作り固定HTMLテンプレートを実装した際、evidence-based-scopeの原則から「2件目の実例が出るまで汎用テンプレートエンジン化しない」と明言していた。今回ユーザーから「specドキュメントもHandoffくらい見やすいHTMLの方が嬉しい」「正本はMarkdownのままでいいが、閲覧時はCSSが当たったHTMLがいい」という提案が出た。これはHandoffのような1schema専用の手作りテンプレートとは別物で、schema横断・MD→HTML変換という性質の異なる機構であり、かつ`render_document.py`の既存コメント「HTML は将来 viewer が担うため engine は MD のみ描画」が最初から見越していた領域でもある。あわせて、この汎用viewerがOKF frontmatterの実際の消費者になり得るため、[[brainstorm-okf-in-waffle]]の保留を解除できるかも合わせて検討する。

---

## アイデアダンプ

1. `render_document.py`の`x-render-target.formats`に`"html"`を追加し、既存のMD生成結果をMarkdown→HTML変換ライブラリに通すだけの薄い追加format
2. Handoffと同様の完全新規usecase（`uc-render-viewer`等）として、MD→HTML変換を独立させる
3. `waffle serve`のような常駐HTTPサーバーを新設し、リクエスト時に動的にMD→HTML変換して配信する
4. 静的サイトジェネレータ的に`.waffle/view/`配下へ全document一括HTML化するバッチコマンドを新設する
5. pandoc等の既存CLIツールをサブプロセスとして呼び出しHTML変換を委譲する（自前でMD→HTML変換ロジックを持たない）
6. ブラウザ側でMDファイルを直接fetchし、marked.js等でクライアントサイドレンダリングする（静的HTMLの事前生成をしない）
7. VSCode/Claude Code等のエディタ内蔵Markdownプレビューに委ね、Waffle側では何も作らない
8. artifact-designツールで都度手動プレビューする現状の運用のまま、汎用化しない
9. CSSは1種類の固定スタイルシートを全document type共通で適用する
10. CSSをdocumentType（Skill/Handoff/Knowledge等）ごとに切り替え可能にする
11. OKF frontmatter（tags/type/timestamp等）をHTMLのヘッダ・パンくず・サイドバーとして視覚的に表示する
12. 本文中の標準Markdownリンク（documentIdへの言及）を、HTML変換時に実際のHTMLページへのハイパーリンクとして解決する
13. Handoffの「読み方」セクションのような、番号付きの構造化ガイドをviewer側にも一般化して転用する
14. 生成したHTMLをArtifactツールで都度publishする運用に寄せ、ローカルファイルとしては持たない

**絞り込み候補:**
- **1**（`x-render-target.formats`への`"html"`追加）— 既存の`RenderDocument`のformats機構にそのまま乗れるため実現性が最も高く、`_select_template`等の既存分岐ロジックをほぼ流用できる
- **9**（CSS 1種固定）— Handoffで確定したPattern G相当のデザイントークン（フォレストグリーン・ニュートラル配色）を流用すれば実装コストが低く、まず動くものを早く出せる
- **11**（OKF frontmatterの視覚的表示）— これが無いとOKF対応をやる理由（消費者）自体が成立しないため、絞り込み候補というより前提条件
- **12**（documentIdリンクの実HTMLリンク解決）— [[brainstorm-okf-in-waffle]]論点4で既に「x-render-targetのpathテンプレートで動的解決する」という設計方針が合意済みのため、素直に実装できる
- **3**（`waffle serve`常駐サーバー）は自己完結ディレクトリという制約・LoomDB検討時の既存合意（コアに依存させない）と同種の理由で、いったんスコープ外候補

---

## 論点 1: 汎用viewerはどの層に実装すべきか（既存RenderDocumentのformat追加 vs 完全新規usecase）

### AI 初期見解
**見解:** 既存の`render_document.py`の`x-render-target.formats`に`"html"`を追加する形（アイデア1）で実装すべきであり、Handoffのときのような完全新規usecase（アイデア2）にはすべきでない。

**根拠:**
- Handoffを完全新規usecaseにした理由は「固定デザイン・1種類の決め打ちHTML・宣言的x-render機構では表現できない」という**Handoff固有の事情**だった。今回はその逆で、「既存のMD生成結果をそのままHTML化するだけ」という汎用処理であり、`x-render-target`の宣言的機構（formats配列）にちょうど収まる
- `formats`が既に配列（`["md"]`）として設計されており、2つ目のformatを追加する拡張ポイントとして最初から用意されている（`fmt = formats[0]  # MD 正本（HTML は将来 viewer が担うため engine は MD のみ描画）`というコメントが、まさにこの拡張を見越して書かれている）
- 全55schema・全documentTypeに横断適用するなら、Handoffのように1つ1つ専用usecaseを書くのは非現実的。既存の`RenderDocument`が持つdiscriminator分岐・pathVars解決・frontmatter生成の仕組みをそのまま使い回せる方が保守コストが低い

### ユーザー見解
> MD自体をHTMLに変換するのとレンダーのモード追加するのとどっちがいいのか確認した上で、実際にuc-render-handoff-templateのMD出力をHTML化した試作モック（OKF frontmatterヘッダ・Handoff同一トークンのCSS・mermaid・シナリオカード付き）を見た。「案外、悪くないね！」と好感触。

### AI 再考見解
**見解:** MD→HTML変換方式（`x-render-target.formats`への`"html"`追加）を採用する。実際に`uc-render-handoff-template`のMD出力を変換した試作で、Handoff（Pattern G）と同一のCSSトークンを転用しても違和感なく成立することを視覚的に確認できた。
**根拠:**
- 試作は既存のMD生成結果をそのまま流し込んだだけで、`part_renderer.py`側には一切手を入れていない。それでも見出し・テーブル・mermaid・受け入れシナリオが破綻なく表現できており、「既存MD出力の変換で足りる」という初期見解の前提が実物で裏付けられた
- Handoffと同じCSSトークンを流用したことで、documentType間の視覚的統一（配色・タイポグラフィが1つのデザイン言語で揃う）という副次的な利点も確認できた

### 合意決定
**決定:** 汎用viewerは`RenderDocument`の`x-render-target.formats`へ`"html"`を追加する形で実装し、既存のMD生成結果をHTMLへ変換する（content.jsonから直接HTMLを生成する専用レンダラーは作らない）。
**理由:** 実物の試作で、既存MD出力の変換だけで十分な見やすさ・情報構造が得られることを確認できたため。`part_renderer.py`側の複製が不要になり、実装・保守コストを最小限に抑えられる。
**次のアクション:** MD→HTML変換の実装方式（自前の軽量パーサーか、既存ライブラリの導入か）をspec化の前に検討する。

### ★訂正（ddd-advisor相談後）
spec化前のddd-advisor相談で、上記「`RenderDocument`のformats拡張」という実装層の判断が誤りだったと判明した。`render_document.py`には既に`fmt = formats[0]  # MD 正本（HTML は将来 viewer が担うため engine は MD のみ描画）`というコメントがあり、これは「formatsへHTMLを追加してよい」根拠ではなく、**逆に「HTMLは別のviewer usecaseが担う」という設計判断を既に先取りしていたもの**だった。誤読していた。

DDD的な理由（CQRS原則）: MD出力（`RenderDocument`）はstatus遷移（RENDERED）・イベント発行・deploy先解決という事後条件を持つ**コマンド実行モデル**の結果であるのに対し、HTML viewerは副作用なし・状態遷移なしの**読み取り専用の投影**。性質の異なる事後条件を1つのusecaseのformats分岐に混在させると、受け入れ基準が曖昧になる。

**訂正後の決定:** 汎用viewerは`RenderDocument`のformats拡張ではなく、**別の新規usecase**として実装する（配置先サブドメインはsd-document-managementのまま、中核分類の判定根拠とも整合）。OKF frontmatter対応もDocument集約自身の属性にはせず、この新usecase側の投影ロジックとして扱う。MD→HTML変換自体（`part_renderer.py`を再利用せず既存MD出力を変換するだけ）という論点1本体の結論は変わらない。

---

## 論点 2: OKF frontmatter対応は今回のviewer機構と同時に実装すべきか

### AI 初期見解
**見解:** 同時に実装すべきであり、別スコープに切り離すべきではない。

**根拠:**
- 前回OKFを保留した唯一の理由が「frontmatterを実際に読む消費者がいない」ことだった。今回のviewerはその消費者そのものなので、viewerを作らずOKFだけ実装すればまた同じ理由で保留に戻り、viewerだけ作ってOKFをやらなければ、HTMLヘッダにtags/type等の構造化メタ情報が出せず「素のMarkdownをただHTML化しただけ」で終わる
- [[brainstorm-okf-in-waffle]]で論点3・4は既に合意済み・実装方針も決まっている（既存フィールドの転記のみ、新schema annotation不要）ため、追加の合意形成コストがほぼ無い「乗っかるだけ」の関係にある
- evidence-based-scopeの観点でも、「viewerというOKFの消費者が今まさに実例として生まれる」タイミングであり、これを逃すとまた「実例なし」に戻ってしまう

### ユーザー見解
> 試作モックのOKF frontmatterヘッダ（tagピル・documentId/schemaRef/updatedAt）を見て、OK。

### AI 再考見解
**見解:** 初期見解のとおり、viewerとOKF frontmatter対応は同時実装で進める。
**根拠:**
- 試作モックのヘッダが実際に評価されたことで、「viewerがOKF frontmatterの消費者になる」という前提が絵空事ではなく実物で成立した

### 合意決定
**決定:** OKF frontmatter（tags/type/timestamp等の既存フィールド転記）は、viewer機構の実装と同時に組み込む。
**理由:** [[brainstorm-okf-in-waffle]]で保留していた「消費者不在」が、今回のviewerで解消されると試作で確認できたため。
**次のアクション:** [[brainstorm-okf-in-waffle]]論点3で洗い出し予定だった「8schema分のdescriptionブロック対応表」を、このviewer実装のspec化と合わせて作成する。

---

## 論点 3: CSSスタイルは全document type共通の1種固定か、documentTypeごとに切り替えるか

### AI 初期見解
**見解:** まずは全document type共通の1種固定スタイル（アイデア9）から始め、documentTypeごとの切り替え（アイデア10）は2件目以降の具体的な不満が出てから検討する。

**根拠:**
- Handoff（Pattern G）で既に確定した配色トークン・タイポグラフィ・カード/表組みのスタイルは、「認知負荷を下げる」という抽象度の高い設計原則に基づいており、documentType固有ではなく汎用的に転用できる
- evidence-based-scope: documentTypeごとに本当にスタイルを変えたい実例（例えば「Knowledgeは判定木の可視化が要る」等）がまだ1つも無い段階で、切り替え機構を先に作るのは先回りの一般化にあたる
- 1種固定であれば、CSSを`_CSS`定数のような形でコード内に1箇所持つだけで済み、schema側に新しいx-render annotationを増やさずに済む

### ユーザー見解
> 試作モックのHandoff同一トークンのCSSを見て、OK。

### AI 再考見解
**見解:** 初期見解のとおり、まずは1種固定スタイルで進める。
**根拠:**
- 試作でHandoffのトークンをそのまま流用しても、spec特有の要素（テーブル・mermaid・gherkinシナリオカード）が違和感なく成立することを確認できた。documentType間の視覚的統一という利点も実物で裏付けられた

### 合意決定
**決定:** CSSは全document type共通の1種固定スタイル（Handoff Pattern G相当のトークン）から開始する。documentTypeごとの切り替え機構は、具体的な不満・2件目の実例が出てから検討する。
**理由:** evidence-based-scope。切り替え機構を要求する具体的な実例が現時点で無く、試作でも1種固定で十分機能することが確認できたため。
**次のアクション:** 特になし（spec化の際、CSSはコード内定数として1箇所に持つ設計にする）。

---

## 論点 4: リポジトリ全体を俯瞰するグラフmapビュー（OKF公式visualizeサブコマンド相当）も今回のスコープに含めるか

### AI 初期見解
**見解:** 今回のスコープには含めず、将来「複数spec間の関係を一覧したい」という具体的なニーズが出たときの別ブレストにすべき。

**根拠:**
- OKF公式`visualize`は単一文書のHTML化ではなく、**バンドル全体を横断してノード・エッジを集計する**という質的に異なる処理（Cytoscape.js等のグラフライブラリ、全document走査、JSON埋め込み）であり、論点1〜3で合意した「1文書のMD→HTML変換」の単純な延長では済まない
- evidence-based-scope: 「全体を俯瞰したい」という具体的な困りごとがまだ1件も無い段階で、グラフmap機能を作るのは先回りの一般化にあたる

### ユーザー見解
> これも入れちゃいたいね！

### AI 再考見解
**見解:** 「今回同時に実装する」のではなく、「viewerのロードマップに正式に位置づけ、独立した2件目のusecaseとして次に着手する」という形で合意したい。
**根拠:**
- OKF公式実装を調べたことで、グラフmapのエッジは論点1〜3と同じ「本文中の標準Markdownリンク」から機械抽出できることが判明した（tagsは検索用途のみ）。つまり論点1〜3で作るリンク解決の仕組み（[[brainstorm-okf-in-waffle]]論点4のdocumentId→パス解決）が、グラフmapの土台としてそのまま再利用できる——完全に別物ではなく、地続きの拡張
- 一方で「全document横断で走査しノード・エッジ集計する」処理は`RenderDocument`（1文書変換）とは責務が異なり、Handoffのときと同じ理由（宣言的x-render機構の語彙で表現できない専用処理）で**別usecase**になる。1つのspec・1回のTDDサイクルに両方を詰め込むと、evidence-based-scopeの「1specに欲張って複数フェーズ分を詰め込まない」というsd-flow-gateで確立した規律に反する
- 「入れたい」という要望自体は、OKFを実装するなら中途半端にせず本来の価値（グラフによる関係の俯瞰）まで見せたい、という一貫した動機であり、思いつきの水増しではないと判断した

### 合意決定
**決定:** グラフmapビューは実装する。ただし論点1〜3の単一文書viewer（`uc-render-document`へのHTML format追加）とは別のusecaseとして、単一文書viewerのリリース後に着手する2件目のフェーズと位置づける。
**理由:** エッジ抽出の土台は共有できるが、全document横断集計は責務が異なる別処理であり、1specに複数フェーズを詰め込まないという既存の規律（sd-flow-gate確立時の合意）に従うため。
**次のアクション:** 論点1〜3のspec化を先に完了させ、その中で確立するリンク解決の仕組みを踏まえた上で、グラフmapビュー用の2件目のusecase spec（例: `uc-render-document-graph`）を別途起票する。

---

## セッションまとめ

### 合意事項一覧
1. 論点1: 汎用viewerは`RenderDocument`の`x-render-target.formats`へ`"html"`を追加する形で実装し、既存MD生成結果を変換する（content.jsonから直接HTMLを生成する専用レンダラーは作らない）
2. 論点2: OKF frontmatter対応（tags/type/timestamp等の既存フィールド転記）は、viewer機構の実装と同時に組み込む
3. 論点3: CSSは全document type共通の1種固定スタイル（Handoff Pattern G相当のトークン）から開始し、documentTypeごとの切り替えは2件目の実例が出るまで作らない
4. 論点4: リポジトリ全体を俯瞰するグラフmapビュー（OKF公式visualize相当）も実装する。ただし単一文書viewer（論点1〜3）とは別usecaseとし、単一文書viewerのリリース後に着手する2件目のフェーズと位置づける

### 次のアクション一覧
- MD→HTML変換の実装方式（自前の軽量パーサーか、既存ライブラリの導入か）を検討する
- [[brainstorm-okf-in-waffle]]論点3で洗い出し予定だった「8schema分のdescriptionブロック対応表」を、このviewer実装のspec化と合わせて作成する
- spec-first手続き（advisor相談→spec作成→TDD実装）でフェーズ1（単一文書viewer）を計画する
- フェーズ1完了後、グラフmapビュー用の2件目のusecase spec（例: uc-render-document-graph）を別途起票する（フェーズ2）

### 保留・未解決の論点
なし（4論点とも合意済み）。実装はいずれもspec-first手続きを経てから、フェーズ1→フェーズ2の順で進める。

---

## advisor相談の結果（spec作成前の判断材料収集）

### ddd-advisor: 配置判断

**判定:** `RenderDocument`の`formats`拡張ではなく**別の新規usecase**として実装する（論点1の訂正、上記参照）。CQRS原則により、MD正本（コマンド実行モデル、status遷移・イベント発行・deploy先解決を伴う）とHTML viewer（読み取り専用の投影）を1つのusecaseに混在させない。OKF frontmatterもDocument集約の属性ではなく新usecase側の投影ロジック。配置先サブドメインはsd-document-management（中核）のまま変わらず。懸念点として、`render_document.py`のdocstring・コメントを「HTMLは別usecaseが担う」という事実に合わせて更新すべきと指摘あり。

### tech-lead-advisor: 実装方式

**evidence-based-scope宣言:** 実証済みの拡張（`uc-render-handoff-template`という同型の「読み取り専用投影usecase」パターンが既に1件稼働しており、2件目の対象へ適用するだけ）。

| 項目 | 判断 |
|---|---|
| MD→HTML変換方式 | **自前の軽量パーサー**を`domain/services/markdown_to_html.py`に実装。サードパーティMarkdownライブラリ（`markdown`/`mistune`等）は追加しない——Waffle自身が`part_renderer.py`で生成するMDは語彙が限定されており（見出し/段落/リスト/テーブル/コードフェンス/水平線/太字）、汎用パーサーはオーバースペック。既存依存（jsonschema/tree-sitter系＝構造処理）の性格を汚すことも避けたい |
| 新usecase名 | `uc-render-document-viewer`（`render_document_viewer.py`、`RenderDocumentViewer`クラス） |
| RenderDocumentとの関係 | 内部で`RenderDocument.run(path, deploy=False)`を呼びMD文字列のみ取得。コマンド実行モデル側の事後条件（deploy・status遷移）を混入させない |
| Mermaid | ```` ```mermaid ````フェンスを`<pre class="mermaid">`へ機械変換し、ブラウザ側mermaid.js（CDN読み込み）に委譲。Waffle側はSVGレンダリングロジックを持たない。Python側の依存には影響しない |
| CSS | Handoff Pattern GのCSSトークンを抽出・共通化した定数として`domain/services/`内に新設 |

**次のアクション:** この内容でuc-render-document-viewerのspecを起票し、TDDで実装する。
