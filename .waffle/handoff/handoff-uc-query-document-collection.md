## 概要

複数Documentを横断してパターン検索・属性絞り込みを行うusecaseの設計判断を実装へ引き継ぐ。

---

# 複数Documentを横断してパターン検索・属性絞り込みする実装引き継ぎ：handoff-uc-query-document-collection

## 引き継ぎ元spec

uc-query-document-collection

---

## 完成イメージ

---

## 設計観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| ddd-advisor | grep_documents/filter_documentsはQueryDocumentから独立したusecaseに切り出す | 既存16操作はすべて「単一document.json＝集約境界の内部を覗く点操作」であり、事前条件（対象パス1つ）も出力形状も統一されている。grep_documents/filter_documentsはディレクトリ配下＝複数document（複数集約）を横断する走査であり、事前条件（対象がdirectory）も出力形状（path単位の集約結果）も異質。domain-model原則の「単一集約に閉じない、複数集約にまたがる計算ロジックは業務サービスとして切り出す」に該当するため、QueryDocumentCollectionという別usecaseとして切り出した。 |
| ddd-advisor | 都度フルスキャン・永続索引なしの設計合意をusecase文書に明記する | 「正典はdocument.json・永続インデックス禁止（LoomDB不採用）」という既存の設計合意と矛盾しないが、全document再帰スキャンを毎回行う実装は将来的に「遅いから索引が欲しい」という圧力を生みやすい。合意の風化を防ぐため、usecaseRationale・operationGuaranteesに都度フルスキャンであることを明記済み。 |
| tech-lead-advisor | 評価時点ではクラス分割は時期尚早と判定されたが、実例2件（grep_documents/filter_documents）を理由に今回は切り出しを決定した | tech-lead-advisorはevidence-based-scope原則（実例1件からの一般化はアンチパターン）に基づき、当初は独立usecase化を「横断操作がさらに増えた実例が観測されてから」と保留判断した。しかしgrep_documents/filter_documentsという同一形状の2実例が既に存在する状態であり、この2件自体がevidence-based-scopeの言う複数実例の閾値を満たすとユーザーが判断し、spec作成の時点で切り出すことを決定した。実装時にこの判断の妥当性が変わる場合は、まずspec側の見直しから行うこと（実装から先に進めない）。 |

---

## 実装観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | ディレクトリ走査・ファイルI/OはDocumentRepositoryポート経由に留める | 既存のindex_scan_dir（_index_scan_dir, query_document.py:167-184）と同型のパターン（DocumentRepository.list_jsonでディレクトリ一覧→loadで個別読込→application層で集計）に倣う。正規表現マッチングや絞り込みロジックはapplication層の純粋な調整処理として実装し、ファイルI/O自体をapplication層に直書きしない。 |
| tech-lead-advisor | grep_documentsの再帰走査ロジックは純粋ヘルパとして分離する | 既存の_find_all（query_document.py:227-238）と同様に、run本体を肥大化させないよう、再帰走査ロジックをファイル末尾の純粋ヘルパ関数として実装すること。 |

---

## 既知の制約・トレードオフ

- 永続インデックスは持たない（都度フルスキャン）。grep_documents/filter_documentsはディレクトリ配下の全documentを毎回読み込んで走査する。コーパス規模が数百件程度である現状では許容範囲だが、実測でボトルネックが判明した場合のみ索引化を再検討する（先回りした索引設計はしない）。
