# Python/ヘキサゴナル構成の採用技術を定めるTech Stack仕様：tech-stack-python-hexagonal

## スタック概要

- **対象領域（ティア: backend=サーバー側 / frontend=画面側 / platform=基盤側）**: backend
- **スタック名**: python-hexagonal

---

## ランタイム

- **言語**: Python 3.12+
- **実行ターゲット**: CLI / ローカルプロセス
- **並行モデル**: 同期主体（MCP 境界のみ async）

---

## フレームワーク

なし（Web フレームワークは使用しない。外部公開は「公開インターフェース」を参照）

---

## 公開インターフェース

### CLI

- **実装**: typer

#### 選定理由

型ヒントから引数解析を自動生成でき、Pythonの型注釈という既存資産をそのままCLI定義に転用できるため

### MCP

- **実装**: fastmcp

#### 選定理由

MCPサーバーの定型的な配線（tool登録・スキーマ変換）を薄く済ませられ、CLIと同じユースケース層をそのまま再利用できるため

---

## ミドルウェア

なし（document.json をファイルとして保存。DB・ブローカー・AP サーバーを持たない）

---

## ライブラリ

### jsonschema

- **分類**: validation
- **用途**: schema-validation
- **バージョン**: ^4

#### 選定理由

document.json自体がJSON Schemaで検証される設計であり、Python標準的なJSON Schema実装として広く使われているため

### 標準 logging

- **分類**: observability
- **用途**: logging

#### 選定理由

ローカルCLI/MCPプロセスであり、外部ロギング基盤との連携要件が無いため、標準ライブラリで十分

### jmespath

- **分類**: query
- **用途**: document-path-query
- **バージョン**: ^1

#### 選定理由

uc-query-documentの17操作のうち10操作（get_field/filter_items/get_items_slice等）を1つの宣言的クエリ式へ統合するために採用。JSONPathより関数・フィルタ式が豊富でPython公式実装が枯れている（AWS CLIの--queryで実績あり）。技術要件（宣言的な絞り込み・射影・スライス、独自関数の登録によるカスタム拡張、blockKeyスコープでのprompt導出との整合）を満たす候補としてjsonpath-ng等も検討したが、カスタム関数拡張機構（jmespath.functions.Functions継承）がfilter_pattern相当の正規表現マッチを同一式言語内に統合するために必須で、spike検証（2026-07-19）で実際に動作を確認済み。標準の想定利用範囲を超えるカスタム関数拡張であるため、アップストリームAPI変更に追従する保守コストが通常のライブラリ利用より高い点は既知のトレードオフとして許容する

---

## 開発ツール

- **パッケージ管理**: uv（.venv / uv.lock 固定）
- **lint / format**: ruff（任意）
- **選定理由**: uvは依存解決とロックファイル管理が高速で、.venv管理も一体化しており、追加のツール(pip/virtualenv/poetry等)を組み合わせる必要がないため

---

## 依存方針

| 種別 | 方針 |
|---|---|
| 必須 | 依存追加は「既存の用途で代替不可か」を確認してから |
| 禁止 | 一覧に無いライブラリを反射的に import する |
| 推奨 | バージョンは範囲指定し uv.lock で固定する |
