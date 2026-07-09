# ハンドオフ: has-udd側で行われたWaffle関連ブレストの引き継ぎ

**作成日:** 2026-07-10
**背景:** Waffleは元々`has-udd`リポジトリ内の自己完結ディレクトリ`waffle/`として開発され、
`git subtree split --prefix=waffle`で本リポジトリへ履歴ごと分離された。分離前にhas-udd側で
行われたブレインストーミングのうち、Waffle自身の設計・命名・今後の方向性に関わる合意事項を
このドキュメントに引き継ぐ。元のブレストファイルはhas-uddリポジトリの`docs/brainstorm/`配下
（`brainstorm-has-udd-oss-separation.md`・`brainstorm-waffle-next-evolution.md`）にあり、
議論の全文（AI初期見解・ユーザー見解・再考見解の応酬）はそちらを参照。本ドキュメントは
**合意済みの結論と、まだ手つかずの論点**を要約する。

---

## 1. なぜWaffleとhas-uddは分かれているか（命名の由来）

`has-udd` = **H**arness **A**gentic **S**crum **U**secase-**D**riven-**D**evelopment の略。
この頭字語は「HAS（Harness Agentic Scrum＝ハーネス/ループ駆動のagent system）」と
「UDD（Usecase-Driven-Development＝Waffleが支える開発手法）」の合成語。

- **Waffle** = document.jsonスキーマ駆動でドキュメントを検証・生成する**エンジン**。
  UDD（Usecase-Driven Development）という開発手法を実践するための道具。
  タグライン案: 「Waffle — スキーマという型で文書を焼き上げる、構造検証＋意味ガイダンス内蔵の
  ドキュメントエンジン」。名前の由来はblockKeyの格子構造（＝ワッフルの格子）とschema検証
  （＝型に入れて焼き上げる）という比喩。
- **has-udd** = Waffleを使って構成される**agent system**（Skill/Agentをテキストベースで
  ハンドリングし、エージェンティックスクラムを構成する側）。「has-udd」という名前と
  UDDという開発手法の呼称は、engineではなくagent system側に残すことで頭字語の本来の由来と
  整合する。

**結論（合意済み）:** engine（Waffle）とagent system（has-udd）は非対称な開発フェーズ
（engineは作り込み済み・agent systemは未着手）にあるが、これは設計の欠陥ではなく単なる開発順序。
Waffleを先に独立OSS化する判断は、この現在地の自然な延長として決まった。

---

## 2. has-uddとの結合方式（依存境界）

**結論（合意済み）:** has-udd（agent system）はWaffleの**内部実装には依存しない**が、
Waffleが提供する**MCP・CLIというインターフェースは引き続き利用**する。

- has-uddとWaffleの入出力は最初からテキストベース（CLI/MCP）に閉じており、Waffleの内部実装
  （Pythonオブジェクト・schemaの内部構造）に一切触れない作りになっている。これは
  「共通インターフェースはテキストベース・各SkillがLLMによる成形を担う」という別ブレスト
  （`brainstorm-loomdb-has-udd-document-db.md`論点5）の疎結合方針が、結果的にagent systemを
  Waffleの実装詳細から完全に切り離す働きもしていた、という発見によるもの。
- したがって「切り離されているのは内部実装への結合であって、インターフェースとしての利用ではない」
  という点が重要——Waffle側でCLI/MCPの入出力契約を変える場合は、has-udd側への影響を意識する必要がある。

---

## 3. パス規約（`.waffle/`）とバンドルされたschemaの位置づけ

**結論（合意済み・実装済み）:**
- schemaの`x-source-target`/`x-render-target`パス規約は`.has-udd/`ではなく**`.waffle/`**を使う
  （`.git/`が道具名を冠するのと同じ発想。schemaがWaffle自身の資産である以上、規約もWaffleの
  ものであるべき、という判断）。
- Waffleにバンドルされているschema（SkillSchema/SpecSchema/CodingSchema/RenderMetaSchema）は
  「has-uddの都合でengineに同梱されている外部依存」ではなく、**Waffle自身のschema資産**
  （Waffleというエンジンが定義するドキュメント型そのもの）。外部化はしない。
- has-udd自身を説明するspec/skill documentのうち、Waffle自身を説明するもの（`bc-waffle-engines`等、
  旧名`bc-has-udd-engines`）はWaffle自身の資産として`.waffle/documents/`に一元管理し、
  has-udd repo root側の`.has-udd/documents/`と重複させない。has-udd repo root側には
  Waffle固有でない汎用skill（`analyze-domain-model.json`等・agent system自身の資産）のみが残る。

---

## 4. 次の一手（`brainstorm-waffle-next-evolution.md`より）— 未決着の論点あり

**目的:** 仕様と実装のドリフト・品質・AI過剰生成という3課題を解決し、非技術者と技術者の両方を
支援する「AI時代の開発標準」としてWaffleが次に何を作るべきか。

**前提（当時の現在地）:** DDDバックボーンのUDD・レイヤードアーキテクチャ・
spec→scaffold→validate→render→ネイティブテスト生成のコアループ完成。ドリフト検知は
「シナリオ名⇔テスト関数名のAST突き合わせ」まで実装済み（意味レベルは未着手）。

### 決着済み: 論点6・論点7

- **論点6（usecase裏のデータアクセス層契約の表現方法）:** 判定基準は
  「同じ資源を操作する複数usecaseの間で保証内容が重複するか」。重複しない（usecase固有）→
  `uc-*.json`に`OperationGuarantees`（EARS形式の`shall`文）＋`GuaranteeScenarios`
  （Given/When/Then）。重複する（資源自体の性質）→既存の集約`invariants`＋
  `unitTestScenarios`。**実装済み**（`DomainSpecSchema/v2.json`に両ブロック追加、
  描画順序は`AcceptanceCriteria`→`OperationGuarantees`→`Errors`→`TestScenarios`→
  `GuaranteeScenarios`で確定）。
- **論点7（CLI/MCPはWHATかHOWか）:** 「この機能をCLI/MCP経由で提供すること自体」が
  事業価値であるならWHATとしてspecに書く（`OperationGuarantees`に「この操作はCLI/MCP経由でも
  同じ保証を維持するshall」を含める）。具体的な実装技術（typer/fastmcp等）は引き続き
  CodingSchemaの領分。

### 未決着: 論点1〜5（ユーザー見解が空欄のまま中断）

15案のアイデアダンプから絞り込んだ上位5候補について、AI初期見解のみ記録され、
ユーザーの検討・合意が未了。Waffle側で作業を再開する際はこの5論点から着手するとよい。

| 論点 | 内容 | AI初期見解（未合意） |
|---|---|---|
| 論点1 | 次に作る一手の優先順位 | #7陳腐化台帳（内容ハッシュで導出物の期限切れ検知）を先に作り、その上に#1シナリオ検死官（mutation testingでシナリオの弱さを機械採点）を載せる |
| 論点2 | 過剰生成対策「ゼロコード審判」(#4)は強制ゲートか診断か | 最初は診断（レポート）として導入し、実測データを見てから強制（コミットブロック）に昇格する2段階 |
| 論点3 | 非技術者支援はスキーマを完全に隠す方向でよいか(#8/#9) | YES。ただし隠すのはUI層だけで、生成物は常に既存のdocument.json＋既存validateを通す |
| 論点4 | 意味レベルのドリフト検知(#2/#14)とAI 0原則の折り合い | 「検知はAIでもよい・執行と記録は機械」という線引き。判決だけは人間、執行は機械 |
| 論点5 | SDD標準ツール群（GitHub Spec Kit/AWS Kiro等）と競合するか | 競合しない。「DDD語彙×シナリオ品質の機械採点×トークン経済」という、既存SDDツールが持たない層で差別化 |

**15案の全アイデアダンプ**（優先順位づけ前の発散結果。論点1の議論で取捨選択する材料）:
シナリオ検死官／往復翻訳ドリフト検知／仕様VM／ゼロコード審判／生成予算法／悪魔の代弁者／
陳腐化台帳／聞き取りコンパイラ／実例先行スキーマ蒸留／ユビキタス語彙台帳／仕様の未来日記／
仕様の試遊／トークン損益計算書／reconcile法廷／意図エントロピー計。詳細な説明は元ファイル
`brainstorm-waffle-next-evolution.md`のアイデアダンプ節を参照（has-udd側リポジトリに現存）。

---

## 5. 次のアクション

Waffle単体としてこのブレストの続きに着手する場合:
1. 論点1〜5について、Waffleリポジトリ側で改めてユーザーと合意形成する
2. 決着済みの論点6・7は実装済みなので変更不要（`DomainSpecSchema/v2.json`参照）
3. §2の依存境界（テキストベースCLI/MCPインターフェース）を壊す変更をする場合は、
   has-udd側（agent system）への影響を確認する
