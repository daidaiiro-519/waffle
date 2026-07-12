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
