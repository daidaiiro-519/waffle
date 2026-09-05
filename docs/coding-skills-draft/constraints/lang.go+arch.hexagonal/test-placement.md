---
id: lang.go+arch.hexagonal.test-placement
layer: lang.go+arch.hexagonal
axes:
  - axis: language
    value: go
  - axis: architecture
    value: hexagonal
category: test
declares: テストの置き場所
updated: 2026-09-05
---

# Go とヘキサゴナル構成におけるテストの置き場所

## 概要

**内側は同じパッケージで、外側は公開する境界から確かめる。**

## 規則一覧

| ID | 規則 | 水準 | 検証方法 | 適用範囲 |
|---|---|---|---|---|
| GH-TP-01 | `model` と `app` のテストは、同じパッケージ（`package model`）に置く | 必須 | レビュー | 内側 |
| GH-TP-02 | `adapter` のテストは外部パッケージ（`package xxx_test`）に置き、公開する識別子だけを呼ぶ | 必須 | レビュー | 外側 |
| GH-TP-03 | 出力ポートの偽物は `app` の中に置き、`adapter` へ置かない | 必須 | レビュー | 内側のテスト |
| GH-TP-04 | 外部サービスを要するテストには、`testing.Short` で外せる印を付ける | 必須 | 静的解析 | 外側 |

## 規則の詳細

### GH-TP-01　`model` と `app` のテストは、同じパッケージに置く

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 内側は非公開の要素を持つので、外から呼ぶと公開範囲を広げることになる |
| 検証方法 | `internal/model` ・ `internal/app` の `_test.go` の package 宣言を見る |
| 例外 | 公開する型だけを確かめるとき |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
// internal/app/register_test.go
package app

func TestRegister_同じ名前は拒否する(t *testing.T) { /* … */ }
```

**違反例**

```go
// internal/app/register_test.go
package app_test // 内部を呼ぶために app 側を export した
```

### GH-TP-02　`adapter` のテストは外部パッケージに置き、公開する識別子だけを呼ぶ

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 外側は外部との契約なので、契約と同じ入口から確かめる |
| 検証方法 | `adapter` の `_test.go` が `package xxx_test` になっているかを見る |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
// internal/adapter/inbound/http/handler_test.go
package http_test
```

**違反例**

```go
package http // 内部関数を直接呼ぶ
```

### GH-TP-04　外部サービスを要するテストには、`testing.Short` で外せる印を付ける

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 外部が要るテストが混ざると、手元でテストが走らなくなる |
| 検証方法 | `go test -short ./...` が、外部なしで通る |
| 例外 | なし |
| 既存コードへの適用 | 一括是正 |

**適合例**

```go
func TestOrderRepository(t *testing.T) {
	if testing.Short() {
		t.Skip("外部のデータベースが要る")
	}
}
```

**違反例**

```go
func TestOrderRepository(t *testing.T) { /* 常に外部へ接続する */ }
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| テストが走る仕組み | 言語 |
| 何を保証するか | 用途 |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| 外部を伴うテストを CI で走らせるか | 用途 | 用意できる環境で決まる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| GH-TP-01 | 規格 | Go 標準 `testing`（内部テストと外部テスト）<br>https://pkg.go.dev/testing | 2026-09-05 取得 | `Short` |
| GH-TP-04 | 規格 | Go 標準 `testing.Short`<br>https://pkg.go.dev/testing | 2026-09-05 取得 | `testing.Short` |