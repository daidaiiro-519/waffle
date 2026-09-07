# 引き継ぎメモ ── 2026-08-19 時点

このセッションが不調な可能性があるため、別セッションへ引き継ぐための資料。
正式な HandoffSchema（廃止済み）ではなく、素の Markdown。読んだら削除してよい。

## 前提として先に読むもの

- `CLAUDE.md`（このリポジトリの Orchestrator 定義。運用ルール・委譲パターンを含む）
- `.waffle/memory/MEMORY.md`（共有メモリの索引。特に下記2件は今回の作業で直接効く）
  - `feedback_redefinition_does_not_reason_from_the_existing.md` ── 再定義中は既存の実装・宣言を根拠にしない
  - `feedback_no_pattern_names_in_spec_vocabulary.md` ── 仕様にパターン名（Fowler/DDD戦術パターンの語）を入れない
- `.waffle/memory/project_waffle_own_knowledge_stage.md`（この一連の作業の背景となっている「現在地」メモ。ただし内容が古い可能性が高いので、本ファイルを優先すること）

## 全体像：いま何をしているか

**「仕様と実装の抽象と具体の境界を、knowledge のもとで正しく再定義する」** という大テーマの中で、
段2（型として立てる8つのスキーマ）を **Domain → Coding → Knowledge → Template → Agents → Skills → Hook → ADR** の順で仕様化している。
いま **Domain が完成イメージのレビュー中**、Coding 以降は未着手。

- 段1（全型共通の契約）は承認済み・完了
- 段2 の対象8つ：Domain・Coding・Knowledge・Template・Agents・Skills・Hook・ADR

## 現在地：Domain の型

### 承認状態

**未承認。** 未決は1点だけ：

> 業務領域を、区切られた文脈の外へ出す記録（`subdomain-placement-remeasured.html` / `subdomain-placement-decision-record.html`、2026-08-11、状態は承認待ち）を、Domain の型と一緒に承認するか。

この記録を前提に Domain の型（8種別・宛先・指針）を組んである。承認すれば一緒に確定、切り離すなら Domain 側の事業領域・属する事業領域・属する業務領域の欄を外す必要がある。

### 確定している内容（Domain の型）

- 型の名前：`DomainSchema/v1`（`DomainSpecSchema/v11` から改名。`Spec` を落とす ── 8つの型すべてで `〜Schema` に揃える）
- 種別は **8つ**：事業領域・業務領域・区切られた文脈・集約・エンティティ・値オブジェクト・業務ユースケース・業務サービス
- 文書数：bc-waffle だけで **44本 → 57本**
- 共有する組み立て6つ：受け入れ基準／シナリオ（**確かめる単位**を持つ）／属性／常に満たすこと／文書への参照／図の宣言
- 新しい欄は5つ：名前の英語表記（全種別）／この事業が顧客へ提供しているもの（事業領域）／属する事業領域（業務領域）／属する業務領域（業務ユースケース）／確かめる単位（シナリオ）
- 描き方：**HTML**（Markdown ではない。理由は「型を起こす9段」の9段目として Domain の型頁 `07` に理由あり）
- 図は「16の主張」＋新たに足した「分かれ」（`cases`）── 図解の記法アーティファクトに追加済み
- 集約は「境界の内側／境界の外／常に満たすこと／外へ公開する操作／出す出来事」を持つ。ルートも別文書にする（エンティティと同じ扱い、集約自身には同一性・属性を持たせない）
- 「常に満たすこと（不変条件）を覆う義務」は**変える操作にだけ**掛かる。変えない操作は破りようがないため義務なし
- ドリフト検知の設計：仕様と実装を結ぶのは「宣言→シナリオ確かめる単位」「実装→名乗り」「シナリオ→テストへの転記」の3辺の三角形。実装の厚み・様式（Fowlerパターン名）は仕様に入れない。詳細は `drift-binding.html` / `drift-walkthrough.html`

### 承認プロセス上の未決（Domain の型のページ内 `11 まだ決めていないこと`）

現在は1点（上記の業務領域の記録の扱い）のみ。他の論点（変える相手を書かせるか／エンティティ値オブジェクトの置き場所／operationIndex／DomainSchema の名前）はこのセッション中にすべて承認済み決定と原理から導いて閉じ済み（Domain の型ページ `10 閉じた論点` 参照）。

## 成果物一覧（Artifact URL）

すべて `docs/adr/*.html` として repo にも保存されている。builder は `docs/adr/build/*.py`。

### Domain の型（本体・未承認）

| 内容 | URL | ファイル |
|---|---|---|
| **Domain の型（メイン。ここが正）** | `https://claude.ai/code/artifact/e0e51605-4fd9-4212-ace1-28fa5bf1075d` | `tier2-domain.html` |
| Domain の8種別・索引 | `https://claude.ai/code/artifact/03177d1b-e558-4bdd-9619-df96e9d4e906` | `tier2-domain-preview.html` |

### Domain の完成イメージ（8枚。索引から辿れる。すべて「1件の文書だけ」の統一構造）

| # | 種別 | URL | ファイル | 公開状態（このセッション終了時点） |
|---|---|---|---|---|
| 1 | 事業領域 / Business Domain | `https://claude.ai/code/artifact/0471e3e5-f19e-4507-9385-b6fb862e9525` | `tier2-domain-business-domain.html` | ✅ 最新反映済み |
| 2 | 業務領域 / Subdomain | `https://claude.ai/code/artifact/bbff2e22-40f6-4d2e-9b04-1377360775e1` | `tier2-domain-subdomain.html` | ✅ 最新反映済み |
| 3 | 区切られた文脈 / Bounded Context | `https://claude.ai/code/artifact/719c98c5-b1f5-4f4c-94ee-ab9245d82cc2` | `tier2-domain-bounded-context.html` | ✅ 最新反映済み |
| 4 | 集約 / Aggregate | `https://claude.ai/code/artifact/7754906c-ab81-4c29-8c55-78f1841438da` | `tier2-domain-aggregate.html` | ✅ 最新反映済み |
| 5 | エンティティ / Entity | `https://claude.ai/code/artifact/a01cd642-9885-4dfa-926b-aeb35a2c6c10` | `tier2-domain-entity.html` | ✅ 最新反映済み |
| 6 | 値オブジェクト / Value Object | `https://claude.ai/code/artifact/de9fa721-f9d6-4a08-96dc-6e6e33529745` | `tier2-domain-value-object.html` | ✅ 最新反映済み |
| 7 | 業務ユースケース / Use Case | `https://claude.ai/code/artifact/16369065-66b1-496a-a1d0-aaa0c1093c23` | `tier2-domain-usecase.html` | ✅ 最新反映済み |
| 8 | 業務サービス / Domain Service | `https://claude.ai/code/artifact/db0885b5-af9d-42f1-8a6f-09a39b4d2812` | `tier2-domain-domain-service.html` | ✅ 最新反映済み（2026-08-19 に再 publish 済み） |

8番（業務サービス）は 2026-08-19 に内容を確認して再 publish 済み。8枚とも最新。

### 関連する既存決定・記録（このセッションで参照・一部訂正）

| 内容 | URL |
|---|---|
| 集約は自分の境界の内側を持つ（未承認、Domain の型の前提） | `https://claude.ai/code/artifact/2e293712-115f-48f0-8a3d-b54858e8b1c8` |
| 値オブジェクトとエンティティを独立して書ける単位にする（承認済み→置き換えられた） | `https://claude.ai/code/artifact/1a0663a7-5c19-433f-a623-899e83d23643` |
| 図解の記法（承認済み、「分かれ」を追加済み） | `https://claude.ai/code/artifact/2adde2ae-48a0-40a9-829c-443df674bbc8` |
| 仕様と実装を、どこで結ぶか（ドリフト検知の設計） | `https://claude.ai/code/artifact/1ebe3dff-e9dd-4967-b736-ca725fd59f59` |
| ずれたとき、何が赤くなるか（ドリフト検知の完成イメージ） | `https://claude.ai/code/artifact/fc3626b7-6755-4848-810a-a2c7799dd3bf` |
| アーティファクト索引（このリポジトリの全成果物索引） | `https://claude.ai/code/artifact/227e331a-b637-473e-b635-78ad8422d635` |

`docs/adr/artifact-index.html`（builder: `build_artifact_index.py`）に全体索引がある。**2026-08-21 に節「08 段2 ── Domain の型」を足して反映済み**（Domain の型・事業領域が持つ欄・8種別の索引・完成イメージ8枚・ドリフト検知2枚の計13行。「載せていないもの」は 09 へ繰り下げ）。

## 今回作った/直した builder（再利用可能な部品）

- `docs/adr/build/card_kit.py` ── Domain 完成イメージ8枚の共通デザイン部品（`page()` `zone()` `two()` `head()` `pair()` `note()`）。**次に Coding 等の完成イメージを作るときもこれを使い回せる**
- `docs/adr/build/build_domain_spec.py` ── Domain の型メインページの builder
- `docs/adr/build/build_cards_rest.py` ── 完成イメージ 1,2,3,4,5,6,8 の builder
- `docs/adr/build/build_card_usecase.py` ── 完成イメージ 7（業務ユースケース）の builder。シーケンス図を手で SVG 記述している
- `docs/adr/build/build_cards_index.py` ── 索引ページの builder
- `docs/adr/build/build_drift_design.py` / `build_drift_walk.py` ── ドリフト検知の設計・完成イメージ
- `docs/adr/build/_common.py` / `newfmt.css` ── 全体共通の CSS・部品。**このセッションでスマホの文字自動拡大バグと表の横はみ出しバグを直した**（`text-size-adjust:100%`、`table.wide` クラスへの分離）。今後もここを直せば全ページに反映される

再生成の仕方：`uv run python docs/adr/build/<script>.py`（repo root から）。全体チェックは `uv run python docs/adr/build/check_all.py`。

## このセッションで学んだ・訂正した重要な設計判断（次のセッションが繰り返さないために）

1. **集約はエンティティでもある**が、それは実装の形の話であって文書を何本立てるかは決めない。ルートのエンティティも独立した文書にする（規則を1つ減らすため）
2. **不変条件を覆う義務は「変える操作」にだけ**掛かる。「コマンド」という語は文書の表面には出さず、指針の中だけで使う（業務エキスパートに伝わらない技術語のため）
3. **業務ロジックの実装方法（トランザクションスクリプト等のFowlerパターン名）を仕様に持ち込みかけて2回差し戻された。** 仕様は「宣言した単位が実装のどこかで名乗られているか」だけを問う。実装の形（クラスか関数か）は問わない
4. **完成イメージに型の説明（「新しい欄」札など）を混ぜない。** 描かれる文書には中身だけが出て、型の定義（必須か・何を書くか）は「Domain の型」ページ側にだけ書く。2箇所に同じ情報を書かない
5. デザインは**まとまり（zone）単位で構造化**し、対になるもの（入力/出力、分類/根拠など）は横並びにする。全部同じ表の羅列にしない
6. 受け入れ基準は EARS 全体を真似ない。**「いつ」を分類の値として持つ**ことだけを取り、英語キーワードは出さない。「1件が単独の主張であること」は構造で強制できていない弱点として明示的に書き残してある
7. **再定義中は既存の実装・宣言を根拠にしない。** 実測は「数える」ためであって「あるべき形の根拠」にしない（何度も指摘された）

## 次にやること

1. Domain の型の未決1点（業務領域の記録を一緒に承認するか）をユーザーに確認 → 承認されたら Domain 完了
2. **Coding の型**へ進む。ユーザー方針：「Coding は仕様と規約の根幹」「メモリかアーティファクトに再定義しかけた形跡があるはず」との発言があったが、このセッションでは未着手・未調査。次セッションでまず `.waffle/memory/` と過去アーティファクト索引を Coding 関連で検索すること
3. Coding 以降も Domain と同じ手順で：型メインページ（決定の理由づけ）→ 完成イメージ（`card_kit.py` を再利用）→ ユーザーレビュー、のサイクルを回す
