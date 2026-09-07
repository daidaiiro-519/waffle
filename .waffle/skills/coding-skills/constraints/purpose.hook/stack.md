---
id: purpose.hook.stack
layer: purpose.hook
axes:
  - axis: purpose
    value: hook
provides:
  architecture: data-port
  runtime: per-invocation
category: tech-stack
declares: 実行時に使うツールと依存
updated: 2026-09-05
approved_by: daidaiiro
approved_at: 2026-09-06
---

# Hook の実行時の依存

## 概要

**起動のたびに払う費用を小さく保つため、実行時の依存を最小にする。**

## 採用するアーキテクチャ

| 軸 | 値 | 採用理由 |
|---|---|---|
| アーキテクチャ | `data-port` | 中心が外部の機能を必要とせず、写して確かめて出すだけで閉じる。反転が要らない |
| 実行環境 | `per-invocation` | 呼び出しごとに1件を処理して終わる |

**別の用途が `hexagonal` を採ってもよい。**
軸は値を複数持ち、どれを採るかはこの規約が指定する。

## 採用する依存

| 用途 | ツール | バージョン指定 | 採用理由 | 代替候補 |
|---|---|---|---|---|
| JSON の解釈と生成 | `serde` ＋ `serde_json` | `1` | 契約が JSON で、型と対応づけられる | 手書きの解析 |
| 診断の出力 | `tracing` ＋ `tracing-subscriber` | `0.3` | 標準エラーへの出力先を差し替えられる | `eprintln!` |
| 失敗型の実装 | `thiserror` | `1` | 言語の規約（RS-ERR-04）を満たす | 手書き |

## 採用しない依存

| ツール | 採用しない理由 |
|---|---|
| 非同期の実行環境（`tokio` 等） | 呼び出しごとに1件を処理するだけで、並行の必要がない。起動の費用だけが増える |
| HTTP クライアント | 契約が標準入出力であり、外部への通信を持たない |
| 設定用のフレームワーク | 読む設定が少なく、環境変数で足りる |

## バージョンの固定

| 対象 | 固定の方法 | 固定するファイル |
|---|---|---|
| 依存 | ロックファイルを追跡する | `Cargo.lock` |
| 実行ファイル | 版を埋め込み、応答に含める | `Cargo.toml` |

## 実行コマンド

| 目的 | コマンド | 実行する場面 |
|---|---|---|
| ビルド | `cargo build --release` | 配布時 |
| 端から端までのテスト | `cargo test --test hook_stdio` | コミット前・CI |
| 起動時間の確認 | `hyperfine './target/release/hook < fixtures/request.json'` | 変更時 |

## 更新の方針

| 対象 | 更新の頻度 | 判断者 |
|---|---|---|
| 実行時の依存 | 脆弱性の報告時は即時、それ以外は四半期ごと | 保守者 |

## ライセンス

| 依存 | ライセンス | 可否 |
|---|---|---|
| `serde` ・ `serde_json` | MIT または Apache-2.0 | 可 |
| `tracing` | MIT | 可 |
| `thiserror` | MIT または Apache-2.0 | 可 |

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| 整形・静的解析・テスト実行のツール | 言語 |
| 依存の書き方 | 言語 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 診断の出力形式（人が読む形か、機械が読む形か） | 実装 | 呼び出し元の運用で変わる |

## 出典

| ツール | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| `serde_json` | 文献 | serde_json の公式ドキュメント<br>https://docs.rs/serde_json/latest/serde_json/ | 2026-09-06 取得 | JSON の読み書き |
| `tracing` | 文献 | tracing の公式ドキュメント<br>https://docs.rs/tracing/latest/tracing/ | 2026-09-06 取得 | 記録の出し方 |