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
updated: 2026-09-05
---

# crate ごとのテストの置き場所

## 概要

**テストは、その crate の中に置く。crate の境界が、そのままテストの境界になる。**

## 規則一覧

| ID | 規則 | 水準 | 検証方法 | 適用範囲 |
|---|---|---|---|---|
| RD-TP-01 | 各 crate の単体テストは、対象と同じファイルの `mod tests` に置く | 必須 | レビュー | すべての crate |
| RD-TP-02 | 写し手の実物入力は `adapters/<接続先>/tests/fixtures/` に置き、他の crate から読まない | 必須 | レビュー | 写し手 |
| RD-TP-03 | 束ねの結合テストは `bundle/tests/` に置き、公開 API だけを呼ぶ | 必須 | レビュー | 束ね |
| RD-TP-04 | 生成した型と schema の一致は、`contract` crate の結合テストで確かめる | 必須 | 静的解析 | データ契約 |

## 規則の詳細

### RD-TP-01　各 crate の単体テストは、対象と同じファイルの `mod tests` に置く

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
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

### RD-TP-02　写し手の実物入力は `adapters/<接続先>/tests/fixtures/` に置き、他の crate から読まない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 実物の入力は接続先ごとに違い、共有すると接続先どうしが結び付く |
| 検証方法 | 相対パスで他の crate の `fixtures` を読んでいないかを見る |
| 例外 | なし |
| 既存コードへの適用 | 一括是正 |

**適合例**

```rust
const RAW: &str = include_str!("fixtures/tool_use.json");
```

**違反例**

```rust
const RAW: &str = include_str!("../../other_adapter/tests/fixtures/tool_use.json");
```

### RD-TP-04　生成した型と schema の一致は、`contract` crate の結合テストで確かめる

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | schema を直しても型が変わらなければ、正が2つになる |
| 検証方法 | `cargo test -p contract` が、生成の再実行と差分の検査を含む |
| 例外 | なし |
| 既存コードへの適用 | 一括是正 |

**適合例**

```rust
#[test]
fn 生成した型は schema と一致する() {
    let regenerated = generate_types(SCHEMA);
    assert_eq!(regenerated, include_str!("../src/types.rs"));
}
```

**違反例**

```rust
// 生成した型を手で直し、schema は変えない
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| テストが走る仕組み | 言語 |
| 何を保証するか | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 実物入力をどこまで集めるか | 用途 | 接続先の数で決まる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| RD-TP-01 | 規格 | Rust Book ch.11 Test Organization | 《版・取得日》 | `unit tests` |
| RD-TP-03 | 規格 | Cargo Book / Tests | 《版・取得日》 | `tests directory` |
