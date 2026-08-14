"""図表の一族を、SVGで直接描く。配置を解く必要が無いので Graphviz を通さない。

軸・帯・割合・格子は、値から位置が一意に決まる。だから座標計算は
その場の算術で済み、レイアウトエンジンの出番が無い。
"""
from __future__ import annotations

import math
from html import escape as e

PAD = 16


def _t(x, y, s, cls="c-label", anchor="middle", dy=0):
    return (f'<text class="{cls}" x="{x:.1f}" y="{y + dy:.1f}" '
            f'text-anchor="{anchor}">{e(str(s))}</text>')


def _svg(w, h, body):
    return (f'<svg class="c-fig" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" '
            f'height="{h:.0f}" role="img">'
            '<defs><marker id="c-head" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path class="c-arrow" d="M0,0 L10,5 L0,10 z"/></marker></defs>'
            f'{body}</svg>')


# ── やり取りの順序 ──────────────────────────────────
def exchange(fig):
    who = fig["participants"]
    steps = fig["steps"]
    colw, rowh, head = 170, 42, 46
    w = PAD * 2 + colw * len(who)
    h = head + rowh * (len(steps) + 1) + PAD
    x = lambda i: PAD + colw * i + colw / 2                       # noqa: E731

    out = []
    for i, name in enumerate(who):
        out.append(f'<rect class="c-box" x="{x(i) - 62:.1f}" y="{PAD}" width="124" '
                   f'height="26" rx="5"/>' + _t(x(i), PAD + 17, name, "c-name"))
        out.append(f'<line class="c-life" x1="{x(i):.1f}" y1="{PAD + 26}" '
                   f'x2="{x(i):.1f}" y2="{h - PAD:.1f}"/>')

    frames = []
    for r, s in enumerate(steps):
        y = head + rowh * (r + 1)
        if s["kind"] == "frame":
            frames.append((s, r))
            continue
        if s["kind"] == "note":
            out.append(f'<rect class="c-note" x="{x(0) - 70:.1f}" y="{y - 15:.1f}" '
                       f'width="{colw * (len(who) - 1) + 140:.1f}" height="24" rx="4"/>'
                       + _t(x(0) + colw * (len(who) - 1) / 2, y + 2, s["text"], "c-note-t"))
            continue
        a, b = who.index(s["from"]), who.index(s["to"])
        cls = "c-msg c-msg--return" if s["kind"] == "return" else "c-msg"
        out.append(f'<line class="{cls}" x1="{x(a):.1f}" y1="{y:.1f}" x2="{x(b):.1f}" '
                   f'y2="{y:.1f}" marker-end="url(#c-head)"/>')
        out.append(_t((x(a) + x(b)) / 2, y - 6, s["text"], "c-msg-t"))

    for s, r in frames:
        y0 = head + rowh * (r + 1) - 22
        y1 = head + rowh * (r + 1 + s["span"]) - 12
        out.insert(0, f'<rect class="c-frame" x="{PAD + 8}" y="{y0:.1f}" '
                      f'width="{w - PAD * 2 - 16:.1f}" height="{y1 - y0:.1f}" rx="4"/>')
        out.insert(1, f'<rect class="c-frame-tab" x="{PAD + 8}" y="{y0:.1f}" width="52" '
                      f'height="16"/>' + _t(PAD + 34, y0 + 12, s["label"], "c-tab-t"))
    return _svg(w, h, "".join(out))


# ── 帯（時間・日程・体験・枝） ────────────────────────
def lanes(fig):
    rows, span = fig["rows"], fig.get("span", 10)
    lw, tw, rh = 110, 460, 30
    w = PAD * 2 + lw + tw
    h = PAD * 2 + rh * len(rows) + (22 if fig.get("axis") else 0)
    out = []
    for i, r in enumerate(rows):
        y = PAD + rh * i
        out.append(_t(PAD + lw - 10, y + 19, r["name"], "c-label", "end"))
        out.append(f'<rect class="c-track" x="{PAD + lw}" y="{y + 6:.1f}" '
                   f'width="{tw}" height="{rh - 12}" rx="4"/>')
        for bar in r["bars"]:
            bx = PAD + lw + tw * bar["from"] / span
            bwid = tw * (bar["to"] - bar["from"]) / span
            out.append(f'<rect class="c-bar c-bar--{bar.get("tone", "plain")}" x="{bx:.1f}" '
                       f'y="{y + 6:.1f}" width="{bwid:.1f}" height="{rh - 12}" rx="3"/>')
            if bar.get("label"):
                out.append(_t(bx + bwid / 2, y + 19, bar["label"], "c-bar-t"))
    if fig.get("axis"):
        ay = PAD + rh * len(rows) + 4
        out.append(f'<line class="c-axis" x1="{PAD + lw}" y1="{ay:.1f}" '
                   f'x2="{PAD + lw + tw}" y2="{ay:.1f}"/>')
        for k, lab in enumerate(fig["axis"]):
            ax = PAD + lw + tw * k / (len(fig["axis"]) - 1)
            out.append(f'<line class="c-tick" x1="{ax:.1f}" y1="{ay:.1f}" x2="{ax:.1f}" '
                       f'y2="{ay + 4:.1f}"/>' + _t(ax, ay + 15, lab, "c-tick-t"))
    return _svg(w, h, "".join(out))


# ── 割合（円） ──────────────────────────────────
def _arc(cx, cy, r, a0, a1):
    p = lambda a: (cx + r * math.cos(math.radians(a - 90)),                # noqa: E731
                   cy + r * math.sin(math.radians(a - 90)))
    x0, y0 = p(a0)
    x1, y1 = p(a1)
    return f"M{x0:.1f},{y0:.1f} A{r:.1f},{r:.1f} 0 {1 if a1 - a0 > 180 else 0},1 {x1:.1f},{y1:.1f}"


def share(fig):
    sl = fig["slices"]
    total = sum(s["value"] for s in sl) or 1
    cx, cy, r = PAD + 70, PAD + 70, 52
    w, h = PAD * 2 + 140 + 240, PAD * 2 + 140
    out, a = [], 0.0
    for i, s in enumerate(sl):
        a1 = a + s["value"] / total * 360
        out.append(f'<path class="c-arc c-tone-{i % 4}" d="{_arc(cx, cy, r, a, a1)}"/>')
        a = a1
    out.append(_t(cx, cy + 5, fig.get("centre", ""), "c-centre"))
    for i, s in enumerate(sl):
        y = PAD + 22 + i * 26
        out.append(f'<rect class="c-chip c-tone-{i % 4}" x="{PAD + 158}" y="{y - 9:.1f}" '
                   f'width="10" height="10" rx="2"/>')
        out.append(_t(PAD + 176, y, s["name"], "c-label", "start"))
        out.append(_t(w - PAD, y, s["value"], "c-num", "end"))
    return _svg(w, h, "".join(out))


# ── 大小（棒と軸） ───────────────────────────────
def bars(fig):
    sl = fig["slices"]
    top = max(s["value"] for s in sl) or 1
    bw, gap, ph = 62, 26, 150
    w = PAD * 2 + 44 + len(sl) * (bw + gap)
    h = PAD * 2 + ph + 30
    x0, y0 = PAD + 44, PAD + ph
    out = [f'<line class="c-axis" x1="{x0}" y1="{PAD}" x2="{x0}" y2="{y0}"/>',
           f'<line class="c-axis" x1="{x0}" y1="{y0}" x2="{w - PAD}" y2="{y0}"/>']
    for k in range(5):
        v = top * k / 4
        y = y0 - ph * k / 4
        out.append(f'<line class="c-grid" x1="{x0}" y1="{y:.1f}" x2="{w - PAD}" y2="{y:.1f}"/>')
        out.append(_t(x0 - 8, y + 4, round(v), "c-tick-t", "end"))
    for i, s in enumerate(sl):
        bx = x0 + 14 + i * (bw + gap)
        bh = ph * s["value"] / top
        out.append(f'<rect class="c-bar c-tone-{i % 4}" x="{bx:.1f}" y="{y0 - bh:.1f}" '
                   f'width="{bw}" height="{bh:.1f}" rx="3"/>')
        out.append(_t(bx + bw / 2, y0 - bh - 6, s["value"], "c-num"))
        out.append(_t(bx + bw / 2, y0 + 17, s["name"], "c-tick-t"))
    return _svg(w, h, "".join(out))


# ── 流れの量 ────────────────────────────────────
def flow(fig):
    links = fig["links"]
    total = sum(l["value"] for l in links) or 1
    w, h = 560, PAD * 2 + 190
    xl, xr, bw = PAD + 96, w - PAD - 96, 12
    out, ly, ry = [], PAD, PAD
    lefts, rights = {}, {}
    for l in links:
        lefts.setdefault(l["from"], 0)
        lefts[l["from"]] += l["value"]
        rights.setdefault(l["to"], 0)
        rights[l["to"]] += l["value"]
    pos_l, pos_r, cy = {}, {}, PAD
    for k, v in lefts.items():
        pos_l[k] = [cy, cy + 190 * v / total]
        cy = pos_l[k][1] + 8
    cy = PAD
    for k, v in rights.items():
        pos_r[k] = [cy, cy + 190 * v / total]
        cy = pos_r[k][1] + 8
    for i, l in enumerate(links):
        hgt = 190 * l["value"] / total
        a, b = pos_l[l["from"]][0], pos_r[l["to"]][0]
        pos_l[l["from"]][0] += hgt
        pos_r[l["to"]][0] += hgt
        m = (xl + xr) / 2
        out.append(f'<path class="c-ribbon c-tone-{i % 4}" d="M{xl + bw},{a:.1f} '
                   f'C{m},{a:.1f} {m},{b:.1f} {xr},{b:.1f} L{xr},{b + hgt:.1f} '
                   f'C{m},{b + hgt:.1f} {m},{a + hgt:.1f} {xl + bw},{a + hgt:.1f} Z"/>')
    for k, (y0, y1) in pos_l.items():
        out.append(f'<rect class="c-node" x="{xl}" y="{y0:.1f}" width="{bw}" '
                   f'height="{y1 - y0:.1f}"/>' + _t(xl - 8, (y0 + y1) / 2 + 4, k, "c-label", "end"))
    for k, (y0, y1) in pos_r.items():
        out.append(f'<rect class="c-node" x="{xr - bw}" y="{y0:.1f}" width="{bw}" '
                   f'height="{y1 - y0:.1f}"/>' + _t(xr + 8, (y0 + y1) / 2 + 4, k, "c-label", "start"))
    return _svg(w, h, "".join(out))


# ── 2軸での位置づけ ─────────────────────────────
def matrix(fig):
    w, h = 460, 330
    x0, y0, x1, y1 = 104, 26, w - 24, h - 44
    out = [f'<rect class="c-quad" x="{(x0 + x1) / 2:.1f}" y="{y0}" '
           f'width="{(x1 - x0) / 2:.1f}" height="{(y1 - y0) / 2:.1f}"/>',
           f'<line class="c-axis" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}"/>',
           f'<line class="c-axis" x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}"/>',
           f'<line class="c-grid" x1="{(x0 + x1) / 2:.1f}" y1="{y0}" '
           f'x2="{(x0 + x1) / 2:.1f}" y2="{y1}"/>',
           f'<line class="c-grid" x1="{x0}" y1="{(y0 + y1) / 2:.1f}" '
           f'x2="{x1}" y2="{(y0 + y1) / 2:.1f}"/>']
    q = fig.get("quadrants", [])
    spots = [((x0 + x1) / 2 + 12, y0 + 16, "start"), (x0 + 12, y0 + 16, "start"),
             (x0 + 12, y1 - 10, "start"), ((x0 + x1) / 2 + 12, y1 - 10, "start")]
    for i, name in enumerate(q[:4]):
        out.append(_t(spots[i][0], spots[i][1], name, "c-quad-t", spots[i][2]))
    for p in fig["points"]:
        px = x0 + (x1 - x0) * p["x"]
        py = y1 - (y1 - y0) * p["y"]
        out.append(f'<circle class="c-dot" cx="{px:.1f}" cy="{py:.1f}" r="4"/>')
        out.append(_t(px, py - 10, p["name"], "c-point-t"))
    out.append(_t((x0 + x1) / 2, h - 12, fig["x"], "c-axis-t"))
    out.append(f'<text class="c-axis-t" transform="translate(22,{(y0 + y1) / 2:.1f}) '
               f'rotate(-90)" text-anchor="middle">{e(fig["y"])}</text>')
    return _svg(w, h, "".join(out))


# ── 箱組み ─────────────────────────────────────
def blocks(fig):
    cols = fig.get("cols", 3)
    cw, ch, gap = 150, 46, 12
    rows = math.ceil(len(fig["cells"]) / cols)
    w = PAD * 2 + cols * cw + (cols - 1) * gap
    h = PAD * 2 + rows * ch + (rows - 1) * gap
    out = []
    for i, c in enumerate(fig["cells"]):
        x = PAD + (i % cols) * (cw + gap)
        y = PAD + (i // cols) * (ch + gap)
        out.append(f'<rect class="c-box c-box--{c.get("tone", "plain")}" x="{x}" y="{y}" '
                   f'width="{cw}" height="{ch}" rx="6"/>'
                   + _t(x + cw / 2, y + ch / 2 + 5, c["name"], "c-name"))
    return _svg(w, h, "".join(out))


KINDS = {"exchange": exchange, "lanes": lanes, "share": share, "bars": bars,
         "flow": flow, "matrix": matrix, "blocks": blocks}


def render_chart(fig):
    return KINDS[fig["kind"]](fig)


CSS = """
  .c-fig{display:block;max-width:100%;height:auto}
  .c-box{fill:var(--surface-2);stroke:var(--rule)}
  .c-box--focus{fill:var(--acc-bg);stroke:var(--acc)}
  .c-name{fill:var(--ink);font-family:var(--sans);font-size:12px}
  .c-label{fill:var(--ink-soft);font-family:var(--sans);font-size:11px}
  .c-num{fill:var(--ink);font-family:var(--mono);font-size:11px}
  .c-life{stroke:var(--rule);stroke-dasharray:3 3}
  .c-msg{stroke:var(--ink-faint);stroke-width:1.2}
  .c-msg--return{stroke-dasharray:4 3}
  .c-arrow{fill:var(--ink-faint)}
  .c-msg-t{fill:var(--ink-soft);font-family:var(--sans);font-size:10px}
  .c-note{fill:var(--warn-bg);stroke:var(--warn)}
  .c-note-t{fill:var(--warn);font-family:var(--sans);font-size:10px}
  .c-frame{fill:none;stroke:var(--acc);stroke-dasharray:4 3;opacity:.7}
  .c-frame-tab{fill:var(--acc-bg);stroke:var(--acc)}
  .c-tab-t{fill:var(--acc);font-family:var(--mono);font-size:9px}
  .c-track{fill:var(--rule-soft)}
  .c-bar{fill:var(--acc)}
  .c-bar--warn{fill:var(--warn)} .c-bar--soft{fill:var(--dead)}
  .c-bar-t{fill:#fff;font-family:var(--sans);font-size:10px}
  .c-axis{stroke:var(--rule)} .c-grid{stroke:var(--rule-soft)}
  .c-tick{stroke:var(--rule)}
  .c-tick-t{fill:var(--ink-faint);font-family:var(--sans);font-size:10px}
  .c-axis-t{fill:var(--ink-faint);font-family:var(--sans);font-size:10px}
  .c-arc{fill:none;stroke-width:24}
  .c-centre{fill:var(--ink);font-family:var(--sans);font-size:12px;font-weight:600}
  .c-chip{stroke:none}
  .c-ribbon{opacity:.45;stroke:none}
  .c-node{fill:var(--ink-faint)}
  .c-quad{fill:var(--acc-bg);opacity:.4}
  .c-quad-t{fill:var(--ink-faint);font-family:var(--sans);font-size:10px}
  .c-dot{fill:var(--acc)}
  .c-point-t{fill:var(--acc);font-family:var(--sans);font-size:10px}
  .c-tone-0{stroke:var(--acc);fill:var(--acc)}
  .c-tone-1{stroke:var(--warn);fill:var(--warn)}
  .c-tone-2{stroke:#7A4368;fill:#7A4368}
  .c-tone-3{stroke:var(--dead);fill:var(--dead)}
  .c-arc.c-tone-0,.c-arc.c-tone-1,.c-arc.c-tone-2,.c-arc.c-tone-3{fill:none}
"""
