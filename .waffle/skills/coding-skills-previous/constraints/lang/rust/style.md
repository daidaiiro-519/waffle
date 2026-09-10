---
id: lang.rust.style
layer: lang.rust
axes:
  - axis: language
    value: rust
category: coding
declares: 綴りと書式
updated: 2026-09-07
approved_by: daidaiiro
approved_at: 2026-09-06
---


# Rust における綴りと書式

## 概要

**書式は整形ツールに委ね、人が判断するのは命名だけにする。**

## 規則一覧

| ID | 規則 | 水準 | 適用範囲 |
|---|---|---|---|
| RS-STY-01 | 書式は `rustfmt` の既定に従い、個別の設定を足さない | 必須 | 全体 |
| RS-STY-02 | 型は `UpperCamelCase`、関数と変数は `snake_case`、定数は `SCREAMING_SNAKE_CASE` | 必須 | 全体 |
| RS-STY-03 | 公開する要素には、何をするかを述べた doc コメントを付ける | 必須 | `pub` の要素 |
| RS-STY-04 | 同じ種類の操作は、同じ語順で名づける | 必須 | 公開する関数 |

## 規則の詳細

### RS-STY-01　書式は `rustfmt` の既定に従い、個別の設定を足さない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 全体 |
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
| 適用範囲 | 全体 |
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
| 適用範囲 | `pub` の要素 |
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

### RS-STY-04　同じ種類の操作は、同じ語順で名づける

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 公開する関数 |
| 根拠 | **語順が割れると、同じことをする関数が別物に見える。**呼ぶ側は、名前から何を返すかを推し量れなくなる |
| 検証方法 | 同じ種類の操作を並べ、語順が1通りかを見る |
| 例外 | 外部の仕様が名前を指定する場合 |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
pub fn calls_of(records: &[Value]) -> Vec<ToolCall>   // <何>_of（…から取る）
pub fn turns_of(records: &[Value]) -> Vec<Turn>
pub fn sources_of(row: &Value) -> Vec<Source>
```

**違反例**

```rust
pub fn session_id_of(raw: &Value) -> Option<&str>     // <何>_of
pub fn received_at(row: &Value) -> Option<f64>        // 同じことをするのに、語順が違う
```

## 整形ツールに委ねる範囲

| 項目 | 誰が決めるか |
|---|---|
| 字下げ・改行・空白・要素の並べ替え | `rustfmt`。人が議論しない |
| 設定の変更 | しない。既定のまま使う |
| 除外 | 生成したコードのみ。手で書いたものは除外しない |
| 検査の位置づけ | 整形されていないことを、変更を取り込む前に落とす |

## 命名

| 対象 | 形 | 例 |
|---|---|---|
| 型・トレイト・列挙の枝 | 語頭を大文字にして繋ぐ | `PortNumber` |
| 関数・変数・モジュール | 小文字と下線で繋ぐ | `read_port` |
| 定数・静的変数 | 大文字と下線で繋ぐ | `MAX_PORT` |
| 変換する関数 | 費用と所有で語頭を分ける | `as_` は借用、`to_` は複製、`into_` は所有を移す |
| 真偽を返す関数 | 述語の文にする | `is_empty` |
| 値を取り出す関数 | `<何>_of` に揃える | `calls_of` ・ `turns_of` |

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

| ID | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| RS-STY-01 | 規格 | rustfmt `Configurations.md`<br>https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md | 2026-09-07 取得（`Default value` 85か所 ・ `rustfmt.toml` 8か所） | 設定ごとに既定が定まっている |
| RS-STY-02 | 規格 | RFC 430 Finalizing naming conventions<br>https://rust-lang.github.io/rfcs/0430-finalizing-naming-conventions.html<br>Rust API Guidelines `C-CASE`<br>https://rust-lang.github.io/api-guidelines/naming.html | 2026-09-07 全文で確認（`C-CASE` は `Casing conforms to RFC 430`） | 綴りの規約と、それを守れという指針 |
| RS-STY-03 | 規格 | rustc lint `missing_docs`<br>https://doc.rust-lang.org/rustc/lints/listing/allowed-by-default.html<br>Rust API Guidelines `C-CRATE-DOC` ・ `C-EXAMPLE` ・ `C-FAILURE`<br>https://rust-lang.github.io/api-guidelines/documentation.html | 2026-09-07 全文で確認（`missing_docs` 5か所 ・ `C-FAILURE` は `Function docs include error, panic, and safety considerations`） | 公開に doc を要求し、何を書くかを定める |
| RS-STY-04 | 文献 | Rust API Guidelines `C-WORD-ORDER`<br>https://rust-lang.github.io/api-guidelines/naming.html | 2026-09-07 全文で確認（`Names use a consistent word order`） | 語順を揃える |
| RS-STY-04 | 実測 | `ctxtrace` の公開関数 62件（2026-09-07）| 11件が `<何>_of`、`session_id_of` と `received_at` が同じことをして語順が割れていた | 語順が実際に割れる |