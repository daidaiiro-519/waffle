---
id: lang.go.test-mechanism
layer: lang.go
axes:
  - axis: language
    value: go
category: test
declares: テストが走る仕組みと、書き方
updated: 2026-09-05
---

# Go におけるテストの仕組み

## 概要

**標準のテスト機構だけで走らせ、表で入力と期待を並べる。**

## 保証する振る舞い

| ID | 振る舞い | 検証の単位 | 前提条件 | 失敗したときの現れ方 |
|---|---|---|---|---|
| GO-TST-01 | すべてのテストが `go test ./...` 1つで走る | 単体・結合 | `_test.go` が標準の位置に在る | 走らないテストが残る |
| GO-TST-02 | テストは実行順に依存せず、並列でも同じ結果になる | 単体 | 共有状態を持たない | `-race` や並列実行で落ちる |

## 走らせ方

| 項目 | 定め |
|---|---|
| 実行コマンド | `go test ./...` ／ 競合の検出は `go test -race ./...` |
| 検出のされ方 | `_test.go` の `TestXxx(t *testing.T)` が走る |
| 並列 | パッケージ間は既定で並列。パッケージ内は `t.Parallel()` を書いたものだけ |
| 失敗の表示 | 期待と実際の両方を出す |

## 書き方

| 項目 | 規則 |
|---|---|
| 名前 | 振る舞いを述べる。`TestReadPort_範囲外は受け付けない` のように、対象と振る舞いを分けて書く |
| 構成 | 入力と期待を表にし、`t.Run` で1件ずつ回す |
| 表明 | 差分が読める形で出す。等価の比較は `cmp.Diff` を使ってよい |
| 後始末 | `t.Cleanup` に登録し、失敗した経路でも戻す |

**適合例**

```go
func TestReadPort(t *testing.T) {
	cases := []struct {
		name string
		in   string
		want uint16
		err  error
	}{
		{name: "範囲内は受け付ける", in: "8080", want: 8080},
		{name: "範囲外は受け付けない", in: "70000", err: ErrOutOfRange},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got, err := ReadPort(c.in)
			if !errors.Is(err, c.err) {
				t.Fatalf("err = %v, want %v", err, c.err)
			}
			if got != c.want {
				t.Errorf("got = %d, want %d", got, c.want)
			}
		})
	}
}
```

**違反例**

```go
func TestReadPort2(t *testing.T) {
	if _, err := ReadPort("70000"); err == nil {
		t.Fail()
	}
}
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| 層ごとにどこへ置くか | 言語 × アーキテクチャ |
| 何を保証するか | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 比較の道具（標準か `cmp` か） | 用途 | 比較する型の複雑さで決まる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| GO-TST-01 | 規格 | Go 標準ライブラリ `testing`<br><small>https://pkg.go.dev/testing</small> | 2026-09-05 取得 | `func TestXxx` |
| GO-TST-02 | 規格 | `testing` パッケージ（並列）<br><small>https://pkg.go.dev/testing</small> | 2026-09-05 取得 | `Parallel` |