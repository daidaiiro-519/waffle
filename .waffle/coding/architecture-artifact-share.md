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
scripts/                 手元で動くプログラム（層を持たないと宣言した領域）
  artifactshare.py       環境を作るCLI。クラウドの権限で動くため、管理操作を持たない
  mcp/                   招かれた投稿者としての受け口。合言葉で本人確認を通り、クラウドの権限を使わない
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
| 必須 | 閲覧ゲートは実行環境の制約（単一ファイル・自前モジュール不可・サイズ上限）により層を持たない。宣言された不変条件を、同じシナリオに紐づくテストとともにその1ファイル内で実装する |
| 必須 | 2つのランタイムが同じ業務ルールを守るとき、ルールの宣言は spec に1つだけ置く。実装はランタイムごとに持つが、両方が同じシナリオに紐づくことで対応を保つ。コードの重複は認めるが、宣言の重複は認めない |
| 必須 | ランタイムをまたいで受け渡すデータの形は infra/contract/ に置き、両方のランタイムがそこを読む。片方が形を直書きすると、もう片方を直したときに気づけない |
| 必須 | 手元で動くプログラムは、動く資格で分ける。クラウドの権限で動くもの（環境を作るCLI）と、合言葉で本人確認を通り招かれた投稿者として動くもの（受け口）を、別のプログラムとして置く |
| 禁止 | クラウドの権限で動くプログラムに管理操作を持たせる／本人確認で動くプログラムにクラウドの権限を使う操作を足す。どちらも「招かれた者だけが公開できる」という前提を、権限を持つ人の手元で成り立たなくする。同じ場所に置いてあることを理由に2つを統合しない |

---

## サブドメイン別の厚み

| Category | 実装の厚み |
|---|---|
| 中核 | 厚い設計（明示的なドメインモデル）。不変条件を型で表し、状態の変更は集約のメソッドを経由させる |
| 一般 | ライブラリを adapter で薄く包む |
| 補完 | 最小のトランザクションスクリプト。一連の更新が完全に成功するか完全に失敗するかで終わることだけを守る |
