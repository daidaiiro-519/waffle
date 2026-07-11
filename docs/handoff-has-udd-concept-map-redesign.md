# ハンドオフ: has-udd後継プロダクト（TUIハーネス/ループ）の設計方針

**作成日:** 2026-07-10
**背景:** has-udd（Harness Agentic Scrum Usecase-Driven-Development）は、Backlog.md導入で
タスク記録機能がコモディティ化したことを契機に、コンセプトマップから再設計中。最終的には
**新しい名称の下、新規リポジトリとして切り出し、Waffleをgit submoduleとして組み込む**予定
（新プロダクトは「agents開発」を必要とし、そのノウハウをWaffleが持っているため）。本ドキュメントは、
その新リポジトリ着手時に必要な設計方針を、has-udd側のブレスト
（`docs/brainstorm/brainstorm-has-udd-concept-map-redesign.md`・全文はhas-udd側にのみ存在）
から要約して引き継ぐ。**新リポジトリ未作成の現時点では、方針の記録場所としてWaffle側に暫定配置**
している。

> **★2026-07-11更新:** goal/loop型タスクオーケストレーション機能（本ドキュメント§4「技術
> スタック」で触れているTUI/PoC部分）は、**独立新プロダクトではなくWaffle自身の機能として
> 実装する方針に変更**された。詳細・最新の設計材料は`docs/handoff-goal-loop-orchestration.md`
> を参照。本ドキュメントの§1〜3（中核価値・UX方針・UXの適用範囲）は依然有効。

---

## 1. 新プロダクトの中核価値（決定済み）

**「アジャイル開発プロセスを自律的にループさせる、外部プラグインに依存しない自己完結の駆動層」**
に純化する。特定の開発方法論（UDD）にもWaffle固有のspec形式にも依存しない汎用的なハーネス/ループ。

- タスクの**記録層（データモデル）**と**意思決定ロジック（ceremony駆動・次の一手の決定・
  エスカレーション判断）**の両方を自前で持つ。**Backlog.md等の外部タスク管理OSSには依存しない**
  （ファイルベース・Git管理・Markdown/YAMLというデータ設計の思想は着想源としてよいが、実装・
  ランタイム依存は持たない）
- 判断基準: 「その依存対象が製品の中核体験を左右する意思決定権を握っているか」。記録層は
  意思決定ロジックと不可分なので自前化。LLM実行（後述）は中核体験ではないため既存ツールに委任
- この判断は、LoomDB（外部NoSQLに依存せず組込ライブラリとして中核データストアを自前で持つ）・
  Waffle（既存SDDツールに乗らず独自document.jsonエンジンを持つ）と一貫する、このエコシステム
  全体のパターン——「製品の中核体験を担うデータ・ロジックは自前で持つ」

---

## 2. UX: CLI/TUIが主戦場（決定済み）。バックエンドLLMは既存CLIをそのまま使う

- 主戦場は**CLI/TUI**。Web UI（ブラウザ）は少なくとも当面持たない
- バックエンドのLLM実行（モデル選択・コンテキスト管理・ツール呼び出し）は**Claude Code CLI /
  GitHub Copilot CLI等の既存機能をそのまま使う**。ハーネス側で再実装・代理制御しない
  （1章の「自前で持つ」対象にLLM実行機能は含まれない）
- 各CLI固有の機能は**パススルーを基本**とし、**ACP（Agent Client Protocol）のように業界標準
  として確立されつつある部分にだけ薄く乗る**、という二層構成。ハーネス独自の変換表・抽象化
  レイヤーは持たない（外部ツールのロードマップに律速されないため）
  - ACP対応ツール（GitHub Copilot CLI・Claude Code経由アダプタ`@zed-industries/claude-code-acp`）
    はACP経由で共通に扱う
  - 非対応ツール（2026年7月時点のKiro CLI等）は個別のCLI呼び出しとして素通しする
  - ACPは2026年7月時点でまだpublic preview段階。ACP非対応でも動くパススルー経路は必ず残す

### 調査済みの各CLIラップ手段（2026年7月時点）

| ツール | ラップ手段 |
|---|---|
| Claude Code CLI | `-p`（printモード）＋`--output-format json`/`stream-json`。`--bg`でバックグラウンド実行→`claude agents`/`attach <id>`/`logs <id>`で外部監視。`-r "<session>"`でセッション再開。認証はAPIキーかサブスク必須 |
| GitHub Copilot CLI | `--server --port 8080`でHTTPサーバー化（`/rpc`にJSON-RPC）。`--acp --port 8080`でACPサーバーモード。Autopilotモードで無介入実行可 |
| Kiro CLI | `KIRO_API_KEY`＋`--no-interactive`によるheadless実行（2026年4月〜、Kiro CLI 2.0）。サーバーモード/ACP対応は未確認 |

---

## 3. UXの適用範囲の境界（決定済み・重要な訂正あり）

TUI/CLI優先の原則は**「開発合意」＝ハーネス/ループが駆動するPO/SM的な意思決定・タスク
ディスパッチ・エージェントセッションの監視というプロセス系UXに限定される**。

**Waffleのspec可視化（OKF graph viewer）はこの原則の対象外**——ドメイン知識を「見る」ための
情報系UXであり、性質が異なる。従来計画通り**ブラウザベースの独立機能として維持する**
（Cytoscape.js+marked.js+mermaid.js、`docs/planning/roadmap.md` Stage C参照）。

- 誤った初期検討（一度提案し撤回済み）: 「WaffleのspecKind階層は木構造だからTUIで代替できる」
  という考え方は誤り。プロセス駆動UX（次の一手を判断・実行する場）と情報閲覧UX（spec間の関連を
  一望する場）は目的が異なり、同じ原則を機械的に両方へ適用すべきではない
- WaffleのCLI操作（`validate`/`render`/`scaffold`等）は、開発合意の**実行アクション**として
  TUIから呼び出されるのは範囲内。Waffle自身のCLIは既に成功時`json.dumps(result.value, ...)`・
  失敗時`{"error": code, "message": ...}`という一貫したJSON出力をしており
  （`src/waffle/adapters/inbound/cli/main.py`）、**この統合にWaffle側の新規作業は不要**
- 未検討: TUI（開発合意）とブラウザ（OKF viewer）の2つのUX面が同じデータ（Waffleのspec）を
  どう共有するか（例: TUI側からOKF viewerを別ウィンドウで開くリンクを提供する等）

---

## 4. 技術スタック（方針決定・実装は未着手）

- **長期の本採用スタック: Rust + ratatui**。理由: 複数CLIエージェントのサブプロセスを並行管理し
  ストリーミング出力を多重化するという本質的に並行処理の問題があり、tokioの非同期ランタイムが
  適する。単一バイナリで配布できる点はLoomDBの「サーバー不要・組込」という設計哲学と一貫する。
  `ratatui`は`gitui`等の実績あるRust製TUIツールを支える成熟フレームワーク。LoomDBで既に
  Rust実装の知見がある
- **直近のPoC（動く最小サンプル検証用）: Python + Textual**。理由: 開発環境にRustツール
  チェーン（cargo/rustc/rustup）が未導入で、即座に検証を始められる環境が必要だったため。
  最小スコープは「Claude Codeを1セッションだけ呼び出し、TUIに出力を表示する」——CLIをTUIで
  ラップするという核心のみを検証する
- **PoC自体はhas-udd/waffleどちらのリポジトリにも配置しない方針**（新リポジトリ未作成のため、
  一旦保留。方針のみ本ドキュメントに記録）

---

## 5. 未決着の論点

- **論点2（新名称）**: 保留中。AI初期見解は`Cadence`（アジャイル業界用語として定着済み・
  ただし「Uber Cadence」という既存ワークフローエンジンと衝突する可能性が高く要事前確認）を
  最有力とし、`Flywheel`・`Relay`を対抗案として提示。ユーザーの最終判断待ち
- **論点1のロールagent再定義との接続**: `brainstorm-has-udd-role-agent-rethink.md`（技術ロール
  ではなくPO/スクラムマスターというプロセス軸でrole agentを構成し直す）との整合は、新プロダクト
  設計が進んだ段階で改めて確認が必要
- **リポジトリ構成**: 新プロダクトがWaffleをgit submoduleとして持つ形は決定済みだが、TUIという
  UI層をどちらのリポジトリが所有するか（ハーネス側が「Waffle用ペイン」を実装するか、Waffle側が
  TUIモードを持ちハーネスが呼び出すだけか）は未決着

---

## 6. 次のアクション

1. 論点2（新名称）の決定
2. 名称確定後、新規リポジトリを作成し、Waffleをgit submoduleとして組み込む
3. Python+TextualでのPoC（Claude Code 1セッション呼び出し）を新リポジトリ内で実施し、
   UXコンセプトを検証する
4. PoCで有望と判断されたら、本採用スタック（Rust+ratatui）への移植を計画する
