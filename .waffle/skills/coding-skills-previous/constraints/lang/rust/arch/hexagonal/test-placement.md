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
updated: 2026-09-08
approved_by: daidaiiro
approved_at: 2026-09-06
---


# Rust とヘキサゴナル構成におけるテストの置き場所

## 概要

**どの構成要素も、対象と同じファイルの中で確かめる。`tests/` へ置くのは、公開する境界から叩くものだけである。**

## 置き場所の対応

**分け方によって、置き場所が変わる。**
どちらを採るかは `element-mapping.md` が定める。

**モジュールに分ける場合**

| 構成要素 | 置き場所 | 何を確かめるか | 呼び方 |
|---|---|---|---|
| `model` | 対象と同じファイルの `mod tests` | 業務モデルの不変条件 | 非公開の要素を直接呼ぶ |
| `application` | 対象と同じファイルの `mod tests` | 業務操作の振る舞い | 二次のポートの偽物を差し込んで呼ぶ |
| `application::ports` | 置かない | ─ | 宣言だけなので、確かめる振る舞いが無い |
| `adapter::inbound` | 対象と同じファイルの `mod tests` | 外部の形式から業務操作へ渡るまで | 非公開の要素を直接呼ぶ |
| `adapter::outbound` | 対象と同じファイルの `mod tests` | 二次のポートの実装が契約どおりに振る舞うか | 非公開の要素を直接呼ぶ |

**クレートに分ける場合**

| クレート | 置き場所 | 何を確かめるか | 呼び方 |
|---|---|---|---|
| ポートの形 | 対象と同じファイルの `mod tests` | 型が満たす不変条件 | 非公開の要素を直接呼ぶ |
| 業務操作 | 対象と同じファイルの `mod tests` | 業務操作の振る舞い | 二次のポートの偽物を差し込んで呼ぶ |
| アダプター | 対象と同じファイルの `mod tests` | 外部の形式が、ポートの形へ写るか | 非公開の要素を直接呼ぶ |
| ポート | 対象と同じファイルの `mod tests` | 接続先ごとの振り分けが揃っているか | 見本を回して呼ぶ（`RH-TP-04`） |
| 入力アダプター | 対象と同じファイルの `mod tests` | 外部の呼ばれ方の解釈 | 非公開の要素を直接呼ぶ |

**どちらでも同じ**

| 何を | 置き場所 | 何を確かめるか | 呼び方 |
|---|---|---|---|
| 実行ファイル全体 | `tests/` | 入口から出口までの一続き | 実行ファイルを起動して呼ぶ（`RH-TP-05`） |
| 共通で通す試験の集合 | 別のクレートに置き `[dev-dependencies]` で引く | どのアダプターも同じ形をしているか | 各アダプターの `mod tests` から呼ぶ（`RH-TP-04`） |

## 偽物の置き場所

| 偽物 | 置き場所 | 作り方 | 置いてはならない場所 |
|---|---|---|---|
| 二次のポートの偽物 | `#[cfg(test)] mod test_doubles`。**どのファイルに置くかは決めない**（`委譲する判断`） | ポートのトレイトを実装した最小の型 | `#[cfg(test)]` の外。リリースの成果物へ出荷される。`ports.rs`。宣言だけの場所に実装が入る |
| 入力の見本 | `src/adapter/inbound/fixtures/` | 実物の形式そのまま | `model` と `application`。内側が外部の形式を知ることになる |
| 外部技術の偽物 | 置かない | ─ | 二次のポートの偽物で足りる。技術の偽物を作ると技術に追従し続けることになる |

**クレートに分けた場合は、`src/application/mod.rs` を業務操作のクレートに、
`src/adapter/inbound/fixtures/` をアダプターのクレートの `src/fixtures/` に読み替える。**
**二次のポートを持たない構成では、偽物そのものが要らない。**

## 規則一覧

| ID | 規則 | 水準 | 適用範囲 |
|---|---|---|---|
| RH-TP-01 | すべての構成要素の単体テストは、対象と同じファイルの `mod tests` に置く | 必須 | すべての構成要素 |
| RH-TP-02 | `tests/` へ置くのは、公開する境界から叩くものだけにする | 必須 | 端から端まで |
| RH-TP-03 | 二次のポートの偽物は `#[cfg(test)]` の中に置き、リリースの成果物へ出荷しない | 必須 | 偽物 |
| RH-TP-04 | アダプターが共通で通す試験の集合は、別の crate に置き、各アダプターが `[dev-dependencies]` で引く | 必須 | アダプター |
| RH-TP-05 | 実行ファイルを起こして確かめる試験は、その crate の `tests/` に置く | 必須 | 実行ファイルを持つ crate |

## 規則の詳細

### RH-TP-01　すべての構成要素の単体テストは、対象と同じファイルの `mod tests` に置く

**`adapter` も含む。** 外側だからといって `tests/` へ出さない。

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | すべての構成要素 |
| 根拠 | 原典が単体テストを「testing one module in isolation at a time, and can test private interfaces」と定めており、モジュールであれば構成要素を問わない。`tests/` から呼ぶと、`element-mapping.md` が定める可視性（`pub(crate)` までにとどめる）を破って公開範囲を広げることになる |
| 検証方法 | モジュールに分けたなら `model` ・ `application` ・ `adapter` の、クレートに分けたなら各クレートの `src/` の、それぞれのファイルに `#[cfg(test)] mod tests` が在るかを見る |
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
| 根拠 | 原典が結合テストを「entirely external to your library ... they can only call functions that are part of your library's public API」と定めている。構成要素を確かめるために `tests/` を使うと、その構成要素を公開する必要が生じ、RH-TP-01 の違反例と同じ状態になる |
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

### RH-TP-03　二次のポートの偽物は `#[cfg(test)]` の中に置き、リリースの成果物へ出荷しない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 偽物 |
| 根拠 | 偽物はテストのためだけの実装であり、本番の成果物に含める理由が無い。原典が `#[cfg(test)]` の効果を「saves space in the resultant compiled artifact because the tests are not included」と述べている |
| 検証方法 | 偽物の定義が `#[cfg(test)]` の中に在ることを見る。**二次のポートが無い構成では、当てる対象が無い** |
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

### RH-TP-04　アダプターが共通で通す試験の集合は、別の crate に置き、各アダプターが `[dev-dependencies]` で引く

**通すこと自体は `arch.hexagonal/test-boundaries.md` の HX-TB-07 が定める。**
ここで決めるのは Rust での置き場所だけである。

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | アダプター |
| 根拠 | アダプターが共有する crate へ通常の依存として置くと、判定の側が本番の成果物へ入る。`[dev-dependencies]` なら入らない ── 原典が「Dev-dependencies are not used when compiling a package for building, but are used for compiling tests」と述べている。あわせて、依存元へ伝播しないのでアダプターどうしも結び付かない |
| 検証方法 | 試験の集合を持つ crate が、どのアダプターからも `[dev-dependencies]` でのみ引かれていることを見る |
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
// アダプターが共有するクレート　通常の依存なので、判定の側が本番へ入る
pub fn assert_all(/* … */) { /* … */ }
```

```rust
// 各アダプターが自分でアサーションを書き起こす。必ずずれる
#[test]
fn 必須の欄が埋まる() { /* アダプターごとに別々に書かれる */ }
```

### RH-TP-05　実行ファイルを起こして確かめる試験は、その crate の `tests/` に置く

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 実行ファイルを持つ crate |
| 根拠 | 終了コードと標準出力は、関数の戻り値では見えない。プロセスとして起こすしかない。原典が `CARGO_BIN_EXE_<name>` を「The absolute path to a binary target's executable. This is only set when building an integration test or benchmark. This may be used with the env macro to find the executable to run for testing purposes」と述べており、**結合テストのときだけ渡される**。単体テストからは指せない |
| 検証方法 | `cargo test -p <crate>` が通ること。あわせて、`env!("CARGO_BIN_EXE_…")` を使う試験が `<crate>/src/` に無いことを見る ── 単体テストからは指せないので、置けばコンパイルで落ちる |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
// crates/cli/tests/hook_stdio.rs
let exe = env!("CARGO_BIN_EXE_ctxtrace");
let out = Command::new(exe).arg("--help").output().unwrap();
assert_eq!(out.status.code(), Some(0));
```

**違反例**

```rust
// crates/cli/src/main.rs　単体テストには渡されない。コンパイルで落ちる
#[cfg(test)]
mod tests {
    #[test]
    fn 実行ファイルを叩く() {
        let _ = env!("CARGO_BIN_EXE_ctxtrace");
    }
}
```

## 消した規則

**番号は詰めない。**消した ID を別の規則に付け直すと、
過去の記録（commit ・ コードのコメント）が別のものを指す。

| 消した ID | 何を言っていたか | なぜ消したか |
|---|---|---|
| `RD-TP-01` ・ `RD-TP-03` ・ `RD-TP-06` ・ `RD-TP-07` | crate ごとのテストの置き場所 | **`data-port` は原典を持たない造語だった。**軸の値ごと消し、規則は `RH-TP-01` ・ `RH-TP-02` ・ `RH-TP-04` ・ `RH-TP-05` として引き継いだ |
| `RD-TP-02` | アダプターの実物入力は `adapters/<接続先>/tests/fixtures/` に置き、他の crate から読まない | **外部の原典が無い。**置き場所の取り決めであって、言語や道具が決めていることではない（`sources.md`） |
| `RD-TP-04` | 生成した型と schema の一致は、`contract` crate の結合テストで確かめる | 同上。**確かめること自体は `HX-TB-05` が保証として持つ** |

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| テストが走る仕組み | 言語 |
| 何を保証するか | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 端から端までのテストを持つか | 用途 | 外部との接続の有無で決まる |
| 偽物を `application` と `adapter` のどちらへ置くか | 実装 | 外部に原典が無い。ヘキサゴナルの原典は偽物をアダプターの一種として数えており、内側へ寄せる根拠は原典から得られない |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| RH-TP-01 | 規格 | Rust Book ch.11 Test Organization<br>https://doc.rust-lang.org/book/ch11-03-test-organization.html | 2026-09-06 取得 | 単体テストの置き場所 |
| RH-TP-02 | 規格 | Rust Book ch.11 Test Organization<br>https://doc.rust-lang.org/book/ch11-03-test-organization.html | 2026-09-06 取得 | 結合テストは別の crate になる |
| RH-TP-03 | 規格 | Rust Book ch.11 Test Organization（`#[cfg(test)]` の効果）<br>https://doc.rust-lang.org/book/ch11-03-test-organization.html | 2026-09-06 取得 | `#[cfg(test)]` は成果物に入らない |
| RH-TP-04 | 規格 | Cargo Book / Specifying Dependencies<br>https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html | 2026-09-07 全文で確認（`dev-dependencies` 11か所 ・ `not used when compiling` 1か所） | `dev-dependencies` は本番の成果物に入らない |
| RH-TP-05 | 規格 | Cargo Reference / Environment Variables<br>https://doc.rust-lang.org/cargo/reference/environment-variables.html | 2026-09-07 全文で確認（`CARGO_BIN_EXE_` 5か所 ・ `integration test` 5か所） | `CARGO_BIN_EXE_<name>` は結合テストにだけ渡される |
