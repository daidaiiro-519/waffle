# handoff-agg-document

## 引き継ぎ元spec

agg-document

---

## 設計観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| ddd-advisor | Document集約のEntityは薄い受動的Entityにする | agg-document.jsonが宣言する不変条件のうち複数は静的構造制約でありJSON Schema自体が担保している。手続き的な不変条件（status遷移・SUPERSEDED終端・schemaRef必須等）は、既にlifecycle_guard.py・schema_ref_guard.pyという純粋関数のドメインサービスとして実装済みのため、Entity自身に複雑な業務ロジックメソッドを持たせる必要が無い。値オブジェクトの不変性・値による等価性という宣言された構造のみを表現すればよい。 |

---

## 実装観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| ddd-advisor | check-aggregate-class-driftの検証対象として実装する | Entityはビジネスロジックの実行主体としてではなく、agg-document.jsonのEntities/ValueObjectsブロックとの構造的な対応関係（クラス名・フィールド名の一致）を、既存のドリフト検知usecaseが機械的に検証する対象として実装する。 |
