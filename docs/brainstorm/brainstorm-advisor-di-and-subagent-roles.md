# ブレスト: advisorのDI注入設計とsubagentの役割分担

**目的:** schema-authoring Skill（各schemaに沿ったドキュメント作成を助けるSkill、
新設検討中）を設計する過程で浮上した、advisorのDI注入方式・subagentの役割分担・
advisorエコシステムのガバナンス・Handoffの人間向け出力という4つの関連論点を
記録する。
**モード:** アイデア発散→一部収束
**作成日:** 2026-07-14
**経緯:** [[brainstorm-qa-advisor-design]]でqa-advisorの配線漏れを解消した流れで、
「schemaごとにどのadvisorが要るか」の整理に進んだところ、DI注入の設計自体・
subagentの役割分担・advisorの育成ガバナンス・Handoffの人間可読出力という4つの
論点に発散した。

---

## 確定事項

1. **各schema作成には必ずadvisorのSkillフォローアップが要る。ただしschemaごとに
   必要なadvisorの組み合わせは異なる**（全schemaに全advisorが必要という意味では
   ない）。理由: x-prompt-writeによる機械的な値埋めだけでは、DDD設計判断・
   アーキテクチャ配置判断・UX判断・品質判断等が抜け落ちるため。
2. **schemaRef→advisorの対応表は、CLAUDE.mdの「Skillフォローアップ」節に集約する**
   （schema自体には持たせない）。理由: tech-lead-advisorの
   `architecture-composition-root`原則（配線は一箇所に集約する）と整合し、
   schema自体がadvisorという概念を知らずに済む（Skill/advisor間のテキストベース
   疎結合原則を保てる）。一覧性（今どのschemaにどのadvisorが要るか）もCLAUDE.md
   一箇所で俯瞰できる。
   **→ 2026-07-15、以下「skill-router Skill」の設計により内容が更新された。
   「CLAUDE.md集約」という結論の骨子（配線を一箇所に集約する）は生きているが、
   集約先はCLAUDE.md自体の生テキストではなく、専用Skill（skill-router）の
   document.jsonへ変わった。詳細は本ファイル末尾の新セクション参照。**
3. **advisorは毎回AgentSchemaのSubagent構造（goal-dispatch）に従い、その都度
   サブエージェントとして起動する**（永続登録はしない、既存確定パターン。
   [[brainstorm-qa-advisor-design]]の「常設Subagentを用意すべきか」参照）。
   各advisorから返ってきた見解を基に、Orchestratorが見解をまとめて最終的な
   結論をユーザーに提示する。
4. **Subagentの役割は4種に分離する**: Investigation（調査型）/
   Spec-authoring（スペック作成型）/ Handoff-authoring（ハンドオフ作成型）/
   Implementation（実装型）。それぞれ**独立したSkill**として表現する
   （`SubagentContent`に discriminator フィールドを足すのではなく、advisor
   Skillと同じパターンで役割ごとに別々のSKILL.mdにする）。
   - 理由: Spec-authoringとHandoff-authoringは動作パターン（scaffold create→
     advisor相談→fill）が同じに見えるため当初は統合案（document-authoring型に
     集約し対象schemaRefを別フィールドで指定）を検討したが、**動作パターンの
     同一性よりセマンティックな分離を優先すべき**という判断で却下された。
     統合すると、Subagentが読み込むSkillだけでは「この段階で何をすべきか」が
     分からず（対象schemaRefという間接情報を都度参照しないと分からない）、
     役割ごとにSkillが分かれていた方がAIの認知負荷が大きく下がる。構造の節約
     （DRY）よりAIが迷わず動ける設計を優先する。
   - Implementationのみ例外的な役割で、CodingSchemaの**ドキュメント**作成では
     なく実際のソースコード実装そのものを指す。他の役割同様、都度
     `skillPreloads`で使うadvisorが設定された上で動作し、一人歩きで実装しない。
5. **Implementationを除く3役割（Investigation/Spec-authoring/Handoff-authoring）
   の成果物は、フォーマットが決まったテンプレート形式のドキュメントとして
   schemaで管理・render管理する。** Spec-authoring（DomainSpecSchema等）・
   Handoff-authoring（HandoffSchema）は既存schemaで足りるが、Investigationの
   成果物（調査レポート）には対応するschemaが無いことが判明した。
   - KnowledgeSchema（確立された恒久的なバックボーン知識を記録する用途）は
     性質が異なるため不適合と確定。
   - **`TemplateSchema/v1`を流用する**方向で確定。現状は「advisor Skillの
     回答テンプレート」用途に限定されているが（`templateKind`は`judgment`の
     1種のみ）、構造自体は「決まったフォーマットのドキュメントをschemaとして
     管理・render・特定Skillのreferencesへdeployする」という汎用機構であり
     転用できる。進め方: (1) `description`を「advisor Skill限定」から
     「Skill全般の出力テンプレート」へ広げる、(2) 既存kind discriminator
     パターン（`SkillSchema.skillKind`等と同型）に従い`templateKind`に新値
     （例: `investigation-report`）を追加、(3) 新kindごとに専用`$defs`ブロック
     （例: `InvestigationReportTemplateContent`）を`if`/`then`で出し分け、
     (4) `x-render-target`の`pathVars`/`path`/`deploy`にも新kind分を追加。
6. **Handoffの人間向け出力にHTMLを追加する方向性を確定**（機構の詳細は未着手）。
   - 目的: AIの認知負荷にはMarkdown/document.jsonが適するが、人間が
     spec→実装の引き継ぎ資料を確認し「実装に進めてよいか」を判断する場面では、
     レイアウトが整理されたHTMLの方が認知負荷が低い。同じHandoff document
     contentから、AI向け（既存Markdown）と人間向け（HTML）の2形式を出す。
   - **Claude Code組み込みのartifact-designスキル（Artifactツール）自体は
     使わない。** ArtifactツールはAnthropicのホスティングサーバーへの
     アップロードが前提で、GitHub Copilot・Kiro等の他ツールでは使えない。
     Waffleはマルチツール前提のOSSであるため、環境非依存（ローカルディスクへの
     静的HTML書き出し、ローカルサーバー等で表示できる形）にする。
     artifact-designスキルは「参考にする原則の出所」であって「実行する仕組み」
     ではない。
   - **レイアウトは都度変えず、毎回固定にする。** 都度artifact-design的に
     作り変える（本来のartifact-designの動作モデル）と、人間の認知負荷という
     観点でむしろ表示のばらつきが生まれる。一貫したレイアウトの方が人間が
     素早く読める。
   - ただし「固定」は「全schemaで1種類のテンプレート」という意味ではない。
     **対象の性質ごとに専用HTMLテンプレートを持つ**（例: バックエンド系の
     HandoffはバックエンドらしいHTML、フロントエンド系はUIイメージを含んだ
     HTML、プラットフォーム系はプラットフォームらしい書式のHTML）。
   - 結論: artifact-designの原則（トークン設計・ライト/ダークテーマ対応・
     CSP自己完結でのインライン化等）は「都度考え直すプロセス」としてではなく、
     **schemaのkind（種別）ごとに人間が一度だけ設計して固定化した静的CSS/
     レイアウト資産**として取り込む。既存kind discriminatorパターンにそのまま
     乗る形になり、renderの決定論性（同じcontentから同じHTMLが出る）を保った
     まま人間向けの見やすさを両立できる。

### 論点6の続き: プロトタイプ評価で判明した本質（2026-07-14〜15）

`handoff-agg-document`を題材に実際にHTMLプロトタイプを作成し評価した過程で、
2つの重要な発見があった。

**発見1: HTML化はcontentの薄さを隠さない、むしろ検知できる。** プロトタイプを
ddd-advisor・tech-lead-advisorに見せて「実装開始に十分か」を評価してもらった
ところ、**両者とも「不十分」と判定**（[[brainstorm-qa-advisor-design]]とは別件、
本ブレスト内の実地検証）。ddd-advisorは集約構造そのもの（集約ルート・Entity/
値オブジェクトの列挙・schemaRefの参照関係・不変条件の全数対応表）の欠落を、
tech-lead-advisorは配置・依存方向のアンチパターンリスク・テスト戦略・命名規約の
欠落を指摘し、対立点なく補完的に「不十分」の結論に一致した。**HTMLのレイアウトは
advisorの判定に影響しなかった**——両者とも見た目ではなくcontentの中身を見て
判断している。これを踏まえ、v2プロトタイプでは「レビュー状況パネル」
（想定advisorのうち実際に参加したのは誰か）と「制約ブロックの空欄明示」を追加し、
**情報の薄さそのものを人間が一目で検知できる**方向にレイアウトを倒した。

**発見2（本質的な動機の確認）: そもそもの問題は「人間がspecを読まなくなった」
こと。** ユーザーより: 従来Markdown/document.jsonはAIの理解しやすさを優先して
書かれてきたため、人間側の認知負荷がかなり上がってしまい、**人間がspecを見て
確認するという行為自体が失われた**。結果、実装が終わるまで何が出来上がるのか
人間がイメージできない状態になっていた。HandoffはSpec→実装の橋渡しという
重要な役割を持つため、ここで人間が認知しやすい形の情報を提示できれば、
「実装に進めてよいか」の判断を人間の手に取り戻せる。

**発見2から導かれた、Handoff HTMLに必要な要素（プロトタイプ未反映、次の
作業対象）:**
1. 要約（決まったことを1〜2文の平易な言葉でまとめる。advisorの生テキストの
   羅列ではなく合成する）
2. **完成イメージ**（実装後どんな形になるかを、文章ではなく視覚的に示す）
3. レビュー状況（v2プロトタイプで実装済み）
4. 決定事項／要検討事項の分離（advisor批評で指摘された欠落を「要検討」として
   明示的に分けて見せる）
5. 制約・トレードオフ（v2プロトタイプで実装済み、空欄明示）
6. 判断の材料としての結び

**発見3（論点6のkind分けの根拠が具体化）: 「完成イメージ」の表現形式は
領域ごとに本質的に異なり、Markdownでは原理的に表現できないものがある。**
これはkind別テンプレートが必要な理由を「見た目のバリエーション」から
「情報表現そのものの必要条件」へと強化する発見。

- **Backend/Domain系**（DomainSpecSchemaのaggregate等）→ 完成イメージは
  構造図（集約ルート・Entity・値オブジェクトの関係図、Mermaid等）
- **Frontend/UI系**（PresentationSpecSchema）→ 完成イメージは実際のUI
  イメージそのもの。これはMarkdownでは原理的に表現できず、HTMLでなければ
  成立しない
- **Platform系**→ 完成イメージはインフラ・アーキテクチャ図

**未着手・次の作業:** 「完成イメージ」（発見2の要素2）を描くには、content側
（`handoff-agg-document.json`）に構造情報（集約ルート・Entity/値オブジェクトの
列挙等）が今無いと描けない。つまり**advisor批評で指摘されたcontent補完
（8項目）を先に行い、それを反映した形でHTML v3を作り直す**、という順番になる
ことが確定した。

### 論点6のデザイン確定（2026-07-15）

Backend系（`handoff-agg-document`、実例）とFrontend/UI系（`handoff-uc-review-
dashboard`、架空の例）の2つのHTMLプロトタイプを作り、ユーザーの確認を得て
**デザイン方針を確定**した。

- 共通トークン（暖色系ニュートラル＋アンバーアクセント、system-uiフォント
  スタック、ライト/ダーク両対応）は両kindで共有
- kindごとに異なるのは「00. 完成イメージ」セクションの表現のみ:
  Backend/Domain系は集約構造の模式図（確定済み=実線囲み／未確定=破線囲みの
  ボックス図）、Frontend/UI系は低精度ワイヤーフレーム（配色・文言はあえて
  未確定のまま、レイアウト意図だけを示す）
- **content補完前でも「完成イメージ」セクションは価値を持つ**ことが判明した:
  `handoff-agg-document`のv3プロトタイプでは、まだcontent補完前の状態でも
  「確定済み/未確定」を模式図として示し、さらに設計観点・実装観点の各セクションに
  advisor指摘8項目を「要追記」の破線カードとして追加することで、**contentの
  薄さを視覚的に検知する仕掛け**として機能させた（発見1の実装）
- ユーザー確認済み（「かなりいい感じです」）。このデザイン方針で確定とする。

### 論点6のさらなる更新: ux-advisorレビュー→タブ化/Mermaid風フロー図へ転換（2026-07-15）

`handoff-agg-document`のcontent補完後、ux-advisorに実際のHTML（style込み）を渡して
レビューを依頼したところ、6件の指摘が返った（結論バナーの埋没・セクション番号の
不整合・判断カードと参照表の視覚的混在・矢印の描き忘れ・空欄文言の内部用語露出・
機能していない凡例）。全て反映し、CSS箱組み図はそのまま維持する形でv6を確定した。

その後ユーザーから「サンプルでもいいのでタブ化とMermaid風の表現も見たい」と
リクエストがあり、比較用サンプルを別途作成（CSS-only タブ＋手描きSVGフロー図、
関係の無いノードには矢印を引かず点線で区切ることで「矢印の描き忘れ」問題を
構造的に起こりにくくした）。ux-advisorは項目数が少ない現状ではタブ化を
非推奨としていたが、**ユーザーが比較の結果サンプル側を明確に支持**
（「全然こっちの方がいいです」）したため、advisorの推奨より人間の主観的な
読みやすさの判断を優先し、この方向で正式版に統合した。

**確定した最終構成**: 00 完成イメージ（SVGフロー図・矢印で実依存関係のみ描く）
→ 01 レビュー状況（advisorカバレッジ、変更なし）→ 02 設計観点・実装観点・制約
（タブ化、CSS-only radio+label方式でJS不要・キーボード操作対応）。

**教訓:** advisorの原則ベースの推奨（通読型 vs タブ化の判断基準）は、あくまで
一般論としての判断材料であり、実際に両方を見比べた本人の体感が異なれば
本人の判断を優先してよい——advisorは「評価はするが最終決定はしない」という
既存の役割分担（[[brainstorm-qa-advisor-design]]の「QAの職責範囲」節と同じ
構造）が、ux-advisorでも同様に機能した実例。

**2026-07-18追記:** [[brainstorm-handoff-document-purpose]]でのデザイン
確定作業中、「00 完成イメージ」の意味（対象成果物の構造・振る舞い図であり、
プロセスの現在地ではない）が本節の確定内容から逸脱して試作されるという
ミスが発生し、訂正された。詳細は同ブレストの「訂正: 『00 完成イメージ』の
意味の取り違え」節を参照。

---

## 完了済み: 論点6のプロトタイプ検証（2026-07-14〜15）

`handoff-agg-document`のcontent補完（ddd-advisor/tech-lead-advisorが指摘した
8項目を実コード調査の上でdesignViewpoints/implementationViewpointsに追記）、
それを反映した完成イメージ（当初CSS箱組み→ux-advisorレビュー→最終的に
Mermaid風SVGフロー図＋タブ化で確定）まで完了。詳細は上記「論点6のさらなる
更新」節を参照。

---

## 論点9: advisor-followupをskill-routerへ一般化（2026-07-15、設計中）

`handoff-agg-document`の議論から派生し、4役割Skill（論点4）とadvisorの結合点
（論点2）をどう設計するかを詰める過程で、当初「advisor-followup Skill」と
呼んでいたものが、より一般的な**skill-router**という概念に収束した。

### 経緯（訂正の連鎖）

1. 当初案: CLAUDE.mdのSkillフォローアップ表に「role skillの後、advisor-followup
   を呼ぶ」という規則を書く → ユーザー指摘「順番がおかしくないか」。DDD設計判断
   （集約境界等）は執筆後の批評ではなく、**執筆前に判断材料として必要**。
   実際`handoff-agg-document`もこの順（advisor相談が先、content執筆が後）で
   作られていた。
2. 訂正案: role skill自身の手順内で「執筆前にadvisor-followupを呼ぶ」ステップを
   内蔵する → ユーザー指摘「それはSkillのフォローアップをrole skillに外出しする
   ことになり、Skill同士が互いを呼ぶ構造になる」（CLAUDE.mdの既存原則
   「advisorが互いを呼ぶのではなくOrchestrator側が組合せを判断する」に反する）。
3. 再訂正: **CLAUDE.md（Orchestrator）が、role skillとadvisor-followupの
   呼び出し順序そのものを決める**。role skillもadvisor-followupも互いの存在を
   知らないまま、CLAUDE.mdが「まずadvisor-followupを呼び判断材料を集め、その
   結果をrole skillへの入力として渡す」という配線を持つ。
4. **一般化への気づき（ユーザー発案）**: advisor-followupの内部は「他Skillの
   名前を記載したルーティング表」を持つ、意図的に結合度の高い唯一のSkillである。
   この「1つのブローカーSkillだけがルーティング表を持ち、CLAUDE.md自体は
   『まずこれに聞け』の1行で済む」という構造は、Waffle固有ではなく**汎用的な
   CLAUDE.mdアーキテクチャパターン**として成立する。名称を`advisor-followup`
   から**`skill-router`**に変更。
5. **schema化の要否**: skill-routerが持つルーティング表は「document管理対象」
   （Waffleで機械的にquery/validate可能にすべき）と判断。新schema家族を作らず、
   既存`SkillSchema`を拡張する方向で検討 → `skillKind`enumに`router`を追加し、
   専用の`RouterContent`（既存`CustomContent`とは別の、絞られた必須ブロック
   構成）を持たせることで確定（「router」の名称は「コンポジションルートの
   仕事＝文脈に応じてどの実装を配線するか決めること」に最も近いという理由で
   `broker`より優先された）。

### routingTableの構造（確定、2026-07-15）

**エントリが存在する条件**: そのSkillが**単独では目的を完結できない**場合のみ。
単独で完結するSkill（例: Investigation）にはエントリが存在しない——「表に
無いことが正常」なケースがある。

**列構成:**

| 列名 | 意味 |
|---|---|
| `skill` | 単独では完結しないrole skill名 |
| `purpose` | どんな目的（schemaRef等）の時に併用が必要か |
| `combinedSkills` | 併用が必要なSkill（**必ずadvisor種別のみ**、後述のガードレール参照） |
| `strength` | block（必須）／nudge（推奨）——qa-advisor設計時に出た「advisorごとに
  強制力が異なる」という論点と同型 |

**具体例（実データで確認済み）:**

| skill | purpose | combinedSkills | strength |
|---|---|---|---|
| Spec-authoring | DomainSpecSchemaのdocument作成 | ddd-advisor, tech-lead-advisor | block |
| Spec-authoring | CodingSchema（tech-stack/architecture/coding-standard） | tech-lead-advisor | block |
| Spec-authoring | CodingSchema（test-standard） | tech-lead-advisor, qa-advisor | block |
| Spec-authoring | PlatformSpec | platform-advisor | block |
| Spec-authoring | PresentationSpecSchema | ux-advisor | nudge |
| Handoff-authoring | HandoffSchemaのdocument作成 | （前段階Spec-authoringで実際に参加したadvisorを動的に引き継ぐ。固定リストではない） | block |
| Implementation | 実装 | （Handoffのdesign/implementationViewpointsに記録されたadvisorを動的に引き継ぐ。固定リストではない） | block |

**行数の非対称性（重要な発見）:** Spec-authoringはschemaRefの数だけ行が増える
（schema家族が増えるたびに新しいpurpose行が要る）が、Handoff-authoring/
Implementationは**常に「前段階の実際の参加者を引き継ぐ」という1つの固定
ルールで済み、schemaRefごとに行を増やす必要が無い**。Investigationは0行。

**ガードレール（ユーザー確定、2026-07-15）: `combinedSkills`に入るのは常に
`skillKind: advisor`のSkillのみ。** role skill同士・role skillと他custom skill
の組み合わせはこの表では扱わない。そのような併用が必要になった場合は、表に
逃がさず**Skillの境界の切り方自体を疑う**（分割が細かすぎる設計ミスのサイン）。
これによりskill-routerが「なんでも組み合わせられる汎用配線盤」に肥大化する
ことを防ぐ。

### 論点9の実装完了（2026-07-17）

- `patch-schema`に`add_def`/`add_kind_branch`の2操作を新設（TDD、spec先行）。
  既存4操作（add_block/rename_block/set_field/remove_block）はいずれも
  「既存content defへの追加・改名・単一フィールド書き換え・除去」しか
  できず、新しいkind（discriminator値）そのものの追加はできなかったため。
  `add_def`は既存content defへの紐付けを持たない独立した新規`$defs`エントリ
  を追加する。`add_kind_branch`はdiscriminatorフィールドのenumに新しいkind値
  を追加し、ルート直下のkind分岐（if/then/else形式・allOf形式）に新しい
  ブランチを追加する（if/then/elseの2値限定二分岐は、3値目を追加する際に
  enumから暗黙のelse値を逆算しつつallOf形式のN分岐へ正規化する）。
- `SkillSchema/v1`に`skillKind: router`を追加。`RoutingTableBlock`
  （`skill`/`purpose`/`combinedSkills`/`strength`の4列、`purpose`は自由記述
  文字列として実装確定）と`RouterContent`（title/purpose/role/routingTable/
  guardrailsが必須）を新設。既存5 advisor Skillは全て引き続きvalidate成功
  （後方互換を実機確認済み）。
- `skill-router`自体のdocumentを作成・ACTIVE化・render/deploy済み
  （`.claude/skills/skill-router/SKILL.md`）。routingTableは本論点で確定した
  7行（Spec-authoring 5行＋Handoff-authoring/Implementation各1行の動的引き継ぎ）
  をそのまま反映。

### 執筆前／執筆後の2タイミング問題の決着（2026-07-17）

「執筆前」（判断材料収集）と「執筆後」（十分性ゲートチェック、
`handoff-agg-document`の実例で価値が確認された）という2種類のフォローアップ
タイミングは、**routingTableにタイミングを持たせない**方針でユーザー確定。

- 理由: 「いつ呼ぶか（WHEN）」は論点9の訂正の連鎖（経緯1〜3）で既に
  「Orchestrator（CLAUDE.md）の責務」と確立済みの原則であり、これを
  timing列としてskill-router側に持たせると、過去に一度否定した
  「Skillが順序を知る」構造に逆戻りしてしまう。
- 結論: routingTableは「誰と組み合わせるか（WHO）」だけを持つ。
  同じ行（同じskill/purpose/combinedSkills）を、role skillのライフサイクル
  内でOrchestratorが執筆前・執筆後の複数回にわたって呼び出してよい
  （執筆前用・執筆後用に行を分けない）。schema変更は不要。
- `skill-router`のpurpose文・guardrailsにこの原則を明記済み
  （「ルーティング表の各行は『いつ呼ぶか』を持たない」）。

### CLAUDE.md側の文言確定（2026-07-17）

「Skillフォローアップ」節に、既存のadvisor批評フォローアップ表とは別の短い
段落として追加した（表の列に混ぜなかった理由: 表の列は「呼び出した後」＝
WHEN固定の意味を持つが、skill-routerはWHO専任でタイミングを持たないため、
同じ表に混ぜると列の意味がぶれる）。

> ### document-authoring系Skill実行時の原則
>
> document-authoring系Skill（schemaRefに基づくdocument作成・実装等）を
> 扱う際は、まず`skill-router`に問い合わせ、routingTableが示すadvisorとの
> 組み合わせ（WHO）を確認する。呼ぶタイミング（執筆前の判断材料収集・
> 執筆後の十分性チェックのいずれか、または両方）はOrchestrator自身が
> 判断する。

論点9関連の未決着はこれで全て解消した。

---

## 論点10: Handoffは何を満たせば「実装に進めてよい」状態なのか（機能要件・受け入れ基準）

論点6でHTMLレイアウト（00完成イメージ→01レビュー状況→02設計観点/実装観点/制約の
タブ化）が確定し、`handoff-agg-document`で実際にレビュー済み・準備完了状態まで
到達した。しかしこれは**表示形式の確定**であり、「Handoffとして何を果たせば
完成なのか」という**機能面の定義**はまだ言語化されていない。この論点を先に
言語化しないと、次にHandoffを他usecase/アグリゲートへ横展開したとき、
毎回「どこまで書けば十分か」を都度その場で判断することになる。

### AI初期見解

**見解:** Handoffの「完成」は表示レイアウトの充足では決まらず、
(a) 想定advisor（skill-router routingTableが定めるcombinedSkills、または
Spec-authoring段階で実際に参加したadvisor）が**全員参加済み**、
(b) advisorが指摘した事項が**ゼロ、または『要検討』として明示的に残されている**
（暗黙の欠落が無い）、(c) 完成イメージが実装後の構造を一意に示せる情報量を
contentが持っている、の3条件が揃った状態として定義できる。

**根拠:**
- 論点6の発見1（`handoff-agg-document`の実地検証）で、ddd-advisor・
  tech-lead-advisorともに**HTMLのレイアウトではなくcontentの中身**を見て
  「不十分」と判定した。つまりレイアウトが整っていても中身が薄ければ
  Handoffとして機能しない、という実証済みの事実がある。
- 一方、現状の`handoff-agg-document.md`/`.json`にはレビュー状況を示す
  `reviewStatus`のような**明示フィールドがcontent自体には存在しない**。
  HTML側（artifact）だけが`coverage-panel`として参加advisorを計算・表示して
  おり、AI向けMarkdownにはこの判定結果が無い。人間がHTMLを見なければ
  「進めてよいか」が分からない状態は、発見2（人間がspecを見て判断する行為を
  取り戻す）の目的を部分的にしか達成できていない。
- Waffle自身の設計哲学（`check-schema-version-drift`等、宣言と実装の対応を
  機械的に検証するusecase群）と整合させるなら、「Handoffが完成しているか」も
  いずれ`check-handoff-readiness`のような機械判定の対象にできる方が、
  Waffiが自分自身をdogfoodする既存パターンと一貫する。今はHTML側の
  計算ロジックにしか存在しないこの判定を、contentが持つ構造化フィールド
  （参加advisor一覧・指摘の解消状態）に格上げすべきタイミングに来ている。

### ユーザー見解（2026-07-19、合意・収束）

AI初期見解の3条件を、以下の通り締める形で確定した。

**(a) 想定advisor全員参加の判定主体**: routingTableは出発点・目安に過ぎず、
最終的に「今回はこの組み合わせで足りる」と判断するのはOrchestrator（AI自身）
の裁量とする。機械的なrouting Table照合だけに委ねない。

**(b) advisorの指摘の解消**: 「要検討」のまま実装へ進むことは許容しない
（手戻りの温床になるため）。完成とは指摘が**全て解消されている**状態を指す。
ただし「既知の制約・トレードオフ」（`constraints`ブロックに書く、意図的に
スコープ外とした決着済みの判断）は「要検討＝未解決」とは別物であり、それ自体は
許容されうる。**その許容可否自体は人間が判断する**（Orchestratorが独断で
「これはトレードオフとして許容してよい」と決めてはならない）。加えて、
**トレードオフが発生すること自体をできるだけ避ける設計を優先する**——
トレードオフの記録は次善策であり、標準ルートとして頼ってはならない。

**(c) 完成イメージの充足判定**: AIの自己判定ではなく、**人間が実際に完成
イメージ（HTML）を見て理解できたと確認したこと自体**を条件とする。
「そもそもハンドオフを見て人間が理解できないまま実装に進むのは怖い」
という懸念が核心——これは論点1・論点6の発見2（人間がspecを見て確認する
という行為自体を取り戻す）と地続きの結論であり、情報量の測定問題ではなく
明示的な人間確認ステップそのものを完成条件に据える。

**確定した完成条件（最終）**:
1. Orchestratorが必要と判断したadvisorが全員参加している
2. advisorの指摘は全て解消されている（「要検討」のまま残さない）。ただし
   決着済みの既知の制約・トレードオフとして`constraints`に記録することは、
   人間の許容判断があれば例外として認められる（多用は避ける）
3. 完成イメージを人間が実際に見て理解できたことを、人間自身が確認している

**補足（デザイン要件との接続）**: [[brainstorm-handoff-document-purpose]]論点5
でのデザイン要求（認知負荷の低さ・情報整理・長文可読性）は、単なる見た目の
好みではなく、この条件(c)を実現可能にするための必須要件だった。デザインが
粗雑だと、そもそも人間が読んで理解するという行為自体が成立せず、(c)が
原理的に満たせなくなる。

---

## 論点4の実装完了（2026-07-17）

4役割Skill（investigation/spec-authoring/handoff-authoring/implementation）を
いずれも`skillKind: custom`のSkill documentとして作成・ACTIVE化・render/deploy
済み（`.claude/skills/{investigation,spec-authoring,handoff-authoring,
implementation}/SKILL.md`）。着手順はInvestigation→Spec-authoring→
Handoff-authoring→Implementation（依存関係が少ない順、ユーザー確定）。

- **advisor/skill-routerの名前を一切書かない**という設計で統一した
  （論点9で確定した「skillPreloadsの決定ロジックはSkill自体に持たせない」
  制約の具体化）。各role skillはinputExpectationで「判断材料（設計観点・
  実装観点等）が事前に呼び出し元から与えられていることを前提とする」と
  受け取るのみで、advisorやskill-routerという固有名詞・併用関係には
  一切言及しない。誰と組み合わせるか（WHO）を知っているのはskill-router
  だけ、いつ・どう組み合わせるか（順序）を知っているのはOrchestrator
  （CLAUDE.md）だけ、という3層分離が実装レベルでも保たれた。
- Investigation: routingTableにエントリなし（単独完結）を体現。判断・実装を
  一切行わず「分かったこと／分からなかったこと／根拠」の3点区別で報告する
  ことに徹する。成果物は現時点で自由形式テキスト（investigation-report向け
  TemplateSchema拡張は論点5として引き続き未実装）。
- Spec-authoring: 既存spec schemaへのscaffold create/fill→validate→render。
  判断材料が不足する箇所を自分で埋めない、という境界を明記。
- Handoff-authoring: VALIDATED以上のspecを前提に、designViewpoints/
  implementationViewpointsへ判断材料を記録する。Handoffがstatusを持たない
  助言記録であることをguardrailsに明記。
- Implementation: 唯一documentを作らず実際のソースコード実装そのものを
  成果物とする。TDD（Red→Green→必要ならRefactor）の順序をguardrailsで固定。

## 論点5の実装完了（2026-07-17）: investigationの成果物形式

4役割Skillの出力形式を洗い出す過程で、investigationの成果物（調査レポート）だけ
自由形式テキストのまま未確定であることが判明。`TemplateSchema/v1`へ
`templateKind: investigation-report`を追加し、schema管理下のテンプレート
（`分かったこと`/`分からなかったこと`/`根拠の書き方`の3ブロック）として確定した。

- `patch-schema`にさらに新操作`set_kind_render_target`を追加（TDD、spec先行）。
  `add_kind_branch`は discriminator enum とルート直下のcontent分岐（if/then/allOf）
  しか扱わず、`x-render-target.pathVars/path/deploy`という**別の**kind別dict
  （render先パスを決める）には手が届かなかったため。judgment kind（既存）と
  investigation-report kind（今回）の2実例があり、evidence-based-scopeの基準
  （実例2件以上）を満たした上での追加。
- `TemplateSchema/v1`に`FindingsGuidanceBlock`/`UnknownsGuidanceBlock`/
  `EvidenceGuidanceBlock`/`InvestigationReportTemplateContent`を追加し、
  `templateKind`のallOf分岐に`investigation-report`ブランチを追加
  （TemplateSchemaは既にallOf形式だったため、if/then/else→allOf正規化は不要
  だった）。既存5 templateドキュメント（judgment kind）は全て引き続き
  validate成功（後方互換を実機確認済み）。
- `template-investigation-report`documentを作成・ACTIVE化・render/deploy済み
  （`.claude/skills/investigation/references/template-investigation-report.md`）。
  `skillRef: investigation`により`x-render-target`のパス変数解決が正しく
  `investigation`に展開されることを実機確認。
- `investigation.json`の`references`ブロックにこのテンプレートへの参照を追加。

**副産物（並行セッションとの衝突）:** この作業中、`uc-patch-schema.json`を
別セッションも同時に編集しており、`errors.items[].condition`が配列に
ラップされて壊れる書き込み衝突が1回発生した（`create_version`操作は
その並行セッションが追加したもの）。fillの再実行で復旧したが、同一document.json
への並行編集はデータ破損リスクがあることが実地で確認された。

## 未決着一覧（次に収束させるべき論点、2026-07-17時点で更新）

論点4・論点5・論点9は完全に決着。

1. **論点6の機構詳細:** `x-render-target.formats`へのhtml追加、kind別テンプレート
   の管理方法、Handoff以外のschemaへの適用範囲 ← 次はこれ候補
2. **advisorを育てるためのSkill:** OSSとしてユーザーがadvisorを自由に定義できる
   基盤（Skill）の中身は未検討
3. **ddd-advisorの「デフォルト必須」表現:** 技術的な表現方法は未検討
4. **KnowledgeSchema→advisor Skillへのdeployのwaffle機能化:** 機構は未着手

## 次のアクション

論点4・論点5・論点9はいずれも完全に決着（`patch-schema`拡張[add_def/
add_kind_branch/set_kind_render_target]・`SkillSchema/v1`拡張・`skill-router`
document作成・執筆前後2タイミング問題・CLAUDE.md文言・4役割Skillのdocument
作成・`TemplateSchema/v1`のinvestigation-report kind追加、いずれも2026-07-17に
完了）。次は未決着1（論点6: Handoff HTML機構の詳細）から着手する方向。
