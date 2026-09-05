---
id: lang.rust+arch.hexagonal.test-placement
layer: lang.rust+arch.hexagonal
axes:
  - axis: language
    value: rust
  - axis: architecture
    value: hexagonal
category: test
declares: テストの置き場所
updated: 2026-09-05
---

# Rust とヘキサゴナル構成におけるテストの置き場所

## 概要

**内側は同じファイルの中で、外側は境界の外から確かめる。**

## 規則一覧

| ID | 規則 | 水準 | 検証方法 | 適用範囲 |
|---|---|---|---|---|
| RH-TP-01 | `model` と `application` のテストは、対象と同じファイルの `mod tests` に置く | 必須 | レビュー | 内側 |
| RH-TP-02 | `adapter` のテストは `tests/` に置き、公開する境界から呼ぶ | 必須 | レビュー | 外側 |
| RH-TP-03 | 出力ポートの偽物は `application::ports` の隣に置き、`adapter` へ置かない | 必須 | レビュー | 内側のテスト |

## 規則の詳細

### RH-TP-01　`model` と `application` のテストは、対象と同じファイルの `mod tests` に置く

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 内側は非公開の要素を持つので、外から呼ぶと公開範囲を広げることになる |
| 検証方法 | `model` と `application` の各ファイルに `#[cfg(test)] mod tests` が在るかを見る |
| 例外 | 補助関数だけのファイル |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
// src/application/register_hook.rs
pub(crate) fn register(/* … */) { /* … */ }

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn 同じ名前の登録は拒否される() { /* … */ }
}
```

**違反例**

```rust
// tests/register_hook.rs から、内側の非公開関数を呼ぶために pub にした
pub fn register(/* … */) { /* … */ }
```

### RH-TP-02　`adapter` のテストは `tests/` に置き、公開する境界から呼ぶ

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 外側は外部との契約なので、契約と同じ入口から確かめる |
| 検証方法 | `tests/` のテストが、公開 API だけを呼んでいるかを見る |
| 例外 | 外部サービスを要するものは、用途の保証規約に従う |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
// tests/hook_stdio.rs
#[test]
fn 壊れた要求には形式の失敗を返す() { /* 公開 API だけを呼ぶ */ }
```

**違反例**

```rust
// tests/hook_stdio.rs で、内部モジュールを直接呼ぶ
use crate::adapter::inbound::internal_parse;
```

### RH-TP-03　出力ポートの偽物は `application::ports` の隣に置き、`adapter` へ置かない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 偽物は内側のテストのための道具であり、外側の実装ではない |
| 検証方法 | 偽物の定義が `adapter` に無いかを見る |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
// src/application/ports.rs
#[cfg(test)]
pub(crate) struct InMemoryHookStore { /* … */ }
```

**違反例**

```rust
// src/adapter/outbound/in_memory_store.rs
pub struct InMemoryHookStore { /* … */ }
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| テストが走る仕組み | 言語 |
| 何を保証するか | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 端から端までのテストを持つか | 用途 | 外部との接続の有無で決まる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| RH-TP-01 | 規格 | Rust Book ch.11 Test Organization<br>https://doc.rust-lang.org/book/ch11-03-test-organization.html | 2026-09-05 取得 | `unit tests` |
| RH-TP-02 | 規格 | Rust Book ch.11 Test Organization<br>https://doc.rust-lang.org/book/ch11-03-test-organization.html | 2026-09-05 取得 | `integration tests` |