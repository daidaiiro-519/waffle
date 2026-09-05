---
id: lang.go.failure
layer: lang.go
axes:
  - axis: language
    value: go
category: coding
declares: 失敗の運び方
updated: 2026-09-05
---

# Go における失敗の運び方

## 概要

**失敗は値として返し、文脈を足しながら呼び出し元へ渡す。**

## 規則一覧

| ID | 規則 | 水準 | 検証方法 | 適用範囲 |
|---|---|---|---|---|
| GO-ERR-01 | 失敗は戻り値の最後の `error` で返し、`panic` で流さない | 必須 | 静的解析 | 全体 |
| GO-ERR-02 | 失敗を包むときは `%w` を使い、原因を辿れるようにする | 必須 | 静的解析 | 包む箇所 |
| GO-ERR-03 | 呼び出し元が分岐する失敗は、番兵値か独自型にする | 必須 | レビュー | 公開する関数 |
| GO-ERR-04 | 失敗を捨てない。捨てる場合は理由をコメントで残す | 必須 | 静的解析 | 全体 |
| GO-ERR-05 | 失敗の文面は小文字で始め、句点で終えない | 必須 | 静的解析 | 全体 |

## 規則の詳細

### GO-ERR-01　失敗は戻り値の最後の `error` で返し、`panic` で流さない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | `panic` は呼び出し元が回復の可否を選べず、境界を越えて伝わる |
| 検証方法 | `go vet` と、`panic(` の出現箇所の確認 |
| 例外 | 初期化時に回復不能と分かった場合。および `main` |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
func ReadPort(raw string) (uint16, error) { /* … */ }
```

**違反例**

```go
func ReadPort(raw string) uint16 {
	n, err := strconv.Atoi(raw)
	if err != nil {
		panic(err)
	}
	return uint16(n)
}
```

### GO-ERR-02　失敗を包むときは `%w` を使い、原因を辿れるようにする

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 包み方を誤ると、呼び出し元が `errors.Is` ・ `errors.As` で判別できない |
| 検証方法 | `go vet` の `errorsas` と、`%v` で包んでいないかの確認 |
| 例外 | 意図して原因を隠すとき。その場合は理由を書く |
| 既存コードへの適用 | 一括是正 |

**適合例**

```go
return fmt.Errorf("load config %s: %w", path, err)
```

**違反例**

```go
return fmt.Errorf("load config %s: %v", path, err)
```

### GO-ERR-03　呼び出し元が分岐する失敗は、番兵値か独自型にする

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 文面での判定は、文面を直すたびに壊れる |
| 検証方法 | 呼び出し元が文字列比較で分岐していないかを見る |
| 例外 | 分岐しない失敗 |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
var ErrNotFound = errors.New("order not found")

if errors.Is(err, ErrNotFound) { /* … */ }
```

**違反例**

```go
if err.Error() == "order not found" { /* … */ }
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| どの失敗を利用者へ提示するか | 用途 |
| 失敗の記録先 | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 番兵値と独自型のどちらを使うか | 用途 | 呼び出し元が要る情報の量で決まる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| GO-ERR-01 | 文献 | Effective Go（エラーの扱い）<br>https://go.dev/doc/effective_go | 2026-09-05 取得 | `errors` |
| GO-ERR-02 | 規格 | Go 標準ライブラリ `fmt.Errorf` の `%w`<br>https://pkg.go.dev/fmt | 2026-09-05 取得 | `%w` |
| GO-ERR-03 | 規格 | Go 標準ライブラリ `errors.Is` ・ `errors.As`<br>https://pkg.go.dev/errors | 2026-09-05 取得 | `errors.Is` |
| GO-ERR-05 | 文献 | Go Code Review Comments（Error Strings）<br>https://go.dev/wiki/CodeReviewComments | 2026-09-05 取得 | `Error Strings` |