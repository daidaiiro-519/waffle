---
id: "architecture-artifact-share"
type: "architecture"
title: "artifact-shareが採用する層構造を定めるArchitecture仕様：architecture-artifact-share"
description: "artifact-shareがヘキサゴナルアーキテクチャを実装する際の層構造・依存方向を定める。閲覧ゲートは実行環境の制約により層を持たないため、その扱いも併せて定める。"
tags: ["tier:backend"]
schemaRef: "CodingSchema/v5"
---

# artifact-shareが採用する層構造を定めるArchitecture仕様：architecture-artifact-share

## 概要

artifact-shareがヘキサゴナルアーキテクチャを実装する際の層構造・依存方向を定める。閲覧ゲートは実行環境の制約により層を持たないため、その扱いも併せて定める。

---

## 実装を受け持つコンテキスト

- bc-artifact-share

---

## レイヤーと依存方向

### 様式

ポートとアダプター（ヘキサゴナル）

| レイヤー | 配置 | 責務 | 依存してよい先 |
|---|---|---|---|
| shared | `lambda/admin_api/shared` | 全層から使える基盤（結果型・エラー等）。業務判断を持たない |  |
| domain | `lambda/admin_api/domain` | 業務ルールと不変条件。トークンの有効性・交差条件・公開状態の判断をここに集める | shared |
| application | `lambda/admin_api/application` | usecase の調整と、外部へ要求する port の宣言。usecases/ と ports/ をこの配下に持つ | domain / shared |
| inbound adapter | `lambda/admin_api/adapters/inbound` | 外部からの入口（Lambda handler・経路の振り分け）。外部入力を usecase 呼び出しへ変換するだけで、判断を持たない | application / shared |
| outbound adapter | `lambda/admin_api/adapters/outbound` | 外部への出口（S3・KVS・Cognito）。application が宣言した port を実装する | application / shared |

---

## ディレクトリ構成

```
lambda/admin_api/
  domain/                業務ルール（トークンの有効性・交差条件・公開状態）
  application/
    usecases/            1 usecase = 1 module
    ports/               application が外部へ要求するインターフェース
  adapters/
    inbound/             受け口（Lambda handler・経路の振り分け）
    outbound/            S3 / KVS / Cognito への出口
  shared/                結果型・エラー
  main.py                結線（合成ルート・層のグラフの外）
infra/
  cloudfront-function/   閲覧ゲート（層を持たないと宣言した領域）
  contract/              ランタイムをまたぐデータの形
scripts/                 環境構築のCLI（層を持たないと宣言した領域）
```

### 1ファイルの粒度

| 概念 | 1ファイルあたり |
|---|---|
| `usecase` | 1 |
| `aggregate` | 1 |
| `domain-service` | 1 |
| `port` | 1 |

### 合成ルート（結線・DI）

Lambdaの起動点に1つだけ置く。合成ルートは層のグラフの外にあり、結線のためにすべてを知ってよい唯一の場所。配線専用に保つ

- lambda/admin_api/main.py

---

## 概念 → 実現形

| 概念 | 配置 | 形（決定レベル） |
|---|---|---|
| `usecase` | `lambda/admin_api/application/usecases` | エントリメソッド1つ・ドメインは port 経由で呼ぶ |
| `aggregate` | `lambda/admin_api/domain` | 整合性境界を持つクラス・不変条件をメソッド内で強制 |
| `entity` | `lambda/admin_api/domain` | 同一性は id・集約の内側でのみ可変 |
| `value-object` | `lambda/admin_api/domain` | 不変（frozen dataclass）・値等価 |
| `domain-service` | `lambda/admin_api/domain` | ステートレス・複数集約を跨る判断 |
| `repository` | interface `lambda/admin_api/application/ports`<br>implementation `lambda/admin_api/adapters/outbound` | aggregate の load/save・集約1つに1リポジトリ |
| `port` | `lambda/admin_api/application/ports` | application が要求する driven インターフェース（Protocol）。構造体のフィールドとして持たず、型として宣言する |
| `inbound-adapter` | `lambda/admin_api/adapters/inbound` | 外部入力を usecase 呼び出しへ変換・判断を持たない |
| `outbound-adapter` | `lambda/admin_api/adapters/outbound` | port を実装・外部ライブラリをここに閉じ込める。合成ルートの中に無名で書かない |

---

## 規約（守るべきルール）

| 種別 | 規約 |
|---|---|
| 必須 | 依存は内向きのみ |
| 必須 | 外部 I/O・外部ライブラリ（boto3等）は outbound adapter に閉じ込める |
| 必須 | 依存（port / repository）はコンストラクタ注入で受け取る（生成は合成ルートのみ） |
| 禁止 | 合成ルート自体に業務ロジックを書く（配線専用に保つ） |
| 禁止 | outbound adapter を合成ルートの中に無名クラスとして書く。実装は独立したファイルに置き、名前で参照できるようにする |
| 必須 | application 境界は結果型で成否を返す。失敗は識別可能なエラーコードを伴う |
| 必須 | 閲覧ゲートは実行環境の制約（単一ファイル・自前モジュール不可・サイズ上限）により層を持たない。宣言された不変条件を、同じシナリオに紐づくテストとともにその1ファイル内で実装する |
| 必須 | 2つのランタイムが同じ業務ルールを守るとき、ルールの宣言は spec に1つだけ置く。実装はランタイムごとに持つが、両方が同じシナリオに紐づくことで対応を保つ。コードの重複は認めるが、宣言の重複は認めない |
| 必須 | ランタイムをまたいで受け渡すデータの形は infra/contract/ に置き、両方のランタイムがそこを読む。片方が形を直書きすると、もう片方を直したときに気づけない |

---

## サブドメイン別の厚み

| Category | 実装の厚み |
|---|---|
| 中核 | 厚い設計（明示的なドメインモデル）。公開と閲覧の可否はこの製品の中核であり、判断を型で表す |
| 一般 | ライブラリを adapter で薄く包む |
| 補完 | 最小のトランザクションスクリプト。一連の更新が完全に成功するか完全に失敗するかで終わることだけを守る |
