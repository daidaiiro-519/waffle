---
name: waffle-own-knowledge-stage
description: 仕様と実装の抽象境界を再定義する作業の現在地。いまは Schema を説明する仕様が無いという発見の前
metadata:
  node_type: memory
  type: project
---

## いまどこにいるか（2026-08-15）

`agg-schema` の整理を終え、**値オブジェクトとエンティティを独立して書ける単位にする**決定まで進んだ地点。
次は、その単位を仕様の種別へ足すところから。

承認済みの決定は **10本**（`docs/adr/adr-*.html`）。

## 済んだこと

| | |
|---|---|
| knowledge 1本 | `spec-implementation-abstraction`（KnowledgeSchema/v6、**ACTIVE**） |
| 決定 | 描くことと配ることを分ける（承認済み） |
| 仕様の分割 | `uc-render-document` 49→37件／**`uc-deploy-document`** 12件（両方 VALIDATED） |

分割のとき、またぐシナリオは0件だった。移した15件のシナリオが全部 `render する` の語彙だったので、配置の語彙へ言い換えた。識別子も3つ改名した。
`uc-deploy-artifact` と名付けたが、**アーティファクトはユビキタス言語に無い**（定義済みは「成果物 ── Document を描画して得られる、読み手向けの出力」）。`uc-deploy-document` へ改名した。

## 今回の発見 ── Schema を説明する仕様が無い

schema が持つ Waffle 独自の宣言と、仕様での言及回数：

| 宣言 | schema 内 | 仕様での言及 |
|---|---|---|
| `x-prompt-write` | **623** | 19 |
| `x-prompt-query` | 216 | 7 |
| `x-render` | 157 | 74 |
| **`x-render-order`** | **156** | **0** |
| `x-render-level` | 152 | **2** |
| `x-render-target` | 10 | 26 |

言及があるものも「描画のユースケースが x-render を読む」という**使う側からの言及**で、**Schema 自身が何を宣言できるかを定義した仕様が無い**。`agg-schema` が持つのは構造の不変条件12件だけで、`x-render-target`・`pathVars`・`deploy` は**0回**。

結果：schema を直しても仕様は何も言わない。転写する受け入れ基準が無いのでテストが書けない。突き合わせる宣言が無いのでドリフト検知も効かない。**`x-render-order` を誰かが消しても何も落ちない。**

構造の正しさは JSON Schema 自身が保証している。埋まっていないのは **Waffle が `x-` で足した部分だけ**。しかも最も使われている `x-prompt-write` が、最も説明されていない。

## 直近で訂正したこと

- **正本の場所は規約ではなく仕様。**「置き場所は規約」を当てたのは誤り。承認済みの分け目で測ると、成果物の場所は読み手が探す場所そのもので、利用者にとって何が起きるかが変わる
- **既存へ肉付けしない。**`agg-schema` に不変条件を1件足す案を出したが、足りないのではなく形が古い前提のままだった → [[correct-toward-the-right-form-not-the-existing-one]]

## 未決（`x-render-target` について）

測ると `path` は9件中8件が種別と識別子から導出でき、Knowledge だけが `{status}` を挟む例外。`AgentSchema` と `TemplateSchema` は discriminator ごとに書き分けているのに値が同一。
ただし**この評価は、Schema を説明する仕様が無いまま行っている**。仕様を起こしてから、仕様の言葉で問い直す。

正本の経路に `status` を入れていることが、今日「置き去りの成果物4件」を生んだ（削除済み）。経路から外すかは未決。

## この先やること（順に）

1. ~~`agg-schema` の整理~~ **済**。ドメインモデルの4部品のうち仕様として書けるのは2つだけで、参照7つのうち `schemaRef` だけが相手の値を写して持っていた（承認済みの決定へ）
1b. **仕様の種別に値オブジェクトとエンティティを足す** ← いまここ
2. Schema を説明する仕様を起こす（`x-` の宣言それぞれの意味と保証）
3. その仕様の言葉で `x-render-target` を問い直し、直す
4. `uc-deploy-document` を TDD で実装し、`render` から配置を外す
5. `AgentSchema` に Orchestrator が読む knowledge を宣言する欄を足す／`KnowledgeSchema` から `skillRefs`・`agentRefs` を外す
6. `spec-implementation-abstraction` を Orchestrator の Ref へ登録して配る
7. **図の描画** ── `recovered/figures/` の `grammar.py`・`figure_schema.py`・`draw.py` を読み、決定と突き合わせる。`pygraphviz` と `dot` を入れて50枚を再現できるかで復元の完全性を測り、`src/` へ載せる
8. 記法を仕様へ／RenderMetaSchema の新版／既存の図の宣言8件の判定
9. knowledge から記入指示への突き合わせ
10. サブドメインの切り直し

## knowledge へ戻すべきもの

**境界の実在性を測る3つの問い**（独立して失敗するか・再利用されるか・許可が別か）。
「描くことと配ることを分ける」の判定に使ったが、いまの knowledge は「潰すと境界が消える」までしか持たない。

## 材料の在りか

- 索引 https://claude.ai/code/artifact/227e331a-b637-473e-b635-78ad8422d635
- 復元した実装268本：`recovered/`（**一時的な置き場。精査して `src/` へ移し空にする**）
- 会話の記録から発言を辿る方法：[[lost-work-lives-in-the-transcript]]

**How to apply:** 再開は1から。schema をどう直すかを考え始めたら、**それを説明する仕様があるかを先に問う**。無いまま直すと、テストもドリフト検知も効かないまま構造だけが変わる。
