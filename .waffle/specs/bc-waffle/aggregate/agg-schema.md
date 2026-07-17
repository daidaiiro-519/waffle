# Schema定義の型と不変条件を守る集約：Schema

## 概要

- Document の型定義（Schema）の不変条件を表す集約。Document が機械生成・検証・描画できることを保証する
- バージョンが変わった際の既存Documentの追従はAIが個別に判断して直す（機械的な自動移行の機構はこの集約の対象外・過剰実装と判断し撤去済み）
- 対象は「Document の schemaRef が指しうる型」に限定する: DomainSpecSchema・PresentationSpecSchema・CodingSchema・SkillSchema・KnowledgeSchema・AgentSchema・TemplateSchema。RenderMetaSchema は Document 型定義ではなく派生構造（x-render 部品）を検証する別概念であり、この集約の対象外

---

## 集約ルート

Schema

### 外部参照（ID）

- Document

---

## エンティティ

### Schema（集約ルート）

Document の型定義（構造・描画・記入/読取指示）の一貫性単位

| 属性 | 型 |
|---|---|
| **schemaId**（識別子） | SchemaId |
| version | Version |
| kindProfiles | KindProfile[] |

---

## 値オブジェクト

### SchemaId

| 表す値 | 振る舞い |
|---|---|
| スキーマ名（例: CodingSchema） | 不変。値が等しければ等価。 |

| 属性 | 型 |
|---|---|
| value | string |

### Version

| 表す値 | 振る舞い |
|---|---|
| 単調増加する版識別子（例: v1, v2） | 不変。値が等しければ等価。上げる方向にのみ進む。 |

| 属性 | 型 |
|---|---|
| value | string |

### KindProfile

| 表す値 | 振る舞い |
|---|---|
| kind（specKind/codingKind/skillKind/agentKind/templateKind）1つに対応する、必須 content ブロック集合とその形状。各kindの目的は各schemaファイルのx-prompt-queryに委ね、ここでは重複させない。 | 不変。kind 名＋必須ブロック集合の組で識別される（同じ値なら同じものとして扱う）。Schema の版が変わらない限り不変。各ブロックが持つ x-render 属性は、RenderMetaSchema が形を規定する。 |

| 属性 | 型 |
|---|---|
| name | string |
| requiredBlocks | string[] |

---

## 不変条件

| ルール | 守り方 | 根拠 |
|---|---|---|
| 値フィールドは常に oneOf / anyOf を持たない | schema | - scaffold が骨格を機械生成できるようにする |
| content の各ブロックは additionalProperties を常に閉じる（固定 properties のみ） | schema | - 未知フィールドの混入を防ぎ構造を決定的にする |
| 再帰は常に有界である（無限ネストを許さない） | schema | - 機械走査が停止することを保証する |
| 各ブロックの x-render は常に RenderMetaSchema の閉じた語彙にのみ従う | schema | - 描画がロジックを持たず決定的であることを保つ |
| status の enum は常に遷移順に並び、先頭が初期状態である | schema | - scaffold が初期状態を enum 先頭から一意に決められる |
| 公開済みの版は遡って構造を変えない（後方互換を壊さない） | guard | - 既存 Document が破損しないよう版の進化を安全にする |
| 各 kind の KindProfile は同一版内で不変であり、他 kind のブロックを持たない（discriminator として機能する） | schema | - kind ごとの content 構造の一貫性を保証し、scaffold/validate が kind から構造を一意に決定できるようにする |
| Schema集約が対象とするのは Document の schemaRef が指しうる型のみ（派生構造を検証する schema は対象外） | schema | - 一貫性境界を「schemaRef の解決先」に閉じ、無関係な検証用 schema を集約に含めない |
| Schemaファイル自体の物理的な整形は、常にPython標準ライブラリの json.dumps(schema, indent=2, ensure_ascii=False) + 改行 の出力と完全一致する | schema | - 整形ルールを一意に固定することで、部分編集・ブロック追加・リネーム等の機械的な差分適用が、既存の無関係な箇所を一切変更せずに行えるようにする<br>- 複数の書式が混在すると、機械編集のたびにどの書式に合わせるべきかが曖昧になり、フォーマット破壊のリスクが生まれる |

---

## 不変条件シナリオ

### 値フィールドに oneOf を持てない

| 分類 | 観点 |
|---|---|
| 異常系 | 不変条件: scaffoldability（値フィールドは oneOf/anyOf を持たない） |

```gherkin
Scenario: 値フィールドに oneOf を持てない
  Given 値フィールドに oneOf を含む Schema
  When scaffoldability を検証する
  Then scaffold 不能として拒否される
```

### 公開済みの版は後方互換を壊さない

| 分類 | 観点 |
|---|---|
| 異常系 | 不変条件: 公開済みの版は遡って構造を変えない |

```gherkin
Scenario: 公開済みの版は後方互換を壊さない
  Given 既にDocumentが参照している既存のSchema版
  When 既存ブロックに必須フィールドを追加しようとする
  Then 後方互換を壊す変更として拒否される
```

### x-render は閉じた語彙にのみ従う

| 分類 | 観点 |
|---|---|
| 異常系 | 不変条件: 各ブロックの x-render は常に RenderMetaSchema の閉じた語彙にのみ従う |

```gherkin
Scenario: x-render は閉じた語彙にのみ従う
  Given 未知の部品種別、または必須属性が欠けた x-render 宣言を持つ Schema
  When x-render の適合を検証する
  Then 不適合として拒否される
```

### Schemaファイルの物理整形は json.dumps(indent=2) と完全一致する

| 分類 | 観点 |
|---|---|
| 異常系 | 不変条件: Schemaファイル自体の物理的な整形は常に json.dumps(schema, indent=2, ensure_ascii=False) の出力と完全一致する |

```gherkin
Scenario: Schemaファイルの物理整形は一意である
  Given 独自の整形（コンパクト配列・キー長揃え等）が施されたSchemaファイル
  When 標準の json.dumps(indent=2, ensure_ascii=False) で再シリアライズした結果と比較する
  Then バイト単位で一致しない場合は不適合として検出される
```
