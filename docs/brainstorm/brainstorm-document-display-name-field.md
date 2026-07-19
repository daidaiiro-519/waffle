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

### ✏️ あなたの考え・反論・追加情報

_（ここに書いてください）_

---

## 論点2: DomainSpecSchemaのsubdomain/bounded-contextに独立フィールドを足すべきか

aggregate（`AggregateRootBlock.name`）・usecase（`NameBlock.operationName`）
と違い、subdomain・bounded-contextは表示名がTitleの説明文に埋め込まれる
だけで、独立して参照（例: 他specから`{name}`のように引用）することができない。
一貫性を取るなら、subdomain/bounded-context用にも同様の独立フィールドを
足すべきか。

### ✏️ あなたの考え・反論・追加情報

_（ここに書いてください）_

---

## 論点3: 表示名フィールドの形式・命名

DomainSpecSchema v5/v6が採用した「業務語彙の説明：識別子」という複合形式を
他schemaにも展開するのか、それとも単純な「表示名」1フィールドとして別途
持たせるのか。既存のDomainSpecSchemaパターンとの一貫性 vs 各schemaの性質に
応じた形式、のどちらを優先するか。

### ✏️ あなたの考え・反論・追加情報

_（ここに書いてください）_
