# check-drift-on-write

## 目的

usecase実装・アダプター実装・対応するtestファイルが書き込まれた直後に、既存の各種driftチェックusecaseを自動実行し、検出があったときだけ結果をモデルへ返す。クリーンなときは沈黙する。新しいdrift検知ロジックはこのスクリプト自身は一切持たない。

---

## いつ働くか

usecase実装・エンティティ・ドメインサービス・対応テストファイルへのEdit/Write直後、およびBash経由でdocument.jsonがscaffold fillされた直後

---

## 委譲先usecase

check-usecase-class-drift / check-operation-drift / check-aggregate-class-drift / check-domain-service-drift / check-scenario-drift（書き込まれたパスパターンに応じて自動選択）

---

## スクリプト実体

.waffle/hooks/check-drift-on-write.py

---

## ガードレール

- 新しいdrift検知ロジックをこのHookスクリプトに持ち込まない。判定ロジックの追加・変更は各usecase側で行う
- クリーンな場合は沈黙する（必要な情報だけを返す方針を維持する）
