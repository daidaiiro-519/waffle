# ブレスト（記録）: 敵対的測定（adversarial measurement）を advisor 批評の汎用エッセンスにする

status: 全論点決着（2026-07-30）。UIモックは【決定済み標準】／spec・codingへの一般化は【knowledge化完了・部分実例】／独立性の本物性・層の問題は【決着・追加着手不要】

## 汎用knowledgeへの昇格（2026-07-19）
evidence-based-scope（実例2件以上で抽象化してよい）を、design-share（デザイン生成）と
spec-authoring（Orchestratorの既存運用: check-spec-integrity/check-scenario-drift＋advisor並列批評＋
knowledge-cultivator）という独立した2実例で満たしたため、`.waffle/documents/knowledge/self-improving-generation-cycle.json`
として汎用knowledge（skillRef無し・canonical配置のみ）に昇格した。coding/implementation領域は
まだ実例として確定していない（試験観測のみ、provenance.caveatsに明記）。

## 決定（2026-07-19・UIモック）
- **最良のUIモックは〈生成→敵対的測定→修正→学びの還元〉サイクルで作る。これが design-share の標準で、スキルの中で完結する。**
- **敵対的測定は UX 専門知識に基づく**。design-share は ux-advisor 由来のUX知識（references/knowledge/、特に frontend-design-principles）を同梱しているので、**外部のux-advisor Skillを呼ばず、その同梱UX知識を土台に自前で測定する**（＝自己完結「実行時に他Skillを呼ばない」と両立）。
- 保つべきは**独立性のみ**（生成者は自己採点できない＝本session実証）。独立性は“別Skill”でなく**“別pass・敵対フレーミング（忖度なし/出荷基準/refute）・実物と数値evidenceの読解”**で担保する（必要なら同梱UX知識を読ませたサブエージェントを敵対レビュアに）。
- → SKILL.md guardrails に「UIモックの標準サイクル」として明記済み。**Orchestrator層/CLAUDE.md Skillフォローアップへの型化は不要**（スキル内完結のため）。


きっかけ: 2026-07-19、design-share の商用モック化で回した〈実証→敵対的測定→知識/資産へ還元〉サイクルが効いた。
特に「独立した ux-advisor が成果物を"実測"して忖度なく欠陥を挙げる」測定が、生成者（Claude 本体）の自己採点バイアスを補正した
（私は sento モックを"製品仕様"と誤って自己申告 → 外部測定が"一歩手前"と訂正 / Laneview のチャート歪みも外部が検出）。
このエッセンスは spec/coding の advisor 批評にも効くはず、という着想を記録する。

---

## 抽出したエッセンス（なぜ今回の測定が効いたか）

1. **独立性**: 批評者は生成者と別人格。生成者の合理化・自己弁護を共有せず、"意図"でなく"実物"を読む。
2. **明示的な物差し（bar / rubric）**: 「商用級か」「核の価値は出ているか」「ありきたりでないか」等、**明示基準で測る**。曖昧な「良い？」ではない。
3. **敵対的スタンス**: 「忖度なし」「出荷基準で厳しく」「欠陥を具体箇所・数値で名指し」「称賛で終わらせない」。default は refute 寄り。
4. **実物＋証拠に接地**: コードを読む／コントラストを計算する／パネル間整合を確認する。印象でなく evidence（数値・箇所名）。
5. **判定＋順位付き修正**: verdict（出せる／一歩手前／コンプ）＋ must-fix / should-fix をランク付けで返す。
6. **fix → re-measure ループ**: 指摘が具体修正を駆動し、必要なら再測定で"閉じたか"を確認する。
7. **finding の分類**: プレースホルダー性（思想の欠陥）vs 仕上げバグ（質が違う）／概念 vs 実装。→ 手戻りの"深さ"が分かる。
8. **前提: 生成者は自己採点できない**。だから外部測定は"任意"でなく**構造的に必要**（今回それが実証された）。

---

## spec / coding への応用可能性

- **Spec**: 著者の自己レビューでなく、独立レビュアが spec を明示 bar で測る（完全性・テスト可能性・境界の正しさ・シナリオ網羅）。著者が無意識に合理化するギャップを捕まえる。
- **Coding**: 「正しそう」で終えず、**失敗シナリオを見つけにいく（refute する）**敵対的レビュー。明示基準で測り、具体的な failure_scenario（入力→誤った出力/クラッシュ）を要求する（ReportFindings 的）。
- **共通の依頼形**: advisor に「批評して」ではなく「**[明示 bar] に照らして敵対的に測定し、実物を読んで、verdict ＋ 順位付き fix ＋ finding 分類を返せ**」と頼む。

---

## 既存 advisor ワークフローとの関係・差分

- CLAUDE.md は既に「advisor を並列 dispatch → template-skill-critique.md（各意見→統合→合意→次アクション）で統合」を持つ。今回もこの器を使った。
- **追加したいエッセンス**（今の器に無い or 弱い部分）:
  (a) 明示的な bar/rubric で"測定"する（意見収集でなく判定）
  (b) 敵対的スタンスを依頼文に明示（忖度なし・出荷基準・欠陥名指し・refute 既定）
  (c) 実物＋数値 evidence に接地させる（コード/計算を読ませる）
  (d) fix → re-measure で"閉じたか"まで回す
  (e) finding を 概念/仕上げ・must/should に分類させる
  (f) 「生成者の自己採点を信用しない」を前提として明文化
- template-skill-critique に"測定モード"（verdict＋ranked-fix＋finding分類＋re-measure）を足せるか、は要検討。

---

## 論点・未解決（未検討）

- 全 advisor 批評を"測定"化すべきか、それとも**探索的批評（発散）と測定（収束・判定）を使い分ける**か。今回のように後半は測定が向く。
- **bar は誰が定義する**？（依頼者が明示 / advisor が提案して合意 / schema に埋める）
- **re-measure のコスト**。毎回 2 周は重い。どこまで回すか（must-fix が"仕上げバグ"に収束したら 1 周で止める等の停止条件）。
- **独立性はどこまで本物か（決着・2026-07-30）**: 敵対的検証の本質は「批評者が生成者と別人格かどうか」ではなく、「一度出した答えを鵜呑みにせず、別観点からの批評を踏まえて再検証するループを回すこと」。この定義は`self-improving-generation-cycle`の既存原則（「fixした本人の自己申告を、検証なしに確定にしない」「fix後は必ず再測定してから確定する」）にすでに明記されており、別途の追記・新規knowledgeは不要と結論した。
- **層の問題（決着・2026-07-30）**: 当初「design-shareは自己完結、spec-authoringはOrchestrator層」という2種類のSkillがあるかのように問いを立てていたが、これは前提が誤りだった。全てのSkillは常に単一の環境非依存な自己完結実装であり（design-share・spec-authoringも例外ではない）、複数のSkillを組み合わせて使うかどうかはSkill自体の設計選択ではなく、常にOrchestrator側の組み合わせ判断（skill-router・委譲パターン）に属する。これは新しい原則ではなく、`skills-creator`の既存の恒久ガードレール（「Skill自体は単一の環境非依存な実装のままにし、統合はSkillの外側（呼び出し側・Orchestrator側）に置く」＝composition-rootの原則）と同一のものだった。よって「層分けの一般化」として新規に何かを作る必要は無い。今後の実務上の論点は、一般化の要否ではなく「そのSkillが実際にこの自己完結構造になっているか」という個別Skillの設計監査に移る。

---

## 次に検討すること（メモ）

- template-skill-critique.md に"測定モード"の型（bar / verdict / must-should-fix / finding分類 / re-measure 停止条件）を追加するか。
- skill-router / advisor 依頼の goal-dispatch に「敵対的測定」の型（明示 bar ＋ 実物読解 ＋ verdict）を用意するか。
- coding では ReportFindings（failure_scenario・verdict CONFIRMED/PLAUSIBLE）が既に近い構造 → その思想を spec/一般批評へ広げられるか。

関連: [[project_design_share_skill]]（このサイクルで商用級到達）、[[feedback_increment_cycle_over_factory]]（工場でなくサイクルを信頼）
