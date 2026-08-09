---
id: "architecture-waffle"
type: "architecture"
title: "Waffle自身が採用するヘキサゴナルアーキテクチャの層構造を定めるArchitecture仕様：architecture-waffle"
description: "Waffle自身がヘキサゴナルアーキテクチャを実装する際の層構造・依存方向を定める。"
tags: ["tier:backend"]
schemaRef: "CodingSchema/v6"
---

# Waffle自身が採用するヘキサゴナルアーキテクチャの層構造を定めるArchitecture仕様：architecture-waffle

## 概要

Waffle自身がヘキサゴナルアーキテクチャを実装する際の層構造・依存方向を定める。

---

## 実装を受け持つコンテキスト

- bc-waffle

---

## レイヤーと依存方向

### 様式

ポートとアダプター（ヘキサゴナル）

| レイヤー | 配置 | 責務 | 依存してよい先 |
|---|---|---|---|
| shared | `shared` | 全層から使える基盤（結果型・エラー等）。業務判断を持たない |  |
| domain | `domain` | ドメインモデル・不変条件・値 | shared |
| application | `application` | usecase の調整・トランザクション境界。外部へ要求する port をここで宣言する | domain / shared |
| inbound adapter | `adapters/inbound` | 外部からの入口（driving：API・CLI 等）。外部入力を application 呼び出しへ変換するだけで、判断を持たない | application / shared |
| outbound adapter | `adapters/outbound` | 外部への出口（driven：DB・外部サービス）。application が宣言した port を実装する | application / shared |

---

## ディレクトリ構成

```
src/{package}/
  domain/
    entities/       entity, aggregate（ルートを通じてのみ触れるもの）
    value_objects/  value-object（同一性を持たず、複数の集約が使ってよい値）
    model/          schema.jsonそのもの（JSON Schema定義の同梱データ。DDD実装クラスの置き場ではない）
    services/       domain-service
  application/
    usecases/       1 usecase = 1 module
    ports/          driven interface の定義
  adapters/
    inbound/        driving（api, cli, ...）
    outbound/       driven（db, external, ...）
  shared/           共通（エラー・結果型 等）
```

### 1ファイルの粒度

| 概念 | 1ファイルあたり |
|---|---|
| `usecase` | 1 |
| `aggregate` | 1 |
| `domain-service` | 1 |
| `port` | 1 |

### 合成ルート（結線・DI）

各エントリポイントに1つだけ置く（adapters/inbound/cli/main.py・adapters/inbound/mcp/main.py）。合成ルートは層のグラフの外にあり、結線のためにすべてを知ってよい唯一の場所。配線専用に保つ

- adapters/inbound/cli/main.py
- adapters/inbound/mcp/main.py

---

## 概念 → 実現形

| 概念 | 配置 | 形（決定レベル） |
|---|---|---|
| `usecase` | `application/usecases` | application service・エントリメソッド1つ・ドメインは port 経由で呼ぶ |
| `aggregate` | `domain/entities` | 整合性境界を持つクラス・不変条件をメソッド内で強制・コマンドはメソッド・永続化は repository 経由 |
| `entity` | `domain/entities` | 同一性は id・集約の内側でのみ可変 |
| `value-object` | `domain/value_objects` | 不変（frozen dataclass）・値等価 |
| `domain-service` | `domain/services` | ステートレス・複数集約を跨る計算 |
| `repository` | interface `application/ports`<br>implementation `adapters/outbound` | aggregate の load/save・集約1つに1リポジトリ |
| `port` | `application/ports` | application が要求する driven インターフェース（ABC / Protocol） |
| `inbound-adapter` | `adapters/inbound` | 外部入力を application 呼び出しへ変換・ロジックを持たない |
| `outbound-adapter` | `adapters/outbound` | port / repository を実装・外部ライブラリをここに閉じ込める |

---

## 規約（守るべきルール）

| 種別 | 規約 |
|---|---|
| 必須 | 依存は layers が宣言する mayDependOn に限る（内向きであっても、宣言に無い層へは依存しない） |
| 必須 | 技術的詳細（外部への入出力・基盤・実行の枠組み）への依存は adapter 層（inbound / outbound）に閉じ込め、domain / application は直接触れない。outbound 側については port を通してのみ触れる。判断の基準は「外部の作者が書いたコードか」ではなく「その依存が実行環境・基盤・枠組みに結びついているか」。純粋な計算だけを行うライブラリは、この制約の対象ではない |
| 禁止 | adapter 層でポート（抽象インターフェース）を定義する。ポートは常に application が「何を必要としているか」の視点で宣言し、adapter は実装のみを持つ。配置が application/ports であっても、その形をアダプターの都合で決めているなら依存方向は実質的に逆転している |
| 禁止 | domain 層での副作用（I/O・グローバル可変状態） |
| 必須 | aggregate / entity の状態フィールドは、外部から直接代入できないようにする（不変化・private 化・読み取り専用プロパティ等、言語機能で経路そのものを塞ぐ）。不変条件を強制するメソッドを用意するだけでは完了とみなさない——メソッドを経由しない代入が残っていれば、その経路から不変条件を迂回できる |
| 禁止 | 外側から受け取った値を domain オブジェクトのフィールドへ直接代入する。状態変更は意図を表すコマンドとして渡し、集約のメソッド呼び出しとして実行する |
| 必須 | 合成ルート（結線・DI）はシステムの最も外側の起動点（inbound adapter のエントリポイント）に置き、各エントリポイントに1つだけ持つ。層のグラフの外にあり、実際の場所は layout の compositionRootPaths が宣言する（ここでは繰り返さない）。依存（port / repository）はコンストラクタ注入で受け取り、生成は合成ルートだけが行う |
| 禁止 | 合成ルートに業務ロジックを書く／個々の usecase・adapter の中でアダプターの具体クラスを生成する（どちらも配線を1箇所に保てなくする） |
| 必須 | application 境界は結果型（Result 等）で成否を返す・domain は不変条件違反をドメイン例外で表す |
| 必須 | 失敗は識別可能なエラーコード（定数文字列）を伴う結果型で返す（メッセージ文字列のみは不可） |
| 必須 | 技術的な失敗は、境界を越える前に port 契約が定める失敗の形（Result 等）へ翻訳する。入口・出口のどちらの境界にも等しく適用し、ライブラリ固有の例外型を application / domain まで伝播させない。時間切れ（タイムアウト）も通常の失敗として同じ形で表す。ただし回復不能な致命的失敗（起動時の構成不備・プログラミング上の誤り等）は、翻訳せず上位へ伝播させ、合成ルート境界で一括処理してよい。この例外は、呼び出し元が業務判断としてその失敗を処理できない場合にのみ適用する |
| 禁止 | 例外の握り潰し（ドメイン例外・技術的例外を問わない）。境界では結果型へ写像するか、回復不能な致命的失敗として上位へ伝播させるかのいずれかとし、失敗を黙って捨てない |
| 必須 | domain が投げる例外は業務ルール違反のみを表す（業務語彙の専用例外型）。技術的失敗の翻訳先として使わない |
| 禁止 | application の境界を越えて domain オブジェクト（entity・aggregate）をそのまま渡す。inbound adapter へ返す形・outbound adapter へ渡す形は、必要な値だけを持つ専用の型にする |
| 必須 | ロギング・キャッシュ・パフォーマンス計測のような純粋に技術的な横断的関心事は、domain/application のコードに書かず、外側（デコレーター・ミドルウェア等）で一括して適用する |
| 必須 | 監査ログ・認可のような業務要件としての横断的関心事は、「何を記録すべきか・誰が実行を許可されるか」の判断を domain/application が持ち、実際の記録・認証手段は port 経由で outbound adapter に委譲する |
| 禁止 | 認可チェックを domain 層の集約メソッドの中に直接書く（「誰がログインしているか」という技術的な認証の仕組みに domain 層が依存し、依存方向が逆転する） |

---

## サブドメイン別の厚み

| Category | 実装の厚み |
|---|---|
| 中核 | 厚い設計（明示的なドメインモデル）。トランザクションスクリプト・アクティブレコードは使わない（業務ルールが複雑になるほど、これらは同じ判断ロジックの重複・不整合を招くため） |
| 一般 | ライブラリを adapter で薄く包む |
| 補完 | 最小のトランザクションスクリプト（またはデータ構造が複雑ならアクティブレコード）。唯一の規律は、一連の更新処理が完全に成功するか完全に失敗するかのどちらかで終わること（トランザクション管理）。業務ルールが複雑化してきたら中核と同じ厚い設計への移行を検討する |
