# ブレインストーミング: advisor育成Skill（新規advisorをOSSとして自由に定義できる基盤）

**目的:** 既存5 advisor（ddd-advisor/tech-lead-advisor/ux-advisor/platform-advisor/qa-advisor）は
手作業で1人ずつ個別に作られてきた。これらを支える共通構造（backbone knowledge・
judgment template・KnowledgeSchemaからのsymlink deploy配線・AgentSchemaの
goal-dispatch構造との連携）を量産できる、新規advisor作成専用のSkillの中身を決める。
**モード:** アイデア発散

**経緯:** `brainstorm-advisor-di-and-subagent-roles.md`（2026-07-17）の「未決着一覧」に
「advisorを育てるためのSkill: OSSとしてユーザーがadvisorを自由に定義できる基盤
（Skill）の中身は未検討」として残っていた論点。2026-07-25の全ブレスト棚卸しで
再発見され、既存の汎用`skills-creator`Skillがadvisor固有の構造を一切知らない
完全汎用のフォルダ生成器であり代替にならないことを確認した上で、独立したブレストとして
起こす。

---

## アイデアダンプ

1. `skills-creator`を拡張し、スキル種別の選択肢に「advisor」を追加する
2. `skills-creator`とは別に新規の`advisor-creator` Skillを新設する
3. advisor作成を対話ヒアリング形式にし、backbone knowledge/judgment templateを順番に埋めていく
4. 既存5 advisorのdocument（`.waffle/documents/skills/*.json`）をテンプレートとして流用し、コピー＆改変方式にする
5. `TemplateSchema`に`advisor-scaffold`kindを追加し、雛形をWaffle文書として管理する
6. advisorの「専門領域」を先にヒアリングし、backbone knowledgeの収集元（既存ドキュメント・URL・ユーザーの経験）を尋ねる対話型にする
7. 既存advisorのbackbone knowledge構造を解析し、共通パターン（principles/classifications/decisionCriteria/examples/antiPatterns）を抽出してテンプレート化する
8. advisor作成をウィザード形式にせず、ミニマムなSKILL.md雛形だけ生成し、knowledge充填は後続の`knowledge-cultivator`に委ねる二段構成にする
9. `AgentSchema`のgoal-dispatch構造と`KnowledgeSchema`のsymlink配線を自動で行うCLIコマンドを新設し、Skillはヒアリングとその呼び出しに徹する
10. advisor作成に「敵対的検証」を組み込み、新規advisorのbackbone knowledgeの妥当性を既存advisorにレビューさせる
11. OSS展開を見据え、advisor定義をYAML/JSON単一ファイルにパッケージ化し、他リポジトリへのエクスポート/インポートを可能にする
12. advisorの「型」を複数用意し（技術系/ドメイン系/UX系等のプリセット）、型を選ぶだけでbackbone knowledgeの雛形が決まるようにする

**絞り込み候補:**
- **2（専用Skill新設）**: 既存の役割Skill体系（investigation/spec-authoring等が薄い専門Skillとして分離されている）と同型で、責務分離の観点で最も筋が良い
- **7（既存5 advisorからの共通パターン抽出）**: 「advisor固有の構造とは何か」を推測ではなく実データから逆算できる、最も裏付けの強いアプローチ
- **9（配線の機械化）**: KnowledgeSchema symlink・AgentSchema goal-dispatch・skill-router登録という「機械的に決まる配線」をCLI側に寄せれば、Skill側はヒアリングと判断に専念できる

---

## 論点 1: `skills-creator`を拡張するか、専用の新規Skill（`advisor-creator`）として独立させるか

### AI 初期見解
**見解:** 専用の新規Skill（仮称`advisor-creator`）として独立させるべきだと考える。

**根拠:**
- `skills-creator`のSKILL.mdを実際に読むと、「あらゆるSkill種別に共通する最小限の雛形生成（SKILL.md本体＋folder-structure判断＋テンプレート要否ヒアリング）」に責務を絞っている。advisor作成に必要な専門知識（backbone knowledge構造、judgment template、KnowledgeSchema symlink配線、AgentSchemaのgoal-dispatch連携）を混ぜ込むと、この「あらゆるSkill種別に共通」という前提が崩れ、単一責任が壊れる
- Waffleの既存アーキテクチャ判断（role skill体系をinvestigation/spec-authoring/handoff-authoring/implementationという薄い専門Skillに分離し、CLAUDE.md=Orchestratorが組み合わせを判断する）と同型のパターンを踏襲できる。「advisorという特殊なSkill種別を専門に作る知識」は、それ自体が一つの専門領域として切り出す方が一貫性がある
- OSS展開時、`advisor-creator`だけを他リポジトリへ移植・フォークする、という単位の分離がしやすくなる。`skills-creator`に混ぜると、advisor機構を持たない他プロジェクトへの移植時に不要な分岐が残る

### ユーザー見解
> この方針が正しい

### AI 再考見解
**見解:** 初期見解のまま確定してよい。対抗意見（skills-creator拡張案）を覆すだけの
根拠は出ておらず、単一責任・既存アーキテクチャとの整合・OSS移植性の3点はいずれも
独立に成立しているため、再考の余地なく採用する。

### 合意決定
**決定:** advisor育成の仕組みは、`skills-creator`を拡張せず、専用の新規Skill
（仮称`advisor-creator`）として独立させる。
**理由:** `skills-creator`は「あらゆるSkill種別に共通する最小限の雛形生成」に
責務を絞っており、advisor固有の専門知識（backbone knowledge構造・judgment
template・KnowledgeSchema symlink配線・AgentSchemaのgoal-dispatch連携）を
混ぜると単一責任が崩れる。既存のrole skill体系（investigation/spec-authoring/
handoff-authoring/implementation）と同じ「薄い専門Skillに分離する」パターンを
踏襲でき、OSS展開時の移植性も上がる。
**次のアクション:** 論点2（`advisor-creator`が生成すべきadvisor固有の共通構造を、
既存5 advisorの実データからどう逆算・テンプレート化するか）へ進む。

---

## 論点 2: advisor固有の共通構造を、既存5 advisorの実データからどう抽出・テンプレート化するか

### AI 初期見解
**見解:** 新しい抽象を発明する必要はない。共通構造は**既にSkillSchema/v2の
`skillKind: "advisor"`分岐として形式化済み**であり、`advisor-creator`の仕事は
このschemaを正しく埋めることと、schemaの外側にある3つの周辺配線（backbone
knowledge文書の作成・symlink deploy、response typeごとの判断テンプレート
ファイル、AgentSchema/skill-routerへの登録）を機械化することに限定すべきだと
考える。

**根拠（5 advisorの実データを実地確認した結果）:**
- 5つのSkillSchema document（`ddd-advisor.json`/`tech-lead-advisor.json`/
  `ux-advisor.json`/`platform-advisor.json`/`qa-advisor.json`）は全て
  `schemaRef: SkillSchema/v2`・`skillKind: "advisor"`で、content構造が
  完全に同型（`title`/`role`/`inputExpectation`/`responseTypes`/
  `knowledgeRefs`/`steps`/`guardrails`/`description`の8ブロック）。
  「advisor固有の構造」はドキュメントとして既にschema側に存在しており、
  `advisor-creator`が新規に定義するものではない
- `role`ブロックの中身にも実際のパターンがある。5つとも「{専門家役割}として、
  確立された{原則名}に基づいて回答する」という1文目から始まり、
  「アンチパターンを見つけたときはリスクと代替案をセットで提示する」
  （またはqa-advisorのように領域に応じた類似表現）で締める構成が共通している
- `knowledgeRefs`（backbone knowledge件数）はddd-advisor 19件〜ux-advisor 5件
  まで幅があり、「専門領域の広さに応じて可変」という性質を持つ。これは
  advisor作成時に固定件数のテンプレートを強制すべきでないことを示す
  （最低1件以上、という緩い制約に留めるべき）
- `references/template-*.md`（判断テンプレート）は`responseTypes`の種類数と
  対応しており、ddd-advisor（3種）・qa-advisor（3種）・tech-lead-advisor
  （1種）は個別ファイルを持つが、ux-advisor・platform-advisorは
  `knowledge/`のみで専用テンプレートを持たない。つまりテンプレートファイルの
  要否・数は`responseTypes`の設計から機械的に決まるものであり、これも
  `advisor-creator`が「ヒアリングで`responseTypes`を先に確定させ、その結果
  テンプレートが要るかどうかを判断する」という順序で扱えばよい
- 「advisorどうしの関係性の宣言」（例: tech-lead-advisorはddd-advisorの
  分類結果を入力として受け取る、ux/platform-advisorはtech-lead-advisorの
  境界判定を前提とする）は`description`フィールドの自由文で表現されている。
  これはSkillSchema側にリレーション専用フィールドが無いことを意味し、
  `advisor-creator`のヒアリング項目に「他advisorとの入出力関係」を明示的に
  含めるべきという設計上の示唆になる

### ユーザー見解
> 基本的にアドバイザー自体はアドバイザーだけで完結するように作るのが好ましい。
> 特定のアドバイザースキルに依存してるような書き方は抽象化があまい

### AI 再考見解
**見解:** 直前の初期見解の最後の箇条書き（「advisorどうしの関係性を明示的にヒアリング
項目に含めるべき」）を撤回する。これはCLAUDE.mdの既存運用ルール「Skill/advisor間は
テキストベース疎結合を保つ（受け手の内部形式を事前に知らなくてよくするため）」に
照らすと、量産すべきパターンではなく是正すべきアンチパターンだった。

実際に確認すると、tech-lead-advisor・ux-advisor・platform-advisorの3つの
`description`/`role`は、他advisorの名前（tech-lead-advisor）や専門領域固有の
成果物（DDDのサブドメイン分類）を名指しで前提条件に埋め込んでおり、受け手が
送り手の内部実装・存在を知っている状態になっている。`advisor-creator`が
この書き方をテンプレートとして教えると、疎結合違反を新規advisorに毎回複製する
ことになる。

正しい指針は「単体で完結して回答できることを前提に、追加の文脈があれば精度が
上がる場合は、その文脈の“形状”だけを抽象的に記述し、誰が生成したかには触れない」
というもの。他の発見（8ブロック構造・role定型パターン・knowledgeRefs可変性・
responseTypesとテンプレートの対応）はこの指摘と無関係で、そのまま有効。

**根拠:**
- CLAUDE.mdの運用ルール表に既に明文化されている原則であり、advisor-creatorが
  新規に判断を作る必要はなく、既存原則をadvisor作成時にも一貫して適用するだけでよい
- 疎結合を破ると、依存元advisorの改名・分割・統合のたびに依存先advisorの記述も
  連鎖的に壊れる。特定advisor名への依存を無くせば、advisor同士は互いの存在を
  知らずに独立して増減できる

### 合意決定
**決定:** `advisor-creator`のガードレールに「他advisor Skillの名前を本文（role/
description/inputExpectation等）に直接書かない」を追加する。ヒアリング項目も
「他advisorとの入出力関係」ではなく「追加の文脈情報があれば精度が上がる場合、
その情報の抽象的な形状（誰が生成したかに触れない）」という聞き方に統一する。
**理由:** CLAUDE.mdの既存疎結合原則をadvisor作成時にも一貫して適用するため。
既存3 advisor（tech-lead-advisor/ux-advisor/platform-advisor）の記述がこの
原則に違反していたことも今回判明した。
**次のアクション:** 論点3（`advisor-creator`が機械化すべき周辺配線の範囲——
KnowledgeSchema symlink deploy・AgentSchema goal-dispatch・skill-router
登録のどこまでを自動化するか）へ進む。既存3 advisorの記述修正（疎結合違反の
是正）自体は、このブレストとは別の直行レーン作業として、ユーザーに実施要否を
確認する。
**決定:**
**理由:**
**次のアクション:**

---
<!-- 論点3以降は「論点N」ブロックを繰り返す -->
