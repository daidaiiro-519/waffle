---
id: lang.rust.failure
layer: lang.rust
axes:
  - axis: language
    value: rust
declares: 失敗の運び方
updated: 2026-09-05
---

# Rust における失敗の運び方

## 概要

**回復できる失敗を値で運び、回復できない失敗だけを巻き戻しに任せる。**
この文書の制約は、言語が Rust である場面すべてで効く。

## 決めないこと

| 何を | どこが決めるか |
|---|---|
| どの失敗を利用者へ見せるか | 用途 |
| 失敗をどの層で受けるか | アーキテクチャ |

## 制約

### RS-ERR-01　回復できる失敗は `Result` で返し、`panic!` で流さない

| 欄 | 値 |
|---|---|
| 依存する軸 | 言語＝rust |
| 種別 | コーディング |
| 穴か | 閉じている |

#### 出どころ

| 種類 | 原典 | 原文で照合する文字列 |
|---|---|---|
| 原典 | The Rust Programming Language, ch.9「Error Handling」（落とした日：《YYYY-MM-DD》） | `recoverable` |

#### 検め方

| 誰が | どうやって |
|---|---|
| 機械 | `cargo clippy -- -D clippy::unwrap_used -D clippy::expect_used` |

#### 守った例

```rust
fn read_port(raw: &str) -> Result<u16, ParsePortError> {
    raw.parse::<u16>().map_err(ParsePortError::Invalid)
}
```

#### 破った例

```rust
fn read_port(raw: &str) -> u16 {
    raw.parse::<u16>().unwrap()
}
```

#### 補足

- テストの中の `unwrap` は、この制約の対象外である
- 回復できない失敗（不変条件の破れ）は `panic!` でよい

### RS-ERR-02　失敗の型は、呼び出し側が分岐できる列挙にする

| 欄 | 値 |
|---|---|
| 依存する軸 | 言語＝rust |
| 種別 | コーディング |
| 穴か | ここは各自が決める（列挙の粒度は用途が決める） |

#### 出どころ

| 種類 | 原典 | 原文で照合する文字列 |
|---|---|---|
| 原典 | Rust API Guidelines「Error types are meaningful and well-behaved」（落とした日：《YYYY-MM-DD》） | `error types` |

#### 検め方

| 誰が | どうやって |
|---|---|
| 人 | 失敗の型が `String` や `Box<dyn Error>` になっていないかを見る |

#### 守った例

```rust
pub enum ParsePortError {
    Invalid(std::num::ParseIntError),
    OutOfRange { got: u32 },
}
```

#### 破った例

```rust
pub fn read_port(raw: &str) -> Result<u16, String> { /* … */ }
```

#### 図

```mermaid
flowchart LR
    call[呼び出し側] -->|分岐できる| enum[失敗の列挙]
    call -.->|分岐できない| text[文字列の失敗]
```

## この文書が空けた穴

| 穴 | 誰が埋めるか |
|---|---|
| 失敗の列挙をどこまで細かく分けるか | 用途 |
