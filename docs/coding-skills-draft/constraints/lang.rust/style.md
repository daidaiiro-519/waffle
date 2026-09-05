---
id: lang.rust.style
layer: lang.rust
axes:
  - axis: language
    value: rust
category: coding
declares: 綴りと書式
updated: 2026-09-05
---

# Rust における綴りと書式

## 概要

**書式は整形ツールに委ね、人が判断するのは命名だけにする。**

## 規則一覧

| ID | 規則 | 水準 | 検証方法 | 適用範囲 |
|---|---|---|---|---|
| RS-STY-01 | 書式は `rustfmt` の既定に従い、個別の設定を足さない | 必須 | 静的解析 | 全体 |
| RS-STY-02 | 型は `UpperCamelCase`、関数と変数は `snake_case`、定数は `SCREAMING_SNAKE_CASE` | 必須 | 静的解析 | 全体 |
| RS-STY-03 | 公開する要素には、何をするかを述べた doc コメントを付ける | 必須 | 静的解析 | `pub` の要素 |
| RS-STY-04 | 型名に実装技術を含めない。含めてよいのは外部と接する要素だけ | 必須 | レビュー | 業務の型 |

## 規則の詳細

### RS-STY-01　書式は `rustfmt` の既定に従い、個別の設定を足さない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 書式の議論を消すために整形ツールを使うので、設定を足すと議論が戻る |
| 検証方法 | `cargo fmt --check` |
| 例外 | なし |
| 既存コードへの適用 | 一括是正 |

**適合例**

```toml
# rustfmt.toml は置かない
```

**違反例**

```toml
max_width = 120
fn_single_line = true
```

### RS-STY-02　型は `UpperCamelCase`、関数と変数は `snake_case`、定数は `SCREAMING_SNAKE_CASE`

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 言語の標準に合わせないと、読み手が綴りから種類を判断できない |
| 検証方法 | `cargo clippy -- -D non_snake_case -D non_camel_case_types` |
| 例外 | 外部の仕様が綴りを指定する場合（属性で個別に無効化する） |
| 既存コードへの適用 | 一括是正 |

**適合例**

```rust
pub struct HookRequest;
pub fn parse_request(raw: &str) -> Result<HookRequest, ParseError> { /* … */ }
pub const MAX_PAYLOAD_BYTES: usize = 1 << 20;
```

**違反例**

```rust
pub struct hook_request;
pub fn ParseRequest(raw: &str) { /* … */ }
```

### RS-STY-03　公開する要素には、何をするかを述べた doc コメントを付ける

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 公開要素は呼び出し側の契約であり、契約の説明がないと使い方が実装依存になる |
| 検証方法 | `cargo clippy -- -D missing_docs` |
| 例外 | 自明な再公開（`pub use`） |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
/// 標準入力から届いた要求を解釈する。
///
/// # Errors
/// 形式が壊れている場合に `ParseError` を返す。
pub fn parse_request(raw: &str) -> Result<HookRequest, ParseError> { /* … */ }
```

**違反例**

```rust
pub fn parse_request(raw: &str) -> Result<HookRequest, ParseError> { /* … */ }
```

### RS-STY-04　型名に実装技術を含めない。含めてよいのは外部と接する要素だけ

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 業務の語彙に技術が混ざると、技術を替えたときに名前が嘘になる |
| 検証方法 | 業務の型に技術名（Json・Sqlite・Http）が入っていないかを見る |
| 例外 | 外部と接する要素は、技術を明示してよい |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
pub struct HookRequest;          // 業務の型
pub struct JsonHookCodec;        // 外部と接する要素
```

**違反例**

```rust
pub struct JsonHookRequest;      // 業務の型に技術が入っている
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| 層ごとの命名の当て方 | 言語 × アーキテクチャ |
| 公開範囲をどこまで広げるか | 言語 × アーキテクチャ |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| doc コメントに書く節の種類 | 用途 | 読み手が誰かで、必要な節が変わる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| RS-STY-01 | 規格 | rustfmt 既定設定 | 《版・取得日》 | `default` |
| RS-STY-02 | 規格 | Rust Reference / Naming conventions（RFC 430） | 《版・取得日》 | `UpperCamelCase` |
| RS-STY-03 | 規格 | rustc lint `missing_docs` | 《版・取得日》 | `missing_docs` |
| RS-STY-04 | 文献 | Rust API Guidelines C-WORD-ORDER | 《版・取得日》 | `naming` |
