---
id: lang.go.style
layer: lang.go
axes:
  - axis: language
    value: go
category: coding
declares: 綴りと書式
updated: 2026-09-06
approved_by: daidaiiro
approved_at: 2026-09-06
---

# Go における綴りと書式

## 概要

**書式は `gofmt` に委ね、人が判断するのは命名と公開範囲だけにする。**

## 規則一覧

| ID | 規則 | 水準 | 適用範囲 |
|---|---|---|---|
| GO-STY-01 | 書式は `gofmt` の出力に一致させる | 必須 | 全体 |
| GO-STY-02 | 公開する識別子は大文字始まり、それ以外は小文字始まりにする | 必須 | 全体 |
| GO-STY-03 | パッケージ名は単数形の小文字1語にし、`util` ・ `common` を使わない | 必須 | パッケージ |
| GO-STY-04 | 公開する識別子には、識別子名で始まる doc コメントを付ける | 必須 | 公開する識別子 |
| GO-STY-05 | 受け取り側は具体型、返す側も具体型にする。抽象は使う側が定める | 必須 | 公開する関数 |

## 規則の詳細

### GO-STY-01　書式は `gofmt` の出力に一致させる

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 全体 |
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

### GO-STY-02　公開する識別子は大文字始まり、それ以外は小文字始まりにする

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 全体 |
| 根拠 | Go では大文字始まりがそのまま公開になる。意図せず大文字にすると、外へ出す約束が増える |
| 検証方法 | 当たる命令が無い（`ST1003` が見るのは package 名と mixedCaps であって、公開の意図との一致ではない）。`go doc <パッケージ>` に出る識別子が、公開したいものと一致するかを見る |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
type Store struct{ db *sql.DB }

func (s *Store) Save(ctx context.Context, u *User) error { return s.insert(ctx, u) }

func (s *Store) insert(ctx context.Context, u *User) error { ... }
```

**違反例**

```go
func (s *Store) Insert(ctx context.Context, u *User) error { ... }
```

### GO-STY-03　パッケージ名は単数形の小文字1語にし、`util` ・ `common` を使わない

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | パッケージ |
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

### GO-STY-04　公開する識別子には、識別子名で始まる doc コメントを付ける

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 公開する識別子 |
| 根拠 | `go doc` の出力は doc コメントそのものである。識別子名で始まらないと、一覧で何の説明か分からない |
| 検証方法 | `staticcheck -checks ST1020,ST1021,ST1022 ./...` と、公開する識別子に doc が付いているか（doc が無いことは `ST1020` では落ちない） |
| 例外 | なし |
| 既存コードへの適用 | 改修時に是正 |

**適合例**

```go
// Save stores u and returns an error when the write fails.
func (s *Store) Save(ctx context.Context, u *User) error { ... }
```

**違反例**

```go
// ユーザを保存する。
func (s *Store) Save(ctx context.Context, u *User) error { ... }
```

### GO-STY-05　受け取り側は具体型、返す側も具体型にする。抽象は使う側が定める

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 公開する関数 |
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

## 整形ツールに委ねる範囲

| 項目 | 誰が決めるか |
|---|---|
| 字下げ・改行・空白・取り込みの並び | `gofmt`。人が議論しない |
| 設定の変更 | できない。設定を持たないことが利点である |
| 除外 | 生成したコードのみ |
| 検査の位置づけ | 整形されていないことを、変更を取り込む前に落とす |

## 命名

| 対象 | 形 | 例 |
|---|---|---|
| 公開する識別子 | 語頭を大文字で繋ぐ | `ReadPort` |
| 公開しない識別子 | 語頭を小文字で繋ぐ | `readPort` |
| 頭字語 | 大小をそろえる | `URL` ／ `url`。`Url` としない |
| 受け手 | 1〜2文字にし、型ごとに統一する | `func (p Port) ...` |
| パッケージ | 小文字1語。利用側の呼び出しと重ねて読む | `port.Read` であって `port.PortRead` ではない |
| 番兵の失敗 | `Err` で始める | `ErrOutOfRange` |

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

| ID | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| GO-STY-01 | 規格 | `gofmt` の説明<br>https://pkg.go.dev/cmd/gofmt | 2026-09-06 取得 | `gofmt` が書式を決める |
| GO-STY-02 | 規格 | Go 仕様 Exported identifiers<br>https://go.dev/ref/spec | 2026-09-06 取得 | 大文字始まりが公開である |
| GO-STY-03 | 文献 | Effective Go<br>https://go.dev/doc/effective_go | 2026-09-06 取得 | パッケージ名の付け方 |
| GO-STY-05 | 文献 | Go Code Review Comments<br>https://go.dev/wiki/CodeReviewComments | 2026-09-06 取得 | インターフェースは使う側に置く |
| GO-STY-04 | 文献 | Go Code Review Comments<br>https://go.dev/wiki/CodeReviewComments | 2026-09-06 取得 | doc は識別子名で始める |