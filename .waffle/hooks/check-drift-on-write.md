---
id: "check-drift-on-write"
type: "usecase-delegate"
title: "check-drift-on-write"
description: "usecase実装・アダプター実装・対応するtestファイルが書き込まれた直後に、既存の各種driftチェックusecaseを自動実行し、検出があったときだけ結果をモデルへ返す。加えて、突き合わせ先そのものが見つからなかった場合もその旨を返す（driftが無いことと、そもそも突き合わせていないことを区別するため）。検査した結果クリーンだったときだけ沈黙する。新しいdrift検知ロジックはこのスクリプト自身は一切持たない。"
schemaRef: "HookSchema/v1"
---

# check-drift-on-write

## 目的

usecase実装・アダプター実装・対応するtestファイルが書き込まれた直後に、既存の各種driftチェックusecaseを自動実行し、検出があったときだけ結果をモデルへ返す。加えて、突き合わせ先そのものが見つからなかった場合もその旨を返す（driftが無いことと、そもそも突き合わせていないことを区別するため）。検査した結果クリーンだったときだけ沈黙する。新しいdrift検知ロジックはこのスクリプト自身は一切持たない。

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
- 検査した結果クリーンだった場合のみ沈黙する（必要な情報だけを返す方針を維持する）
- 突き合わせ先が見つからなかった場合は沈黙しない。「検査して綺麗だった」と「そもそも検査していない」が同じ見た目になると、対応が取れていない状態が綺麗な状態として通過する（2026-08-01に実際に発生。artifact-shareの132シナリオが誰とも突き合わされていない状態を、無出力を根拠にdrift無しと判断した）
