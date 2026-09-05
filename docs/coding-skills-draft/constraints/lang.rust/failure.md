---
id: lang.rust.failure
layer: lang.rust
axes:
  - axis: language
    value: rust
category: coding
declares: 失敗の運び方
updated: 2026-09-05
---

# Rust における失敗の運び方

## 概要

**回復可能な失敗を値として運び、回復不能な失敗だけをパニックに任せる。**

## 規則一覧

| ID | 規則 | 水準 | 検証方法 | 適用範囲 |
|---|---|---|---|---|
| RS-ERR-01 | 回復可能な失敗は `Result` で返し、`panic!` で流さない | 必須 | 静的解析 | 公開関数すべて |
| RS-ERR-02 | 失敗型は、呼び出し側が分岐できる列挙にする | 必須 | レビュー | 公開関数の失敗型 |
| RS-ERR-03 | `Result` を捨てない。捨てる場合は理由を残す | 必須 | 静的解析 | 全体 |
| RS-ERR-04 | 失敗型は `std::error::Error` を実装する | 必須 | 静的解析 | 公開する失敗型 |

## 規則の詳細

### RS-ERR-01　回復可能な失敗は `Result` で返し、`panic!` で流さない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
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

### RS-ERR-02　失敗型は、呼び出し側が分岐できる列挙にする

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 文字列の失敗は分岐に使えず、呼び出し側は文面の一致で判定するしかなくなる |
| 検証方法 | 公開関数の失敗型が `String` ・ `Box<dyn Error>` になっていないかを見る |
| 例外 | 実行ファイルの最上位（`main`）は集約した失敗型でよい |
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

### RS-ERR-04　失敗型は `std::error::Error` を実装する

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 実装がないと、呼び出し側で連鎖（`source`）を辿れない |
| 検証方法 | `cargo clippy -- -D clippy::missing_errors_doc` と、公開型の実装確認 |
| 例外 | 内部専用の失敗型 |
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
#[derive(Debug)]
pub struct LoadConfigError(String);
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

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| RS-ERR-01 | 文献 | The Rust Programming Language ch.9 Error Handling<br>https://doc.rust-lang.org/book/ch09-00-error-handling.html | 2026-09-05 取得 | `recoverable` |
| RS-ERR-02 | 文献 | Rust API Guidelines C-GOOD-ERR<br>https://rust-lang.github.io/api-guidelines/interoperability.html | 2026-09-05 取得 | `error types` |
| RS-ERR-03 | 規格 | Rust std `#[must_use]`<br>https://doc.rust-lang.org/std/result/index.html | 2026-09-05 取得 | `must_use` |
| RS-ERR-04 | 文献 | Rust API Guidelines（相互運用・失敗型）<br>https://rust-lang.github.io/api-guidelines/interoperability.html | 2026-09-05 取得 | `std::error::Error` |