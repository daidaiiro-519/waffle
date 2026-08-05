# design-share

UIモックとDesign.md（デザインシステム定義）を対話で作り、自前のAWS環境（S3 + CloudFront）へトークン保護付きURLとして公開するツール。Claude Code Skillとして会話から使うほか、CLI・ローカルWeb UI・MCPからも直接操作できる。

## これは何か

- **Claude Code Skill**：「UIモックを作りたい」「Design.mdを直したい」と言うだけで、目的のヒアリングからDesign.md確定・UIモック生成・デプロイまでを対話で進める
- **CLI（`scripts/ds.py`）**：Skillが内部で呼んでいるのと同じコマンドを、ターミナルから直接叩ける
- **ローカルWeb UI（`ds.py console`）**：公開状態の一覧・トークン再発行・確定操作等をブラウザで行える（localhost限定）
- **MCP（`scripts/mcp_server.py`）**：MCP対応クライアントから管理操作をツールとして呼べる

4つの入り口はすべて同じスクリプト（`ds.py`）に委譲されており、実体は1つ。

## 導入（一度だけ）

design-shareはAWS上に自分専用の配信基盤（S3 + CloudFront + CloudFront Functions + KVS）を持つ。この構築は**プロジェクトへの導入時に一度だけ**行い、以降の会話・利用では意識しない。

```bash
cd .claude/skills/design-share
uv run scripts/ds.py init
```

対話式にAWSプロファイル・リージョン・スタック名・S3バケット名を確認し、既存スタックがあれば再利用、無ければCloudFormationで新規構築する（課金が発生するため作成前に確認が入る）。完了すると `design-share.env` が書き出され、以降のすべてのコマンド・Skillの会話がこれを読んで動く。

要件：`uv`がインストール済みで、AWS認証情報が設定されていること（`aws sso login`等）。

環境を壊す場合は対になる `uv run scripts/ds.py destroy` を使う。

## 使い方

導入後は、AWSの存在を意識する必要はない。

- **Skillとして**：Claude Codeで「UIモックを作りたい」「Design.mdを直したい」と話しかける（SKILL.mdの実行手順に沿って進む）
- **CLIとして**：`uv run scripts/ds.py <command>`（`--help`で一覧）
- **Web UIとして**：`uv run scripts/ds.py console` でlocalhostに管理画面を起動
- **MCPとして**：`scripts/mcp_server.py` をMCPクライアントに登録

主なコマンド：

| コマンド | 用途 |
|---|---|
| `deploy <html> "<表示名>"` | パターンをデプロイ（slug＋トークン発行） |
| `deploy --design <DESIGN.md> <spec.html> "<名>"` | DESIGN.md視覚スペックシートをレビュー用に公開 |
| `redeploy <slug> <html>` | 既存パターンの内容だけ差し替え（URL・トークン・コメントは維持） |
| `confirm-design <slug> [--to <dir>]` | レビュー済みDESIGN.mdを正式配置（1プロジェクトにつき常に1つ） |
| `confirm <slug>` / `unconfirm <slug>` | UIモックの確定/取消（複数同時確定可） |
| `list` / `export <slug>` / `rotate <slug>` / `disable <slug>` | 一覧・エクスポート・トークン再発行・無効化 |
| `project create/list/add/remove/set/export` | プロジェクト（名前付きギャラリー）の管理 |
| `console` | ローカルWeb管理コンソールを起動 |
| `smoke` | 実機スモークテスト（使い捨てパターンで往復検証） |

## フォルダ構成

成果物はプロジェクトフォルダの `.design-share/<プロジェクト名>/` 配下に置く（design-share自身の運用ではこのSkillディレクトリ内、通常の利用ではリポジトリのルート）。

```
.design-share/<プロジェクト名>/
├── DESIGN.md          # 確定済みデザインシステム定義（コミット対象）
├── mocks/             # デプロイ用UIモックHTML一式（コミット対象）
├── preview/           # DESIGN.mdのレンダリング確認用（.gitignore対象、再生成可）
├── backups/           # 確定時の.bak退避（.gitignore対象）
└── exports/           # エクスポートしたzip（.gitignore対象）
```

ローカル/クラウドの同期状態はマニフェストファイルを持たず、その場でハッシュ比較して判定する（複数人・複数マシンで触っても機械的に食い違わない）。

## 中核概念

- **Design.md**：google-labs-code/design.md仕様のYAMLトークン＋Markdown本文。色・タイポグラフィ・レイアウト等の固定順セクションを持つ、コーディングエージェント向けのビジュアルアイデンティティ文書
- **プロジェクト**：1つのDesign.md（確定済みは常に1つ）と、複数のUIモック（同時に複数確定可）をまとめる単位
- **パターン**：1つのUIモックHTML。パターン単位でURL＋トークンが発行される
- **敵対的測定**：生成したUIモックを自己批評だけで完成としない。コンセプト・レイアウト・デザインの3ゲートで独立した検証をかけてから確定する

詳細な設計判断・ガードレールはSKILL.mdを参照。
