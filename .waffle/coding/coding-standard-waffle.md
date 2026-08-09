---
id: "coding-standard-waffle"
type: "coding-standard"
title: "Waffle自身が採用するコーディング規約を定めるCoding Standard：coding-standard-waffle"
description: "Waffle自身のコーディング規約（命名・スタイル・docstring）を定める。"
tags: ["tier:backend"]
schemaRef: "CodingSchema/v6"
---

# Waffle自身が採用するコーディング規約を定めるCoding Standard：coding-standard-waffle

## 概要

Waffle自身のコーディング規約（命名・スタイル・docstring）を定める。

---

## 命名

### ファイル名

- **由来**: type
- **変換**: pascal-to-snake
- **拡張子**: .py

### 表記

| 対象 | 可視性 | 表記 | 接頭辞 |
|---|---|---|---|
| `module` |  | snake |  |
| `type` |  | pascal |  |
| `function` |  | snake |  |
| `field` |  | snake |  |
| `function` | private | snake | `_` |

### 規範

| 適用先 | 規範 |
|---|---|
| 語彙 | 仕様（spec）のユビキタス言語に一致させる（勝手な言い換え禁止） |
| domain | ユビキタス言語のみで構成する。Impl/DTO/Manager/Helper等の技術的接尾辞を付けない（付いている時点でその概念はドメインの言葉でなく実装都合で存在している兆候） |
| application | 動詞＋目的語の業務操作として命名し、対応する usecase spec が宣言する操作名とそのまま一致させる（例: RequestPickup、CancelOrder）。Engine 等の装飾的な接尾辞を付けない。ファイル名はこのブロックのファイル名3欄が導く |
| outbound adapter | 使用する技術名を明示してよい（例: PostgresShipmentRepository、InMemoryShipmentRepository）。ポート実装であることが責務そのものなので技術名を隠す理由が無い |
| レイヤー境界を越えるDTO | 層の外に出るための入れ物であることが分かる名前にする（例: ShipmentStatusResponse）。ドメインオブジェクトと同じクラス名を使い回さない |

---

## スタイル

| 種別 | 規約 |
|---|---|
| 必須 | 型注釈を公開関数の引数・戻り値に付ける |
| 必須 | 1関数＝1責務 |
| 禁止 | 循環 import |
| 推奨 | 早期 return で条件分岐の入れ子を避ける |
| 必須 | importは標準ライブラリ／サードパーティ／ローカル（自プロジェクト）の3グループに分け、グループ間を空行で区切る。グループ内はアルファベット順。自動整形ツール（isort/ruff等）の設定をこの規約のSSOTとし、手動での並べ替えはしない |

---

## docstring

- **スタイル**: Google スタイル docstring
- **構文の種類**: tagged
- **パラメータ**: Args:
- **戻り値**: Returns:
- **例外**: Raises:

### 必須とする対象

| 対象 | 可視性 | 必須 |
|---|---|---|
| `module` | any | ✓ |
| `type` | public | ✓ |
| `function` | public | ✓ |
| `function` | private | - |

### 要約行の書き方

「何をするか・いつ使うか」を1行の平叙文で。インデックスに載る前提で、検索と判断に効く語を選ぶ。

```
def calculate_total(order: Order, coupon: Coupon | None = None) -> Money:
    """注文の合計金額を計算する。クーポン適用後の金額を返す。

    Args:
        order: 対象の注文。
        coupon: 適用するクーポン（無ければ定価のまま）。

    Returns:
        クーポン適用後の合計金額。

    Raises:
        InvalidCouponError: クーポンの適用条件を満たさない場合。
    """
```

---

## 決定ルール

| 種別 | 規約 |
|---|---|
| 必須 | 公開要素に要約行つき docstring を書く |
| 禁止 | コードから導出できる情報を docstring に書く（型の列挙・実装手順の逐語説明） |
| 推奨 | コメントは「なぜ」を書く（「何を」は命名と要約行が表現する） |
