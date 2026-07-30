# ブレスト（記録）: KnowledgeSchemaにdomain/process種別の区別を持たせる

status: 【決定済み・spec-authoring未着手】

## きっかけ（2026-07-29）

`self-improving-generation-cycle`（KnowledgeSchema/v4、status: DRAFT、skillRefs空）を実際にadvisorへ配線しようとしたところ、既存55件のKnowledge文書がほぼ全て「ドメイン専門知識」（business-domain/subdomain→ddd-advisor、tdd/test-smells→qa-advisor等）である一方、この1件だけが「advisorの批評の"やり方"やOrchestratorの進行管理の"やり方"に関わる横断的な方法論知識」で、種類が異質であることに気づいた。KnowledgeSchemaにはこの2種類を区別する仕組みが無かった。

## 決定事項（2026-07-29、ddd-advisor/tech-lead-advisorへの並列相談を経て）

- **`knowledgeKind: domain | process`は単なる分類タグとして追加する（discriminatorにしない）**。ddd-advisor・tech-lead-advisorの両者が独立に到達した結論。理由：domain/process間でKnowledgeContentの構造（principles/classifications/decisionCriteria/examples/antiPatterns/provenance/relatedConcepts）に実質差が無く、AgentSchemaの`agentKind`のような「content形状が丸ごと変わる」真のdiscriminatorとは性質が違う。`self-improving-generation-cycle`が既に単一形状のまま記録できている、という事実がこれを裏付ける。
- **process種別knowledgeのOrchestratorへの配布経路は、KnowledgeSchemaに`skillRefs`と並ぶ新規配列フィールド`agentRefs`を追加する**。AgentSchema側に`knowledgeRefs`を対称に追加する案（1回目の相談での結論）は、tech-lead-advisorの再検証（テンプレート遵守を明示させた2回目の相談）で撤回された。理由：Knowledge起点で配布先を宣言する既存の方向（`skillRefs`）と、AgentSchema起点で受け取りを宣言する方向が併存すると、「誰が配布関係を宣言するか」が2つに分裂し、配線の集約（architecture-composition-root）に反する。`skillRefs`に`"waffle"`等の特殊識別子を混在させる案（(b)）も、型の意味の一貫性が崩れるため両者から明確に否定された。
- **物理的なdeploy先**：CLAUDE.md/AGENTS.mdは単一ファイルデプロイで、Skillの`references/knowledge/`に相当するディレクトリを持たない。新規ディレクトリ（例: `.waffle/agent/references/knowledge/{documentId}.md`）を設け、canonicalな`.waffle/knowledge/{status}/{documentId}.md`からsymlinkする。CLAUDE.md本文はSKILL.mdの「参照knowledge」節と同じ形式でそこを言及する。
- **`render_document.py`の一般化**：`_resolve_tool_deploy_targets`の配列pathVar fan-out処理は現状`skillRefs`1種類のみを想定した実装（コメントに明記）だが、`agentRefs`が加わることで実例2件になり、evidence-based-scopeの一般化基準を満たす。2種類の配列pathVarを扱えるよう一般化する。
- **既存55件の移行**：`knowledgeKind`はまずoptionalで追加し、55件に`domain`、`self-improving-generation-cycle`に`process`をscaffold fillでbackfillしてvalidateを全件通す。全件backfill後に次バージョンでrequired化する2段階移行。

## 副産物：advisor委譲の忠実性問題の発見と是正（2026-07-29）

1回目のadvisor相談を`general-purpose`のAgentへ要約指示で代行させたところ、両advisorとも自身のresponseTypesが指すテンプレート構造（判断フロー・判定・推奨アクション・注意）を踏襲せず、自由な見出しで回答した。`waffle-subagent`（goal-dispatch形式の正式な受け皿）でテンプレート遵守を明示して再実行すると、tech-lead-advisorの結論そのものが変わった（AgentSchemaへの対称追加→KnowledgeSchema側への新規フィールド追加）。これは是正した：

- CLAUDE.mdの`delegationPatterns`（advisor行）に、waffleサブエージェントとして呼び出すこと・要約指示による代行はしないこと・出力をresponseTypesのテンプレート構造と照合して確認することを明記（validate/render済み）。
- `delegation-fidelity-verification`（KnowledgeSchema/v4、status: DRAFT）をknowledge候補として記録。knowledge-cultivatorの審査対象。

## 実装完了（2026-07-29）

`knowledgeKind`（分類タグ）・`agentRefs`（配列、KnowledgeSchema/v5で追加）・render engineの配列pathVar fan-out一般化（skillRefs/agentRefsの2種類同時対応）・既存66件のknowledgeへのbackfill（domain 55件・process 11件）・`.waffle/agent/waffle/references/knowledge/`への実deployまで完了。テストスイート524件パス。

process 11件の内訳：`self-improving-generation-cycle`、`delegation-fidelity-verification`（本日の副産物）、design-share由来の`knowledge-cand-*`9件（当初「既存55件は全てdomain」と誤認していたが、内容確認の結果これらも横断的な方法論知識と判明し訂正した）。

## SessionStart Hook実装完了（2026-07-29）

`.waffle/hooks/inject-process-knowledge-on-session-start.py`（hookKind: usecase-delegate、既存usecase（query-collectionのfilter_documents／queryのquery_path）の再利用のみ、新規usecaseは不要と判明）を新設し、`.claude/settings.json`のSessionStart（startup/resume/compact）に配線済み。process種別knowledge 11件の`description.text`要約を、セッション開始・再開・compact直後に自動注入する。

これにより「CLAUDE.md本文への『参照knowledge』節の追加」案は不要と結論した。当初の目的は「Orchestratorがprocess種別knowledgeの存在に気づける経路を作る」ことだったが、Hookはこれをより強い形（都度フレッシュに自動注入、内容も動的に追随）で実現しており、CLAUDE.md本文に静的な参照節を追加しても同じ内容の劣化版を二重に持つだけで機能的な上積みが無いため。
