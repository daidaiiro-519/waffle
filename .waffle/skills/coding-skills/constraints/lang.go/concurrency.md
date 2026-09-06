---
id: lang.go.concurrency
layer: lang.go
axes:
  - axis: language
    value: go
category: coding
declares: 並行の単位と、共有の扱い
updated: 2026-09-06
approved_by: daidaiiro
approved_at: 2026-09-06
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

| ID | 規則 | 水準 | 適用範囲 |
|---|---|---|---|
| GO-CON-01 | 起動した goroutine は、終わり方を必ず決める | 必須 | 全体 |
| GO-CON-02 | 外部呼び出しを跨ぐ関数は、第1引数に `context.Context` を取る | 必須 | 公開する関数 |
| GO-CON-03 | 共有する可変状態は、チャネルか同期の型で守る | 必須 | 全体 |
| GO-CON-04 | `context.Context` を構造体に保持しない | 必須 | 全体 |

## 規則の詳細

### GO-CON-01　起動した goroutine は、終わり方を必ず決める

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 全体 |
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

### GO-CON-02　外部呼び出しを跨ぐ関数は、第1引数に `context.Context` を取る

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 公開する関数 |
| 根拠 | 呼び出し元が締め切りと取り消しを渡せなければ、外部呼び出しは打ち切れない |
| 検証方法 | 当たる命令が無い（`go vet` の35検査に第1引数を見るものは無い）。`go doc <パッケージ>` の出力で、外部を呼ぶ公開関数の第1引数が `ctx context.Context` かを見る |
| 例外 | 外部呼び出しを行わない関数 |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
func FetchUser(ctx context.Context, id string) (*User, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url(id), nil)
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}
	return do(req)
}
```

**違反例**

```go
func FetchUser(id string) (*User, error) {
	resp, err := http.Get(url(id))
	if err != nil {
		return nil, err
	}
	return parse(resp)
}
```

### GO-CON-03　共有する可変状態は、チャネルか同期の型で守る

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 全体 |
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

### GO-CON-04　`context.Context` を構造体に保持しない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 全体 |
| 根拠 | `Context` は呼び出し1回ぶんの寿命を持つ。構造体に入れると、その寿命が構造体の寿命に置き換わる |
| 検証方法 | 当たる命令が無い（`go vet` の35検査に、構造体の欄を見るものは無い）。構造体の欄に `context.Context` が無いかを見る |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
type Client struct {
	http *http.Client
}

func (c *Client) Get(ctx context.Context, id string) (*User, error) { ... }
```

**違反例**

```go
type Client struct {
	ctx  context.Context
	http *http.Client
}
```

## 共有の扱い

| 共有するもの | 扱い方 | 使う仕組み | 選ぶ条件 |
|---|---|---|---|
| 処理の結果 | 値を送る | チャネル | 生産と消費を分けるとき |
| 所有権の受け渡し | 値を送り、送った側は触らない | チャネル | 書き換える主体を移せるとき |
| 読むだけの値 | 複製して渡す | 値のコピー | 小さい構造体のとき |
| 書き換える値（移せない） | 排他で守る | `sync.Mutex` | 複数の goroutine が同じ値を書くとき |
| 一度だけの初期化 | 1回に固定する | `sync.Once` | 遅延して作る値があるとき |
| 中断の合図 | 文脈を渡す | `context.Context` | 呼び出しの打ち切りを伝えるとき |

**共有して守るより、送って共有しないほうを先に採る。**
排他は正しく書けるが、守り忘れた1か所を検査が指すのは実行時であり、しかも再現しない。

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

| ID | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| GO-CON-01 | 文献 | Go Blog "Concurrency Patterns"<br>https://go.dev/blog/pipelines | 2026-09-06 取得 | goroutine の終わり方を決める |
| GO-CON-02 | 規格 | Go 標準ライブラリ `context`<br>https://pkg.go.dev/context | 2026-09-06 取得 | 取り消しと期限を引数で運ぶ |
| GO-CON-03 | 規格 | Go の競合検出器<br>https://go.dev/doc/articles/race_detector | 2026-09-06 取得 | 競合の検出 |
| GO-CON-04 | 規格 | `context` の説明<br>https://pkg.go.dev/context | 2026-09-06 取得 | Context を構造体に保持しない |