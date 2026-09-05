---
id: lang.go.concurrency
layer: lang.go
axes:
  - axis: language
    value: go
category: coding
declares: 並行の単位と、共有の扱い
updated: 2026-09-05
---

# Go における並行の扱い

## 概要

**通信で共有し、共有で通信しない。始めた並行は、終わらせる責任を持つ。**

## 並行の単位

| 単位 | 何を表すか | いつ使うか |
|---|---|---|
| goroutine | 実行環境が切り替える軽い実行の単位 | 待ちが多いとき、独立した仕事を並べるとき |
| チャネル | goroutine のあいだの受け渡し | 値を渡すとき |
| `context.Context` | 取り消しと期限の伝達 | 外部からの呼び出しを跨ぐとき |

## 規則一覧

| ID | 規則 | 水準 | 検証方法 | 適用範囲 |
|---|---|---|---|---|
| GO-CON-01 | 起動した goroutine は、終わり方を必ず決める | 必須 | レビュー | 全体 |
| GO-CON-02 | 外部呼び出しを跨ぐ関数は、第1引数に `context.Context` を取る | 必須 | 静的解析 | 公開する関数 |
| GO-CON-03 | 共有する可変状態は、チャネルか同期の型で守る | 必須 | 静的解析 | 全体 |
| GO-CON-04 | `context.Context` を構造体に保持しない | 必須 | レビュー | 全体 |

## 規則の詳細

### GO-CON-01　起動した goroutine は、終わり方を必ず決める

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 終わり方の無い goroutine は、資源を保持したまま残る |
| 検証方法 | `go test -race` と、`go func(` の各所で終了条件を確認する |
| 例外 | プロセスと同じ寿命を持つと明記した場合 |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
go func() {
	defer wg.Done()
	for {
		select {
		case <-ctx.Done():
			return
		case job := <-jobs:
			handle(job)
		}
	}
}()
```

**違反例**

```go
go func() {
	for job := range jobs {
		handle(job)
	}
}()
```

### GO-CON-03　共有する可変状態は、チャネルか同期の型で守る

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 競合は、動く場合と動かない場合が実行のたびに変わる |
| 検証方法 | `go test -race ./...` |
| 例外 | 読むだけの共有 |
| 既存コードへの適用 | 一括是正 |

**適合例**

```go
type counter struct {
	mu sync.Mutex
	n  int
}
```

**違反例**

```go
var total int // 複数の goroutine から書く
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| 並行度の上限 | 用途 |
| 取り消しの伝え方（期限の値） | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| チャネルの容量 | 用途 | 流れる量と待ちの許容で決まる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| GO-CON-01 | 文献 | Go Blog "Concurrency Patterns"（終わり方） | 《版・取得日》 | `pipeline` |
| GO-CON-02 | 規格 | Go 標準ライブラリ `context` | 《版・取得日》 | `context.Context` |
| GO-CON-03 | 規格 | Go の競合検出器 | 《版・取得日》 | `-race` |
| GO-CON-04 | 規格 | `context` の説明（構造体に保持しない） | 《版・取得日》 | `Do not store Contexts` |
