# スキーマ駆動でDocumentを検証・生成・描画するリポジトリ全体を編成するOrchestrator：waffle

## 管轄範囲

- **管轄ディレクトリ**: waffle/
- **概要**: スキーマという型で文書を焼き上げる、構造検証＋意味ガイダンス内蔵のドキュメントエンジン「Waffle」。JSON Schemaでdocument.jsonを検証・query・render・scaffoldする。自己完結ディレクトリ（`git subtree split --prefix=waffle`で独立可能）。

---

## 運用ルール

| ルール | なぜ | 適用方法 |
|---|---|---|
| document.json操作は必ずCLI/MCP経由で行う | 自分自身がdogfood対象のため | create/fill/validate/render/query/check-*/scan-source-code/lint-docstringを使う（直接読み書きしない） |
| document.jsonのパスは`.waffle/`を使う | has-udd汎用パス（`.has-udd/`）と混在させないため | `waffle/.waffle/documents/`配下に置く |
| Skill/advisor間はテキストベース疎結合を保つ | 受け手の内部形式を事前に知らなくてよくするため（腐敗防止層と同型） | 入出力はテキストに統一し、構造化への成型は受け手側が行う |
| 作業開始時に`.waffle/memory/MEMORY.md`を確認し、関連する既存メモリがあれば踏まえる | ツールを問わず、過去の決定・訂正・フィードバックを引き継ぐため | 関連する重要な決定・訂正・知見が生じたらmemory-cultivator Skillで`.waffle/memory/`へ記録する |
| 新規capability・挙動変更・schema変更を伴う作業は、調べる（Investigation）→決める（Spec-authoring）→引き継ぐ（Handoff-authoring）→作る（Implementation）というフルサイクルを通す。単一フィールド修正・機械的な文言変換・調査単体はmechanicalTasksの直行レーンでよい | フルサイクルと直行レーンを先に定義しておくことで、毎回ゼロから作業規模を見積もる負荷を減らす。規模の見積もりを誤ると、spec合意前の実装（既知の再発パターン）か、逆に軽微な修正への過剰な儀式化のどちらかに振れる | 境界事例（例：複数フィールドにまたがるが挙動は変わらない修正）はjudgmentTasksの基準に従う |
| スキーマ構造を変えず、documentの表現レベルだけを直す修正は、必ずx-prompt-write/x-prompt-query側を先に直してからfillする。documentの値を直接書き換えて終わらせない | document側だけを直接直すと、その表現不備を生んだx-promptのガイダンスが実際に機能したかを一切検証しないまま個別修正で終わってしまう。スキーマ構造の変更を伴わない表現レベルの不備は、その定義上x-promptの記述不足のシグナルであり、documentを直接直すとこのシグナルを握りつぶし、同じ不備が他のdocumentやfill先で再発する | waffle patch-schemaでx-prompt-write/x-prompt-queryを先に修正し、その上でwaffle scaffold fillでdocument側へ反映する。document側をfillだけで直接書き換える修正はしない |

---

## 主要コマンド

| コマンド | 用途 |
|---|---|
| uv run pytest | unit/integration/acceptance/contractの4層テストを実行する |
| uv run waffle validate --path <document.jsonのパス> | document.jsonをschemaに適合検証する |
| uv run waffle render --path <document.jsonのパス> | document.jsonを成果物（SKILL.md等）へ描画し、deploy先（.claude/skills/等）へ配置する |
| uv run waffle query --operation <操作名> --path <document.jsonのパス> | document.jsonの内容を確認・検索する（get_block/get_field等16操作） |
| uv run waffle scaffold --operation create\|fill ... | document.jsonの骨格生成、および既存documentへの値の書き込みを行う |
| uv run waffle check-spec-integrity / check-scenario-drift / check-schema-version-drift | spec参照整合性・シナリオドリフト・schema版ドリフトを確認する |

---

## 自身の役割

調べる→決める→引き継ぐ→作るのフルサイクルと、mechanicalTasksの直行レーンという2つの正式な経路を使い分け、作業の規模に応じてどちらを通すかを判断するOrchestrator。構造の検証・生成・描画はWaffleが機械的に担い、判断は専門家advisorが確かめる。

---

## 機械的に行える作業

| 作業 | 適用方法 |
|---|---|
| 既存document.jsonをscaffold fillで反映する（値そのものの決定はjudgmentTasksを参照。ここでの機械性は反映操作の手順を指す） | 配列は query で現在値取得→組み立て→fill で丸ごと置き換え |
| repo rootから`uv run --project waffle waffle <command>`で呼ぶ | waffleはrepo rootとは別プロジェクトのため。deploy先パスは`waffle/`配下を明示する |
| spec-authoringの概念的な手順のうち、雛形生成・整合確認・成果物確定をWaffleコマンドへ対応させる（Skill自身にはWaffle固有の語彙を持ち込まない。対応関係はここに集約する） | 「対象spec種別の雛形を用意する」=`waffle scaffold create --schemaRef <対応するschemaRef> --discriminator <対応するdiscriminator>`（既存document更新時は省略）／「構造の整合を確認する」=`waffle validate`／「成果物として確定する」=`waffle render`。「雛形のガイダンスと判断材料に従って値を埋める」（fillの中身の決定）は機械的操作ではない（judgmentTasksを参照） |
| handoff-authoringの概念的な手順のうち、対象確認・雛形生成・整合確認・成果物確定をWaffleコマンドへ対応させる | 「対象specとの対応を確認する」=対象specのdocument.jsonのstatusが VALIDATED 以上か`waffle query --operation get_meta`で確認／「雛形を用意する」=`waffle scaffold create --schemaRef HandoffSchema/v2`（既存document更新時は省略）／「構造の整合を確認する」=`waffle validate`／「成果物として確定する」=`waffle render-handoff-template --path <documentPath> --outputPath .waffle/handoff/<documentId>.html`（**汎用の`waffle render`ではない**。HandoffSchemaは`x-render-target`を意図的に持たず、`waffle render`を実行するとNO_RENDER_TARGETエラーになる。HTML固定テンプレートのみが正しい成果物）。「受け取った判断材料を記録する」（fillの中身の決定）は機械的操作ではない（judgmentTasksを参照） |
| knowledge-cultivatorの概念的な手順のうち、記録の器の生成と昇格操作をWaffleコマンドへ対応させる | 「knowledge候補を記録する」（下書き状態の記録手段）=`waffle scaffold create --schemaRef KnowledgeSchema/v2`でstatus DRAFTのdocumentを作成（記録する内容自体の決定はjudgmentTasksを参照）／「蓄積した下書き候補を審査用にとりまとめる」=`waffle query --operation find_all`等でstatus DRAFTのKnowledgeSchema documentを洗い出す／採用決定後の正式採用への反映（このSkillの責務外）=Orchestratorが`waffle scaffold fill`でstatus ACTIVEへ変更→`waffle validate`→`waffle render` |

---

## AIの推論を要する作業

| 状況 | 判断基準 | 理由 |
|---|---|---|
| schemaに新規トップレベルキーを追加する必要が生じたとき | そのキーが本当に新規必須キー追加に該当するかを判断し、該当する場合のみEdit/Writeを許容する | fill/createは新規キーの後追いマージをしないため。check-schema-version-driftで検知されたキーのみEdit/Writeで追記する |
| spec-authoring/handoff-authoring/knowledge-cultivatorのfillで実際に書き込む値を決めるとき | 対象フィールドのx-prompt-write（執筆ガイダンス）を読み、advisor相談で得た判断材料（設計観点・実装観点等）と整合する内容を組み立てる。判断材料が不足している場合はOrchestrator自身が独自に判断材料を作り出さず、advisor相談等で確認する | fillは値を書き込む操作自体は機械的だが、何を書き込むかはx-prompt-writeの解釈とドメイン判断を要するため、mechanicalTasksに含めると『考えずに埋めてよい』という誤解を生む |
| 作業がフルサイクルと直行レーンのどちらに属するか自明でないとき | 「振る舞いが変わるか」「将来同種の判断が繰り返されるか」のいずれかがYesならフルサイクル、両方Noなら直行レーン | レーンの定義だけでは境界事例を割り切れないため、最終判断はOrchestrator自身に残す |

---

## 委譲パターン

| 対象 | タイミング | 範囲 | アクション | 理由 |
|---|---|---|---|---|
| skill-router | before | category | Spec-authoring/Handoff-authoring/Implementationのいずれかを使う前に、まずskill-routerへ問い合わせ、routingTableが示すadvisorとの組み合わせ（WHO）を確認する（Investigationはrouting表にエントリが無く単独で完結するため対象外）。返ってきたcombinedSkillsの一覧を、続くadvisor委譲パターンへの入力として渡す | role skillとadvisor Skillが互いを呼ぶ構造を避け、組み合わせ判断の一次窓口をOrchestrator側に置くため（skill-router自身の設計原則）。呼ぶタイミング（執筆前の判断材料収集・執筆後の十分性チェックのいずれか、または両方）はOrchestrator自身が判断する |
| advisor（ddd-advisor/tech-lead-advisor/ux-advisor/qa-advisor等） | after | category | skill-routerが返したcombinedSkillsに従い、敵対的検証を依頼する各advisor（同じadvisorへの敵対的検証フェーズ再検証を含む）ごとに、AgentSchemaのgoal-dispatch構造（目的・役割・読み込むSkill・タスク・成果物・受け入れ基準）で内容を組み立て、Agentツールで並列に呼び出す（1体ずつ直列に呼ばない。複数advisorへの依頼は1回のメッセージで同時に発行する）。敵対的検証の対象が1件のみで他advisorとの突き合わせが不要な場合は単体呼び出しでよい。全員の結果が揃ってから、template-skill-adversarial-verification.mdの形式で統合する | advisorはWaffleが所有・出荷する成果物であり、単一advisorの一発出力を無検証で確定させない運用はWaffle自身のOrchestratorの責務。advisorが互いを呼ぶのではなくOrchestrator側が組合せを判断することで、Skill/advisor間のテキストベース疎結合原則を保てる。並列dispatchにするのは、直列に1体ずつ呼ぶと後段のadvisorが前段の結論に引きずられ、独立した意見として機能しなくなるため（診断的差し戻しの前提となる複数視点の独立性を保つ） |
| knowledge-cultivator | before | single | advisor相談への応答生成中に次の3種のいずれかに該当したら、knowledge-cultivator Skillを呼ぶ: (1)ユーザーの明示的な反論・訂正 (2)既存knowledgeでカバーできない実際の遭遇 (3)複数advisor並列dispatch時の矛盾。Claude Code専用の`feedback_*`メモリは経由せず、`waffle scaffold create/fill`で直接KnowledgeSchema DRAFT文書として記録する | マルチツール（Claude Code以外のAIツールを含む）で動作する記録経路にする必要があるため。Claude Code専用の記憶機構はツール依存で他ツールから記録できない |
| knowledge-cultivator | after | single | knowledge-cultivatorのStep3（候補審査の対話完了後）で採用が決定した候補について、Orchestratorが通常のCLI操作（scaffold fillでstatus: ACTIVEへ変更→対象advisorへのskillRef確認→validate→render）で昇格を実行する。却下・保留の候補はDRAFTのまま残す | knowledge-cultivatorは候補の検知・記録・審査（人間対話によるバイアス防止）までを自己完結で担う。この審査対話は汎用のbrainstorm skillとは責務が異なる特化型の対話であり、混同して同じ仕組みに載せない。昇格実行のみCLAUDE.mdの既存運用ルールの範囲内の通常操作として切り出し、専用手順を持たせない |
| memory-cultivator | after | single | 4段階（Investigation/Spec-authoring/Handoff-authoring/Implementation）のいずれの作業中でも、ユーザーによる明示的な訂正・重要な決定・参照情報など、将来のセッションやツールをまたいで再利用すべき事実に気づいたとき、またはユーザーから明示的に「覚えておいて」と頼まれたときに、memory-cultivator Skillを呼ぶ | ツールを問わず共有される.waffle/memory/へ記録することで、次回セッション・別ツールでも過去の決定・訂正・知見を引き継げるようにするため（operatingRulesが定める作業開始時のMEMORY.md確認と対をなす） |
