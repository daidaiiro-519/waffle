# ブレスト: document.jsonの人間向け表示名フィールド

**目的:** documentId（kebab-case英語識別子）とは別に、人間が読んで理解できる
表示名を持つフィールドを、Waffleのdocument.jsonモデルに導入すべきかを検討する。
**モード:** アイデア発散
**作成日:** 2026-07-19
**経緯:** [[brainstorm-handoff-document-purpose]]で「ブレスト→specハンドオフ」
のプロトタイプを作成する過程で、DDD配置図（bounded-context/subdomain/
usecase等）にdocumentIdをそのまま表示していたところ、「サブドメインや集約
等がdocumentIdなのは分かりづらい、普通は日本語ではないか」という指摘を受けた。
調査の結果、DomainSpecSchema/v5・v6は既に対応済み（Titleブロックが
「業務語彙の説明：識別子」形式を要求し、実データにも
「開発フローのフェーズ遷移を機械的に判定するサブドメイン：sd-flow-gate」の
ように反映されていた）と判明。一方、他の8schema（AgentSchema/CodingSchema/
HandoffSchema/KnowledgeSchema/PresentationSpecSchema/SkillSchema/
TemplateSchema/PlatformSpec）は全てTitle=documentIdのままで、人間可読な
表示名を持つ場所自体が無いことも判明した。

---

## 調査結果サマリー（investigation Skillで実施済み、2026-07-19）

対象16schemaファイルを全数調査。

**Title=documentIdパターン（人間可読な表示名なし）**:
AgentSchema v1/v2/v3、CodingSchema v2、DomainSpecSchema v2/v3/v4、
HandoffSchema v1、KnowledgeSchema v1/v2、PresentationSpecSchema v1、
SkillSchema v1、TemplateSchema v1、PlatformSpec v1（x-prompt-write自体が
未設定で実質「指示なし」）

**人間可読な名前を別途持っている**:
- DomainSpecSchema v5/v6のみ、Titleブロック自体が「業務語彙の説明：識別子」
  形式の独自指示（specKindがbounded-context/subdomain/aggregateなら
  種別語を末尾に含める）
- DomainSpecSchema全バージョン共通で、specKindがaggregateなら
  `AggregateRootBlock.name`、usecaseなら`NameBlock.operationName`という
  構造化フィールドが別途存在する

**確認できていないもの**: DomainSpecSchema v5/v6でも、subdomain・
bounded-contextについては人間可読な名前がTitleブロックの説明文中に
埋め込まれる形式のみで、独立した構造化フィールド（aggregateのnameや
usecaseのoperationNameに相当するもの）は無い。

---

## 論点1: 現在Title=documentIdの8schemaすべてに表示名フィールドが必要か

Handoff HTML render機構（[[brainstorm-advisor-di-and-subagent-roles]]論点6）
やブレスト→specハンドオフのような人間向け成果物を今後増やす計画がある以上、
最低限HandoffSchemaには必要になる見込み。他のschema（Agent/Coding/
Knowledge/PresentationSpec/Skill/Template/PlatformSpec）は、そもそも
人間向けにレンダリングして見せる機会があるかどうかで必要性が変わる。

### 収束（最終確定・2026-07-19、ユーザーによる訂正あり）

advisor相談では「HandoffSchemaのみ今すぐ、他は必要が具体化してから」という
慎重論で一致したが、これは**「まだレンダリングされていない」という前提が
事実誤認だった**ためユーザーが訂正した。

**訂正後の基準**: 「人間向けレンダリング要件が具体的に発生した時点で」ではなく、
**「schemaRefに`x-render-target`が既に定義されている（＝既に人間が読む成果物
としてレンダリングされる）かどうか」**を客観的な基準にする。レンダリング対象は
すべてこの表示名でレンダリングする。documentIdは変わらず内部的に持ち続ける
（識別子としての役割は維持、表示にだけ使わない）。

調査した結果、対象8schema全てに既に`x-render-target`（formats: ["md"]）が
定義済みだった:

| schema | formats | deploy |
|---|---|---|
| AgentSchema/v2 | md | orchestrator→CLAUDE.md/AGENTS.md、subagent→なし |
| CodingSchema/v2 | md | なし |
| HandoffSchema/v1 | md | なし |
| KnowledgeSchema/v2 | md | `.claude/skills/{skillRef}/references/knowledge/{documentId}.md` |
| PresentationSpecSchema/v1 | md | なし |
| SkillSchema/v1 | md | `.claude/skills/{documentId}/SKILL.md` |
| TemplateSchema/v1 | md | judgment/investigation-report→`.claude/skills/{skillRef}/references/{documentId}.md` |
| PlatformSpec/v1 | md | なし |

**結論: 全8schemaが対象**（Waffleのdocument.jsonモデルは実質全schemaが
既にMarkdown成果物としてレンダリングされる設計だったため）。
advisorの「evidence-based-scope」的判断自体は原則として妥当だが、
今回は前提事実（レンダリング済みかどうか）の確認不足によって保守的すぎる
結論に至っていた、という教訓が残る。

---

## 論点2: DomainSpecSchemaのsubdomain/bounded-contextに独立フィールドを足すべきか

aggregate（`AggregateRootBlock.name`）・usecase（`NameBlock.operationName`）
と違い、subdomain・bounded-contextは表示名がTitleの説明文に埋め込まれる
だけで、独立して参照（例: 他specから`{name}`のように引用）することができない。
一貫性を取るなら、subdomain/bounded-context用にも同様の独立フィールドを
足すべきか。

### 収束（合意・実装完了、2026-07-19）

合わせるべき、と合意。あわせて`content.name.operationName`（usecase）という
既存の命名自体も「ブロックキーが`name`なのに中の値が`operationName`で
意味が読み取りにくい」という指摘を受け、`content.usecase.operationName`へ
改名した。最終的な統一パターン:

- `content.aggregateRoot.name`（既存・不変）
- `content.usecase.operationName`（`content.name.operationName`から改名）
- `content.subdomain.name`（新規）
- `content.boundedContext.name`（新規）

**必須制約の発見**: `check_backward_compatible`は「必須プロパティの追加・
除去」を、そのschema版に実際の参照文書があるかどうかを見ずに常に禁止する
（純粋なスキーマ構造の差分チェックであり、文書の実在有無を判定材料にしない）。
そのため`rename_block`のような単純なブロック改名操作は、後から使えなく
なる。正しい回避策は**`create_version`の`edits`パラメータ**——新版作成時の
編集は後方互換チェックの対象外という、ツールに元々備わっている正規の
仕組み——を使い、**新版作成の1回のcreate_version呼び出しの中に構造変更を
全部含める**こと。これにより`usecase`を引き続き必須フィールドのまま改名
できた（`subdomain`/`boundedContext`は新規追加なので任意フィールドのまま）。

**実施内容**:
1. `DomainSpecSchema/v7`を新設（v6複製＋`Name`→`Usecase`改名を`create_version`の
   `edits`に含めて実施）
2. v7へ`SubdomainBlock`・`BoundedContextBlock`を追加（任意フィールド）
3. 既存29件（bounded-context 1・subdomain 7・aggregate 2・usecase 19）を
   `migrate_schema`でv7へ移行し、usecase 19件は`content.name`→
   `content.usecase`へcontent構造を書き換え、subdomain 7件・
   bounded-context 1件に新設フィールドをbackfill
4. ソースコード側の副作用を修正: `check_operation_drift.py`・
   `check_usecase_class_drift.py`が`content.name.operationName`という
   旧パスを直書きしていたため`content.usecase.operationName`へ修正。
   関連する2テストファイルのフィクスチャも同様に修正
5. `pytest`433件全通過、`check-spec-integrity`・`check-schema-version-drift`
   とも全項目クリーンを確認

---

## 実装完了（2026-07-19）

論点3（形式は既存DomainSpecSchemaの粒度をそのまま踏襲。冗長ではないと判断
＝h1見出しとして単体表示される文脈では、kind語を含めた自己完結した説明の方が
親切）に基づき、残り7schema全てのTitleBlockへ`patch-schema set_field`で
x-prompt-query・properties.title.x-prompt-writeを追加/更新した。

| schema | kind discriminator | 対応 |
|---|---|---|
| AgentSchema/v2 | agentKind（orchestrator/subagent） | kind語を含める形式に更新 |
| CodingSchema/v2 | codingKind（4値） | kind語を含める形式に更新 |
| HandoffSchema/v1 | なし | kind語なしの形式に更新 |
| KnowledgeSchema/v2 | なし | kind語なしの形式に更新 |
| PlatformSpec/v1 | specKind（11値） | x-prompt-query/writeとも新規追加（元は完全に未設定だった） |
| PresentationSpecSchema/v1 | specKind（screen/flow） | kind語を含める形式に更新 |
| SkillSchema/v1 | skillKind（3値） | kind語を含める形式に更新 |
| TemplateSchema/v1 | templateKind（judgment/investigation-report） | kind語を含める形式に更新 |

`pytest`433件全通過を確認済み。

**既存document.jsonの一括backfillも完了（2026-07-19）**: 約100件
（agent 1・coding 9・handoff 6・knowledge 55・platform 11・skill 16・
template 6）全てのtitleフィールドを新形式で埋め直した。加えて、AgentSchemaは
並行セッションが`v3`を新設していたことが判明したため、v2に続きv3のTitleBlock
にも同じパッチを適用した（実際にdocumentが参照しているのはv3だった）。

**副作用の修正**: titleの変更によりrender結果のh1見出しが変わり、
`tests/acceptance/test_uc_render_document.py`の2テスト
（`test_検証済み_Document_を成果物に描画する`、
`test_SkillSchemaをMarkdownにレンダリングする`）が固定文字列
`"# tech-lead-advisor"`を期待していたため失敗した。これは意図した変更の
帰結なので、アサーションを新しい表示名（`"# コード配置・レイヤー境界・
依存方向の判断を担うadvisor Skill：tech-lead-advisor"`）に更新して対応した。

---

## 論点3: 表示名フィールドの形式・命名（収束済み、上記参照）

DomainSpecSchema v5/v6が採用した「業務語彙の説明：識別子」という複合形式を
他schemaにも展開するのか、それとも単純な「表示名」1フィールドとして別途
持たせるのか。既存のDomainSpecSchemaパターンとの一貫性 vs 各schemaの性質に
応じた形式、のどちらを優先するか。

### ✏️ あなたの考え・反論・追加情報

_（ここに書いてください）_
