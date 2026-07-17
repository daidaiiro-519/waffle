# 開発フローのフェーズ遷移を機械的に判定するサブドメイン：sd-flow-gate

## 概要

- ブレスト→spec→TDD→検証→レビューという開発フローの各フェーズ遷移について、進んでよいか(ready)・まだ足りないか(blocked)・機械的に判別できず人間の判断が要るか(needs_human)を判定し続ける業務領域。sd-reconciliationが「既存の成果物間の構造的整合性」を検知するのに対し、こちらは「プロセスが次フェーズへ進める状態にあるか」というプロセス状態そのものを対象にする。

---

## サブドメイン分類

### 分類

中核

### 根拠

- spec-first+TDDというWaffle自身の開発プロセスに固有の遷移判定であり、spec(acceptanceScenarios)とテストの対応関係という、Waffleの独自ドキュメントモデルを理解した上でしか判定できない。SonarQubeのQuality GateやGitHub branch protection等の既製ツールは、テストの合否は見られてもspec⇄テストという対応関係自体を理解できないため代替できない。

---

## 業務ユースケース一覧

- uc-check-verification-gate

---

## 詳細設計ガイド

- 中核ゆえドメインモデルで厚く実装する。既存sd-reconciliationのcheck-*系usecase（Orchestrator主導・読み取り専用・冪等）と同じ実装パターンを踏襲し、判定ロジックはAIに委ねず自前の決定的コードで書く。テスト実行自体はusecaseの責務外とし、既に生成済みのテスト結果レポートを読むにとどめる。
