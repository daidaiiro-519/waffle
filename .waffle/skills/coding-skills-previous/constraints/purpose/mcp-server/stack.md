---
id: purpose.mcp-server.stack
layer: purpose.mcp-server
axes:
  - axis: purpose
    value: mcp-server
provides:
  architecture: hexagonal
  runtime: resident
category: tech-stack
declares: 採用するアーキテクチャ・実行環境・実行時の依存
updated: 2026-09-05
approved_by: daidaiiro
approved_at: 2026-09-06
---

# MCP サーバーの技術構成

## 概要

**受け取って写し、能力を呼んで返すだけなので、反転を持たない構成を採る。**

## 採用するアーキテクチャ

| 軸 | 値 | 採用理由 |
|---|---|---|
| アーキテクチャ | `hexagonal` | 外部から呼ばれて、メッセージを写して業務操作を呼ぶだけで閉じる。**一次のポートだけを持ち、二次のポートを持たない** ── 原文が「It doesn't appear that there is any particular damage in choosing the "wrong" number of ports」と述べており、ポートの数は構成の要件ではない |
| 実行環境 | `resident` | 接続のあいだ生き続ける |

**業務操作が外部（記憶・他のサービス）を必要とするなら、二次のポートを足す。**構成は替えない。
その判断は、提供する能力が決まった時点で見直す。

## 採用する依存

| 用途 | 依存 | バージョン指定 | 採用理由 | 代替候補 |
|---|---|---|---|---|
| メッセージの解釈と生成 | `serde` ＋ `serde_json` | `1` | 契約が JSON で、型と対応づけられる | 手書きの解析 |
| 失敗型の実装 | `thiserror` | `1` | 言語の規約を満たす | 手書き |
| 診断の出力 | `tracing` ＋ `tracing-subscriber` | `0.3` | 標準エラーへの出力先を差し替えられる | `eprintln!` |
| 手順の実装 | `rmcp` | `0.x`（版を固定する） | **手順は仕様が定めており、写して持つ価値が無い。**公式の Rust 実装が在り、`ServerHandler` を満たす形で能力を出せる | 自前で書く（仕様の変化に自分で追随することになる） |

## 採用しない依存

| 依存 | 採用しない理由 |
|---|---|
| HTTP クライアント | 経路が標準入出力であり、外部への通信を持たない |
| 大きな非同期の実行環境 | `rmcp` が要求する範囲でだけ使う。それを超えて広げない |
| 手順の自前実装 | 仕様の版が上がるたびに、こちらが追随することになる。**手順は差別化する場所ではない** |

## バージョンの固定

| 対象 | 固定の方法 | 固定するファイル |
|---|---|---|
| 依存 | ロックファイルを追跡する | `Cargo.lock` |

## 実行コマンド

| 目的 | コマンド | 実行する場面 |
|---|---|---|
| ビルド | `cargo build --release` | 配布時 |
| 端から端までのテスト | `cargo test --test mcp_stdio` | コミット前・CI |

## ライセンス

| 依存 | ライセンス | 可否 |
|---|---|---|
| `serde` ・ `serde_json` | MIT または Apache-2.0 | 可 |
| `tracing` | MIT | 可 |

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| 整形・検査・テスト実行のツール | 言語 |
| 提供する能力の中身 | 業務操作 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 手順の実装を採るか自前で書くか | 実装 | 仕様の原典を読んでから決める |

## 出典

| 依存 | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| `serde_json` | 文献 | serde_json の公式ドキュメント<br>https://docs.rs/serde_json/latest/serde_json/ | 2026-09-06 取得 | JSON の読み書き |
| 手順 | 規格 | Model Context Protocol の仕様<br>https://modelcontextprotocol.io/specification/2025-06-18 | 2026-09-06 取得 | 能力の申告 |
| `rmcp` | 文献 | rmcp の公式ドキュメント<br>https://docs.rs/rmcp/latest/rmcp/ | 2026-09-06 取得 | サーバーの実装 |