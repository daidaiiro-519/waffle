"""session 部品 ── 操作と、返ってきたものの対比をHTMLへ写す。"""
from html import escape as e

def render_session(figure):
    scenes = []
    for sc in figure["scenes"]:
        wins = []
        for at in ("before", "after"):
            w = sc[at]
            lines = "".join(
                f'<span class="line line--{ln["kind"]}">{e(ln["text"])}</span>'
                for ln in w["lines"])
            wins.append(
                f'<div class="win win--{at}">'
                f'<div class="win__bar"><span class="win__dots"></span>'
                f'<span class="win__title">{e(w["title"])}</span>'
                f'<span class="win__tag">{"変更前" if at == "before" else "変更後"}</span></div>'
                f'<pre class="win__body">{lines}</pre></div>')
        scenes.append(f'<div class="scene"><p class="scene__label">{e(sc["label"])}</p>'
                      f'<div class="scene__pair">{"".join(wins)}</div></div>')
    return (f'<figure class="fig fig--session">{"".join(scenes)}'
            f'<figcaption>{e(figure["intent"])}</figcaption></figure>')