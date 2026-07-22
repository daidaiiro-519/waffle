# ブレインストーミング: ツール固有フォーマット規約をWaffleのどのschema/kindで管理するか

**目的:** Claude CodeのHooks/Skill/Agent、Codexのagent定義など、外部ツールが要求する
「書き方の作法（フォーマット規約）」を、実装のたびに公式ドキュメントを都度参照するのではなく
Waffle側で正式に管理する場合、既存のCodingSchema／KnowledgeSchemaのどちらに載せるべきか、
それとも新しいschema/kindを起こすべきかを決める。
**モード:** アイデア発散

**経緯:** HookSchemaのレンダリング成果物（MD）は「設計意図の記録」に留まり、実際にツールへ
配線する部分（`.claude/settings.json`のhooksセクション等）はツールごとにフォーマットが違う。
この配線フォーマット自体の知識（実装時に必ず必要になる）を、都度その場で公式ページから
解決する運用にしないなら、どこかに規約として持たせる必要があるのでは、というユーザーの
指摘から始まった。

---

## アイデアダンプ

1. KnowledgeSchemaの新規ACTIVE文書として、ツール／成果物種別ごとに1件作る
   （例: `knowledge-claude-code-hooks-format`）
2. CodingSchemaに新kind（例: `tool-integration`）を追加する
3. 全く新しいschema（例: `ToolConventionSchema`）を新設する
4. `.waffle/config.json`の`toolMappings`を拡張し、パステンプレートだけでなく
   フォーマット規約の説明文も持たせる
5. HookSchema/SkillSchema/AgentSchema自体の`x-render-target`等に、ツールごとの
   フォーマット説明を埋め込む
6. Templateの一種として、scaffold時に自動生成される雛形コメントに埋め込む
   （公式仕様が変わると陳腐化するリスクが高い）
7. 実装時にWebFetchで都度公式ドキュメントを参照する運用にし、規約化しない
   （このブレストの前提そのものを否定する対抗案として残す）
8. tech-lead-advisorのSKILL.md自体にツールごとのフォーマット知識を直接書き込む
9. `.claude/skills`配下に「tool-format-reference」という参照専用Skillを新設し、
   advisor・role skillから読ませる
10. PlatformSpecの新specKind（例: `tool-integration`）として扱う
11. CodingTemplateの`subdomainRichness`のような粒度概念を転用し、ツールごとの
    「薄い外部integration」として別区分で管理する
12. GitHubの公式リポジトリ／スキーマ定義へのリンクだけを記録し、本文は持たない
    （知識の鮮度を自前で追わない代わりに参照先だけ確定させる）

**絞り込み候補:**
- **1（KnowledgeSchemaに載せる）**: 実現性最も高い。既存メカニズム（advisor相談・
  昇格フロー）がそのまま使え、新規schema設計コストがゼロ。
- **2（CodingSchemaに新kind追加）**: 実現性は高いが、既存4kindとの意味的整合を
  慎重に検討する必要がある（後述の論点1）。
- **3（新schema新設）**: 実現性は中程度、責務分離のインパクトは大きい。
- **7（規約化しない・都度WebFetch）**: 実現性は高いが「知識を蓄積しない」という
  真逆の方針であり、比較対象として残す。

---

## 論点 1: この知識はCodingSchema寄りか、KnowledgeSchema寄りか、独立schemaが要るか

### AI 初期見解
**見解:** どちらの既存schemaにもそのまま乗せるべきではなく、まず両者の"意味の軸"の違いを
はっきりさせた上で判断すべきだと考える。現時点では、既存2schemaと少しずつ性質が異なる
"第三の軸"に見えており、無理に既存へ押し込むより新kind（CodingSchemaへの追加が現実的な
落とし所）を検討する方に傾いている。ただし確信度は高くなく、根拠を以下に示す。

**根拠:**
- CodingSchemaの4kind（tech-stack/architecture/coding-standard/test-standard）は、
  いずれも「Waffleが生成・支援する**対象コードベース**の技術選定・規約」を扱っている
  （`tech-stack`のx-prompt-writeは"identity/runtime/framework/interface/middleware/
  libraries/tooling/policy"という粒度で、対象システムの技術スタックを指す）。今回の
  対象は対象コードベースの技術ではなく、**Waffle自身の成果物を読み込むAIツール
  （Claude Code/Codex等）が要求する契約**であり、軸が一段外側にある。既存4kindの
  どれに追加するかを考えるより、5つ目のkindとして独立させる方が意味的に素直
- KnowledgeSchemaは現状、advisorが判断相談時に参照する"判断材料"（principles/
  classifications/decisionCriteria/examples/antiPatterns等）を格納する用途で運用
  されている。「settings.jsonのhooksセクションはmatcher+commandを持つ」という
  情報は、判断・トレードオフを伴う知識ではなく、**契約仕様（合っているか間違って
  いるかが機械的に決まる参照情報）**に近い。KnowledgeSchemaの器（判断基準の記述
  フィールド群）とは中身の形が合わない
- 一方で「実装時に参照する」という使われ方はKnowledgeSchemaの既存運用（tech-lead-
  advisor等が判断時に参照）と重なる部分もあり、完全に無関係とは言い切れない。
  この重なりがあるため、新schemaではなくCodingSchemaへの新kind追加という
  "半歩"の選択肢が、既存の仕組み（CodingTemplate経由の参照・スキーマ検証）を
  再利用できる分、現実的だと考える

### ユーザー見解
> 私も同じ見解ですね。waffleはエージェントによるAI駆動開発でもありますので、
> ツール特有の規約はコーディングスキーマに寄せるべきです。

### AI 再考見解
**見解:** CodingSchemaへの新kind追加に確定してよい。ユーザーの指摘で、私の初期見解の
根拠が一段強化された：私は「対象コードベースの技術 vs Waffle自身を読むAIツールの契約」
という**軸の違い**を理由にKnowledgeSchemaを消去法で除外していたが、ユーザーの指摘は
それを覆すのではなく、その軸の違いそのものを無効化する上位の前提を示している。
Waffleが前提とする開発形態がAIエージェント駆動である以上、「AIツールが要求する
成果物フォーマット」は対象コードベースにとって外部の契約ではなく、**開発の一部を
担うAIエージェントという"実行環境"自体の技術スタック**であり、tech-stack kindが
"identity/runtime/framework/interface/middleware/libraries/tooling/policy"を
記述する対象がそのまま一段広がっただけ、と捉え直せる。人間エンジニアがコードを書く
前提の開発ならCI/CDツールの設定ファイル書式を"コーディング規約"とは呼ばないだろうが、
AIエージェントが実装を担う開発では、そのエージェントが読み書きするファイル形式は
実装成果物の一部そのものであり、CodingSchemaの管轄がむしろ正しい。
**根拠:**
- 初期見解で示した「判断・トレードオフを伴う知識」対「機械的に正誤が決まる契約仕様」
  というKnowledgeSchemaとの形の不一致は変わらず有効であり、この点でもCodingSchema
  （ルール・規約を記述する器）の方が形が合う
- ユーザーの指摘により、CodingSchemaへの追加が単なる「実現性を優先した妥協」では
  なく、「AI駆動開発ではツール規約こそがコーディング規約である」という積極的な
  理由付けに格上げされた

### 合意決定
**決定:** ツール固有フォーマット規約は、CodingSchemaに新kindを追加する形で管理する
（KnowledgeSchema・独立schema新設・都度WebFetch解決のいずれも不採用）。
**理由:** Waffleが前提とするAIエージェント駆動開発では、AIツールが要求する成果物
フォーマットは対象コードベースにとっての外部契約ではなく、実装を担うエージェントの
実行環境の技術スタックそのものであり、tech-stack的な性質を持つ。KnowledgeSchemaが
持つ判断材料的な形（principles/antiPatterns等）は今回の「機械的に正誤が決まる
契約仕様」には合わない。
**次のアクション:** 新kindの名称・スコープ（tech-stackとは別kindにするか、
tech-stack kindの記述対象を拡張するか）を論点2として検討する。

---

## 論点 2: 新kindの名称・スコープをどう決めるか（tech-stack kindを拡張するか、別kindを新設するか）

### AI 初期見解
**見解:** tech-stack kindの記述対象を拡張するのではなく、5つ目の新kind（仮称
`tool-integration`）として独立させるべきだと考える。

**根拠:**
- **カーディナリティが噛み合わない。** tech-stackは通常「1製品につき1つの一貫した
  スタック像」を記述する単位（identity/runtime/framework/...という単一のナラティブ）
  だが、ツールフォーマット規約は「外部ツール1つにつき1つの契約」（例:
  `tool-integration-claude-code-hooks`、`tool-integration-claude-code-skill`、
  `tool-integration-codex-agent`）という、独立して増減する複数文書になる。これを
  tech-stackの1文書内のサブフィールドとして詰め込むと、tech-stack文書が「製品の
  スタック像」と「無関係な複数の外部契約の寄せ集め」を同時に背負うことになり、
  1文書1責務が崩れる
- **内容の粒度が異なる。** tech-stackの各フィールド（identity/runtime/framework等）
  は意思決定レベルの記述（「何を選んだか」）だが、ツールフォーマット規約は
  「settings.jsonのhooksセクションはmatcher+commandを持つ」のような、選択の余地が
  ない仕様documentationに近い。同じx-prompt-writeの粒度感で両者を扱うのは無理がある
- **プリセット機構との相性が良い。** 直近で実装したCodingSchemaのpreset/product-
  document分離（`brainstorm-codingschema-preset-and-product-naming.md`）の教訓が
  そのまま当てはまる。ツールフォーマット規約は対象コードベースの言語・stackに
  依存せず（Claude Code Hooksの契約はPythonでもTypeScriptでも同じ）、むしろ
  tech-stackよりもさらに「製品非依存の汎用知識」という性質が強い。tech-stackの
  一部として埋め込むと、製品ごとにこの契約を重複して持つ・更新し忘れるという、
  まさにpreset分離で解決したのと同じ問題を再発させる。独立kindにしてpreset的に
  1つだけ持たせる方が自然

**新kind名の案:** `tool-integration`（Waffle成果物が消費される外部ツール側の契約、
という意味を素直に表す）。他候補として`tool-contract`・`agent-runtime-format`も
検討の余地あり。

### ユーザー見解
> いいと思いますね

### AI 再考見解
**見解:** 初期見解のまま確定してよい。カーディナリティ（1製品1像 vs 1ツール1契約）・
粒度（意思決定 vs 仕様documentation）・preset機構との相性（言語・製品非依存）の
3つの根拠はいずれも独立に成立しており、ユーザーの合意で覆すべき対抗意見も出て
いないため、再考の余地なく初期見解を採用する。

### 合意決定
**決定:** ツール固有フォーマット規約は、CodingSchemaの5つ目の新kind
`tool-integration`として独立させる。tech-stack kindの拡張は行わない。
**理由:** カーディナリティ（1製品=1スタック像 vs 1外部ツール=1契約）・記述粒度
（意思決定レベル vs 仕様documentation）・preset機構との相性（言語・製品非依存の
汎用知識であり、tech-stackに埋め込むと重複・更新漏れを再発させる）の3点で、
既存kindへの拡張よりも独立kindの方が形が合う。
**次のアクション:** `tool-integration` kindの具体的なブロック構成を論点3として
設計する（優先度は低くないと判断し直した——名前・スコープの決定自体、実際に
1件書けるかで検証しないと合意の中身が空虚になるため、実例(Claude Code Hooks)を
当てはめながら論点3を続けて詰める）。

---

## 論点 3: `tool-integration` kindのブロック構成を、実例（Claude Code Hooks）で検証する

### AI 初期見解
**見解:** 既存4kind（特にtech-stack）のブロックパターン（Identity的な素性ブロック→
契約の実体ブロック→配線ブロック→規約ブロック→description）を踏襲しつつ、
「対象コードベースの技術選択」ではなく「外部ツールが要求する契約」という性質に
合わせて中身を作り変える。5ブロック構成を提案する。

**根拠となる実例（Claude Code Hooksで試作）:**

| ブロック | 役割 | Claude Code Hooksで埋めるとどうなるか |
|---|---|---|
| `identity` | このtool-integration文書の素性 | toolName: "claude-code"、artifactKind: "Hook"（Waffle側のどのdocumentTypeに対応する成果物の配線知識か）、officialDocRef: 公式ドキュメントURL |
| `artifactShape` | ツールが要求する成果物自体の構造契約 | 「PostToolUse hookはstdinでJSON payloadを受け取り、`hookSpecificOutput.hookEventName`/`additionalContext`（または`permissionDecision`+`permissionDecisionReason`）を持つJSONをstdoutに出力する」という、フィールド名・必須/任意を列挙 |
| `wiring` | ツール側への実際の登録方法 | `.claude/settings.json`の`hooks.PreToolUse[]`/`hooks.PostToolUse[]`が`matcher`+`hooks[].command`を持つ配列であること、matcherの正規表現の書き方、実際の設定例（code block） |
| `rules` | 配線・実装時の落とし穴・規約 | 「symlink作成をsettings.json登録より先に行う（さもないとBashが全面ブロックされる）」「1イベントに複数Hookを登録すると全て直列実行される」等、level(必須/禁止/推奨)+ruleの形（LevelEnum再利用） |
| `description` | 既存パターン踏襲 | 汎用のDescriptionBlock（他kindと共通定義を再利用） |

**この5ブロックで実際に既存知識（今回作ったdispatcher Hook等）を表現できるか机上検証:**
`artifactShape`にhookSpecificOutputの構造、`wiring`にPreToolUse/PostToolUseの
matcher配列構造とsymlink手順、`rules`に「新しい判定ロジックを持ち込まない」の
ような個別Hookのguardrailではなく「Claude Code Hooks全般に共通する配線規約」
（例: symlink順序、複数Hook直列実行）を書けば過不足なく表現できる。個別Hookの
意図・判定ロジック自体はHookSchemaの責務のままで重複しない（`tool-integration`は
「Claude Code Hooksという仕組み自体の配線契約」、HookSchemaは「個々のHookが
何をするか」という別の軸）。

### ユーザー見解
> まずこれは実装の際に参照されるものとしての認識であってますか？（→是認）
> フック自体のスクリプトはhooksスキーマが元になって作られる認識であってるかな？
> 今回のはsetting.jsonとかその辺りの実装成果物にコーディングスキーマですよね？
> （→是認。HookSchema=個々のHookの設計記録、tool-integration=ツール全体の配線契約、
> という役割分担を確認）
> ツールって言ってるのはclaude・codex・GitHub Copilot・kiroとかそういう単位です
> （→identityの`toolName`/`artifactKind`の粒度を訂正するきっかけになった）
> もう少し詰めると各ツールの各機能ですね。全てまとめて欲しい。agentsからskills,
> hooksなどそれぞれのツールで使用できる機能があると思います
> できれば全てを網羅できるような形をこのtool-integration kindとしたい

### AI 再考見解
**見解:** 初期見解の5ブロック構成（identity/artifactShape/wiring/rules/description）
は、Claude Code Hooksという1事例だけでは妥当性を検証しきれていなかった。Web検索で
Claude Code・Codex CLI・GitHub Copilot・Kiroの4ツールの機能を裏取りした結果、
10カテゴリ（常時指示ファイル／条件付き指示ファイル／Skill／Subagent・カスタム
Agent／Hook／プロンプトテンプレート／振る舞いモード切替／要件〜実装計画の構造化
（Kiro Specs）／外部ツール接続（MCP）／配布バンドル（Plugins））が実在すると判明
した。このうちKiro Specs（requirements.md/design.md/tasks.mdの3ファイル1組）と
MCP（1設定ファイル内に複数サーバーをエントリとして登録）は、`wiring`を「1ファイル
パス」前提で設計すると表現できない。`wiring`を配置エントリの配列
（`placements: [{pathPattern, mechanism, note}]`、mechanismは
directory-convention/registration-array/config-entry/single-file等）に変更する
ことで、単一ファイル系（Hook/Skill/Agent/Instructions）も複数ファイル1組系
（Specs）もレジストリ系（MCP）も同じ器で表現できる。また`identity.artifactKind`
は固定enumにせず自由記述にすべきと判断を修正する——4ツールの調査だけで10カテゴリ
見つかっており、今後も新ツール・新カテゴリの発見が続く性質のものである以上、
enumで固定すると発見のたびにschema変更（`patch-schema`）を要し、CodingSchemaの
他kindが前提とする「安定したブロック構造」という性質と合わない。
**根拠:**
- Web検索で実在を確認した10カテゴリのうち、Hook/Skill/Agent/Instructions（4種）
  は単一ファイル1エントリの`wiring`で表現できるが、Specs（3ファイル1組）・MCP
  （1ファイル内複数エントリ）は表現できず、当初のブロック設計のままでは
  ユーザーの要求（「全てを網羅できる形にしたい」）を満たせないことが実例検証で
  判明した
- `artifactShape`（フィールド一覧＋自由記述の形）は元々どの事例にも対応できる
  汎用性を持っていたため変更不要。崩れていたのは`wiring`の単一パス前提のみ
- 副次的な発見として、Claude CodeとCodexのSkillは同一のオープン標準（Agent
  Skills standard）に基づくため、SKILL.mdフォーマット自体はツール横断で共通。
  これは論点4以降（artifactShapeの再利用・参照関係）で扱う価値がある発見として
  残す

### 合意決定
**決定:** `tool-integration` kindのブロック構成を次の5ブロックとする:
`identity`（toolName・artifactKind[自由記述]・officialDocRef）、`artifactShape`
（フィールド一覧＋自由記述、複数ファイル1組・レジストリ形式の説明も含められる
自由度を持たせる）、`wiring`（`placements`配列。各要素は
`pathPattern`/`mechanism`（directory-convention/registration-array/
config-entry/single-file等）/`note`）、`rules`（LevelEnum再利用の規約列挙）、
`description`（既存パターン踏襲）。
**理由:** Claude Code Hooksの1事例だけでなく、Web検索で裏取りした4ツール10
カテゴリすべてに対して机上で当てはめ、単一ファイル系・複数ファイル1組系
（Kiro Specs）・レジストリ系（MCP）のいずれも表現できることを確認した上での
決定であり、「全てを網羅できる形にしたい」というユーザーの要求を満たす。
`artifactKind`を固定enumにしないことで、将来の新ツール・新カテゴリ発見時に
schema変更を伴わずに新規documentを追加できる。
**次のアクション:** 実際のschema変更（CodingSchemaへの`tool-integration`
kind追加、`patch-schema add_kind_branch`等）は、CLAUDE.mdのフルサイクル原則
に従い、正式なspec-authoring段階として着手する。最初の1文書は
`tool-integration-claude-code-hooks`（今回の検証で最も詳細に机上設計済み）を
候補とする。着手タイミングは次に実際にこの知識を書きたくなった時（新しい
Hook/Skill等をゼロから作る場面）とする。

**実装完了（2026-07-23）:** skill-routerのroutingTable（「技術スタック・
アーキテクチャ・コーディング規約の作成」＝tech-lead-advisor block）に従い
事前相談。tech-lead-advisorから「条件付きYes」で、(1) 5ブロックに`title`
（TitleBlock）を追加し既存4kindの「先頭に文書見出しブロックを持つ」パターンに
揃える、(2) `add_kind_branch`は`x-frontmatter`を自動更新しないため別途手動追記
する、(3) `rules`のdef名は`ToolIntegrationRulesBlock`とし既存3kindのkind専用
命名慣行に合わせる、(4) Plugins（配布バンドル）は複合artifactKindのため
今回のスコープ外とし`description`/`rules`側の自由記述に一言残すに留める、
(5) `artifactKind`表記揺れ対策（ドリフトチェッカー）は実例0件のため今は不要、
という5点の指摘を受け、全て反映した上でCodingSchema/v4へ実装（commit
`6c49527`）。最初の文書`tool-integration-claude-code-hooks`も作成・validate・
render済み。全519テストpass、check-schema-version-driftクリーン。

---
<!-- 論点4以降は「論点N」ブロックを繰り返す -->
