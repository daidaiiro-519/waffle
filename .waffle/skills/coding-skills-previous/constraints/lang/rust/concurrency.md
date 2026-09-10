---
id: lang.rust.concurrency
layer: lang.rust
axes:
  - axis: language
    value: rust
category: coding
declares: 並行の単位と、共有の扱い
updated: 2026-09-07
approved_by: daidaiiro
approved_at: 2026-09-06
---


# Rust における並行の扱い

## 概要

**共有せずに渡すことを既定とし、共有するなら所有と借用の規則で守る。**

## 並行の単位

| 単位 | 何を表すか | いつ使うか |
|---|---|---|
| スレッド | OS が割り当てる実行の単位 | 処理が計算で詰まるとき |
| 非同期タスク | 実行環境が切り替える軽い単位 | 待ちが多いとき。実行環境の採用は用途が決める |
| プロセス | 独立した実行 | 失敗を隔離したいとき |

## 規則一覧

| ID | 規則 | 水準 | 適用範囲 |
|---|---|---|---|
| RS-CON-01 | 状態を共有せず、所有権を渡して受け渡す | 必須 | 全体 |
| RS-CON-02 | 共有が必要なら、`Arc` と同期の型で包み、素の可変参照を跨がせない | 必須 | 全体 |
| RS-CON-03 | ロックを持ったまま、待つ操作を呼ばない | 必須 | ロックを使う箇所 |

## 規則の詳細

### RS-CON-01　状態を共有せず、所有権を渡して受け渡す

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 全体 |
| 根拠 | 共有しなければ、競合そのものが起きない |
| 検証方法 | 共有された可変状態が在るかを見る |
| 例外 | 読むだけの共有 |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
let (tx, rx) = std::sync::mpsc::channel();
std::thread::spawn(move || tx.send(build_report()).ok());
```

**違反例**

```rust
static mut TOTAL: usize = 0;
```

### RS-CON-02　共有が必要なら、`Arc` と同期の型で包み、素の可変参照を跨がせない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 全体 |
| 根拠 | 素の可変参照はスレッドを跨げない。跨がせるには `unsafe` が要り、そこでコンパイラの検査が外れる |
| 検証方法 | `cargo build` ・ `cargo clippy --all-targets -- -D warnings` に加えて、**`Send` ・ `Sync` を要求する試験を1本置く**。原典が示す形——`fn assert_send<T: Send>() {}` を呼ぶ |
| 例外 | **`lock()` の返りを `unwrap` すること。**原文が `Most usage of a mutex will simply unwrap() these results` と述べており、`RS-ERR-01` の例外（不変条件の破れ）に当たる |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
let shared = Arc::new(Mutex::new(State::default()));
let handle = {
    let shared = Arc::clone(&shared);
    thread::spawn(move || shared.lock().unwrap().advance())
};
```

**違反例**

```rust
struct Shared(*mut State);
unsafe impl Send for Shared {}
```

### RS-CON-03　ロックを持ったまま、待つ操作を呼ばない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | ロックを使う箇所 |
| 根拠 | ロックの保持中に待つと、待ち時間の分だけ他が止まる |
| 検証方法 | ロックの範囲に入出力・待機が入っていないかを見る |
| 例外 | **`lock()` の返りを `unwrap` すること**（`RS-CON-02` と同じ） |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```rust
let snapshot = { state.lock().unwrap().clone() };
write_to_disk(&snapshot)?;
```

**違反例**

```rust
let guard = state.lock().unwrap();
write_to_disk(&guard)?;
```

## 共有の扱い

| 共有するもの | 扱い方 | 使う仕組み | 選ぶ条件 |
|---|---|---|---|
| 読むだけの値 | 複製して渡すか、参照を借りる | `Clone` ／ `&T` | 小さい値、または生存期間が明らかなとき |
| 読むだけの値（生存期間が跨る） | 所有を共有する | `Arc<T>` | 複数のスレッドが同じ値を読むとき |
| 書き換える値 | 所有を移して1か所に閉じる | 移動 ／ チャネル | 書き換える主体を1つにできるとき |
| 書き換える値（閉じられない） | 排他で守る | `Arc<Mutex<T>>` | 複数のスレッドが同じ値を書くとき |
| 処理の結果 | 値を送る | チャネル | 生産と消費を分けるとき |

**共有して守るより、所有を移して共有しないほうを先に採る。**
排他は正しく書けるが、取る順序を誤ると止まる。移動とチャネルにはその失敗が無い。

**`lock()` は `Result` を返す。**保持していたスレッドが `panic!` すると、その排他は「汚れた」状態になり、
以降の `lock()` が失敗する（poisoning）。
**この失敗は運ばない。**原文が `Most usage of a mutex will simply unwrap() these results,
propagating panics among threads to ensure that a possibly invalid invariant is not witnessed` と述べており、
**不変条件が破れているので、回復しない**——`RS-ERR-01` の例外に当たる。

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| 非同期の実行環境を採るかどうか | 用途 |
| 並行度の上限 | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| チャネルの種類（同期・非同期・容量） | 用途 | 流れる量と待ちの許容で決まる |
| 非同期の実行環境を、公開 API に出すか | 用途 | **Rust 公式の定めが無い。**API Guidelines の全文（139,730 B）に `async` ・ `runtime` ・ `tokio` ・ `executor` が0件だった。出典を持たない言明は規則にしない（`sources.md`） |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| RS-CON-01 | 文献 | The Rust Programming Language ch.16 Fearless Concurrency<br>https://doc.rust-lang.org/book/ch16-02-message-passing.html | 2026-09-07 全文で確認（`Do not communicate by sharing memory` 1か所 ・ `channel` 33か所） | 所有権を渡して共有しない |
| RS-CON-02 | 規格 | The Rust Programming Language ch.16 Shared-State Concurrency<br>https://doc.rust-lang.org/book/ch16-03-shared-state.html | 2026-09-07 全文で確認（`Mutex` 46か所 ・ `Arc` 10か所） | 共有は `Arc` と同期の型で包む |
| RS-CON-02 | 文献 | Rust API Guidelines `C-SEND-SYNC`<br>https://rust-lang.github.io/api-guidelines/interoperability.html | 2026-09-07 全文で確認（`Tests like the following can help catch unintentional regressions`） | 試験で `Send` ・ `Sync` を守る |
| RS-CON-03 | 規格 | Rust std `Mutex`<br>https://doc.rust-lang.org/std/sync/struct.Mutex.html | 2026-09-07 全文で確認（`deadlock` 3か所 ・ `poison` 39か所） | ロックを持つ間は他が待つ。`lock()` の失敗は運ばない |