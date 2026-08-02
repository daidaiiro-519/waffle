---
id: "architecture-typescript-hexagonal"
type: "architecture"
title: "TypeScript/ヘキサゴナルアーキテクチャの層構造を定めるArchitecture仕様：architecture-typescript-hexagonal"
description: "TypeScriptでヘキサゴナルアーキテクチャを実装する際の層構造・依存方向を定める。"
schemaRef: "CodingSchema/v5"
---

# TypeScript/ヘキサゴナルアーキテクチャの層構造を定めるArchitecture仕様：architecture-typescript-hexagonal

## 概要

TypeScriptでヘキサゴナルアーキテクチャを実装する際の層構造・依存方向を定める。

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
src/
  domain/
    model/
    value-objects/
    services/
  application/
    usecases/
    ports/
  adapters/
    inbound/
    outbound/
  shared/

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

- adapters/inbound/main.ts

---

## 概念 → 実現形

| 概念 | 配置 | 形（決定レベル） |
|---|---|---|
| `usecase` | `application/usecases`（single） | エントリメソッド1つ・ドメインは port 経由で呼ぶ |
| `aggregate` | `domain/model`（single） | 不変条件はメソッド経由でのみ変更できる形にする（コンストラクタとメソッド内に検証ロジックを閉じ込める）。外部の集約はIDで参照し、直接オブジェクトとして保持しない。集約はできるだけ小さく設計する |
| `entity` | `domain/model`（single） | 同一性はidで判定する（フィールドの値ではない）。単独では実装しない。必ず集約の内部にのみ存在する |
| `value-object` | `domain/value-objects`（single） | 構造的等価性・不変（readonlyフィールドのみ・状態変更メソッドを持たない） |
| `domain-service` | `domain/services`（single） | ステートレス（同じ入力に対して常に同じ結果を返す）。複数集約を単一トランザクションでまとめて変更するための抜け道にはしない（1集約=1トランザクションの原則は業務サービスがあっても変わらない） |
| `repository` | `application/ports`（interface）<br>`adapters/outbound`（implementation） | インターフェースはports、具象はoutbound adapterに置く |
| `port` | `application/ports`（single） | インターフェース定義のみ・実装を持たない。ポートは常にコア（domain/application）が「何を必要とするか」の視点で定義し、アダプター側の実装都合に引きずられない |
| `inbound-adapter` | `adapters/inbound`（single） | 外部プロトコルの受け口。usecaseを呼び出すだけで業務ロジックを持たない |
| `outbound-adapter` | `adapters/outbound`（single） | portの実装。外部システムとの実際のやり取りを担う |

---

## 規約（守るべきルール）

| 種別 | 規約 |
|---|---|
| 必須 | 依存は常に内向き（adapters→application→domain）。domainは他レイヤーを一切importしない |
| 必須 | DIはコンストラクタ注入で行い、実装（class）ではなくport（インターフェース）型で受け取る |
| 必須 | domain/applicationからadapter/外部ライブラリの型を直接importしない（型はportsで自前定義する） |
| 推奨 | エラー伝播は、想定内の失敗（業務ルール違反等）は戻り値の判別可能な型（Result型相当）で表現し、想定外の異常はthrowする。境界（adapter）で例外を捕捉し外部向けの形に翻訳する（内側→外側方向の翻訳） |
| 必須 | outbound adapter内で発生した技術的失敗（特定ライブラリ・ドライバ固有の例外型）を、そのままdomain/applicationへ伝播させない。抽象化した失敗の形に翻訳してから内側へ渡す（外側→内側方向の翻訳） |
| 禁止 | outbound adapterの実装の詳細（クエリ・スキーマ形式等）がapplication/domainへ漏れること |
| 必須 | レイヤー境界を越えてdomainオブジェクト（entity・aggregate）をそのまま渡さない。外部に出る形は必要な値だけをコピーした専用のDTOにする |
| 禁止 | 個々のusecase・adapterの中でアダプターの具体クラスをnewする。配線（DI）はcompositionRootの1箇所に集約する |
| 必須 | Promiseのrejectionは必ず境界（adapter/composition root）で捕捉する。未処理のPromise拒否をdomain/applicationの外へ漏らさない。外部呼び出しにはタイムアウトを設定し、タイムアウトも通常の失敗としてResult型相当で表現する |

---

## サブドメイン別の厚み

| Category | 実装の厚み |
|---|---|
| 中核 | aggregate/entity/value-object/domain-serviceをフルに用いて厚く設計する |
| 一般 | 既存ライブラリ・外部サービスを薄いadapterで包む程度に留める |
| 補完 | 最小限のusecase内の手続き的処理のみ（別途domainモデルを起こさない）。唯一の規律は、一連の更新処理が完全に成功するか完全に失敗するかのどちらかで終わること（トランザクション管理） |
