---
name: hooks-are-spec-managed-without-exception
description: フックは判断であれ配線であれ、例外なく仕様として管理する。自前で振る舞う型を抜け穴にしない
metadata:
  node_type: memory
  type: feedback
---

フックは**例外なく仕様として管理される**。「判断を持つから仕様が要る／配線だから要らない」という線引きで免除しない。

**Why:** ユーザーの指摘「これ判断だろうが何だろうが仕様として正しく管理されるべきだと思いますので」。HookSchema/v1 は `usecase-delegate`（判定を usecase へ委ねる）と `self-contained`（`behavior` の散文だけを持つ）の2種別を持つが、実測すると15件中8件が自前型で、うち6件は**受け入れ基準もシナリオも持たないまま判断している**（protect-document-json / protect-raw-json-access / enforce-spec-first / require-handoff-before-implementation / require-svg-render-check / notify-validate-render-after-write）。散文しか根拠が無いので、鳴っている警告が正しいのか誤検知なのかを誰も判定できない。`self-contained` は事実上、判断を仕様の外へ逃がす抜け穴として働いていた。

種別が生えた経緯も残す。`f49f86b`（2026-07-19・別セッション）で「実際に3件がusecase委譲型、4件が判定ロジック完結型**だった**」という実測を根拠に discriminator を採用している。方針に照らせばその4件は違反として判定されるべき対象であり、実測を根拠に方針を決めたことで違反が仕様になった（[[knowledge-cand-policy-is-ssot-measurement-is-judged]] と同じ取り違え）。当時4件だった自前型は今日8件まで増えている——抜け穴は広がる方向に働く。

**決定（ユーザー承認済み）:** `self-contained` を廃止し、HookSchema/v2 では `usecaseRef` を必須にする。種別が1つになるので `hookKind` discriminator 自体も廃止する——1種しかないものを判別する鍵は儀式にしかならない。ディスパッチャは `usecaseRef` を配列にして束ねている委譲先を全部並べる（「判断を持たない配線」という例外を作らない。複数の判断を順に駆動している、と書けば正確）。移行順序は **委譲先ユースケースの起草 → v2 → フック文書の運搬**。先に v2 を切ると、委譲先が未起草のフックが行き場を失う。

**How to apply:** 新しいフックを作るときは、判断の有無にかかわらず先に仕様を起こす。既存の自前型は、判断を持つものからユースケースを起こして委譲型へ移す。配線だけのもの（ディスパッチャ）も仕様を持たせる——「判断が無い」ことは仕様が不要な理由にならず、仕様に書くべき事実そのもの。あわせて、Handoff 廃止に伴い `require-handoff-before-implementation` は削除の対象。関連: [[feedback_udd_implementation_before_spec]] [[feedback_hook_symlink_bootstrap_order]]
