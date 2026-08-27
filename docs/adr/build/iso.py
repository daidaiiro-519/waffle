#!/usr/bin/env python3
"""立体の板で図を組むための共通部品。

事業領域の1枚絵で使った見た目を、他の図でも同じ言葉で組めるようにする。
色は CSS 変数から取るので、明るい紙面でも暗い紙面でもそのまま通る。
"""

def plate(cx, y, w, h, t, tone, label, fs=13):
    """立体の板を1枚。上面のひし形＋左右の側面で厚みを出す。"""
    top = "%d,%d %d,%d %d,%d %d,%d" % (cx, y, cx+w, y+h//2, cx, y+h, cx-w, y+h//2)
    lf = "%d,%d %d,%d %d,%d %d,%d" % (cx-w, y+h//2, cx, y+h, cx, y+h+t, cx-w, y+h//2+t)
    rf = "%d,%d %d,%d %d,%d %d,%d" % (cx, y+h, cx+w, y+h//2, cx+w, y+h//2+t, cx, y+h+t)
    out = ('<polygon points="%s" class="k-side l %s"/><polygon points="%s" class="k-side r %s"/>'
           '<polygon points="%s" class="k-top %s"/>') % (lf, tone, rf, tone, top, tone)
    if label:
        out += ('<text x="%d" y="%d" class="k-lb" text-anchor="middle" font-size="%d">%s</text>'
                % (cx, y+h//2+4, fs, label))
    return out


def slab(x, y, w, h, t, tone, lines, fs=13):
    """立体の平板（横長）。ひし形にしたくないものに使う。"""
    out = ('<polygon points="%d,%d %d,%d %d,%d %d,%d" class="k-side l %s"/>'
           '<polygon points="%d,%d %d,%d %d,%d %d,%d" class="k-side r %s"/>'
           '<rect x="%d" y="%d" width="%d" height="%d" rx="6" class="k-top %s"/>'
           ) % (x, y+h, x+w, y+h, x+w, y+h+t, x, y+h+t, tone,
                x+w, y, x+w, y+h+t, x+w, y+h+t, x+w, y, tone,
                x, y, w, h, tone)
    n = len(lines)
    st = y + h/2 - (n-1)*10 + 4
    for i, (txt, f) in enumerate(lines):
        out += ('<text x="%d" y="%d" class="k-lb" text-anchor="middle" font-size="%d">%s</text>'
                % (x+w//2, int(st+i*21), f, txt))
    return out


def chip(cx, cy, label, cls="k-chip", w=76, fs=12):
    return ('<rect x="%d" y="%d" width="%d" height="30" rx="15" class="%s"/>'
            '<text x="%d" y="%d" class="k-ct" text-anchor="middle" font-size="%d">%s</text>'
            ) % (cx-w//2, cy-15, w, cls, cx, cy+4, fs, label)


def orbit_back(cx, cy, rx, ry):
    return '<path d="M %d %d A %d %d 0 0 1 %d %d" class="k-orb"/>' % (cx-rx, cy, rx, ry, cx+rx, cy)


def orbit_front(cx, cy, rx, ry):
    return '<path d="M %d %d A %d %d 0 0 1 %d %d" class="k-orb front"/>' % (cx+rx, cy, rx, ry, cx-rx, cy)


def arrow_down(x, y1, y2, cls="k-a"):
    return ('<line x1="%d" y1="%d" x2="%d" y2="%d" class="%s"/>'
            '<polygon points="%d,%d %d,%d %d,%d" class="k-ah"/>'
            ) % (x, y1, x, y2-9, cls, x-7, y2-9, x+7, y2-9, x, y2)


def arrow_up(x, y1, y2, cls="k-a"):
    return ('<line x1="%d" y1="%d" x2="%d" y2="%d" class="%s"/>'
            '<polygon points="%d,%d %d,%d %d,%d" class="k-ah"/>'
            ) % (x, y1, x, y2+9, cls, x-7, y2+9, x+7, y2+9, x, y2)


def arrow_right(x1, x2, y, cls="k-a"):
    return ('<line x1="%d" y1="%d" x2="%d" y2="%d" class="%s"/>'
            '<polygon points="%d,%d %d,%d %d,%d" class="k-ah"/>'
            ) % (x1, y, x2-9, y, cls, x2-9, y-7, x2, y, x2-9, y+7)


def eyebrow(x, y, text):
    return ('<line x1="%d" y1="%d" x2="%d" y2="%d" class="k-rule"/>'
            '<text x="%d" y="%d" class="k-eye">%s</text>') % (x, y, x+58, y, x, y+36, text)


def fig(view_h, aria, body, klass="figwrap hero flat", view_w=1000):
    return ('<div class="%s"><svg class="wf-fig" viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg></div>'
            % (klass, view_w, view_h, aria, body))


CSS = """.figwrap.hero.flat{padding:0;border:none;background:none;overflow-x:auto}
.k-eye{font-family:var(--mono);font-size:13px;letter-spacing:.34em;fill:var(--ink-faint)}
.k-h1{font-family:var(--serif);font-size:30px;font-weight:600;fill:var(--ink)}
.k-h2{font-family:var(--serif);font-size:20px;font-weight:600;fill:var(--ink)}
.k-sub{font-family:var(--sans);font-size:14px;fill:var(--ink-soft)}
.k-note{font-family:var(--sans);font-size:12px;fill:var(--ink-faint)}
.k-ax{font-family:var(--sans);font-size:12px;fill:var(--ink-faint);letter-spacing:.2em}
.k-rule{stroke:var(--infer);stroke-width:3}
.k-top{stroke-width:1.4}
.k-top.t1{fill:var(--fact-bg);stroke:var(--fact)}
.k-top.t2{fill:var(--infer-bg);stroke:var(--infer)}
.k-top.t3{fill:var(--surface-2);stroke:var(--ink-soft)}
.k-top.t4{fill:var(--assume-bg);stroke:var(--assume)}
.k-top.t5{fill:var(--against-bg);stroke:var(--against)}
.k-side{stroke:none}
.k-side.l.t1{fill:var(--fact);fill-opacity:.22} .k-side.r.t1{fill:var(--fact);fill-opacity:.36}
.k-side.l.t2{fill:var(--infer);fill-opacity:.22} .k-side.r.t2{fill:var(--infer);fill-opacity:.36}
.k-side.l.t3{fill:var(--ink-soft);fill-opacity:.18} .k-side.r.t3{fill:var(--ink-soft);fill-opacity:.30}
.k-side.l.t4{fill:var(--assume);fill-opacity:.22} .k-side.r.t4{fill:var(--assume);fill-opacity:.36}
.k-side.l.t5{fill:var(--against);fill-opacity:.20} .k-side.r.t5{fill:var(--against);fill-opacity:.32}
.k-lb{font-family:var(--sans);fill:var(--ink)}
.k-step{font-family:var(--sans);font-size:12px;font-weight:700;fill:var(--infer);letter-spacing:.16em}
.k-cut{stroke:var(--infer);stroke-width:1.4;stroke-dasharray:7 6}
.k-orb{fill:none;stroke:var(--assume);stroke-width:1.6;stroke-dasharray:8 7;opacity:.55}
.k-orb.front{opacity:1;stroke-dasharray:none;stroke-width:2}
.k-chip{fill:var(--assume-bg);stroke:var(--assume);stroke-width:1.6}
.k-chip.ng{fill:var(--against-bg);stroke:var(--against)}
.k-chip.hum{fill:var(--fact-bg);stroke:var(--fact);stroke-width:2}
.k-ct{font-family:var(--sans);fill:var(--ink)}
.k-a{stroke:var(--ink-faint);stroke-width:2}
.k-a.ng{stroke:var(--against);stroke-width:2;stroke-dasharray:7 5}
.k-ah{fill:var(--ink-faint)}
"""


# ── 形が自明なものは、その形で描く ───────────────────────────
def person(cx, cy, s=1.0, cls="g-hum"):
    """人。頭と肩で人の形にする。菱形や箱で代用しない。"""
    r = 9 * s
    sh = 16 * s
    return ('<circle cx="%.1f" cy="%.1f" r="%.1f" class="%s"/>'
            '<path d="M %.1f %.1f A %.1f %.1f 0 0 1 %.1f %.1f Z" class="%s"/>'
            ) % (cx, cy - 13*s, r, cls,
                 cx - sh, cy + 17*s, sh, sh, cx + sh, cy + 17*s, cls)


def bot(cx, cy, s=1.0, cls="g-bot"):
    """エージェント。頭部・目・アンテナで、人ではない働き手に見せる。"""
    w, h = 36*s, 32*s
    return ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="g-wire"/>'
            '<circle cx="%.1f" cy="%.1f" r="%.1f" class="%s"/>'
            '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" class="%s"/>'
            '<circle cx="%.1f" cy="%.1f" r="%.1f" class="g-eye"/>'
            '<circle cx="%.1f" cy="%.1f" r="%.1f" class="g-eye"/>'
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="g-wire"/>'
            ) % (cx, cy - h/2 - 9*s, cx, cy - h/2, 
                 cx, cy - h/2 - 12*s, 3*s, cls,
                 cx - w/2, cy - h/2, w, h, 9*s, cls,
                 cx - 7*s, cy - 3*s, 3*s, cx + 7*s, cy - 3*s, 3*s,
                 cx - 6*s, cy + 8*s, cx + 6*s, cy + 8*s)


def docs(cx, cy, s=1.0, cls="g-doc"):
    """ナレッジと規約。重ねた紙で表す。"""
    w, h = 58*s, 44*s
    out = ""
    for dx, dy in ((10*s, 10*s), (5*s, 5*s), (0, 0)):
        out += ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" class="%s"/>'
                % (cx - w/2 + dx, cy - h/2 + dy - 5*s, w, h, 4*s, cls))
    for i in range(3):
        y = cy - h/2 + 9*s + i * 10*s - 5*s
        out += ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="g-line"/>'
                % (cx - w/2 + 9*s, y, cx + w/2 - 12*s, y))
    return out


GLYPH_CSS = """.g-hum{fill:var(--fact);stroke:none}
.g-hum.on{fill:var(--infer)}
.g-bot{fill:var(--surface-2);stroke:var(--ink-soft);stroke-width:1.6}
.g-bot.lead{fill:var(--infer-bg);stroke:var(--infer);stroke-width:2}
.g-eye{fill:var(--ink-soft)}
.g-bot.lead ~ .g-eye{fill:var(--infer)}
.g-wire{stroke:var(--ink-soft);stroke-width:1.6;fill:none}
.g-doc{fill:var(--assume-bg);stroke:var(--assume);stroke-width:1.6}
.g-line{stroke:var(--assume);stroke-width:1.4;opacity:.55}
"""
