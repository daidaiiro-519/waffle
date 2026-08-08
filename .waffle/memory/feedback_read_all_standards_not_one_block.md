---
name: feedback_read_all_standards_not_one_block
description: 規約は複数の文書とブロックに分かれている。1つ開いて判断しない
metadata:
  type: feedback
---

規約を根拠に判断するとき、**関係する規約文書とブロックを全て開いてから**判断する。1つのブロックだけを見て「宣言が無い」「規約はこう定めている」と断定しない。2026-08-08、同じ形の誤りを3回繰り返して指摘された。

**Why:** 実例3つ。(1) dunder の扱いを `coding-standard.docstring.required` の表だけで見て「宣言が無い空白」と断定した。(2) 同じ規約の `rules` に「コードから導出できる情報を docstring に書く」が**禁止**として入っているのを読まず、型や fixture の説明を足す方向を提案した。(3) **`test-standard-waffle` に専用の `docstring` ブロックがある**——テスト関数の docstring は「シナリオの宣言行と Given/When/Then を一字一句転記する器」と `target`/`style`/`transcriptionGuidance` で明示されている——のを読まず、`coding-standard` の形式（Args/Returns/Raises）をテストに当てて「709件の違反」と報告した。正しくは実装側134件で、テストの383件は当ててはいけない規約で測った数字だった。

**How to apply:** 「規約がこう定めている／定めていない」と言う前に、(a) その事柄を扱いうる規約文書を列挙する（`coding-standard` / `test-standard` / `architecture` / `tech-stack`）、(b) 各文書のブロック一覧を `waffle query --expression 'keys(@)'` で出す、(c) 関係しそうなブロックを実際に開く。特に「〜には宣言が無い」と言うときは、無いことを1文書で確かめても意味がない。

あわせて、検査コマンドが受け取る規約が1つだけのとき（`lint-docstring --standardRef` は coding-standard を1つ取る）、その検査は他の規約が定める例外を知らない。**測る範囲がその規約の対象と一致しているか**を、数字を報告する前に確かめる。

関連: [[feedback_stay_on_the_asked_axis]]（測る軸を取り違えない）、[[feedback_query_path_blockkey_vs_find_all]]（空の結果を「未設定」と読まない）
