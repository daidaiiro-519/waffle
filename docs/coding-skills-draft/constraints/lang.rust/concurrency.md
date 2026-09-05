---
id: lang.rust.concurrency
layer: lang.rust
axes:
  - axis: language
    value: rust
category: coding
declares: 並行の単位と、共有の扱い
updated: 2026-09-05
---

# Rust における並行の扱い

## 概要

**共有せずに渡すことを既定とし、共有するなら所有と借用の規則で守る。**

## 並行の単位

| 単位 | 何を表すか | いつ使うか |
|---|---|---|
| スレッド | OS が割り当てる実行の単位 | 処理が計算で詰まるとき |
| 非同期タスク | 実行環境が切り替える軽い単位 | 待ちが多いとき。実行環境の採用は用途が決める |
| プロセス | 独立した実行 | 失敗を隔離したいとき |

## 規則一覧

| ID | 規則 | 水準 | 検証方法 | 適用範囲 |
|---|---|---|---|---|
| RS-CON-01 | 状態を共有せず、所有権を渡して受け渡す | 必須 | レビュー | 全体 |
| RS-CON-02 | 共有が必要なら、`Arc` と同期の型で包み、素の可変参照を跨がせない | 必須 | 静的解析 | 全体 |
| RS-CON-03 | ロックを持ったまま、待つ操作を呼ばない | 必須 | レビュー | ロックを使う箇所 |
| RS-CON-04 | 非同期の実行環境を、ライブラリの公開 API に現さない | 必須 | レビュー | ライブラリの crate |

## 規則の詳細

### RS-CON-01　状態を共有せず、所有権を渡して受け渡す

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 共有しなければ、競合そのものが起きない |
| 検証方法 | 共有された可変状態が在るかを見る |
| 例外 | 読むだけの共有 |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
let (tx, rx) = std::sync::mpsc::channel();
std::thread::spawn(move || tx.send(build_report()).ok());
```

**違反例**

```rust
static mut TOTAL: usize = 0;
```

### RS-CON-03　ロックを持ったまま、待つ操作を呼ばない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | ロックの保持中に待つと、待ち時間の分だけ他が止まる |
| 検証方法 | ロックの範囲に入出力・待機が入っていないかを見る |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
let snapshot = { state.lock().unwrap().clone() };
write_to_disk(&snapshot)?;
```

**違反例**

```rust
let guard = state.lock().unwrap();
write_to_disk(&guard)?;
```

### RS-CON-04　非同期の実行環境を、ライブラリの公開 API に現さない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 実行環境を公開に出すと、利用側の選択を奪う |
| 検証方法 | 公開する型・関数に実行環境固有の型が出ていないかを見る |
| 例外 | 実行ファイルの crate |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
pub fn parse(input: &[u8]) -> Result<Record, ParseError> { /* 入出力を持たない */ }
```

**違反例**

```rust
pub async fn parse(input: tokio::fs::File) -> Result<Record, ParseError> { /* … */ }
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| 非同期の実行環境を採るかどうか | 用途 |
| 並行度の上限 | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| チャネルの種類（同期・非同期・容量） | 用途 | 流れる量と待ちの許容で決まる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| RS-CON-01 | 文献 | The Rust Programming Language ch.16 Fearless Concurrency<br>https://doc.rust-lang.org/book/ch16-02-message-passing.html | 2026-09-05 取得 | `Message Passing` |
| RS-CON-02 | 規格 | Rust std `Arc` ・ `Mutex`<br>https://doc.rust-lang.org/book/ch16-02-message-passing.html | 2026-09-05 取得 | `Message Passing` |
| RS-CON-04 | 文献 | Rust API Guidelines（公開 API の設計）<br>https://rust-lang.github.io/api-guidelines/naming.html | 2026-09-05 取得 | `naming` |