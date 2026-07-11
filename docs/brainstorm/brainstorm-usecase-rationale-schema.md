# ブレスト: usecaseに「なぜ必要か」を書く場所がスキーマにない問題

**作成日:** 2026-07-10
**経緯:** reconcileサブドメイン（`sd-reconciliation`）の棚卸しレビュー中、
`uc-check-scenario-drift`の`orphaned_in_tests`フィールドについて、実装・テストの
挙動としては「specに宣言のないテスト関数を検出する」だが、その**狙い**は
「TDDの手順（spec→シナリオ→テスト→実装）を逆走した抜け駆け実装の検知」という
積極的な意味を持つことが、対話の中で明らかになった。ところが仕様書
（`uc-check-scenario-drift.json`の`summary`/`actorIntent`）にはこの狙いが
一切書かれておらず、「メカニズムは書いてあるが、なぜそれが重要かは書かれていない」
という漏れが発覚した。

調査の結果、これは当該usecase固有の書き漏れではなく、**スキーマ構造そのものの
非対称**であることが判明した。

---

## 発見: SubdomainとUsecaseの非対称

`DomainSpecSchema/v2`の`$defs`を比較すると:

- **`SubdomainCategoryBlock`**（subdomain階層）: `classification`
  （core/supporting/generic）と**`rationale`（必須）**のペアを持つ。
  「なぜこの分類なのか」を書かせる場所が構造的に用意されている
- **`UsecaseContent`**（usecase階層）: `actorIntent`ブロックは
  「誰が・何を達成したいか」（`actor`/`intent`）はあるが、
  **「なぜこのusecaseが必要か（どんなリスクを防いでいるか）」を書く場所が
  存在しない**

subdomainには「なぜそのカテゴリーか」を必ず説明させる構造があるのに、
usecase（UDDの核となる単位）には「なぜこのusecaseが必要か」を書く場所が
仕様上どこにも用意されていない、という非対称。UDD
（Usecase-Driven-Development）を名乗る以上、この非対称は看過できない可能性がある。

今回の`orphaned_in_tests`の例はこの穴が顕在化した一例に過ぎず、
**他のusecaseでも同種の「メカニズムは書いてあるが、なぜそれが重要かは
書かれていない」という漏れが潜んでいる可能性がある**（reconcileサブドメイン
全体・あるいは他のsubdomainのusecaseも含めて未調査）。

---

## 論点 1: usecase階層に「なぜ必要か」を書く必須ブロックを追加すべきか

**AI初期見解:** 追加する方向が妥当。`SubdomainCategoryBlock`と対称的な位置づけで、
`ActorIntentBlock`に`rationale`相当のフィールドを追加する（または新規ブロックを
起こす）ことで、「誰が・何を（actor/intent）」に加えて「なぜこの操作が
業務上重要か」を必須で書かせる。

**検討すべき点:**
- 既存の`ActorIntentBlock`に`rationale`フィールドを追加するか、
  それとも独立した新規ブロック（例: `UsecaseRationaleBlock`）にするか
- 既存の全usecase document（4つのreconcile系usecase含む）への遡及的な
  追記が必要になる（スキーマの必須フィールド追加は破壊的変更）
- `summary`ブロックとの役割分担（`summary`は「何をするか」の要約、
  新フィールドは「なぜ必要か」の理由、と棲み分けるべきか）

**未検討:** ユーザーとの合意形成はこれから

---

## 論点 2: postconditionsの個別フィールドにも意図を書く場所が必要か

**背景:** `uc-check-scenario-drift`の場合、usecase全体の意図（論点1）とは別に、
**個別の返り値フィールド単位**で異なる意図を持っていた
（`missing_in_tests`=TDD順走の確認、`orphaned_in_tests`=TDD逆走の検知、
という2つの異なる狙いが1つのusecaseに同居している）。論点1の解決
（usecase単位のrationale追加）だけでは、この「フィールド単位の意図の違い」
までは表現しきれない可能性がある。

**AI初期見解:** 論点1がusecase単位の粗い粒度だとすれば、論点2は
`postconditions.items`の各要素に対して意図を注記する、より細かい粒度の話。
今の`postconditions`は文章の箇条書き（`items: string[]`）であり、
フィールドごとの構造化された意図を持たせるには、
`items`をオブジェクト配列（`{field, description, rationale}`等）に
拡張する必要があるかもしれない。ただしこれは`postconditions`という
既存ブロックの構造を変える、より大きな変更になる。

**検討すべき点:**
- 論点1（usecase単位のrationale）だけで実用上十分か、
  それとも論点2（フィールド単位の意図）まで踏み込む必要があるケースが
  実際にどれだけあるか（`uc-check-scenario-drift`以外の実例調査が先に要る）
- 踏み込む場合、`postconditions`ブロックの構造変更は影響範囲が広い
  （全usecase documentの`postconditions.items`がstring配列前提で書かれている）

**未検討:** ユーザーとの合意形成はこれから。論点1が決着してから
着手するかどうかも含めて要相談

---

## 決着: 論点1（実装済み・2026-07-11）

**決定:** 独立ブロック`UsecaseRationaleBlock`（`blockType: "UsecaseRationale"`,
`title: "存在意義"`, `rationale: string`）を`ActorIntentBlock`の直後
（`x-render-order: 3`）に追加し、`UsecaseContent`の必須プロパティとする。
既存ブロックへのフィールド追加ではなく独立ブロックにしたのは、
「何を(actorIntent)」と「なぜ(rationale)」の境界が同一ブロック内で
混在すると解釈に誤解が生まれるため。全usecaseに対して必須（optionalでの
段階導入はしない）。

**実施内容:**
- `DomainSpecSchema/v3`を新設（`v2.json`は変更せず履歴として残す）
- `bc-waffle`配下の全18文書（bc 1・aggregate 2・subdomain 5・usecase 10）の
  `schemaRef`を`v2`→`v3`に直接Edit（スキーマ改版は破壊的変更のため
  `scaffold fill`では反映できず、CLAUDE.mdの運用ルール
  「schemaに新規必須トップレベルキー追加時のみEdit/Writeを許容する」に
  従い直接編集した）
- `check-schema-version-drift`を実行し、10 usecase文書に
  `content.usecaseRationale.rationale`の不足を機械検知（dogfooding成功）
- 検知された10件全てに、各usecaseの実際の存在意義を執筆して直接Edit
- 全18文書を`validate`で再検証しVALIDATED、`pytest`188件green、
  10 usecase文書を`render`して.md成果物に反映、を確認

**次点で見送ったこと:** 既存の`orphaned_value_objects`等の10フィールドを
含む`postconditions`構造自体（論点2）は今回変更していない。論点2は
別途合意形成してから着手する。

## 決着: 論点2（見送り・2026-07-11）

**決定:** `postconditions.items`を`{field, description, rationale}`のような
オブジェクト配列に構造化する提案は、YAGNIとして見送る。

**理由（`tech-lead-advisor`の`architecture-evidence-based-scope`知識に基づく
経済的判断）:** 判断基準は「その抽象化を必要とする具体的な実例が、既に1つ以上
観測されているか」。唯一の候補だった`uc-check-scenario-drift`
（`missing_in_tests`/`orphaned_in_tests`の意図の違い）は、論点1の対応
（`usecaseRationale`）で書き分けることで実際に解決済みであり、実例は
**ゼロ**の状態。実例が無い段階で構造を確定させると、推測が当たっていた
としても「オプション性のコスト（後でより良い情報を得てから決め直す選択権を
失う）」と「NPVコスト（構築コストは今日払うが便益は実現しない）」を
先払いすることになる。また`uc-check-spec-integrity`の`postconditions`には
特定の1フィールドに対応しない横断的な注記も含まれ、無理に`{field, ...}`
構造へ押し込めない実態もある。

**副次的な発見（このブレストの過程で見つけて修正済み）:** 議論の途中で
「Gherkinの`gherkin`フィールドも1文字列にまとまっているのはおかしいのでは」
という関連指摘があり、検討する過程で`PresentationSpecSchema`と
`PlatformSpec`のx-prompt-query/writeに、既に完全撤去された`.feature`生成
（`07a2820`）を前提にした古い記述が残っていたことを発見した。
`DomainSpecSchema`は`242f47a`で「AIネイティブテスト書き起こし前提」に
修正済みだったが、この修正が兄弟schemaに伝播していなかった。両schemaを
`DomainSpecSchema`の現行表現に揃えて修正した（コミット参照:
`0c378f1 PresentationSpecSchema/PlatformSpecから.feature前提の記述を除去`）。
`gherkin`フィールド自体の構造化（Given/When/Then分割）は、Gherkinが
JSONではなく外部DSL自体の構造を持つこと・And/But/Table/Scenario Outline等
JSON化コストが高いこと・具体的な不具合実例が無いこと、から同じくYAGNIとして
見送った。

## 次のアクション

1. ~~論点1について、ユーザーと合意形成する~~ → 完了（2026-07-11実装済み）
2. ~~論点2（postconditions個別フィールドへの意図記述）について、
   ユーザーと合意形成する~~ → 完了（2026-07-11、YAGNIとして見送り決定）
3. 他のsubdomain/usecaseにも同種の「メカニズムは書いてあるが意図が
   書かれていない」漏れがないか、横断的に棚卸しする（本ブレストの発端は
   reconcileサブドメインのレビューだったが、対象はwaffle全体のusecaseに
   広げるべきかもしれない）——ただし論点1の実装により、今後新規作成される
   usecaseはスキーマレベルで`usecaseRationale`が必須になったため、
   この棚卸しの緊急度はやや下がった。本論点も同じ理由（実例が観測されて
   いない）でYAGNIとして見送ってよい可能性が高い
