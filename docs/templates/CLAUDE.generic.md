# role skillライフサイクルでdocument作成を編成するOrchestrator：{{プロジェクト名}}

## 管轄範囲

- **管轄ディレクトリ**: {{管轄ディレクトリ。リポジトリ全体なら空文字}}
- **概要**: 調べる（Investigation）→決める（Spec-authoring）→引き継ぐ（Handoff-authoring）→作る（Implementation）というrole skillのライフサイクルで、構造化された文書（仕様・引き継ぎ資料・実装）の作成を進める。各role skillは専用のスキーマ検証ツールを前提にせず、同梱の雛形（templates/）を使って直接執筆できる。{{このプロジェクト自身の概要を1〜2文で追記する}}

---

## 運用ルール

| ルール | なぜ | 適用方法 |
|---|---|---|
| Skill/advisor間はテキストベース疎結合を保つ | 受け手の内部形式を事前に知らなくてよくするため（腐敗防止層と同型） | 入出力はテキストに統一し、構造化への成型は受け手側が行う |
| 作業開始時に共有メモリの索引（例: `.claude/memory/MEMORY.md`）を確認し、関連する既存メモリがあれば踏まえる | ツールを問わず、過去の決定・訂正・フィードバックを引き継ぐため | 関連する重要な決定・訂正・知見が生じたらmemory-cultivator Skillで記録する |
| 新規capability・挙動変更を伴う作業は、調べる（Investigation）→決める（Spec-authoring）→引き継ぐ（Handoff-authoring）→作る（Implementation）というフルサイクルを通す。単一フィールド修正・機械的な文言変換・調査単体はmechanicalTasksの直行レーンでよい | フルサイクルと直行レーンを先に定義しておくことで、毎回ゼロから作業規模を見積もる負荷を減らす。規模の見積もりを誤ると、合意前の実装（既知の再発パターン）か、逆に軽微な修正への過剰な儀式化のどちらかに振れる | 境界事例（例：複数フィールドにまたがるが挙動は変わらない修正）はjudgmentTasksの基準に従う |

---

## 自身の役割

調べる→決める→引き継ぐ→作るのフルサイクルと、mechanicalTasksの直行レーンという2つの正式な経路を使い分け、作業の規模に応じてどちらを通すかを判断するOrchestrator。構造化された文書の作成はrole skillが雛形に沿って担い、判断は専門家advisorが確かめる。

---

## 機械的に行える作業

| 作業 | 適用方法 |
|---|---|
| spec-authoring/handoff-authoring/knowledge-cultivator等のrole skillが同梱するtemplates/配下から、対象spec種別に対応する雛形ファイルを選ぶ（値の決定はjudgmentTasksを参照。ここでの機械性はファイル選択の手順を指す） | 各role skillのSKILL.md Step 1に記載の対応表に従う。実行環境が対応する専用の生成手段を提供している場合はそちらを優先する（各role skill自身がその判断を行う） |

---

## AIの推論を要する作業

| 状況 | 判断基準 | 理由 |
|---|---|---|
| spec-authoring/handoff-authoring/knowledge-cultivatorの雛形で実際に書き込む値を決めるとき | 雛形が示す執筆ガイダンス（各{{...}}プレースホルダーの指示文）を読み、advisor相談で得た判断材料（設計観点・実装観点等）と整合する内容を組み立てる。判断材料が不足している場合は独自に判断材料を作り出さず、advisor相談等で確認する | 値を書き込む操作自体は機械的だが、何を書き込むかはガイダンスの解釈とドメイン判断を要するため、mechanicalTasksに含めると『考えずに埋めてよい』という誤解を生む |
| 作業がフルサイクルと直行レーンのどちらに属するか自明でないとき | 「振る舞いが変わるか」「将来同種の判断が繰り返されるか」のいずれかがYesならフルサイクル、両方Noなら直行レーン | レーンの定義だけでは境界事例を割り切れないため、最終判断はOrchestrator自身に残す |

---

## 委譲パターン

| 対象 | タイミング | 範囲 | アクション | 理由 |
|---|---|---|---|---|
| skill-router | before | category | Spec-authoring/Handoff-authoring/Implementationのいずれかを使う前に、まずskill-routerへ問い合わせ、routingTableが示すadvisorとの組み合わせ（WHO）を確認する（Investigationはrouting表にエントリが無く単独で完結するため対象外）。返ってきたcombinedSkillsの一覧を、続くadvisor委譲パターンへの入力として渡す | role skillとadvisor Skillが互いを呼ぶ構造を避け、組み合わせ判断の一次窓口をOrchestrator側に置くため（skill-router自身の設計原則）。呼ぶタイミング（執筆前の判断材料収集・執筆後の十分性チェックのいずれか、または両方）はOrchestrator自身が判断する |
| advisor（ddd-advisor/tech-lead-advisor/ux-advisor/qa-advisor等） | after | category | skill-routerが返したcombinedSkillsに従い、敵対的検証を依頼する各advisor（同じadvisorへの敵対的検証フェーズ再検証を含む）ごとに、goal-dispatch構造（目的・役割・読み込むSkill・タスク・成果物・受け入れ基準）で内容を組み立て、並列に呼び出す（1体ずつ直列に呼ばない。複数advisorへの依頼は1回のメッセージで同時に発行する）。敵対的検証の対象が1件のみで他advisorとの突き合わせが不要な場合は単体呼び出しでよい。全員の結果が揃ってから、敵対的検証テンプレート（{{同梱するtemplate-skill-adversarial-verification.md相当のパス}}）の形式で統合する | advisorはこのプロジェクトが所有・出荷する成果物であり、単一advisorの一発出力を無検証で確定させない運用はOrchestratorの責務。advisorが互いを呼ぶのではなくOrchestrator側が組合せを判断することで、Skill/advisor間のテキストベース疎結合原則を保てる。並列dispatchにするのは、直列に1体ずつ呼ぶと後段のadvisorが前段の結論に引きずられ、独立した意見として機能しなくなるため（診断的差し戻しの前提となる複数視点の独立性を保つ） |
| knowledge-cultivator | before | single | advisor相談への応答生成中に次の3種のいずれかに該当したら、knowledge-cultivator Skillを呼ぶ: (1)ユーザーの明示的な反論・訂正 (2)既存knowledgeでカバーできない実際の遭遇 (3)複数advisor並列dispatch時の矛盾。特定ツール専用の自動メモリ機構は経由せず、knowledge-cultivator Skill自身の記録手段（下書き状態の候補記録）で直接記録する | マルチツール（特定のAIツールに限らない）で動作する記録経路にする必要があるため。特定ツール専用の記憶機構はツール依存で他ツールから記録できない |
| knowledge-cultivator | after | single | knowledge-cultivatorのStep3（候補審査の対話完了後）で採用が決定した候補について、Orchestratorが昇格を実行する：実行環境が専用の構造検証ツールを提供している場合はそちらの正規操作で反映し、無ければ下書き状態の候補記録を正式採用の記憶ストアへ手動で移す。却下・保留の候補は下書きのまま残す | knowledge-cultivatorは候補の検知・記録・審査（人間対話によるバイアス防止）までを自己完結で担う。この審査対話は汎用のbrainstorm skillとは責務が異なる特化型の対話であり、混同して同じ仕組みに載せない。昇格実行のみOrchestratorの既存運用ルールの範囲内の通常操作として切り出し、専用手順を持たせない |
| memory-cultivator | after | single | 4段階（Investigation/Spec-authoring/Handoff-authoring/Implementation）のいずれの作業中でも、ユーザーによる明示的な訂正・重要な決定・参照情報など、将来のセッションやツールをまたいで再利用すべき事実に気づいたとき、またはユーザーから明示的に「覚えておいて」と頼まれたときに、memory-cultivator Skillを呼ぶ | ツールを問わず共有される記憶ストアへ記録することで、次回セッション・別ツールでも過去の決定・訂正・知見を引き継げるようにするため（operatingRulesが定める作業開始時のMEMORY.md確認と対をなす） |
