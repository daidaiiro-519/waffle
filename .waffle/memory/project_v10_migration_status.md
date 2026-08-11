---
name: project_v10_migration_status
description: DomainSpecSchema v10（操作保証を廃止）への移設状況と、bc-artifact-share を意図的に v8 に留めている理由
metadata:
  type: project
---

2026-08-11、DomainSpecSchema v10 を切り、`operationGuarantees` と `guaranteeScenarios` を廃止した。業務ユースケースは状態を持たないので全称の主張の置き場所を原理的に持てず、書けば必ず集約の不変条件の写しになる、という再定義からの帰結。実測でも80件のうち元の意図（portやrepositoryの抽象表現）で書かれたものは1件も無かった。

**移設の状況**

- bc-waffle: 保証の行き先はすべて移設済み（エラー契約は errors 登録＋受け入れ基準として主張を起こし直し、残りは受け入れ基準と受け入れシナリオへ）。ただし41件がまだ追いついておらず（v8が31件・v9が10件）、`covers` 229件を `satisfies` へ対応づける作業が残っている。v10 まで移せたのは `uc-check-schema-version-drift` と `uc-check-path-is-projection` のみ。
- **bc-artifact-share は意図的に v8 のまま**。理由: 操作保証を廃した再定義がこの文脈へまだ回っておらず、いま追いつかせると30件の保証が行き先を決める前に消える。待っているのは bc-artifact-share 自体の再定義。ユーザーの指示は「アーティファクトシェアは完全に再定義が完了してからがいい」。

**Why:** 版が古いまま放置される状態をユーザーが嫌っている（64件が v8 で滞留していた）。ただし「後で変える」こと自体は必要としている。

**How to apply:** `uc-check-schema-version-drift` は最新でない参照を情報ではなく**違反**として上げる仕様に変えた（実装は未着手）。bc-artifact-share の分は上記の理由がある既知の違反として扱い、他の違反と区別するのはこのメモリで行う。**専用の宣言用スキーマや台帳文書は作らない**——一度作って却下された。
