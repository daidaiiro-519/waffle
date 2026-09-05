---
id: lang.go.style
layer: lang.go
axes:
  - axis: language
    value: go
category: coding
declares: 綴りと書式
updated: 2026-09-05
---

# Go における綴りと書式

## 概要

**書式は `gofmt` に委ね、人が判断するのは命名と公開範囲だけにする。**

## 規則一覧

| ID | 規則 | 水準 | 検証方法 | 適用範囲 |
|---|---|---|---|---|
| GO-STY-01 | 書式は `gofmt` の出力に一致させる | 必須 | 静的解析 | 全体 |
| GO-STY-02 | 公開する識別子は大文字始まり、それ以外は小文字始まりにする | 必須 | 静的解析 | 全体 |
| GO-STY-03 | パッケージ名は単数形の小文字1語にし、`util` ・ `common` を使わない | 必須 | レビュー | パッケージ |
| GO-STY-04 | 公開する識別子には、識別子名で始まる doc コメントを付ける | 必須 | 静的解析 | 公開する識別子 |
| GO-STY-05 | 受け取り側は具体型、返す側も具体型にする。抽象は使う側が定める | 必須 | レビュー | 公開する関数 |

## 規則の詳細

### GO-STY-01　書式は `gofmt` の出力に一致させる

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 書式の議論を消すために整形ツールを使うので、例外を置くと議論が戻る |
| 検証方法 | `gofmt -l .` が何も出力しない |
| 例外 | 生成されたコード |
| 既存コードへの適用 | 一括是正 |

**適合例**

```go
func ReadPort(raw string) (uint16, error) {
	n, err := strconv.ParseUint(raw, 10, 16)
	if err != nil {
		return 0, fmt.Errorf("parse port: %w", err)
	}
	return uint16(n), nil
}
```

**違反例**

```go
func ReadPort(raw string) (uint16, error) { n,err := strconv.ParseUint(raw,10,16); if err!=nil { return 0,err }; return uint16(n),nil }
```

### GO-STY-03　パッケージ名は単数形の小文字1語にし、`util` ・ `common` を使わない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 名前が中身を言わないパッケージは、置き場所の判断を毎回必要にする |
| 検証方法 | パッケージ名の一覧を見る |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
package order
```

**違反例**

```go
package utils
```

### GO-STY-05　受け取り側は具体型、返す側も具体型にする。抽象は使う側が定める

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 根拠 | 抽象を先に置くと、使う側が要らない約束に縛られる |
| 検証方法 | 公開する関数の引数と戻り値を見る |
| 例外 | 標準ライブラリの `io.Reader` のような、既に確立した抽象 |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
func Load(path string) (*Config, error)
```

**違反例**

```go
func Load(loader ConfigLoader) (ConfigProvider, error)
```

## 適用範囲外

| 何を | どの層が決めるか |
|---|---|
| 層ごとの命名の当て方 | 言語 × アーキテクチャ |
| パッケージの分け方 | 言語 × アーキテクチャ |

## 委譲する判断

| 委譲する判断 | 委譲先 | 委譲する理由 |
|---|---|---|
| doc コメントに書く節 | 用途 | 読み手が誰かで変わる |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 照合する文字列 |
|---|---|---|---|---|
| GO-STY-01 | 規格 | `gofmt` の説明<br><small>https://pkg.go.dev/cmd/gofmt</small> | 2026-09-05 取得 | `gofmt` |
| GO-STY-02 | 規格 | Go 仕様 Exported identifiers<br><small>https://go.dev/ref/spec</small> | 2026-09-05 取得 | `exported` |
| GO-STY-03 | 文献 | Effective Go（パッケージ名）<br><small>https://go.dev/doc/effective_go</small> | 2026-09-05 取得 | `Package names` |
| GO-STY-05 | 文献 | Go Code Review Comments（インターフェースの置き場所）<br><small>https://go.dev/wiki/CodeReviewComments</small> | 2026-09-05 取得 | `interfaces` |