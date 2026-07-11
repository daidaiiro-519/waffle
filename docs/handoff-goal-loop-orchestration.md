# ハンドオフ: goal/loop型タスクオーケストレーションをWaffleの機能として実装する

**作成日:** 2026-07-11
**背景:** has-udd後継プロダクト（`docs/handoff-has-udd-concept-map-redesign.md`参照・全文は
has-udd側の`brainstorm-has-udd-concept-map-redesign.md`）の設計検討から、Claude Codeの
`/goal`・`/loop`の構造調査に発展した。当初は独立した新プロダクト（TUIハーネス/ループ・
Waffleをgit submoduleとして組み込む）として構想していたが、**この機能（goal/loop型の
タスクオーケストレーション）自体をWaffleの機能として実装する方針に変更**された。本ドキュメントは
その方針転換後の設計材料を引き継ぐ。

---

## 1. 実装方針の転換（重要）

- Waffleは既にCLI（typer）＋MCP（fastmcp）の二面構成インフラを持っており、これをそのまま
  流用できる。新プロダクト側にゼロからCLI/MCPを作る必要がない
- **Skillとして提供する部分は、既存4 advisor（ddd-advisor/tech-lead-advisor/ux-advisor/
  platform-advisor）と同じ配布パターンを踏襲する**: Waffle所有のSkillとして
  `waffle/.waffle/skills/`に作成し、各ツールが認識できる場所（`.claude/skills/`等）へ
  シンボリックリンクを張ることで利用可能にする
- ただし**Skillという概念自体はClaude Code固有**であり、シンボリックリンクで配置しても
  Copilot CLI/Kiro等の別ツールからは認識されない（symlinkはClaude Codeの`.claude/skills`
  探索に対して有効なだけで、Copilot CLI等は`.claude/skills`ディレクトリ自体を読まない）。
  **マルチツール対応（Copilot CLI等）が必要な部分はMCP＋CLIとして提供する**、という整理は
  維持すべき

## 2. 配信方式の使い分け（推奨方針・要確定）

| 用途 | 配信方式 |
|---|---|
| Claude Code向けUX（対話的に使う） | Waffle所有のSkillとして実装し、既存advisorと同じsymlink配布 |
| マルチツール/自動化向け（Copilot CLI等からも呼べる） | WaffleのCLI＋MCPとして提供する |

両者は同じ内部ロジックを共有すべきで、**Skillは薄いラッパー（実体はCLIを叩くだけ）に
とどめる**のが望ましい。これはWaffleの既存の思想（CLIが正・Skillはそれを呼ぶガイド）とも
一致する。

## 3. `/goal`・`/loop`の構造理解（本調査で確定した内容）

Claude Code CLIは「ハーネス（アプリ本体）」と「モデル」が分離した構造を持ち、`/goal`・`/loop`
はこのハーネス側の継続制御ロジックを変えるスラッシュコマンド。

- **`/goal <条件>`**: 各ターン終了後、**ハーネスが軽量モデル（Haiku）に条件充足を評価させる**
  外部審判方式。未達なら即座に（時間を空けず）次のターンを自動起動。条件達成 or `/goal clear`
  で停止
- **`/loop`（動的モード、引数に間隔指定なし）**: **モデル自身が`ScheduleWakeup`ツールを呼び、
  次回起床タイミングを自己申告する**自己ペース配分方式。時間を意図的に空けて同じセッションに
  戻ってくる。7日で自動失効、セッション終了で停止
- **`/loop`（固定間隔モード）**: ハーネス側の単純なタイマーが指定間隔でセッションを起こす
- **`/loop`（メンテナンスモード、引数なし）**: PR・ビルド等の定型メンテナンスを自動管理する既定動作

**両者ともClaude Code独自機能であり、他ツールに移植できない。** 新機能はこの2つの
**パターン**（条件駆動 vs 時間駆動）を、Waffle自身のロジックとして汎用的に再実装する必要がある
——`/goal`・`/loop`は依存対象ではなく、設計の妥当性を裏付ける参照実装という位置づけ。

## 4. バックエンドCLIの実力マトリクス（2026年7月時点・調査済み）

| ツール | セッション再開 | ヘッドレス（自動化）での利用可否 |
|---|---|---|
| **Claude Code CLI** | `-r "<session>"` | ✅ 利用可 |
| **GitHub Copilot CLI** | `copilot --resume SESSION-ID` / `copilot --continue`。全会話履歴・許可設定込みで完全復元 | ✅ 利用可 |
| **Kiro CLI** | `kiro-cli chat --resume-id <ID>`（対話モードでは存在） | ❌ **headlessモード（`--no-interactive`）ではセッションIDが機械可読な形で出力されないため不可**。未解決issue: [kirodotdev/Kiro#9066](https://github.com/kirodotdev/Kiro/issues/9066)。解決されるまで対応保留 |

各CLIのヘッドレス呼び出し手段（参考）:
- Claude Code: `-p`（printモード）＋`--output-format json`/`stream-json`。`--bg`でバックグラウンド実行→`claude agents`/`attach <id>`/`logs <id>`で外部監視
- GitHub Copilot CLI: `--server --port 8080`でHTTPサーバー化（`/rpc`にJSON-RPC）。`--acp --port 8080`でACP（Agent Client Protocol）サーバーモード。Autopilotモードで無介入実行可
- Kiro CLI: `KIRO_API_KEY`＋`--no-interactive`によるheadless実行（Kiro CLI 2.0〜）。サーバーモード/ACP対応は未確認

## 5. PoC状況（has-udd側に作成済み・Waffleへの移植参考実装）

以下はhas-udd repo側に作成した検証コードで、まだWaffleには移植していない。

- **Skill版**（Claude Code専用・実際にSkillとして動作確認済み）:
  `has-udd/.claude/skills/harness-poc-goal-style/SKILL.md`（条件駆動: 完了条件を満たすまで
  同一ターン内で連続処理）
  `has-udd/.claude/skills/harness-poc-loop-style/SKILL.md`（時間駆動: 1回の呼び出しで1件のみ
  処理し、`ScheduleWakeup`で次回起床を予約）
- **外部プロセス版**（マルチバックエンド対応の実証。claude CLIでは実際にサブプロセスとして
  動作確認済み。copilot/kiroはこの環境に未インストールのため未検証、コマンドテンプレートは
  調査に基づく推測）: `has-udd/examples/harness-poc/orchestrator.py`
  （`--mode goal|loop --backend claude|copilot|kiro`）
- 検証用フィクスチャ: `has-udd/examples/harness-poc/tasks.yaml`

**重要な限界（要再設計）:** 上記のorchestrator.py版は、タスクごとに**まっさらな新規サブプロセス**
を起動しており、セッション連続性を持たない（`§4`で確認した`-r`/`--resume`を使っていない）。
これは`/goal`・`/loop`本来の「同じ会話状態を跨いでターンを重ねる」という構造を再現できておらず、
**Waffle実装では`-r`/`--resume`を使った本物のセッション再開に作り直す必要がある**。

## 6. 未決着事項

- 新しいWaffle engineとして正式に設計するか（既存4 engine=query/render/scaffold/validateに
  加えて5つ目の"orchestration engine"とするか、既存engineの拡張とするか）は未検討
- Skillの名称・具体的な配置場所は未検討
- タスクの記録層（自前実装・Backlog.md非依存という、元の新プロダクト構想の論点1の結論）を
  Waffle側でどう持つか——Waffle自身の既存document.jsonパイプラインと整合させるか、別のデータ
  モデルを新設するかは未確定
- 条件評価（`/goal`のHaiku相当）をWaffle側でどう実装するか——別途軽量モデルを呼ぶAPI課金が
  必要になる可能性があり、`brainstorm-loomdb-has-udd-document-db.md`論点5で確立した「サブスク
  範囲内で完結させる（セッション内推論を使う）」方針との整合を検討する必要がある

## 7. 次のアクション

1. orchestration engineの設計要否を判断する（既存4 engineとの関係整理）
2. `-r`/`--resume`ベースのセッション継続版オーケストレーターを試作し、条件駆動・時間駆動の
   両パターンを本物のセッション連続性込みで再検証する
3. Skill版（Claude Code向け）をWaffle所有のSkillとして正式に作成し、既存advisorと同じ
   symlink配布パターンに乗せる
4. 条件評価ロジック（`/goal`のHaiku相当）の実現方式を決める
