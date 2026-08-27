---
name: project_playwright_page_screenshot
description: HTMLページを画像にする手段としてplaywrightをWaffleへ採用（2026-08-22）。libasoundの回避策と実行コマンド
metadata:
  node_type: memory
  type: project
---

**HTMLページ全体を画像にする手段が無く、ADRや成果物を「見ないまま」提示していた**問題を解消するため、playwright を Waffle の dev 依存として採用した（2026-08-22、ユーザーの明示的な判断「playwrightくらい入ってない環境はもうダメだろ」）。

- `pyproject.toml` の `[dependency-groups] dev` に `playwright>=1.62` を追加済み
- ブラウザ本体は `uv run playwright install chromium` で `~/.cache/ms-playwright/` へ入る
- 撮影スクリプト: `tools/shoot.py`（明暗2テーマ、縦に長いページは既定2000pxごとに分割してPNG化。生成枚数を標準エラーへ出す）

**必ず `LD_LIBRARY_PATH` が要る。** この環境の chromium は `libasound.so.2` を欠いており、そのままでは起動に失敗する（`error while loading shared libraries`）。sudo が要らない回避策として、過去のセッションが `~/.cache/waffle-shoot-libs/` へ同ライブラリを展開済みなので、それを指す:

```
LD_LIBRARY_PATH=$HOME/.cache/waffle-shoot-libs \
  uv run python tools/shoot.py <HTMLパス> --out-dir <出力先>
```

**Why:** 自動検査（幾何検査・文字列解析）は「壊れていない」ことしか言えず、詰まり・読みにくさ・矢印の向き・明暗への追随は描いた結果を見ないと分からない。SVG断片をPNGにする道具（`render_svg_check.py`）はあったが、HTMLページ全体を見る手段が無かった。実際、採用直後にこの手段でADRを見たところ、表の列が狭すぎて「採らない」が「採ら／ない」に割れている・判定の✓が他列と色が食い違う、という2件を見つけた ── どちらも静的検査（タグの閉じ・トークン定義・外部参照）は全て通っていた。

**How to apply:** 図やHTMLを含む成果物を提示する前に、必ずこれで画像化して全枚数を読む（[[look-at-the-render-not-only-the-checks]] の運用手段にあたる）。`libasound` の件を忘れて「playwrightが動かない」と結論しないこと ── 環境に無いのはこの1つだけで、上記の1行で解決する。
