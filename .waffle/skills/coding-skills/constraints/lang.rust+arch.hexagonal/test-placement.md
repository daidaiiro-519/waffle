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
updated: 2026-09-06
approved_by: daidaiiro
approved_at: 2026-09-06
---


# Rust とヘキサゴナル構成におけるテストの置き場所

## 概要

**どの層も、対象と同じファイルの中で確かめる。`tests/` へ置くのは、公開する境界から叩くものだけである。**

## 置き場所の対応

| 層 | 置き場所 | 何を確かめるか | 呼び方 |
|---|---|---|---|
| `model` | 対象と同じファイルの `mod tests` | 業務モデルの不変条件 | 非公開の要素を直接呼ぶ |
| `application` | 対象と同じファイルの `mod tests` | 業務操作の振る舞い | 出力ポートの偽物を差し込んで呼ぶ |
| `application::ports` | 置かない | ─ | 宣言だけなので、確かめる振る舞いが無い |
| `adapter::inbound` | 対象と同じファイルの `mod tests` | 外部の形式から業務操作へ渡るまで | 非公開の要素を直接呼ぶ |
| `adapter::outbound` | 対象と同じファイルの `mod tests` | 出力ポートの実装が契約どおりに振る舞うか | 非公開の要素を直接呼ぶ |
| 実行ファイル全体 | `tests/` | 入口から出口までの一続き | 実行ファイルを起動して呼ぶ |

## 偽物の置き場所

| 偽物 | 置き場所 | 作り方 | 置いてはならない場所 |
|---|---|---|---|
| 出力ポートの偽物 | `src/application/mod.rs` の `#[cfg(test)] mod test_doubles` | ポートのトレイトを実装した最小の型 | `#[cfg(test)]` の外。リリースの成果物へ出荷される。`ports.rs`。宣言だけの場所に実装が入る |
| 入力の見本 | `src/adapter/inbound/fixtures/` | 実物の形式そのまま | `model` と `application`。内側が外部の形式を知ることになる |
| 外部技術の偽物 | 置かない | ─ | 出力ポートの偽物で足りる。技術の偽物を作ると技術に追従し続けることになる |

## 規則一覧

| ID | 規則 | 水準 | 適用範囲 |
|---|---|---|---|
| RH-TP-01 | すべての層の単体テストは、対象と同じファイルの `mod tests` に置く | 必須 | すべての層 |
| RH-TP-02 | `tests/` へ置くのは、公開する境界から叩くものだけにする | 必須 | 端から端まで |
| RH-TP-03 | 出力ポートの偽物は `#[cfg(test)]` の中に置き、リリースの成果物へ出荷しない | 必須 | 偽物 |

## 規則の詳細

### RH-TP-01　すべての層の単体テストは、対象と同じファイルの `mod tests` に置く

**`adapter` も含む。** 外側だからといって `tests/` へ出さない。

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | すべての層 |
| 根拠 | 原典が単体テストを「testing one module in isolation at a time, and can test private interfaces」と定めており、モジュールであれば層を問わない。`tests/` から呼ぶと、`layer-mapping.md` が定める可視性（`pub(crate)` までにとどめる）を破って公開範囲を広げることになる |
| 検証方法 | `model` ・ `application` ・ `adapter` の各ファイルに `#[cfg(test)] mod tests` が在るかを見る |
| 例外 | 補助関数だけのファイル |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
// src/adapter/inbound/mod.rs
pub(crate) fn parse(/* … */) { /* … */ }

#[cfg(test)]
mod tests {
    use super::*;
    const RAW: &str = include_str!("fixtures/tool_use.json");
    #[test]
    fn 壊れた要求は形式の失敗になる() { /* … */ }
}
```

**違反例**

```rust
// tests/register_hook.rs から呼ぶために、内側の非公開関数を pub にした
pub fn register(/* … */) { /* … */ }
```

### RH-TP-02　`tests/` へ置くのは、公開する境界から叩くものだけにする

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 端から端まで |
| 根拠 | 原典が結合テストを「entirely external to your library ... they can only call functions that are part of your library's public API」と定めている。層を確かめるために `tests/` を使うと、その層を公開する必要が生じ、RH-TP-01 の違反例と同じ状態になる |
| 検証方法 | `tests/` のテストが、実行ファイルの起動か、crate の公開 API のどちらかだけを使っているかを見る |
| 例外 | 外部サービスを要するものは、用途の保証規約に従う |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
// tests/hook_stdio.rs　実行ファイルを起動し、標準入出力だけを確かめる
#[test]
fn 壊れた要求には形式の失敗を返す() { /* … */ }
```

**違反例**

```rust
// tests/hook_stdio.rs
// crate:: は、この結合テスト自身の crate を指す。ライブラリではないので解決できない。
// ライブラリを指すなら `use mycrate::…` だが、そのためには adapter を公開する必要があり、
// 今度は可視性の定めを破る。
use crate::adapter::inbound::internal_parse;
```

### RH-TP-03　出力ポートの偽物は `#[cfg(test)]` の中に置き、リリースの成果物へ出荷しない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 偽物 |
| 根拠 | 偽物はテストのためだけの実装であり、本番の成果物に含める理由が無い。原典が `#[cfg(test)]` の効果を「saves space in the resultant compiled artifact because the tests are not included」と述べている |
| 検証方法 | 偽物の定義が `#[cfg(test)]` の中に在ることを見る |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
#[cfg(test)]
mod test_doubles {
    use super::ports::*;
    pub(crate) struct InMemoryHookStore { /* … */ }
}
```

**違反例**

```rust
// src/adapter/outbound/in_memory_store.rs　リリースの成果物へ入る
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
| 偽物を `application` と `adapter` のどちらへ置くか | 実装 | 外部に原典が無い。ヘキサゴナルの原典は偽物をアダプタの一種として数えており、内側へ寄せる根拠は原典から得られない |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| RH-TP-01 | 規格 | Rust Book ch.11 Test Organization<br>https://doc.rust-lang.org/book/ch11-03-test-organization.html | 2026-09-06 取得 | 単体テストの置き場所 |
| RH-TP-02 | 規格 | Rust Book ch.11 Test Organization<br>https://doc.rust-lang.org/book/ch11-03-test-organization.html | 2026-09-06 取得 | 結合テストは別の crate になる |
| RH-TP-03 | 規格 | Rust Book ch.11 Test Organization（`#[cfg(test)]` の効果）<br>https://doc.rust-lang.org/book/ch11-03-test-organization.html | 2026-09-06 取得 | `#[cfg(test)]` は成果物に入らない |