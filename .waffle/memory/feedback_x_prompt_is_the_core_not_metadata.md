---
name: feedback-x-prompt-is-the-core-not-metadata
description: x-prompt-write/x-prompt-queryはWaffleの根幹（AI推論の唯一の接面）であり、schema編集の付随物として扱わない
metadata:
  type: feedback
---

x-prompt-write / x-prompt-query は Waffle の根幹。schemaの構造（型・必須・enum）は
機械が読むが、**AIが何を書くべきか・どう読むべきかを決めているのは x-prompt だけ**であり、
ここが弱いと構造がいくら正しくても中身が誤る。schema編集の付随物として扱ってはいけない。

2026-08-03、ユーザーから「これx-prompt-queryもx-prompt-writeもかなり軽視してるよね？
これwaffleの根幹といっても差し支えないレベルのai推論に響く部分なんだけどな」と指摘を受けた。
実測で裏付けられた具体的な劣化は2種類:

1. **同じ欄について write と query が矛盾していた**
   `layout.tree` の x-prompt-write は「正典ディレクトリツリー」と書き、
   同じ欄について LayoutBlock の x-prompt-query は「機械はここから決定を読み取らない」
   と書いていた。書く側の「正典」に従った結果、機械が読む `layers[].path` ではなく
   自由テキストの図を先に書き、両者が食い違ったまま出荷された。

2. **query が構造変更に追随していなかった**
   `ConceptPlacementBlock` の x-prompt-query が enum から削除済みの値 `single` を
   参照し続けていた。write側は v5 作成時に直したが query 側は直さなかった。

**Why:** Waffleは「構造の検証は機械、中身の判断はAI」という分担で成立している。
x-prompt はその分担のうちAI側の入力そのもの。構造が正しくても x-prompt が誤っていれば
AIは誤った値を書き、しかも構造検証は通るので誰も気づかない。write と query が矛盾して
いる場合、書き手と読み手が別々の前提で動くため、documentは構造上妥当なまま意味的に壊れる。

**How to apply:**
- schemaの構造を変えたら、その欄の x-prompt-write と x-prompt-query を**必ず対で**見直す。
  enum値の削除・フィールドの分割・意味の変更は、両方に波及していないか確認する
- 1つの欄について write と query が**同じ事実**を語っているかを確認する。
  「これは宣言か、投影か」「機械が読むか、人が読むか」の答えが両側で一致すること
- 禁止（〜しない）を書くときは、**行き先（代わりにどこへ置くか）を対で書く**。
  「ポートを層として並べない」だけでは、ではどこへ置くのかが決まらず宙に浮く
- x-prompt-query は `document_index.py` が `{blockType}Block` 直下しか読まない。
  末端フィールドに書いても死文になるので、読み方はブロック単位に集約する
  （write は末端まで書く。粒度が違うのは設計であって手抜きではない）
- 検査コードが読まない宣言（`layers[].path` / `mayDependOn` 等）は、誤っていても
  誰も気づかない。x-prompt を直すだけでは再発を止められないので、
  宣言を読む検査の有無もあわせて確認する

関連: [[feedback-fix-x-prompt-before-document]] [[feedback-udd-implementation-before-spec]]
