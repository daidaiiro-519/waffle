# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{タイトル}}` | 「業務エキスパートが理解できる日本語の説明：識別子」の形式で設定してください。説明部分はこのSpecが何であるかを業務語彙で簡潔に表す句（documentIdやクラス名をそのまま繰り返さない）。specKindがbounded-context/subdomain/aggregateの場合は、説明の末尾にその種別を表す語（bounded-contextなら「〜を行う境界づけられたコンテキスト」、subdomainなら「〜を担うサブドメイン」、aggregateなら「〜を守る集約」）を含め、読んだだけでこのSpecがDDDのどの構成要素かがわかるようにしてください（usecaseの場合はこの種別語を付けない）。識別子部分はspecKindに応じて設定する: usecaseの場合はcontent.name.operationNameと同じ値、aggregateの場合はcontent.aggregateRoot.nameと同じ値、bounded-context/subdomainの場合はdocumentIdをそのまま使う（識別子は既に別の構造化フィールドが正であり、ここでは表示のためだけに引用する。実装と乖離しても他のフィールドのように機械的ドリフト検知の対象にならないため、識別子以外の実装レベルの詳細をここに書き込まない）。（JSON上のフィールド: content.title.title） |
| `{{概要.論点1}}` | 論点ごとに列挙する（1〜2項目が目安）。この文脈/業務領域/集約/ユースケースが何かを1〜2文で（ドメイン語彙のみ・技術用語禁止）。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.summary.items[]） |
| `{{サブドメイン分類.分類}}` | 中核=core / 補完=supporting / 一般=generic。競争優位を生むか・既製品があるかで判定。見出しにはcore→中核、supporting→補完、generic→一般の日本語ラベルが使われる。（JSON上のフィールド: content.category.classification） |
| `{{サブドメイン分類.根拠1}}` | 根拠を独立した論点ごとに列挙する。そのカテゴリーである根拠（差別化の有無）。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.category.rationale[]） |
| `{{業務ユースケース一覧.ユースケース1}}` | この業務領域に属するusecaseのidを列挙。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.members.items[]） |
| `{{詳細設計ガイド.方針1}}` | 実装方針を論点ごとに列挙する。実装方針を1〜2文で。中核=ドメインモデルで厚く/一般=既製ライブラリを薄く包む/補完=薄いトランザクションスクリプト。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.implementationGuidance.items[]） |
| `{{外部解決策}}` | 採用する既製ライブラリ/サービス名と、それが @stack のどの能力に当たるか。中核/補完なら不要。（任意ブロック：一般カテゴリーの業務領域でなければexternalSolutionブロック自体を省略してよい）（JSON上のフィールド: content.externalSolution.text） |
| `{{ドメインサービス.項目1.業務サービス}}` | 業務サービス名。例: パステンプレート解決 / 整形描画（ドメイン語彙で、他の集約に属さない業務ロジックであることが分かる名前にする）（任意ブロック：複数集約に跨る/集約に収まらないステートレスな業務ロジックが無ければdomainServicesブロック自体を省略してよい）（JSON上のフィールド: content.domainServices.items[].name） |
| `{{ドメインサービス.項目1.責務}}` | 何を計算/判定するか・どの集約に跨るか・入力→出力（何を受け何を返すか）を1文で。実装手順は書かない。（JSON上のフィールド: content.domainServices.items[].responsibility） |
| `{{業務サービスシナリオ.背景}}` | 複数シナリオ共通の前提。無ければ空文字。（任意ブロック：domainServicesが無ければdomainServiceScenariosブロック自体を省略してよい）（JSON上のフィールド: content.domainServiceScenarios.background） |
| `{{業務サービスシナリオ.シナリオ1.シナリオ名}}` | シナリオ名（概要）。（JSON上のフィールド: content.domainServiceScenarios.scenarios[].name） |
| `{{業務サービスシナリオ.シナリオ1.分類}}` | 分類: 正常系 / 異常系 / 境界値。（JSON上のフィールド: content.domainServiceScenarios.scenarios[].category） |
| `{{業務サービスシナリオ.シナリオ1.観点}}` | 観点: 何を計算/判定するか＋検証の狙い。（JSON上のフィールド: content.domainServiceScenarios.scenarios[].viewpoint） |
| `{{業務サービスシナリオ.シナリオ1.本文}}` | Given/When/Then。ドメイン語彙で書き、実装詳細は書かない。（JSON上のフィールド: content.domainServiceScenarios.scenarios[].gherkin） |
| `{{業務サービスシナリオ.シナリオ1.参照}}` | 対応するdomainServicesの項目への参照。（JSON上のフィールド: content.domainServiceScenarios.scenarios[].covers） |

---

# {{タイトル}}

---

## 概要

- {{概要.論点1}}

---

## サブドメイン分類

### 分類

{{サブドメイン分類.分類}}

### 根拠

- {{サブドメイン分類.根拠1}}

---

## 業務ユースケース一覧

- {{業務ユースケース一覧.ユースケース1}}

---

## 詳細設計ガイド

- {{詳細設計ガイド.方針1}}

---

## 外部解決策

{{外部解決策}}

---

## ドメインサービス

| 業務サービス | 責務 |
|---|---|
| {{ドメインサービス.項目1.業務サービス}} | {{ドメインサービス.項目1.責務}} |

---

## 業務サービスシナリオ

### 背景

{{業務サービスシナリオ.背景}}

### {{業務サービスシナリオ.シナリオ1.シナリオ名}}

| 分類 | 観点 |
|---|---|
| {{業務サービスシナリオ.シナリオ1.分類}} | {{業務サービスシナリオ.シナリオ1.観点}} |

```gherkin
{{業務サービスシナリオ.シナリオ1.本文}}
```
