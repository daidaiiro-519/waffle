---
name: lost-work-lives-in-the-transcript
description: 作業ファイルが消えたと判断する前に、会話の記録から復元を試みる。Write と Bash の内容がそのまま残っている
metadata:
  node_type: memory
  type: feedback
---

作業ファイルが見当たらないとき、**「消えた」と結論する前に会話の記録を探す**。`~/.claude/projects/<プロジェクト>/<セッションID>.jsonl` に、その作業で書いたファイルの中身がそのまま残っている。

探す先の順序:

| 順 | 場所 | 何が取れるか |
|---|---|---|
| 1 | 会話の記録（jsonl） | **Write の `input.content`／Bash のヒアドキュメント本文。**書いた全文が取れる |
| 2 | git（stash・dangling blob） | コミットしかけたもの |
| 3 | 作業領域（/tmp の scratchpad） | セッションが変わると消える |
| 4 | 配置済みの成果物 | 出力だけ。入力は取れない |

取り出し方は、jsonl を1行ずつ JSON として読み、`name` が `Write` の要素から `input.file_path` と `input.content` を拾う。Bash で書いた分は `cat > <path> <<'EOF' ... EOF` を正規表現で拾う。同名で複数回書かれていたら、いちばん長いものを採る。

**Why:** 図の描画の実装を「前のセッションで消えた。git にも scratchpad にも無い」と繰り返し報告し、作り直す計画まで立てた。ユーザーの「これ本当に実装消えてる？tmpとかもみたの？」で探し直したところ、**同じセッションの記録から268本が全文で復元できた**。私が見ていたのは git と scratchpad だけで、**自分が書いた記録を見ていなかった**。作り直しは丸ごと不要だった。

**How to apply:** 「失われた」は観測ではなく判断である。判断する前に、上の4か所を順に当たる。特に1は、自分がその作業をした本人である以上、必ず残っている。あわせて、復元したものは作業領域に置いたままにしない——消えた場所と同じ場所である。関連: [[look-at-the-render-not-only-the-checks]] [[skip-confirmation-before-acting]]
