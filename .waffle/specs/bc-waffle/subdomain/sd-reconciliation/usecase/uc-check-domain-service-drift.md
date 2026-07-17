# 業務サービス名と実装ファイルの対応を検証する：CheckDomainServiceDrift

## 概要

- bounded-context specが宣言する業務サービスのgroup（実装ファイル単位）が、実際に対応するファイルとして実在するかを機械的に検証する。1業務サービス＝1ファイルという規約を強制せず、複数サービスが同じgroupを共有し同じファイルに同居することを許容した上で、宣言と実装の対応関係のドリフトを検出する。

---

## 存在意義

- 業務サービスは値オブジェクト・集約と異なり、宣言された名前から実装ファイルパスを機械的に導出できない（1サービス1ファイルという規約が無く、関連する複数サービスが同じファイルに同居することがある）。宣言（bounded-context spec）と実装（domain/services配下のファイル）が乖離しても、他のusecase/aggregateクラスドリフト検知と違い、これを検知する仕組みが無かった。TDDが担保するのは振る舞いの正しさであり、宣言と実装の対応関係という別の関心事は別途機械的に検証する必要がある。

---

## 主アクターと意図

### 主アクター

Orchestrator（HarnessAgent）

### 意図

業務サービスのgroupが実際の実装ファイルと対応しているかを確認したい

---

## 事前条件

- Document集約の実インスタンス群を走査する対象ディレクトリ（documents_root）が与えられている
- 業務サービス実装ファイルの配置ルートディレクトリ（src_root）が与えられている

---

## 基本フロー

```mermaid
sequenceDiagram
    Orchestrator->>DomainServiceFileTree: documents_root/src_rootを指定してドリフト検査を依頼する
    DomainServiceFileTree->>DomainServiceFileTree: documents_root配下のbounded-context document(specKind=bounded-context)を走査し、各documentのcontent.domainServices.itemsが宣言するgroupを集める
    DomainServiceFileTree->>DomainServiceFileTree: 各groupに対応する実装ファイル（src_root配下）が実在するかを確認する
    DomainServiceFileTree-->>Orchestrator: missing_implementation_fileのオブジェクト配列を返す
```

---

## 事後条件

- 返り値はmissing_implementation_file（groupから導出したファイルパスが実在しない業務サービスの組）フィールドを持つ
- ファイルパスの導出は、groupをsnake_caseに変換し、src_root配下に{group}.pyとして配置されている前提で行う
- 同じgroupを持つ複数の業務サービスは、1回のファイル存在確認にまとめられる（同じファイルを重複してチェックしない）
- ファイルの実在確認のみを行い、ファイル内の具体的な関数・クラス定義までは検証しない（内容の正しさはTDDが別途担保する）
- missing_implementation_fileが空配列であれば、全業務サービスのgroupと実装ファイルが一致している（正常系）

---

## 受け入れ基準

- When 業務サービスのgroupから導出したファイルパスが実在しないとき、システムはその組をmissing_implementation_fileに含める shall。
- While 全業務サービスのgroupと実装ファイルが一致しているとき、システムはmissing_implementation_fileを空配列で返す shall。
- While 複数の業務サービスが同じgroupを共有しているとき、システムは対応するファイルの存在確認を1回にまとめる shall（重複報告しない）。
- If 対象のdocuments_rootまたはsrc_rootが存在しないとき、システムはINVALID_PATHエラーを返す shall。

---

## 操作保証

- When 対象のdocuments_rootまたはsrc_rootが存在しないとき、システムは INVALID_PATH エラーを返す shall（対象を特定し取得する解決プロセス自体の契約であり、複数のusecaseに共通する）。

---

## エラー

| コード | 条件 |
|---|---|
| `INVALID_PATH` | - documents_rootまたはsrc_rootが存在しない、またはパストラバーサルを含む |

---

## 受け入れシナリオ

### 全業務サービスのgroupと実装ファイルが一致するとき差分なしと判定する

| 分類 | 観点 |
|---|---|
| 正常系 | 整合：全groupが対応する実装ファイルと一致するとき正常系（空配列） |

```gherkin
Scenario: 全業務サービスのgroupと実装ファイルが一致するとき差分なしと判定する
  Given 全業務サービスのgroupが、対応する実装ファイルと一致するspecツリー
  When ドリフト検査を実行する
  Then missing_implementation_fileが空配列で返る
```

### 実装ファイルが存在しない業務サービスを検出する

| 分類 | 観点 |
|---|---|
| 異常系 | ドリフト：groupから導出したファイルが実在しない |

```gherkin
Scenario: 実装ファイルが存在しない業務サービスを検出する
  Given groupから導出したファイルパスに対応する実装ファイルが実在しない業務サービス宣言
  When ドリフト検査を実行する
  Then missing_implementation_fileにその組が含まれる
```

### 同じgroupを共有する複数サービスは1回のファイル確認にまとめられる

| 分類 | 観点 |
|---|---|
| 境界値 | 重複排除：同一groupの複数サービスをそれぞれ個別に報告しない |

```gherkin
Scenario: 同じgroupを共有する複数サービスは1回のファイル確認にまとめられる
  Given 同じgroupを宣言する2件以上の業務サービス（対応する実装ファイルは実在しない）
  When ドリフト検査を実行する
  Then missing_implementation_fileには重複を除いた1件だけが含まれる
```

---

## 操作保証シナリオ

### 存在しないdocuments_rootはINVALID_PATH

| 分類 | 観点 |
|---|---|
| 異常系 | エラー：走査起点の不在 |

```gherkin
Scenario: 存在しないdocuments_rootはINVALID_PATH
  When 存在しないdocuments_rootでドリフト検査を実行する
  Then INVALID_PATHエラーが返る
```
