---
name: "design-share"
description: "UIモックを作成して関係者に共有・レビューしてもらいたいとき、またはDesign.md（デザインシステム定義）を対話式で作成・改善したいときに使う。「UIモックを作りたい」「デザイン案を見せたい」「Design.mdを作りたい・直したい」と言われたときに使い、成果物は自前のAWS環境（S3+CloudFront）へトークン保護付きURLとして公開する。"
disable-model-invocation: true
---

# design-share

## 目的

UIモックを作成して関係者に共有・レビューしてもらいたいとき、またはDesign.md（デザインシステム定義）を対話式で作成・改善したいときに使う。「UIモックを作りたい」「デザイン案を見せたい」「Design.mdを作りたい・直したい」と言われたときに使い、成果物は自前のAWS環境（S3+CloudFront）へトークン保護付きURLとして公開する。

---

## 役割

- Design.mdを対話式で作成・改善する（内蔵アーキタイプギャラリーからの選択と、試作artifactによる視覚確認を挟む）
- Design.mdから複数パターンのUIモックHTML（コメント機能内蔵）を生成する
- UIパターンをパターン単位のURL＋トークンで自前AWS環境へ公開する
- 公開済みパターンの無効化・エクスポート・トークンローテーション・横断管理の手段を提供する

---

## 処理対象と成果物

### 処理対象

作りたいUIの目的・対象ユーザー・参考イメージ（対話でヒアリング）、または既存のDesign.mdとそれに対する改善要望・閲覧者からのコメント。

### 成果物

Design.md（google-labs-code/design.md仕様のYAMLフロントマター＋Markdown本文）と、コメントUIを内蔵した外部依存ゼロの自己完結UIパターンHTML（トークンゲートは配信基盤側のedge-gateが担う）。デプロイ時はパターンごとの共有URL＋トークン。

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| 作りたいUIの目的・対象ユーザー | 明示されなければ対話の最初にヒアリングする |
| 既存Design.mdの有無と場所 | 指定がなければプロジェクト直下のDESIGN.mdを確認し、あれば改善モード・なければ新規作成モードで開始する |
| デプロイ先AWS環境の有無 | 未構築なら初回構築3手順（①infra/cloudformation.yamlでスタック作成 → ②Outputsからdesign-share.envを作成 → ③scripts/deploy_function.shでedge-gate本体を反映）を提案する。②③を省くと全URLが503のままになる。デプロイ不要（ローカル確認のみ）の場合はデプロイ手順を省略する |
| 生成するUIパターン数 | 指定がなければ2〜3案を提案する |
| 管理操作の入り口の好み | 指定がなければscripts/ds.sh（CLI）を直接使う。画面で見たい場合はds.sh console（Web UI）、MCPクライアントから使う場合はscripts/mcp_server.pyを案内する |

---

## 実行手順

### Step 1: セッションを開始しDesign.mdの状態を確認する

既存Design.mdがあれば改善モード、なければ新規作成モードで開始する。新規の場合は非デザイナーでも指差しで選べるよう、内蔵アーキタイプギャラリーを最初に提示する。

#### アーキタイプギャラリーを提示する

6種の方向性（コーポレート・クリーン／エディトリアル・ウォーム／プレイフル・スタートアップ／ミニマル・ラグジュアリー／テクニカル・ブループリント／信頼重視・パブリック)を業種レベルの想起ワード付きで見せ、近いものを選んでもらう。

#### 目的と対象ユーザーをヒアリングする

この画面が果たす仕事・見る人・言語化しづらい要望を対話で引き出し、選んだアーキタイプとの差分として記録する。

### Step 2: Design.mdを対話と試作artifactの往復で確定する

design.md仕様の固定順セクションに沿ってトークン値を決めていく。言葉だけで決めず、2つのチェックポイントで試作artifactを生成して見て判断してもらう。

#### Colors・Typographyを確定し試作①を見せる

配色スウォッチと見出し・本文サンプル程度の小さな試作を生成し、視覚確認を経てトークン値を確定する。

#### Layout・Componentsを確定し試作②を見せる

実コンテンツに近い試作ページを生成し、レイアウト構想とコンポーネントトークンを確定する。

#### Design.mdを検証しスナップショット保存する

lintで構造・コントラストを検証し、バージョンとしてスナップショット保存する。過去版との比較はdiffをオンデマンドで実行する。

### Step 3: DESIGN.mdを関係者レビューにかけ確定する

確定前のDESIGN.mdを視覚スペックシートとして公開し、関係者のコメントで方向性を合意してから正式な配置場所へ確定配置する。UIモックの量産はこの確定の後に行う。

#### スペックシートを生成しレビュー用に公開する

references/templates/template-design-spec-body.html にDESIGN.mdのトークン（スウォッチ・タイプスケール・状態チップ全種・部品の実物）と本文（Overview/Layout/Do's & Don'ts）を流し込み、template-pattern-page.html の {{モック本体}} に載せる。ds.sh deploy --type design-review --design <DESIGN.mdパス> <spec.html> "<表示名>" でURL＋トークンを発行する。値は必ずトークンから導出し、その場で新しい色・サイズを発明しない（round-tripを閉じる）。

#### コメントで方向性を合意する

関係者はコメント欄で「この方向でOK／修正希望」を名前付きで返す（アカウント不要・数秒ごとに同期＝ライブレビュー可）。修正希望があればDESIGN.mdを直してスペックシートを再デプロイし、合意できるまで往復する。

#### 確定して正式な配置場所へ置く

合意できたら ds.sh confirm-design <slug> [--to <ディレクトリ>] を実行する。deploy時にS3へ保存したDESIGN.md本体を <配置先>/DESIGN.md（既定はカレント）として配置し、既存があれば上書き前にバックアップを取り、確定の事実（confirmedAt・配置先）をmetaへ記録し、レビューコメントを記録として同伴エクスポートする。confirm-designはUIモックを生成しない（生成は確定後の対話で行う）。

### Step 4: UIパターンHTMLを生成する

確定したDesign.mdをもとに、references/templates/template-pattern-page.htmlを雛形として複数パターンのモックHTMLを生成する。コメントUIは外部依存ゼロのvanilla JSでページに内蔵し、単体で配布可能な自己完結ファイルにする。トークンゲートはHTMLに含めない（配信基盤側のedge-gateが担う）。

### Step 5: パターン単位でデプロイしURL＋トークンを発行する

scripts/ds.sh deploy <HTMLファイル> "<表示名>" を実行する。slugとトークンが生成されてホスティング先へ配置され、URLとトークンはこの場で一度だけ表示される。トークンは別チャネルで共有相手へ渡すよう案内する。デプロイ直後に閲覧者と同じ手順（URLを開く→トークン入力→コメント1件投稿→一覧表示）のセルフスモークを必ず1周する。

### Step 6: コメントを回収しDesign.mdへ反映する

scripts/ds.sh export <slug> のzip、または aws s3 sync でコメントJSONを取得して要点を整理し、Design.mdへの差分として反映する。必要ならパターンを再生成・再デプロイして改善サイクルを回す。

### Step 7: 公開中パターンを管理する

管理操作はCLI（scripts/ds.sh）・Web UI（ds.sh console、localhostのみ）・ローカルMCP（scripts/mcp_server.py）の3経路から選べる。いずれも実体は同じスクリプトに委譲される。閲覧者に横断閲覧を提供する場合は共有ギャラリー（共通トークン）を有効化する。

- 一覧: ds.sh list（全パターンの公開状態・slug・更新日）
- 無効化: ds.sh disable <slug>。アクセスを止めるがデータは残す。既定でzipエクスポートを先に実行する
- 再発行/再公開: ds.sh rotate <slug>。新トークン発行で旧トークンは失効（URL不変）。無効化済みパターンに対して実行すると再公開になる
- エクスポート: ds.sh export <slug>。公開を維持したままバックアップを取得する
- 共有ギャラリー: ds.sh gallery init で1つのランディングURL＋共通トークンを発行し、閲覧者が公開中の全パターンを一覧・横断閲覧できるようにする（rotate/disableで共通トークンを管理）
- カテゴリ（名前付きギャラリー）: ds.sh galleries create でカテゴリを発行し、ds.sh galleries add/remove/set で各パターンの所属を管理する。カテゴリのトークンは所属パターンだけを開ける（スコープ共有）

---

## 出力形式

デプロイ時は「パターン名／URL／トークン／有効状態」を表形式で一度だけ提示する。Design.md確定時は変更されたトークンと本文セクションの要約を報告する。

---

## ガードレール

- 動作要件: aws CLI v2・python3 がインストール済みで、AWS認証情報が設定されていること（scripts・Web UI・MCPサーバーの全経路が前提とする。python3はaws CLIに同梱されないため別途必要。zip等の追加バイナリには依存しない＝エクスポートのzip化はpython3標準のzipfileで行う）
- Design.mdの実体フォーマットはgoogle-labs-code/design.md仕様に従い、独自フォーマットを発明しない
- トークンは発行・再発行の瞬間にチャットへ一度だけ表示し、平文でファイルやリポジトリに永続保存しない（閲覧者側ではCookieに保持される点は既知の設計）。ただしlocalhost限定の管理コンソールは、開発者がKVSから現在トークンを読んで表示・コピーしてよい（ファイルには残さない）
- 無効化してもホスティング上のデータは即削除しない（エクスポート可能な状態を保つ）
- トークン失効・無効化・新規デプロイのエッジ反映は数秒〜数十秒の伝播遅延がある（KVSは結果整合で収束するまで非単調。新規発行・再発行直後のパターンは一時的に403＝無効化済み表示に見えうる）。「即時」とは案内せず、少し待って再読み込みするよう伝える
- コメント内容は必ずテキストとして描画する（innerHTML禁止）。加えてedge-gateがコメントPUTのキー形状（.jsonのみ）とcontent-type（application/jsonのみ)を検査し、配信ドメイン上へのHTML設置を拒否する
- コメントPUTにはサイズ・レート制限がない（トークン保持者によるゴミ投棄は受容リスク）。共有相手は信頼できる範囲に留めること
- 実行時に他のSkill（ux-advisor等）を呼び出さない。knowledgeはこのSkill内のreferencesで自己完結させる
- 特定企業サイトのデザイントークン抽出・同梱・名指し参照をしない（アーキタイプの想起ワードは業種レベルに留める）
- 外部URL（Figma・実アプリ画面）の取り込み機能は提供しない
- トークン値（色・タイポグラフィ等）は言葉だけで確定せず、必ず試作artifactの視覚確認を経て確定する
- Design.md確定・試作生成・パターン生成の前に、references/knowledge/frontend-design-principles.md の概念層（題材に根ざす／ありきたりを避ける／主役を立てる／理由を言い切る／効かせどころを絞る／下限を守る）に照らす。特に『理由を言い切る』＝「なぜこれがありきたり（同種の題材なら誰でも出る型どおりの姿）でないか」を自分の言葉で言えることを確認する。○×チェックリストの照合にしない（毎回題材ごとに答えが変わる生成的な問いとして回す）。アクセシビリティ等の下限が通っていることを、ありきたりでない証拠の代わりにしない。
- UIモック生成時は、生成したモックをそのDESIGN.mdが言い切った制約に照らして点検する（『理由を言い切る』を確定時だけでなく実装時にも適用）: 効かせどころ＝アクセントが実装でも一点に集約されているか（見出し等に撒いていないか）／主役は状態を跨いで機能する姿を見せているか（1状態だけ『置いた』のは装飾）／状態専用と宣言した色を別用途に流用していないか／DESIGN.mdに無い値を発明していないか（round-trip）。違反は実装をDESIGN.mdへ戻すか、掟の方を直す。
- 商用級モックの入力コントラクト（value-prop=自己完結・AWSのみを保つ）: 書体（assets/fonts＋embed_fonts.py）・統一SVGアイコン（references/assets/ui-icons.md）・生成SVG/CSSクラフト（チャート/パターン/データビズ）はスキル内蔵で埋める。実写・ロゴ・プロダクト画面などの画像は顧客提供とし、外部画像生成には依存しない。SaaSサーフェスは絵より部品（アイコン/チャート/表/状態）が主なので内蔵アセットで商用に届きやすい。LP/コーポレートはブランド画像の提供が前提。emojiをアイコン代わりにしない
- 【UIモックの標準サイクル】最良のUIモックは〈生成→敵対的測定→修正→学びの還元〉のサイクルで作る。自己批評（理由を言い切る／DESIGN.mdの掟に照らす）だけで完成としない。生成したモックは、UXを熟知した批評者=ux-advisorによる敵対的測定にかける: 明示的な物差し（商用級か／核の価値／ありきたりでないか）に照らし、実物を読ませ数値evidence（コントラスト等）で欠陥を具体箇所で名指しさせ、verdict＋順位付きmust/should-fixを得る→修正→必要なら再測定で閉じる→学びをdesign-shareの知識/アセットへ還元する。測定者は汎用批評でなくUX専門(ux-advisor)であること。design-shareは自己完結（実行時に他Skillを呼ばない）ため、この敵対的測定はスキル内でなくOrchestrator層が回す（スキルは自己批評まで持ち、外部測定は上位が回す層分け）。

---

## 参照

- `references/knowledge/frontend-design-principles.md`: 試作artifact・UIパターン生成時の判断基準（hero＝主張、タイポグラフィが個性を運ぶ、大胆さの一点集中等）
- `references/knowledge/design-md-conventions.md`: Design.mdの仕様（YAMLトークン＋固定順セクション）と、試作往復・スナップショット運用の規約
- `references/knowledge/design-system-tokens.md`: デザイントークンの設計原則（既存knowledgeの再利用）
- `references/knowledge/visual-hierarchy-and-restraint.md`: 視覚的階層と抑制の原則（既存knowledgeの再利用）
- `references/knowledge/ui-copywriting.md`: UIコピーの原則（既存knowledgeの再利用）
- `references/knowledge/accessibility-baseline.md`: アクセシビリティの最低基準（既存knowledgeの再利用）
- `references/templates/design-archetypes/`: 内蔵アーキタイプ6種のDesign.md雛形（対話の最初に提示する選択肢）
- `references/templates/template-pattern-page.html`: コメントUI内蔵・外部依存ゼロのUIパターンHTML雛形（トークンゲートは含めない）
- `references/templates/template-design-spec-body.html`: DESIGN.mdを視覚スペックシート（スウォッチ・タイプスケール・状態チップ全種・部品の実物・Do/Don't）としてレンダリングする本体断片。template-pattern-page.htmlの{{モック本体}}に載せてレビュー用に公開し、既存のコメント・トークンゲート機構をそのまま再利用する
- `infra/cloudformation.yaml`: S3＋CloudFront＋CloudFront Functions＋KeyValueStoreの初回構築テンプレート（構築後にdeploy_function.shの実行が必須）
- `infra/cloudfront-function/edge-gate.js`: トークン照合・無効化判定・コメントPUT検査(形状/content-type/16KBサイズ上限)・名前付きギャラリーのスコープ判定・一覧書き換えを行うエッジ関数。KVS読み取りは通常1回、ギャラリー横断/スコープ経路で最大約6回（所属は最大3件・fail-closed）
- `scripts/ds.sh`: 統一CLI: list／deploy／export／rotate／disable／console／update-function／confirm-design（レビュー済みDESIGN.mdの確定配置）
- `scripts/confirm_design.sh`: レビュー（design-review）を経たDESIGN.mdを正式な配置場所（既定 ./DESIGN.md）へ確定配置する。既存があればバックアップし、確定事実をmetaへ記録、レビューコメントを同伴エクスポートする。UIモックは生成しない
- `scripts/common.sh`: 共通設定ローダー（design-share.env）とKVS・metaヘルパー
- `scripts/deploy_function.sh`: edge-gate.js本体をCloudFront Functionへ反映する（初回構築後に必ず1回実行）
- `scripts/console_server.py`: Web管理コンソール（localhostのみ・Host検証＋乱数トークンでCSRF防御）。行ごとの⋯メニューでエクスポート/改名/トークン再発行/無効化・再公開、共有ギャラリーの有効化/共通トークン再発行/無効化も操作できる。カテゴリ（名前付きギャラリー）の作成・一覧・所属編集もできる
- `scripts/mcp_server.py`: ローカルMCPサーバ（stdio・依存なし）。MCPクライアントから管理操作をツールとして呼べる
- `references/templates/gallery-page.html`: 共有ギャラリー（公開中パターンの一覧・横断閲覧）のランディングページ雛形。gallery/index.htmlとして配置される
- `scripts/gallery.sh`: 共有ギャラリーの管理（init/rotate/disable/url）。プロジェクト共通トークンの発行・失効とギャラリーページ配置を行う
- `scripts/rename_pattern.sh`: パターンの表示名のみを変更する（slug・トークン・公開状態は不変。ギャラリー一覧へも反映）
- `scripts/galleries.sh`: 名前付きギャラリー（カテゴリ）の管理（create/list/rotate/disable/delete/add/remove/set）。所属はタグ式・アクセスはスコープ
- `references/templates/gallery-app.html`: 名前付きギャラリーのランディング雛形（URLからgslugを読み /g/{gslug}/index.json を表示）。gallery/app.htmlとして全カテゴリ共用配置
- `assets/fonts/`: 自己完結アセット層の同梱書体（Lato OFL 3ウェイト＋DejaVu Mono、Latin subset woff2＋ライセンス）。商用の見た目を外部依存ゼロで出すための書体。README.md参照。日本語・ブランド書体は顧客提供
- `scripts/embed_fonts.py`: 生成HTMLの@font-faceの『FONT:<name>』マーカーを、同梱woff2のbase64 data URIへ置換し自己完結HTMLにする（ランタイム依存はpython3のみ）
- `references/assets/ui-icons.md`: 商用UI向けの統一インラインSVGアイコン集（24px/stroke/round・絵文字を使わない）。ブランドロゴはnavアイコンと別形にする
