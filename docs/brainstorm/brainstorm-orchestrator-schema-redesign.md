# ブレインストーミング: Orchestrator（AgentSchema/v2）のスキーマ設計見直し

**目的:** CLAUDE.md/AGENTS.mdの原本であるAgentSchema/v2のスキーマ構造・運用ルールを見直し、今回発覚した3つの構造的ギャップ（時制表現の欠如、カテゴリ単位ルールの置き場所欠如、deploy path解決の罠）を解消する設計に合意すること
**モード:** 問題解決

---

## 問題の再定義

AgentSchema/v2のスキーマ構造が実際の運用ニーズ（Skill呼び出し前の一般確認・Skillカテゴリ単位の原則・自由記述と構造化の境界）を表現しきれていないせいで、過去に複数回、原本（document.json）を経由しない直接CLAUDE.md編集が発生し、内容の同期崩れ・消失が起きた。

## 原因候補

- **表面的原因**: 過去のセッションがWaffleの「document.json経由で編集する」原則を守らず、CLAUDE.mdへ直接Edit/Writeした
- **根本原因1**: スキーマが表現できる語彙（operatingRulesの自由記述／skillFollowUpの「特定1Skillの事後フック」）に、今回のような「Skillカテゴリ全体への事前確認」を書く場所が無かった。書きたい内容があるのにフィールドが無い状態が、直接編集という逸脱行動の誘因になった
- **根本原因2**: このdocumentのdeploy先パス解決が呼び出しディレクトリに依存する設計になっており（`waffle/CLAUDE.md`という相対パス表現）、実際の開発セッションの大半が別のディレクトリ階層からCLIを呼んでいたため、正しい手順で作業しても事故る（入れ子ディレクトリ誤生成）リスクを常に抱えていた

---

## 前提整理: Orchestratorがハンドリングすべき責務の7分類（ユーザー提示・合意済み） → のち6分類へ修正

個別のフィールド設計に入る前に、Orchestratorが本来持つべき責務を洗い出して合意した。

| # | 責務 | 現状の器 |
|---|---|---|
| 1 | 自身の役割 | 無し（`scope`の"概要"は「このディレクトリ・プロダクトが何か」であって「Orchestratorとして何をする存在か」ではない） |
| 2 | 担当範囲 | `scope`（既存） |
| 3 | 厳守するルール | `operatingRules`（既存だが「厳守」と「参考程度」が自由記述に混在） |
| 4 | 機械的に行える作業 | 無し（判断不要、手順通りにやるだけの操作） |
| 5 | AIの推論を要する作業 | 無し（状況を見て判断が必要な操作） |
| ~~6~~ | ~~委譲先（ディレクトリ）~~ | ~~`subOrchestratorRefs`~~ → **論点6で削除に合意**（下記参照） |
| 7 | 委譲パターン（Skill/advisorへ） | `skillFollowUp`に近いが、固定参照ではなく状況に応じたパターン（いつ・何に・どう委譲するか、WHO/HOW） |

以下の論点1〜4は、この7分類のうち特に3〜5・7の境界が曖昧だったことに起因する。論点6で#6自体の必要性を再検討し、削除に合意した（最終的に6分類になる）。

---

## 論点 1: operatingRulesとskillFollowUpの境界線をどう引き直すべきか？

### AI 初期見解
**見解:** 現在の境界線（自由記述 vs 構造化）に加えて「時制」の軸を明示すべきである。operatingRulesは「常に成り立つ一般則」、skillFollowUpは「特定Skillを呼んだ後」専用フックという二分法だが、今回のケース（カテゴリ単位の"呼ぶ前"チェック）はどちらにも属さない第3のパターンだと判明した。
**根拠:**
- skillFollowUpのprompt定義自体が「呼び出した**後**に、機械的に踏むべき次のアクション」と明記しており、事前チェックを表現する語彙を持たない
- 今回復旧した内容（document-authoring系Skillを扱う際はskill-routerに問い合わせる）は、実際にはCLAUDE.mdの自由文がhookから読まれているわけではなく、`notify-advisor-consultation.py`は`skill-router.json`のroutingTableをCLI経由で直接参照している。つまりCLAUDE.md側のこの1行は、hookにとっては不要な重複説明で、人間が読むための誘導文でしかない
- 自由記述（operatingRules）に押し込めば技術的には書けるが、「後から機械的に検索・参照したい情報」と「人間向けの一般的な心構え」を同じ自由文の器に混ぜると、将来また同じ理由（書きたいことの型が合わない）で直接編集の誘因が再発する

### ユーザー見解
> 私が思うに以下はマスト：自身の役割・担当範囲・厳守するルール・機械的に行える作業・AIの推論を要する作業・委譲先・エージェント起動トリガー（今のskillFollowUpに近いかも）。委譲先はSkillになるかもしれない。サブエージェントは固定で存在するものではないので、委譲パターンみたいなのはあってもいいかもしれない。アドバイザーとかには委譲したりするし。→「委譲パターン」という統合概念でいいと思う。そっちの方が分かりやすいかもしれない。

### AI 再考見解
**見解:** operatingRules/skillFollowUpという既存2区分ではなく、まず「自身の役割／担当範囲／厳守するルール／機械的にできる作業／AIの推論を要する作業／委譲先（ディレクトリ）／委譲パターン（Skill・advisorへの委譲）」という7分類を土台に置き直す。論点1で困っていたのは、この中の「AIの推論を要する作業」と「委譲パターン」という2つの独立した概念が、operatingRules（自由記述）とskillFollowUp（事後専用）という性質の違う2つの箱に無自覚に混在していたことだった。
**根拠:**
- ユーザーの指摘通り、委譲先は固定的な参照（documentIdで名指しする子Orchestrator）ではなく、状況に応じたパターン（いつ・何に・どう委譲するか）として持つ方が実態に合う。サブエージェントの型自体が都度定義されるものであり、固定リストにできない
- 既存skillFollowUpの「advisor全般」行は、内容としてはすでに「委譲パターン」（goal-dispatch構造で並列にAgent起動する）であり、「フォローアップ（事後処理）」という命名の方が実態とズレていた
- 論点1（時制の欠如）は、委譲パターンという概念に`timing: before/after`属性を持たせることで吸収できる。新しいブロックを増やす必要がない

### 合意決定
**決定:** `skillFollowUp`を「委譲パターン」として再定義し、`timing`（before/after）・対象範囲（単一Skill or カテゴリ）を属性に持たせる。`subOrchestratorRefs`（ディレクトリへの委譲）とは別軸として維持し、統合しない
**理由:** 委譲パターンという1つの概念に集約した方が「前後どちらに書くべきか」の判断の迷いが減り、既存内容（advisor全般の行）の実態とも一致する。ディレクトリへの委譲とSkillへの委譲は関心事が異なる（WHERE vs WHO/HOW）ため、別軸のまま維持する
**次のアクション:** 「委譲パターン」ブロックの具体的なフィールド定義（timing・対象範囲・パターン・outputFormat/templateの必須/任意条件・why）を次の論点として詰める

---

## 論点 2: 「Skillカテゴリ全体への事前確認」を表現する新しいフィールドが必要か？

**合意:** 論点1の合意に統合。「委譲パターン」の`timing: before`・対象範囲=カテゴリ、という属性の組み合わせとして表現する。独立ブロックは新設しない（元のAI初期見解でも同じ結論＝軽量な属性拡張が妥当、としていた）。

---

## 論点 3: deploy先パス解決の罠（`waffle/`prefix問題）をどう構造的に防ぐか？

### AI 初期見解
**見解:** 相対パス表現（`waffle/CLAUDE.md`）を、呼び出しディレクトリに依存しない表現に変更すべきである。
**根拠:**
- 今回、正しい手順（scaffold fill→validate→render）を踏んでも、CLIの実行ディレクトリが暗黙の前提（`/home/daidaiiro/workspace/`から`--project waffle`で呼ぶ）とズレていたために、入れ子`waffle/waffle/`ディレクトリが誤生成された。これは人間・AIどちらが操作しても再発しうる構造的な罠である
- このセッション中の他のdocument（knowledge-cultivator等）は`.claude/skills/...`という、リポジトリルート相対のパスをdeploy先に持ち、実行ディレクトリに関わらず正しく解決されていた。waffle.json documentだけが特殊な「一段上から呼ぶ前提」を持つのは非対称であり、他のdocumentと同じ「常にリポジトリルート相対」の表現に統一する方が事故りにくい
- ただし、この特殊な相対パスがなぜ必要だったのか（`git subtree split --prefix=waffle`で独立可能、というCLAUDE.md自身の記述と関係がありそうだ）を先に確認せずに変更すると、本来の意図を壊す可能性がある。この論点は経緯の確認が先

### ユーザー見解
> 基本的にシンボリックリンクで済む範囲はシンボリックがいい。ただツールによってはそれ用に形を整えてデプロイしないといけないのもあるかもしれない。全部デプロイする（実体コピー）のがいいか、シンボリックリンクがいいかをまず見解が欲しい。→ それがいいかも。基本全部waffle配下を製本（＝canonical）としたい。

### AI 再考見解
**見解:** deploy先を`.waffle/config.json`（仮）で管理し、各deploy先エントリに`mode: "symlink" | "render"`を持たせる。既定は`symlink`。ツールが独自形式を要求する場合のみ`render`（実体コピー）にする。パス解決は`.waffle/`自身の位置を基準にし、呼び出し元のcwdに依存させない。canonicalは常に`.waffle/`配下（documentも成果物も）。
**根拠:**
- 今回発生した2つの事故（CLAUDE.mdの内容消失、私自身のknowledge-cultivator行の直接Edit）は、どちらも「同一内容の実体コピーが2箇所に存在し、どちらかが古くなりうる」という構造そのものが原因だった。シンボリックリンクは物理的に同一ファイルなので、この失敗モードが構造的に起こり得なくなる
- 既存の`brainstorm` skill（`.claude/skills/brainstorm` → `.waffle/skills/brainstorm`のディレクトリシンボリックリンク）は、このセッション中に何度直接編集しても`.waffle`側と絶対にズレなかった。一方`knowledge-cultivator`（実体コピー）やCLAUDE.md/AGENTS.md（実体コピー）は今回どちらも同期崩れを経験した。実例で効果が裏付けられている
- CLAUDE.md/AGENTS.mdは実際に内容を比較しても常に同一だった（differ検証済み）。本来シンボリックリンクで足りていたはずで、実体コピーにしていたこと自体が今回の一因
- cwd依存の`waffle/`prefix問題も、パス解決の基準を「呼び出し元のcwd」から「`.waffle/`自身の位置」に変えることで併せて解消できる

### 訂正の訂正: 「Waffle管理/非管理で置き場所を分ける」も誤り。全Skillは最終的にWaffle document管理へ寄せる

一度は「手書きSkillはcanonicalを`.claude`側にすべき」と訂正したが、これも誤り。正しくは、`brainstorm`のような手書きSkillが今`.waffle/skills/`に実体を持ちながらdocument.jsonを持たない、という状態自体が**正しい設計ではなく未完了の移行（技術的負債）**である。長期的には全Skillが`investigation`/`knowledge-cultivator`と同じようにWaffleのSkillSchema documentとして管理されるべきで、そうなればcanonicalは例外なく`.waffle`配下に統一される。

よって正しい原則は：

- **長期的な原則**: 全SkillはWaffleのSkillSchema documentとして管理する。canonicalは常に`.waffle`配下（例外なし）
- **各ツールのフォルダ**（`.claude/skills/`、将来の他ツール用フォルダ等）は、その`.waffle`側canonicalへのsymlinkを持つだけ
- **現状の`brainstorm`/`ddd-advisor`等**（document.json無しで`.waffle/skills/`に直置き）は、この原則から見ると「まだdocument化されていないSkill」という積み残し。deploy先設計とは別に、SkillSchema化の移行タスクとして扱う

### 合意決定
**決定:** deploy先解決を`.waffle/config.json`（仮称）に外出しし、deploy先ごとに`mode: symlink（既定） | render（ツール固有形式が必要な場合のみ）`を持たせる設計にする。canonicalは全Skill共通で`.waffle`配下に統一する（例外を設けない）。各ツールのフォルダはそこへのsymlinkのみを持つ
**理由:** 実体コピーという構造そのものが同期崩れの根本原因だったため、symlink既定・canonical一元化の方針は変えない。「Waffle管理/非管理で置き場所を分ける」という一度の訂正は、未完了の移行状態を正しい設計であるかのように追認してしまっていたため撤回する
**次のアクション:** `.waffle/config.json`の具体的なスキーマ（deploy先一覧、ツール名、mode）を設計する。`brainstorm`・`ddd-advisor`・`tech-lead-advisor`・`ux-advisor`等、document.json化されていない手書きSkill群をSkillSchema documentへ移行する作業を、別途積み残しタスクとして棚卸しする（knowledge-cultivator作成時と同じ手順が使える）

---

## 論点 4: CLAUDE.md/AGENTS.md（成果物側）への直接編集を防ぐガードレールを追加すべきか？

### AI 初期見解（論点3の合意を踏まえ更新）
**見解:** 追加すべきである。`protect-document-json.py`が原本（document.json/schema.json）への直接Edit/Writeを防いでいるのと対になる形で、render成果物側（CLAUDE.md/AGENTS.md、SKILL.md等）への直接Edit/Writeも防ぐガードが無いのは非対称であり、これが今回の同期崩れの直接の入口だった。
**根拠:**
- 今回発見した2件の同期崩れ（document-authoring系原則の消失、私自身のknowledge-cultivator行の直接Edit）は、どちらも「render成果物への直接書き込みが技術的に可能だった」ことが共通の原因
- 論点3の合意により、`brainstorm`等の手書きSkillも最終的にはWaffle document管理へ移行する方針になった。移行が完了すればこのガードに例外を設ける必要はなくなるが、移行完了までの過渡期は「まだdocument化されていないSkill」を誤ってブロックしないよう、対象かどうかを動的に判定する必要がある（`notify-advisor-consultation.py`が`skill-router`のroutingTableを動的参照しているのと同じやり方）

### ユーザー見解
> 「動的判定でblockするhook」の具体的な仕組みを聞きたい。

### AI 再考見解
**見解:** 判定方法は2案ある。案A: 対象パスのrealpath（symlinkをたどった実体）が`.waffle/`配下（documents/やhooks/等の除外を除く）かどうかを見る。案B: `.waffle/config.json`のpathTemplate群と対象パスを逆マッチさせる。ただしどちらも、論点3（symlink移行）または論点5（config.json実装）のどちらかが先に完了していないと動かせない。今日時点ではCLAUDE.md/knowledge-cultivator等がまだ実体コピーのままで、symlinkもconfig.jsonも存在しないため、このhook自体は今すぐ実装できない。
**根拠:**
- 案Aはsymlink化（論点3）が前提。symlinkさえ張られていれば実体パスを見るだけで機械的に判定できる、最もシンプルな方法
- 案Bはconfig.json（論点5）が前提。pathTemplateとの逆マッチでdocumentIdまで特定でき、denyメッセージに「どのdocumentを更新すべきか」を具体的に示せる利点がある
- 実装順序を今ここで決め打ちするより、論点3のsymlink移行が終わった後に実際に使える情報（symlinkの実体 or config.json）を見て選ぶ方が手戻りが少ない

### 合意決定
**決定:** 「成果物への直接編集を防ぐガードレール」の必要性自体は合意する。ただし判定方式（案A: symlink realpath判定／案B: config.jsonパターン逆マッチ）は今は決め打ちせず、論点3（symlink移行）完了後に実際の状況を見て選定する
**理由:** どちらの案も未実装の前提（symlink化 or config.json）に依存しており、今この時点で方式を確定させても実装時に手戻りが起きる可能性が高い
**次のアクション:** 論点3のsymlink移行が完了した段階で、案A/案Bのどちらを採るか再検討し、hookを実装する

---

## 論点 5: config.jsonの役割は何か（deploy先リストの外出し／種別×ツールのマッピングルール）？

### AI 初期見解
**見解:** config.jsonは「documentごとのdeploy先リスト」を外出しするものではなく、「document種別（kind: skill/agent/hook等）×ツール（claude-code/codex等）」で決まる**配置ルールそのもの**を1箇所にまとめるべきである。既存の`x-render-target.deploy`（document/schema側が個別に持つ具体パス列挙）は、この種別×ツールマッピング＋documentIdから自動的に導出される形に置き換わる。
**根拠:**
- マルチツール対応の本質は「同じ中身（例: Skill）でも、ツールごとに置き場所・形式のルールが違う」ことであり、このルールはdocument1件ごとに違うのではなく**種別ごとに共通**（Skillが10個あればClaude Code向けの置き方ルールは10個とも同じ）
- ルールを種別×ツール単位で1箇所にまとめれば、新しいツールを追加するときにconfig.jsonへ1ブロック足すだけで済み、既存の全document/schemaを書き換えずに済む
- 逆に「documentごとの具体パスリスト」を外出しするだけなら、情報がschema側とconfig.json側の2箇所に分散するだけで、今回の同期崩れと同型の問題を新たに生む。種別×ツールという一段抽象化したルールにすることで、情報の重複自体を無くせる

### ユーザー見解
> マルチツールなので各ツールごとにskill・agent・hooksなどの形式がある。これをWaffleのものをツールごとに適切に配置するために必要。→ そういうことになりますな（種別×ツールのマッピングルール、という理解で合意）。

### AI 再考見解
**見解:** ユーザーの意図と一致していることを確認できた。`{documentKind, tool}`をキーに`{pathTemplate, mode}`を引く、というテーブル構造で確定する。
**根拠:**
- documentKind（skill/agent/hook等）は各schemaが既に`documentType`として持っている情報と対応させられる
- pathTemplateは`{documentId}`のようなプレースホルダーを含む文字列で、既存のknowledge-cultivatorのpathVars機構（`x-render-target.pathVars`）と同様の解決方法が使える

### 合意決定
**決定:** `.waffle/config.json`（仮称）は「documentKind × tool → {pathTemplate, mode}」のマッピングテーブルを持つ。既存の`x-render-target.deploy`による個別パス列挙は、将来的にこのマッピングテーブルからの自動導出に置き換える
**理由:** マルチツール対応の本質的な必要性（種別ごとに共通のツール別配置ルール）に対応した最小限の抽象化であり、documentごとの重複列挙も避けられる
**次のアクション:** documentKindの一覧（skill/agent/hook/その他）を洗い出し、pathTemplateのプレースホルダー解決方法（既存のpathVars機構の再利用可否）を含めた具体的なJSON Schema相当の定義を次回詰める。実装は`render_document.py`のdeploy解決ロジック変更を伴う大きめの変更になるため、着手前に影響範囲の調査（investigation skill）を挟むのが妥当

---

## 論点 6: 「委譲先（ディレクトリ／子Orchestrator）」という分類自体が必要か？

advisorレビュー後の再検証で、7分類のうち「委譲先（#6、`subOrchestratorRefs`）」の必要性そのものに疑問が出た。

### AI初期見解（ユーザー指摘を受けての検討）
**見解:** #6は削除すべきである。「子Orchestratorを階層的に運用する」という設計自体に実用上の旨みが無い。
**根拠:**
- waffleは「自己完結ディレクトリ」（`git subtree split --prefix=waffle`で独立可能）という前提で、既に1つのまとまった統治単位として扱われている。中にさらに別統治が要るサブ領域は無い
- 本当に別統治が要るほど性質の異なる領域があるなら、それは「子」ではなく「別の独立したWaffleプロジェクト」（`/home/daidaiiro/workspace/`直下の`has-udd`・`loomdb`のような、対等な別リポジトリ）になるはずで、親子の階層ではなく対等な別プロジェクトとして扱う方が実態に合う
- ディレクトリごとに多少ルールが違う程度なら、1つのOrchestrator documentの中でscoped ruleとして表現すれば足り、document自体を分けてrender・deploy・advisor相談ループを丸ごと複製する理由が無い
- 現在このリポジトリには`subOrchestratorRefs`の実例が0件（「委譲先なし」）であり、evidence-based-scope的にも実証された需要が無い

### ユーザー見解
> 普通にサブオーケストレーターの用途も旨みもなくないですか？

### 合意決定
**決定:** #6（委譲先／ディレクトリ）を7分類から削除し、6分類（自身の役割・担当範囲・厳守するルール・機械的作業・AIの推論作業・委譲パターン）にする。AgentSchema/v2の新版作成時に`subOrchestratorRefs`ブロックも削除する
**理由:** 階層的な子Orchestrator運用は実証された需要が無く、実用上の価値も見出せない。別統治が本当に必要な場合は「子」ではなく「対等な別プロジェクト」として扱う方が実態に合う
**次のアクション:** AgentSchema/v2新版のブロック一覧から`subOrchestratorRefs`を除外する。CLAUDE.mdの「委譲先」セクション自体も削除対象に含める

---

## セッションまとめ

### 合意事項

1. **前提（6分類、当初7分類から#6を削除）**: Orchestratorの責務を「自身の役割／担当範囲／厳守するルール／機械的にできる作業／AIの推論を要する作業／委譲パターン（Skill・advisorへ）」の6つで捉え直す。特に「自身の役割」「機械的作業」「AIの推論作業」は現行スキーマに器が無いと判明。「委譲先（ディレクトリ／子Orchestrator）」は論点6で実用上の価値が無いと判断し削除
2. **skillFollowUp → 「委譲パターン」への再定義**: `timing: before/after`・対象範囲（単一Skill/カテゴリ）を属性に持たせる形で拡張し、独立ブロックは新設しない。advisorレビューにより、4（機械的作業）・5（AI推論作業）とは別に、7（委譲パターン）は「実行主体が自分から他者に移る」という質的に異なる関心事として維持することも確認した
3. **deploy先はsymlinkを既定にする**: `mode: symlink（既定） | render（ツール固有形式が必要な場合のみ）`。パス解決基準は`.waffle/`自身の位置にし、cwd依存を解消する
4. **canonicalは全Skill共通で`.waffle`配下に統一（例外なし）**: `brainstorm`等の手書きSkillが`.waffle/skills/`に直置きされている現状は「未完了の移行（技術的負債）」であり、正しい設計ではない。長期的には全SkillをSkillSchema document化する
5. **成果物への直接編集ガードレール**: 必要性は合意。判定方式（symlink realpath判定 or config.jsonパターン逆マッチ）は論点3の移行完了後に選定する
6. **config.jsonの役割**: 「documentKind × tool → {pathTemplate, mode}」のマッピングテーブル。新ツール追加時に1ブロック足すだけで済む設計とし、既存の`x-render-target.deploy`個別列挙を置き換える
7. **委譲先（ディレクトリ／子Orchestrator）の削除**: 実証された需要が無く実用上の価値も見出せないため、7分類から削除し6分類にする。`subOrchestratorRefs`ブロックもAgentSchema/v2新版で削除する

### 次のアクション一覧

- `.waffle/config.json`の具体的スキーマ設計（documentKind一覧・pathTemplateプレースホルダー解決方法）
- `brainstorm`・`ddd-advisor`・`tech-lead-advisor`・`ux-advisor`等の手書きSkillをSkillSchema documentへ移行（knowledge-cultivator作成時と同じ手順）
- CLAUDE.md/AGENTS.md・knowledge-cultivatorのSKILL.md等、既存の実体コピーをsymlinkへ置き換える移行作業
- 「委譲パターン」ブロックの具体的なフィールド定義（AgentSchema/v2の新版作成が必要、4/5を別フィールド構造にする点も含む）
- `subOrchestratorRefs`ブロックの削除、CLAUDE.mdの「委譲先」セクションの削除
- 成果物直接編集防止hookの実装（symlink移行完了後に方式選定）
- `render_document.py`のdeploy解決ロジック変更（config.json対応）は影響範囲が大きいため、着手前にinvestigation skillで調査を挟む

### 保留・未解決

- 特になし（論点1〜5すべて合意済み）。ただしいずれも**設計合意のみで未実装**。実装着手は別セッション・別タスクとして扱う

---
