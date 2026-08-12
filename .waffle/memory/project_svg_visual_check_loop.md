---
name: project_svg_visual_check_loop
description: 図を含む成果物は描いて画像を読み返してから出す。手順はdesign-structured-html Skill、強制はrequire-svg-render-check Hook
metadata:
  type: project
---

手で座標を書いたSVGは、描くまで崩れているかどうかが分からない。座標が数値として正しく
見えることと、絵として成立していることは別だった。

## どこに置いたか

| 何を | どこ | なぜそこか |
|---|---|---|
| 手順とスクリプト | `.claude/skills/design-structured-html/scripts/render_svg_check.py` ＋ SKILL.md §8 | SVGの描画確認はWaffle固有ではない。CLAUDE.mdへ書くとSkillを持ち出したときに落ちる |
| 忘れない仕掛け | `.waffle/hooks/require-svg-render-check.py`（PreToolUse / matcher `Artifact`） | 手順を書くだけでは再発する。実際に一度、描画結果を見ないまま提示していた |

Hookは、図を含むHTMLをArtifactへ出す直前に、(1)スクリプトを走らせた形跡 と
(2)出てきたPNGを Read で読み返した形跡 の両方を会話の記録から探し、欠けていれば拒否する。
成果物を書き換えた時点で両方の形跡を捨てる（書き換える前に見た画像は別の図だから）。

## 描画の経路

systemインストールは要らない。`uv` が都度取ってくるウィールだけで済む。

```
uv run --no-project --with resvg-py --with fonttools \
    python3 .claude/skills/design-structured-html/scripts/render_svg_check.py <html> --out-dir <dir>
```

rsvg-convert / Inkscape / resvg / ImageMagick / headless Chrome はこの環境に無い。
`resvg-py` が唯一、systemインストールなしで本物のSVGレンダラを使える経路だった。

**resvg は解決できない `font-family` の文字を、豆腐も警告も出さず黙って落とす。**
これに2回はまった。だから (a) フォントの内部名を fonttools で引いて `font-family` へ
書き込む (b) 文字を消した版を描いて画像が変わらなければ「何も描かれていない」として
報告する、の2つを入れてある。

`svglib` + `reportlab` + `pypdfium2` でも描けるが、出力の質が明確に落ち、
SVGの機能も一部しか実装していない。resvg を使う。

## 静的検査だけでは足りなかった理由

以前の検査はviewBoxからのはみ出しと箱より広い文字しか見ていなかった。実際に出た崩れは
全て**囲み（破線の枠）と中身の関係**で、どれもviewBoxの内側だったので素通りした。
`docs/adr/sample-gate1-subdomain.html` で3件。描いて見るまで気づけなかった。

文字の高さは行送りではなく墨の乗る範囲（上0.72em / 下0.22em）で測る。行送りで測ると
枠の外に置いた注記が誤検知になる（実際に3件誤検知した）。

## 残っている限界

HTML/CSS側のレイアウト（Grid・Flex）は依然として見ていない。見ているのはSVGの中だけ。
そこまで潰すには headless Chrome が要り、`uv` では取れない。
