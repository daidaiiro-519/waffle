# ブレスト: マルチツール対応の/loop・/goalをリバースエンジニアリングで作る

**作成日:** 2026-07-12
**経緯:** `docs/handoff-goal-loop-orchestration.md`で、Claude Code CLI固有の
`/goal`・`/loop`の構造調査（条件駆動 vs 時間駆動という2パターン、ハーネスと
モデルの分離構造）は済んでいる。この調査結果を「参照実装」として、
Claude Code以外のツール（GitHub Copilot CLI・Kiro CLI等）でも動く汎用版を
Waffle側にリバースエンジニアリングで作りたい、という話が挙がった。

---

## 前提: 既に分かっていること（`docs/handoff-goal-loop-orchestration.md`より）

- `/goal <条件>`: 各ターン終了後、ハーネスが軽量モデルに条件充足を評価させる
  外部審判方式（条件駆動）
- `/loop`（動的モード）: モデル自身が`ScheduleWakeup`で次回起床タイミングを
  自己申告する自己ペース配分方式（時間駆動）
- 両者ともClaude Code独自機能で他ツールに移植できない。移植すべきは実装その
  ものではなく「条件駆動 vs 時間駆動」という**パターン**
- バックエンドCLIのセッション再開・headless対応調査（2026年7月時点）:
  Claude Code CLI（`-r`/`--resume`、ヘッドレス可）、GitHub Copilot CLI
  （`--resume`/`--continue`、ヘッドレス可）、Kiro CLI（headlessでのセッション
  再開が未解決issue、対応保留）

## 今回新しく出た論点: 「リバースエンジニアリング」という進め方

これまでの調査は公開ドキュメント・観察された挙動からの間接的な構造理解
だったが、今回「リバースエンジニアリングして作成したい」という踏み込んだ
表現が出た。これは単なる参照実装としての理解に留めず、実際に動作する
（Claude Code非依存の）汎用オーケストレーターの実装まで踏み込みたい、
という意思表示と解釈している（要確認）。

---

## 未検討

- 「リバースエンジニアリング」の具体的な対象・手段（Claude Code CLIの
  挙動を実際に観察・計測して仕様を精密化するのか、公開されている情報の
  範囲に留めるのか）
- has-udd側に既にあるPoC（`harness-poc-goal-style`/`harness-poc-loop-style`
  Skill、`orchestrator.py`外部プロセス版）を土台にするか、ゼロから設計し
  直すか。既存PoCは「タスクごとに新規サブプロセスを起動しセッション連続性を
  持たない」という限界が判明済み（`-r`/`--resume`ベースへの作り直しが必要と
  結論済み）
- Kiro CLIのheadlessセッション再開が未解決issue（kirodotdev/Kiro#9066）の
  ままの場合、3ツール対応を待つか、Claude Code＋Copilot CLIの2ツールで
  先行するか
- 条件評価（`/goal`のHaiku相当）をどう実現するか（別途軽量モデルAPI課金か、
  セッション内推論で完結させるか）は`docs/handoff-goal-loop-orchestration.md`
  の未決着事項としても残っている
- これをWaffleの5つ目のengine（orchestration engine）とするか、既存4 engine
  の拡張とするかも未決着（同上ドキュメント参照）

---

## 詳細ブレスト（2026-07-13〜）

**目的:** 上記「未検討」に列挙された論点を1つずつ深掘りし、次にspec-first
（`sd-schema-management`配下でのusecase spec合意）へ進めるところまで合意を作る。
**モード:** アイデア発散

---

### アイデアダンプ

上記の未検討論点にどう手を付けるか、思いつく限りのアプローチを列挙する（実現性は問わない）。

1. Claude Code CLIの`/goal`・`/loop`の実際の挙動をログ・ネットワークキャプチャ等で計測し、公開ドキュメントにない詳細（審判モデルの正確な呼び出し頻度・プロンプト等）まで解明してから移植する
2. 公開ドキュメント・観察可能な範囲（今回のhandoffで既に判明した範囲）に留め、パターン（条件駆動/時間駆動）の移植だけを目標にする
3. has-uddの`orchestrator.py`をそのまま`-r`/`--resume`対応に作り直し、Waffleへ移植する
4. `orchestrator.py`は参考程度に留め、Waffle CLI/MCPの既存アーキテクチャ（typer+fastmcp）に合わせてゼロから設計し直す
5. まずClaude Code CLI 1ツールだけで本物のセッション継続版を作り、動くものができてから他ツール対応を横展開する
6. 最初から3ツール（Claude Code/Copilot/Kiro）共通のインターフェースを設計し、各バックエンドのアダプタを同時に作る
7. Kiro CLIのheadless issue解決を待たず、Kiroだけ「対話モードのみ対応」という制限付きで先行実装する
8. 条件評価（`/goal`のHaiku相当）を、Waffle自身がセッション内で（別課金なしで）自己評価する形にする
9. 条件評価を、外部の軽量LLM API（別課金）を叩く形にする
10. 条件評価を、LLM判定ではなく機械的な条件（テスト green・特定ファイルの存在等）に限定し、あいまいな自然言語条件は対象外にする
11. orchestration engineを既存4 engine（query/render/scaffold/validate）と並ぶ5つ目の正式engineとして設計する
12. 新engineを作らず、既存engineの薄い組み合わせ（scaffoldでタスク記録・queryで状態確認等）として実装する
13. タスク記録層をWaffleの既存document.jsonパイプラインに乗せる（新documentType化）
14. タスク記録層は既存パイプラインと分離し、軽量な別データモデル（YAML等）にする
15. まずspec（`sd-schema-management`配下のusecase）を書き、実装は後回しにする（UDD spec-first厳守）

**絞り込み候補（実現性・後続論点への影響度で選定）:**
- 案11/12（engineとして設計するか）→ 他の全論点（spec配置・記録層設計）の前提になるため最優先
- 案5（1ツール先行）→ 案6（3ツール同時設計）より着手障壁が低く、`docs/handoff-goal-loop-orchestration.md`の「次のアクション2」（`-r`/`--resume`ベースの再検証）とも整合
- 案15（spec-first厳守）→ 前回の差し戻し（[[feedback-udd-implementation-before-spec]]相当）を繰り返さないための必須制約として、どの案を選んでも横断的に適用

---

### 論点 1: goal/loop型タスクオーケストレーションは、Waffleの5つ目の正式engineとして設計すべきか

#### AI 初期見解
**見解:** 5つ目の正式engineとして設計すべきである。既存engineの組み合わせで済ませる（案12）のは、当面の実装コストは低いが、後続の全論点（spec配置・記録層・condition評価の置き場）が宙に浮いたままになる。

**根拠:**
- 既存4 engine（query/render/scaffold/validate）はいずれも「document.jsonという静的な構造化データを対象にした単発操作」という共通性質を持つ。goal/loopは「セッションを跨いで継続する制御ループ」という質的に異なる責務（`-r`/`--resume`によるプロセス継続、条件評価、待機タイミングの自己申告）を持ち、既存engineのどれにも自然に収まらない
- Waffle自身がCLAUDE.mdで「document.json操作は必ずCLI/MCP経由」という運用ルールを持つように、engineという単位はWaffleにとって「他のSkill/機能から一貫して呼べる正式なAPI境界」を意味する。組み合わせで済ませると、この機能固有のルール（例: セッション再開の失敗時の扱い、条件評価の課金方針）を書く正式な置き場がなく、結局spec化されないまま実装が先行するリスクが高い（これは前回のHandoffSchemaでの差し戻しと同型のリスク）
- 5つ目のengineとして正式に切り出すことで、`sd-schema-management`のような既存subdomainの隣に`sd-orchestration`のような新subdomainを立て、spec-firstの手続き（usecase spec合意→実装）に自然に乗せられる。既存engineの拡張という体裁だと「拡張は軽微だからspec不要」という判断に流れやすく、UDD原則を回避する抜け道になりかねない

#### ユーザー見解
> ✏️ _（あなたの考え・反論・追加情報をここに書いてください）_

#### AI 再考見解
**見解:** _（ユーザー見解を受けて記述）_

#### 合意決定
**決定:** _（保留）_
**次のアクション:** _（合意後に記述）_

---

**この後に控えている論点（ユーザー確認の上で1つずつ進める）:**
2. 既存PoC（`orchestrator.py`）を土台に作り直すか、ゼロから設計し直すか
3. 「リバースエンジニアリング」の具体的な手段（挙動計測 vs 公開情報限定）
4. 3ツール同時対応か、1ツール（Claude Code）先行か
5. 条件評価（`/goal`のHaiku相当）の実現方式（自己評価/外部API/機械的条件のみ）

