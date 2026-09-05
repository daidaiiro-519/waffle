---
id: lang.rust.toolchain
layer: lang.rust
axes:
  - axis: language
    value: rust
category: tech-stack
declares: Rust の標準ツール
updated: 2026-09-05
---

# Rust のツールチェーン

## 概要

**言語に同梱されたツールで整形・静的解析・テストを行い、追加のツールは理由がある場合だけ採用する。**

## 採用するツール

| 用途 | ツール | バージョン指定 | 採用理由 | 代替候補 |
|---|---|---|---|---|
| 整形 | `rustfmt` | ツールチェーンに同梱 | 言語に同梱され、既定で合意が要らない | なし |
| 静的解析 | `clippy` | ツールチェーンに同梱 | 規則の検証方法として指定できる | なし |
| テスト実行 | `cargo test` | ツールチェーンに同梱 | 言語の仕組みで走る | `nextest`（速度が問題になった場合） |
| 依存管理 | `cargo` | ツールチェーンに同梱 | ─ | なし |
| 失敗型の実装 | `thiserror` | `1` | 失敗型の定型実装を減らす | 手書き |

## 採用しないツール

| ツール | 採用しない理由 |
|---|---|
| `anyhow` | 失敗を1つの型へ潰すため、呼び出し側が分岐できなくなる（RS-ERR-02 と衝突する）。実行ファイルの最上位でのみ検討する |
| `unsafe` を前提とする最適化ライブラリ | 失敗の切り分けが難しくなる。性能の問題が観測されてから検討する |

## バージョンの固定

| 対象 | 固定の方法 | 固定するファイル |
|---|---|---|
| ツールチェーン | チャンネルと版を明記する | `rust-toolchain.toml` |
| 依存 | ロックファイルを追跡する | `Cargo.lock` |

## 実行コマンド

| 目的 | コマンド | 実行する場面 |
|---|---|---|
| 整形の確認 | `cargo fmt --check` | コミット前・CI |
| 静的解析 | `cargo clippy --all-targets -- -D warnings` | コミット前・CI |
| テスト | `cargo test --all-targets` | コミット前・CI |
| 依存の監査 | `cargo audit` | CI（日次） |

## 更新の方針

| 対象 | 更新の頻度 | 判断者 |
|---|---|---|
| ツールチェーン | 安定版が出てから1か月後 | 保守者 |
| 依存 | 脆弱性の報告時は即時、それ以外は月次 | 保守者 |

## ライセンス

| 依存 | ライセンス | 可否 |
|---|---|---|
| `thiserror` | MIT または Apache-2.0 | 可 |

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| 実行時の依存（HTTP・シリアライズ等） | 用途 |
| CI の構成 | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| `nextest` を採るか | 用途 | 実行時間が問題になるかは、テストの量で決まる |

## 出典

| ツール | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| `rustfmt` | 規格 | rustfmt 公式ドキュメント<br><small>https://rust-lang.github.io/rustfmt/</small> | 2026-09-05 取得 | `rustfmt` |
| `clippy` | 規格 | Clippy 公式ドキュメント<br><small>https://doc.rust-lang.org/clippy/</small> | 2026-09-05 取得 | `clippy` |
| `thiserror` | 文献 | thiserror の README<br><small>https://rust-lang.github.io/api-guidelines/interoperability.html</small> | 2026-09-05 取得 | `std::error::Error` |