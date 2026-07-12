# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | 「業務エキスパートが理解できる日本語の説明：識別子」の形式で設定してください。説明部分はこのSpecが何であるかを業務語彙で簡潔に表す句（documentIdやクラス名をそのまま繰り返さない）。specKindがbounded-context/subdomain/aggregateの場合は、説明の末尾にその種別を表す語（bounded-contextなら「〜を行う境界づけられたコンテキスト」、subdomainなら「〜を担うサブドメイン」、aggregateなら「〜を守る集約」）を含め、読んだだけでこのSpecがDDDのどの構成要素かがわかるようにしてください（usecaseの場合はこの種別語を付けない）。識別子部分はspecKindに応じて設定する: usecaseの場合はcontent.name.operationNameと同じ値、aggregateの場合はcontent.aggregateRoot.nameと同じ値、bounded-context/subdomainの場合はdocumentIdをそのまま使う（識別子は既に別の構造化フィールドが正であり、ここでは表示のためだけに引用する。実装と乖離しても他のフィールドのように機械的ドリフト検知の対象にならないため、識別子以外の実装レベルの詳細をここに書き込まない）。 |
| `{{summary.items[1]}}` | 論点ごとに列挙する（1〜2項目が目安）。この文脈/業務領域/集約/ユースケースが何かを1〜2文で（ドメイン語彙のみ・技術用語禁止）。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{category.classification}}` | 中核=core / 補完=supporting / 一般=generic。競争優位を生むか・既製品があるかで判定。見出しにはcore→中核、supporting→補完、generic→一般の日本語ラベルが使われる。 |
| `{{category.rationale[1]}}` | 根拠を独立した論点ごとに列挙する。そのカテゴリーである根拠（差別化の有無）。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{members.items[1]}}` | この業務領域に属するusecaseのidを列挙。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{implementationGuidance.items[1]}}` | 実装方針を論点ごとに列挙する。実装方針を1〜2文で。中核=ドメインモデルで厚く/一般=既製ライブラリを薄く包む/補完=薄いトランザクションスクリプト。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{externalSolution.text}}` | 採用する既製ライブラリ/サービス名と、それが @stack のどの能力に当たるか。中核/補完なら不要。（任意ブロック：一般カテゴリーの業務領域でなければexternalSolutionブロック自体を省略してよい） |
| `{{domainServices.items[1].name}}` | 業務サービス名。例: パステンプレート解決 / 整形描画（ドメイン語彙で、他の集約に属さない業務ロジックであることが分かる名前にする）（任意ブロック：複数集約に跨る/集約に収まらないステートレスな業務ロジックが無ければdomainServicesブロック自体を省略してよい） |
| `{{domainServices.items[1].responsibility}}` | 何を計算/判定するか・どの集約に跨るか・入力→出力（何を受け何を返すか）を1文で。実装手順は書かない。 |
| `{{domainServiceScenarios.background}}` | 複数シナリオ共通の前提。無ければ空文字。（任意ブロック：domainServicesが無ければdomainServiceScenariosブロック自体を省略してよい） |
| `{{domainServiceScenarios.scenarios[1].name}}` | シナリオ名（概要）。 |
| `{{domainServiceScenarios.scenarios[1].category}}` | 分類: 正常系 / 異常系 / 境界値。 |
| `{{domainServiceScenarios.scenarios[1].viewpoint}}` | 観点: 何を計算/判定するか＋検証の狙い。 |
| `{{domainServiceScenarios.scenarios[1].gherkin}}` | Given/When/Then。ドメイン語彙で書き、実装詳細は書かない。 |
| `{{domainServiceScenarios.scenarios[1].covers}}` | 対応するdomainServicesの項目への参照。 |

---

# {{title.title}}

---

## 概要

- {{summary.items[1]}}

---

## サブドメイン分類

### 分類

{{category.classification}}

### 根拠

- {{category.rationale[1]}}

---

## 業務ユースケース一覧

- {{members.items[1]}}

---

## 詳細設計ガイド

- {{implementationGuidance.items[1]}}

---

## 外部解決策

{{externalSolution.text}}

---

## ドメインサービス

| 業務サービス | 責務 |
|---|---|
| {{domainServices.items[1].name}} | {{domainServices.items[1].responsibility}} |

---

## 業務サービスシナリオ

### 背景

{{domainServiceScenarios.background}}

### {{domainServiceScenarios.scenarios[1].name}}

| 分類 | 観点 |
|---|---|
| {{domainServiceScenarios.scenarios[1].category}} | {{domainServiceScenarios.scenarios[1].viewpoint}} |

```gherkin
{{domainServiceScenarios.scenarios[1].gherkin}}
```
