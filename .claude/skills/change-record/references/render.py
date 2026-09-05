#!/usr/bin/env python3
"""マークダウンを描画し、変更箇所に印を付ける。

  python3 render.py <file.md> <marks.json>  > body.html

marks.json の形。find は描画後のHTMLに現れる文字列。
  [{"find": "...", "before": "変更前の原文", "why": "なぜ変えたか"}, ...]

当たらなかった find は標準エラーに出す。黙って落とさない。
"""
import re, html, io, sys, json

def inline(t):
    t = html.escape(t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    return t.replace('&lt;br&gt;', '<br>').replace('&lt;br/&gt;', '<br>')

def render(md):
    out, L, i = [], md.split('\n'), 0
    while i < len(L):
        l = L[i]
        if l.startswith('```'):
            lang = l[3:].strip(); j = i + 1; b = []
            while j < len(L) and not L[j].startswith('```'):
                b.append(L[j]); j += 1
            cls = 'mermaid' if lang == 'mermaid' else 'code'
            out.append(f'<pre class="{cls}">' + html.escape('\n'.join(b)) + '</pre>')
            i = j + 1; continue
        m = re.match(r'^(#{1,4})\s+(.*)', l)
        if m:
            n = len(m.group(1))
            out.append(f'<h{n}>{inline(m.group(2))}</h{n}>'); i += 1; continue
        if l.startswith('|'):
            rows = []
            while i < len(L) and L[i].startswith('|'):
                rows.append(L[i]); i += 1
            cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
            def sep(row):
                return all(re.match(r'^:?-{2,}:?$', c.strip()) for c in row if c.strip()) \
                       and any(c.strip() for c in row)
            body = [c for c in cells if not sep(c)]
            t = '<div class="wrap"><table>'
            if len(body) > 1:
                t += '<tr>' + ''.join(f'<th>{inline(c)}</th>' for c in body[0]) + '</tr>'
            for r in body[1:]:
                t += '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
            out.append(t + '</table></div>'); continue
        if l.startswith('>'):
            b = []
            while i < len(L) and L[i].startswith('>'):
                b.append(L[i][1:].strip()); i += 1
            out.append('<blockquote>' + inline('<br>'.join(b)) + '</blockquote>'); continue
        if l.strip() == '---':
            out.append('<hr>'); i += 1; continue
        if not l.strip():
            i += 1; continue
        b = []
        while i < len(L) and L[i].strip() and not L[i].startswith(('|', '>', '#', '```')) \
              and L[i].strip() != '---':
            b.append(L[i]); i += 1
        out.append('<p>' + inline('<br>'.join(b)) + '</p>')
    return '\n'.join(out)

def outside_pre(h):
    """<pre> の外だけを、印を付けてよい範囲として返す。

    コードと図の中に印を差し込むと、その中身が壊れる。
    mermaid は差し込んだ時点で描画されなくなる。
    """
    spans, i = [], 0
    while True:
        a = h.find("<pre", i)
        if a < 0:
            spans.append((i, len(h))); break
        spans.append((i, a))
        b = h.find("</pre>", a)
        i = len(h) if b < 0 else b + 6
    return spans


def mark(h, marks):
    hit = 0
    for c in marks:
        f = c["find"]
        if f not in h:
            print("  当たらず: " + f[:60], file=sys.stderr); continue
        if not any(h.find(f, s, e) >= 0 for s, e in outside_pre(h)):
            print("  コードか図の中にしかない: " + f[:60], file=sys.stderr); continue
        a = html.escape(c.get("before", ""), quote=True)
        w = html.escape(c.get("why", ""), quote=True)
        if not w:
            print("  なぜが無い: " + f[:60], file=sys.stderr)
        at = next(h.find(f, s, e) for s, e in outside_pre(h) if h.find(f, s, e) >= 0)
        h = (h[:at] + f'<mark class="chg" tabindex="0" role="button" '
                      f'aria-expanded="false" data-b="{a}" data-w="{w}">{f}</mark>'
             + h[at + len(f):])
        hit += 1
    print(f"  {hit}/{len(marks)} 件に印を付けた", file=sys.stderr)
    return h

if __name__ == "__main__":
    md = io.open(sys.argv[1], encoding="utf-8").read()
    ms = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else []
    print(mark(render(md), ms))
