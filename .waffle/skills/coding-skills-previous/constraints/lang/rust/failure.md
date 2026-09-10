---
id: lang.rust.failure
layer: lang.rust
axes:
  - axis: language
    value: rust
category: coding
declares: 失敗の運び方
updated: 2026-09-07
approved_by: daidaiiro
approved_at: 2026-09-06
---


# Rust における失敗の運び方

## 概要

**回復可能な失敗を値として運び、回復不能な失敗だけをパニックに任せる。**

## 失敗の区分

| 区分 | 意味 | 表し方 | 呼び出し元の扱い |
|---|---|---|---|
| 回復できる失敗 | 入力や外部の状態が想定の範囲で崩れた | `Result::Err` | 受け取って分岐する |
| 回復できない失敗 | 前提そのものが壊れている（不変条件の破れ） | `panic!` | 受け取らない。プロセスが終わる |
| 想定していない状態 | 実装の誤り | `unreachable!` ／ `debug_assert!` | 開発時に落として気づく |

**外から与えられたものの不備は、回復できる失敗である。**
入力の検査に `panic!` を使うと、呼び出し元は分岐する手段を失う。

## 失敗の型

| 項目 | 定め |
|---|---|
| 型の作り方 | 失敗の種類ごとに列挙の枝を作り、枝ごとに必要な値を持たせる |
| 表示 | `Display` を実装し、何が起きたかを一文で述べる。原因の値を含める |
| 連鎖 | 元の失敗を `source` として保つ。握りつぶさない |
| 変換 | 境界を越えるところで、自分の層の型へ写す |
| 公開 | 公開する関数の失敗の型は、公開の一部として扱う。枝を消すのは壊れる変更である |

## 規則一覧

| ID | 規則 | 水準 | 適用範囲 |
|---|---|---|---|
| RS-ERR-01 | 回復可能な失敗は `Result` で返し、`panic!` で流さない | 必須 | 公開関数すべて |
| RS-ERR-02 | 失敗型は `std::error::Error` ・ `Send` ・ `Sync` を実装する | 必須 | 公開関数の失敗型 |
| RS-ERR-03 | `Result` を捨てない。捨てる場合は理由を残す | 必須 | 全体 |
| RS-ERR-04 | `()` を失敗型にしない。運ぶ値が無くても、名前のある型を作る | 必須 | 公開関数の失敗型 |

## 規則の詳細

### RS-ERR-01　回復可能な失敗は `Result` で返し、`panic!` で流さない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 公開関数すべて |
| 根拠 | 呼び出し側が回復の可否を選べなくなり、失敗が制御の外へ出る |
| 検証方法 | `cargo clippy -- -D clippy::unwrap_used -D clippy::expect_used` |
| 例外 | テストコード。および不変条件が破れた場合（回復不能） |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
fn read_port(raw: &str) -> Result<u16, ParsePortError> {
    raw.parse::<u16>().map_err(ParsePortError::Invalid)
}
```

**違反例**

```rust
fn read_port(raw: &str) -> u16 {
    raw.parse::<u16>().unwrap()
}
```

### RS-ERR-02　失敗型は `std::error::Error` ・ `Send` ・ `Sync` を実装する

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 公開関数の失敗型 |
| 根拠 | **`Error` が無いと、連鎖（`source`）を辿れない。**`Send` が無い失敗は `thread::spawn` から返せず、`Sync` が無い失敗は `Arc` で跨げない。`String` は `Error` を実装しないので、この規則で除かれる |
| 検証方法 | `Send + Sync + 'static` を要求する試験を1本置く（`crates/cli/tests/error_types.rs`）。**型で落ちる** |
| 例外 | 内部専用の失敗型 |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
#[derive(Debug, thiserror::Error)]
pub enum ParsePortError {
    #[error("port is not a number: {0}")]
    Invalid(#[from] std::num::ParseIntError),
    #[error("port out of range: {got}")]
    OutOfRange { got: u32 },
}
```

**違反例**

```rust
pub fn read_port(raw: &str) -> Result<u16, String> { /* … */ }
```

### RS-ERR-03　`Result` を捨てない。捨てる場合は理由を残す

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 全体 |
| 根拠 | 捨てた失敗は観測できず、原因の切り分けができなくなる |
| 検証方法 | `cargo clippy -- -D unused_must_use` |
| 例外 | なし |
| 既存コードへの適用 | 一括是正 |

**適合例**

```rust
if let Err(error) = flush() {
    tracing::warn!(%error, "flush failed; retrying on next start");
}
```

**違反例**

```rust
let _ = flush();
```

### RS-ERR-04　`()` を失敗型にしない。運ぶ値が無くても、名前のある型を作る

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 公開関数の失敗型 |
| 根拠 | **`()` は `Error` も `Display` も実装しない。**呼び出し側は文面を自分で書くしかなく、`?` でも運べない |
| 検証方法 | `Result<_, ()>` を返す公開関数が無いことを数える |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
#[derive(Debug, thiserror::Error)]
#[error("failed to load config from {path}")]
pub struct LoadConfigError {
    path: String,
    #[source]
    cause: std::io::Error,
}
```

**違反例**

```rust
pub fn load() -> Result<Config, ()> { /* … */ }
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| どの失敗を利用者へ提示するか | 用途 |
| 失敗をどの層で受け止めるか | アーキテクチャ |
| 失敗の記録先 | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 失敗の列挙をどこまで細分するか | 用途 | 分岐の必要は、外部との契約で決まる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| RS-ERR-01 | 文献 | The Rust Programming Language ch.9 Error Handling<br>https://doc.rust-lang.org/book/ch09-00-error-handling.html | 2026-09-07 全文で確認（`recoverable` 14か所 ・ `unrecoverable` 6か所） | 回復できる失敗と回復できない失敗 |
| RS-ERR-02 | 文献 | Rust API Guidelines `C-GOOD-ERR`<br>https://rust-lang.github.io/api-guidelines/interoperability.html | 2026-09-07 全文で確認（`error types should implement the Send and Sync traits`） | 失敗型が満たすべき3つ |
| RS-ERR-03 | 規格 | Rust Reference `must_use` 属性<br>https://doc.rust-lang.org/reference/attributes/diagnostics.html | 2026-09-07 全文で確認（`must_use` 63か所） | 戻り値を捨てさせない |
| RS-ERR-04 | 文献 | Rust API Guidelines `C-GOOD-ERR`<br>https://rust-lang.github.io/api-guidelines/interoperability.html | 2026-09-07 全文で確認（`Never use () as an error type`） | `()` を禁じる |
| RS-ERR-02 | 実測 | `ctxtrace` の公開する失敗型 4件（2026-09-07）| `LoadError` ・ `SchemaSqlError` ・ `DispatchError` ・ `NormalizeError`。`Send` ・ `Sync` は満たしていたが、**守る試験が無かった** | 満たしていても、黙って崩れる |