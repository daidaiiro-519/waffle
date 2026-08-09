---
id: "tech-stack-artifact-share"
type: "tech-stack"
title: "artifact-shareが採用する技術要素を定めるTech Stack仕様：tech-stack-artifact-share"
description: "artifact-shareがAWS上で採用する技術要素と、その選定理由を定める。閲覧の面はCloudFront Functionsという実行環境がJavaScriptを強制するため、1つのプロダクトが2つのランタイムを持つ。"
tags: ["tier:backend"]
schemaRef: "CodingSchema/v7"
---

# artifact-shareが採用する技術要素を定めるTech Stack仕様：tech-stack-artifact-share

## 概要

artifact-shareがAWS上で採用する技術要素と、その選定理由を定める。閲覧の面はCloudFront Functionsという実行環境がJavaScriptを強制するため、1つのプロダクトが2つのランタイムを持つ。

---

## スタック概要

- **対象領域（ティア: backend=サーバー側 / frontend=画面側 / platform=基盤側）**: backend
- **スタック名**: artifact-share

---

## ランタイム

- **実行ターゲット**: サーバーレス関数（Lambda）／エッジ関数（CloudFront Functions）／利用者のブラウザ（管理画面・閲覧画面）／ローカルCLI
- **並行モデル**: 同期主体（1リクエスト1実行。共有状態を持たない）

### 言語

| 言語 | 版 | 拡張子 | 役割 |
|---|---|---|---|
| `python` | >=3.11 | `.py` | primary |
| `javascript` |  | `.js` | edge |
| `javascript` |  | `.js / .html` | browser |

---

## フレームワーク

Webフレームワークは使用しない。Lambdaの関数URL/API Gatewayが受け口を担い、経路の振り分けは自前のディスパッチ表で足りる規模のため。

---

## 公開インターフェース

### HTTP API

- **実装**: AWS Lambda（API Gateway経由）

#### 選定理由

管理操作は認証を要し実行回数も少ないため、常駐プロセスを持たない構成が費用と運用の両面で釣り合うため

### 閲覧ゲート

- **実装**: CloudFront Functions

#### 選定理由

閲覧のたびにLambdaを起こすと遅延と費用が乗る。トークン照合は配信の面で完結させたいため。実行環境がJavaScriptとサイズ上限を強制する点は制約として受け入れる

### CLI

- **実装**: argparse（PEP723のインラインスクリプト）

#### 選定理由

環境構築の手順を1ファイルで配れるようにするため。追加の依存を要求しない

---

## ミドルウェア

### Amazon S3

- **役割**: object-storage
- **アクセス手段**: boto3

#### 選定理由

公開物と索引をそのまま置ける。配信の面（CloudFront）から直接読めるため中間層が要らない

### CloudFront KeyValueStore

- **役割**: key-value
- **アクセス手段**: boto3 / cloudfront組み込みモジュール

#### 選定理由

エッジ関数から同期で読める唯一の保管。トークン照合を配信の面で完結させるために必要

### Amazon Cognito

- **役割**: identity
- **アクセス手段**: boto3

#### 選定理由

管理操作の認証を自前で持たないため

---

## ライブラリ

### boto3

- **分類**: cloud-sdk
- **用途**: aws-access

#### 選定理由

AWSの各サービスへ触れる唯一の手段。Lambdaの実行環境に同梱されており追加の配布が要らない

---

## 開発ツール

- **パッケージ管理**: uv（PEP723のインラインスクリプトで依存を宣言）
- **選定理由**: 環境構築のCLIを1ファイルで配れるようにするため。Lambda側は実行環境の同梱物だけで動くので、パッケージの束ね方を持ち込まない

---

## 依存方針

| 種別 | 方針 |
|---|---|
| 必須 | 依存追加は「実行環境に同梱されているもので代替できないか」を確認してから。Lambdaとエッジ関数は配布物の大きさが実行可否に直結する |
| 禁止 | エッジ関数に外部ライブラリを持ち込む（実行環境が自前モジュールの読み込みを許さない） |
