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

**回復できる失敗を値で運び、回復できない失敗だけを巻き戻しに任せる。**

## 規則

| 印 | 規則 | 水準 | 検証 |
|---|---|---|---|
| RS-ERR-01 | 回復できる失敗は `Result` で返し、`panic!` で流さない | 必須 | 機械 |
| RS-ERR-02 | 失敗の型は、呼び出し側が分岐できる列挙にする | 必須 | 人 |
| RS-ERR-03 | 失敗を握りつぶさない。捨てるなら、捨てる理由を書く | 必須 | 機械 |

## 規則ごとの詳細

### RS-ERR-01　回復できる失敗は `Result` で返し、`panic!` で流さない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 検証 | `cargo clippy -- -D clippy::unwrap_used -D clippy::expect_used` |
| 例外 | テストの中と、不変条件が破れた場合（回復できない失敗） |

```rust
fn read_port(raw: &str) -> Result<u16, ParsePortError> {
    raw.parse::<u16>().map_err(ParsePortError::Invalid)
}
```

```rust
fn read_port(raw: &str) -> u16 {
    raw.parse::<u16>().unwrap()
}
```

### RS-ERR-02　失敗の型は、呼び出し側が分岐できる列挙にする

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 検証 | 失敗の型が `String` や `Box<dyn Error>` になっていないかを見る |
| 例外 | 無い |

```rust
pub enum ParsePortError {
    Invalid(std::num::ParseIntError),
    OutOfRange { got: u32 },
}
```

```rust
pub fn read_port(raw: &str) -> Result<u16, String> { /* … */ }
```

### RS-ERR-03　失敗を握りつぶさない。捨てるなら、捨てる理由を書く

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 検証 | `cargo clippy -- -D unused_must_use` |
| 例外 | 無い |

```rust
if let Err(e) = flush() {
    // 書き出しの失敗は、次の起動で回復する
    tracing::warn!(error = %e, "flush failed");
}
```

```rust
let _ = flush();
```

## 対象外

| 何を | どの層が決めるか |
|---|---|
| どの失敗を利用者へ見せるか | 用途 |
| 失敗をどの層で受けるか | アーキテクチャ |

## 下位へ委ねる判断

| 委ねる判断 | 委ねる先 | 委ねる理由 |
|---|---|---|
| 失敗の列挙をどこまで細かく分けるか | 用途 | 分岐の必要は、外との契約で決まる |

## 出典

| 印 | 種類 | 原典 | 照合する文字列 |
|---|---|---|---|
| RS-ERR-01 | 原典 | The Rust Programming Language, ch.9 Error Handling（落とした日：《YYYY-MM-DD》） | `recoverable` |
| RS-ERR-02 | 原典 | Rust API Guidelines, C-GOOD-ERR（落とした日：《YYYY-MM-DD》） | `error types` |
| RS-ERR-03 | 原典 | Rust std, `#[must_use]` の説明（落とした日：《YYYY-MM-DD》） | `must_use` |
