---
id: lang.rust+arch.data-port.test-placement
layer: lang.rust+arch.data-port
axes:
  - axis: language
    value: rust
  - axis: architecture
    value: data-port
category: test
declares: テストの置き場所
updated: 2026-09-06
approved_by: daidaiiro
approved_at: 2026-09-06
---


# crate ごとのテストの置き場所

## 概要

**テストは、その crate の中に置く。crate の境界が、そのままテストの境界になる。**

## 置き場所の対応

| crate | 置き場所 | 何を確かめるか | 呼び方 |
|---|---|---|---|
| `contract` | 同じファイルの `mod tests` | 生成した型に schema の制約が効くこと | 生成した型に値を入れて呼ぶ |
| `core` | 同じファイルの `mod tests` | データ契約の上の処理 | 契約の型を組み立てて渡す |
| `adapters/<接続先>` | 同じファイルの `mod tests` ／ `tests/` | 生の入力が契約の型へ正しく写ること | `normalize` を実物の入力で呼ぶ |
| `bundle` | `bundle/tests/` | 接続先の振り分けが漏れなく効くこと | 公開 API だけを呼ぶ |
| `cli` | `tests/` | 入口から出口までの一続き | 実行ファイルを起動して呼ぶ |

## 偽物の置き場所

| 偽物 | 置き場所 | 作り方 | 置いてはならない場所 |
|---|---|---|---|
| 実物の入力 | `adapters/<接続先>/src/fixtures/` | 接続先が実際に出した記録をそのまま置く | 共有の置き場。接続先どうしが結び付く |
| 契約の型の見本 | `contract` crate の `#[cfg(test)]` | 生成した型を組み立てる補助 | `core`。組み立て方が処理側に散る |
| 外部技術の偽物 | 置かない | ─ | 写し手は関数なので、実物の入力を渡せば足りる |

## 規則一覧

| ID | 規則 | 水準 | 適用範囲 |
|---|---|---|---|
| RD-TP-01 | 各 crate の単体テストは、対象と同じファイルの `mod tests` に置く | 必須 | すべての crate |
| RD-TP-03 | 束ねの結合テストは `bundle/tests/` に置き、公開 API だけを呼ぶ | 必須 | 束ね |
| RD-TP-06 | 写し手が共通で通す試験の集合は、別の crate に置き、各写し手が `[dev-dependencies]` で引く | 必須 | 写し手 |

## 規則の詳細

### RD-TP-01　各 crate の単体テストは、対象と同じファイルの `mod tests` に置く

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | すべての crate |
| 根拠 | crate の外から呼ぶと、公開範囲を広げることになる |
| 検証方法 | 各 crate に `#[cfg(test)] mod tests` が在るかを見る |
| 例外 | 生成された型だけの crate |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
// crates/core/src/normalize.rs
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn 欠けた欄には理由が付く() { /* … */ }
}
```

**違反例**

```rust
// crates/core/tests/normalize.rs から内部関数を呼ぶために pub にした
pub fn normalize_inner(/* … */) { /* … */ }
```

### RD-TP-03　束ねの結合テストは `bundle/tests/` に置き、公開 API だけを呼ぶ

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 束ね |
| 根拠 | `tests/` の各ファイルは別の crate としてコンパイルされる。公開 API 以外は呼べない |
| 検証方法 | 当たる命令が無い。`bundle/tests/` の各ファイルが `use bundle::` だけを使い、他の crate を直接呼んでいないかを見る |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
// bundle/tests/roundtrip.rs
use bundle::{convert, Format};

#[test]
fn converts_every_registered_format() {
    for f in Format::all() {
        assert!(convert(f, SAMPLE).is_ok());
    }
}
```

**違反例**

```rust
// bundle/tests/roundtrip.rs
use core::pipeline::Stage;
```

### RD-TP-06　写し手が共通で通す試験の集合は、別の crate に置き、各写し手が `[dev-dependencies]` で引く

**通すこと自体は `arch.data-port/test-boundaries.md` の DP-TB-05 が定める。**
ここで決めるのは Rust での置き場所だけである。

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 写し手 |
| 根拠 | `adapters/common` に通常の依存として置くと、判定の側が本番の成果物へ入る。`[dev-dependencies]` なら入らない ── 原典が「Dev-dependencies are not used when compiling a package for building, but are used for compiling tests」と述べている。あわせて、依存元へ伝播しないので写し手どうしも結び付かない |
| 検証方法 | 試験の集合を持つ crate が、どの写し手からも `[dev-dependencies]` でのみ引かれていることを見る |
| 例外 | なし |
| 既存コードへの適用 | 一括是正 |

**適合例**

```toml
# adapters/claude_code/Cargo.toml
[dev-dependencies]
contract-test-kit = { path = "../contract-test-kit" }
```

```rust
// adapters/claude_code/src/lib.rs
#[cfg(test)]
mod tests {
    use super::*;
    const RAW: &str = include_str!("fixtures/tool_use.json");
    #[test]
    fn 契約の試験を通る() {
        contract_test_kit::assert_all(&normalize(RAW).unwrap());
    }
}
```

**違反例**

```rust
// adapters/common/src/lib.rs　通常の依存なので、判定の側が本番へ入る
pub fn assert_all(/* … */) { /* … */ }
```

```rust
// 各写し手が自分でアサーションを書き起こす。必ずずれる
#[test]
fn 必須の欄が埋まる() { /* 写し手ごとに別々に書かれる */ }
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| テストが走る仕組み | 言語 |
| 何を保証するか | 用途 |
| 生成物が手で編集されていないかの検査 | 用途。テストではなく、ビルドの組み方で決まる |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 実物入力をどこまで集めるか | 用途 | 接続先の数で決まる |
| 生成物を commit するか、`build.rs` で毎回生成するか | 用途 | ビルドの組み方と、生成器を持たない環境の有無で決まる |
| 実物入力を crate のどこへ置くか | 実装 | 外部に原典が無い。実装が決める |
| 生成した型の検証をどの単位へ置くか | 実装 | 外部に原典が無い。RD-TP-03（結合テストは公開 API だけを呼ぶ）を手掛かりに、実装が決める |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| RD-TP-01 | 規格 | Rust Book ch.11 Test Organization<br>https://doc.rust-lang.org/book/ch11-03-test-organization.html | 2026-09-06 取得 | 単体テストの置き場所 |
| RD-TP-03 | 規格 | Cargo Book / Tests<br>https://doc.rust-lang.org/cargo/guide/tests.html | 2026-09-06 取得 | 結合テストは公開 API だけを呼ぶ |
| RD-TP-06 | 規格 | Cargo Book / Specifying Dependencies<br>https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html | 2026-09-06 取得 | `dev-dependencies` は本番の成果物に入らない |