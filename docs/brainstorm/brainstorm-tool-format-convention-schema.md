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
<!-- 論点2以降は「論点N」ブロックを繰り返す -->
