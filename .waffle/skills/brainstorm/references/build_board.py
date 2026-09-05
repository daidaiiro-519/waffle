"""論点を、見て選べる1枚へ組む。

文字だけで案を説明すると、読み手が頭の中で像を作ることになり、そこで解釈がぶれる。
だから案は成果物として組む ── 読み手は像を補完せず、見えているものだけで決められる。

散文で並べない。**案は表で、帰結は表で、理由は連鎖で、図は図で置く。**
情報の型が、表現の形を決める。

使い方:
    from build_board import board, Option, Table, write
    html = board(
        theme="ADR の構造", no=1, total=3,
        question="ADR の節の並びを、どういう順にするか",
        note="論点5つのうち3つが決着し、1つ新しく出た。",
        figures=[(SVG, "図の読み方")],
        kept=[Option("決定を先頭のまま、反証の節を足す",
                     "決定 → 反証 → 実測 → 残る弱点",
                     "書き手が自分の決定を攻めることになる")],
        tables=[Table("この選択が置くもの", ["段1", "段2"],
                      {"A": ["契約が3つ増える", "増えない"]})],
        dropped=[("判断の経路をたどる形", "承認の場で読み飛ばされる")],
        found=["3案が2案になった", "軸が変わった"],
        pick=("A", [("測った", "押し返されなければ承認されていた誤りが4件あった"),
                    ("結論", "A ── 決定を先頭のまま、反証の節を足す")]))
    write(html, "/path/to/board.html", "節の同一性")
"""
from __future__ import annotations

import html as _h
from dataclasses import dataclass, field

LETTERS = "ABCDEFGH"


@dataclass
class Option:
    """反証を通過した案。代償を必ず添える ── 代償が無いと選べない。

    name / gist / cost は、表の1行に収まる長さで書く。
    説明が1行に収まらないなら、それは図か、別の表になるものである。

    対話の途中で案が変わったら、before と why を添える。そうすると案の名前が
    印になり、押すと「変更前」と「なぜ変えたか」が開く ── 履歴を別の場所へ
    追い出すと、いまの盤面と突き合わせながら読むことになる。
    """
    name: str
    gist: str
    cost: str
    before: str | None = None
    why: str | None = None


@dataclass
class Table:
    """案ごとの帰結を並べる表。列は呼び出し側が決める。

    rows は {案の記号: [その案の各列の値]}。案の記号は kept の並び順（A・B・C…）。
    """
    caption: str
    columns: list[str]
    rows: dict[str, list[str]]
    lead: str | None = None


def _mark(text: str, before: str, why: str, deleted: bool = False) -> str:
    """変わった箇所の印。押すと、変更前と理由が開く。"""
    return (f'<mark class="chg{" del" if deleted else ""}" tabindex="0" role="button" '
            f'aria-expanded="false" data-b="{_h.escape(before, quote=True)}" '
            f'data-w="{_h.escape(why, quote=True)}">{text}</mark>')


def _sec(no: int, title: str, body: str) -> str:
    return f'<h2><span class="sn">{no}</span>{_h.escape(title)}</h2>{body}'


def _table(head: list[str], rows: list[list[str]], cls: str = "") -> str:
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table class="{cls}"><tr>{h}</tr>{b}</table></div>'


def _key(letter: str, tone: str = "") -> str:
    return f'<span class="n {tone}">{letter}</span>'


def board(theme: str, no: int, total: int, question: str,
          kept: list[Option], dropped: list[tuple[str, str]] | None = None,
          found: list[str] | None = None,
          pick: tuple[str, list[tuple[str, str]]] | None = None,
          figures: list[tuple[str, str]] | None = None,
          tables: list[Table] | None = None,
          note: str | None = None) -> str:
    """論点1つを1枚に組む。

    Args:
        theme: このブレスト全体のテーマ。
        no / total: いま何番目の論点か。
        question: 論点そのもの。
        kept: 反証を通過した案。2つ以上あること ── 1つしか残らないなら、
            それは論点の立て方が誤っている。表の1行として並ぶ。
        dropped: (落とした案の名前, 落とした理由) の並び。黙って消さない。
        found: 反証で分かったことを、1つずつ短く。散文にしない。
        pick: (推す案の記号, 理由の連鎖)。連鎖は (段の種別, 一文) の並びで、
            段の種別は「測った」「確かめていない」「だから」「一方で」
            「結論」「引き受ける」「反証」から選ぶ。
        figures: (SVG, 図の読み方) の並び。案の違いは、まず図で見せる。
        tables: 案ごとの帰結の表。列は呼び出し側が決める。
        note: 盤面の冒頭に置く、いまの状態の1〜2文。

    Returns:
        1枚ぶんのHTML。

    Raises:
        ValueError: 残った案が2つ未満のとき。
    """
    if len(kept) < 2:
        raise ValueError("反証を通過した案が2つ未満。論点の立て方を見直す "
                         "── 1つしか残らないなら、それは選択ではない")
    secs, n = [], 0

    if figures:
        n += 1
        secs.append(_sec(n, "案の違いを、図で", "".join(
            f'<figure>{svg}<figcaption>{cap}</figcaption></figure>'
            for svg, cap in figures)))

    n += 1
    rows = []
    for i, o in enumerate(kept):
        name = f"<b>{o.name}</b>"
        if o.before and o.why:
            name = _mark(name, o.before, o.why)
        rows.append([_key(LETTERS[i]), name, o.gist, f'<span class="cost">{o.cost}</span>'])
    secs.append(_sec(n, "反証を通過した案", _table(["", "案", "中身", "代償"], rows, "opts")))

    for t in tables or []:
        n += 1
        lead = f'<p class="lead">{t.lead}</p>' if t.lead else ""
        rows = [[_key(k)] + list(v) for k, v in t.rows.items()]
        secs.append(_sec(n, t.caption, lead + _table([""] + t.columns, rows)))

    if dropped:
        n += 1
        rows = [[_key("×", "out"),
                 _mark(f"<b>{d}</b>", "この案は残っていた", w, deleted=True), w]
                for d, w in dropped]
        secs.append(_sec(n, "落とした案と、その理由",
                         _table(["", "案", "落とした理由"], rows, "out")))

    if found:
        n += 1
        secs.append(_sec(n, "反証で分かったこと",
                         "<ul class='found'>" + "".join(f"<li>{f}</li>" for f in found) + "</ul>"))

    if pick:
        n += 1
        letter, chain = pick
        rows = [[f'<span class="st">{_h.escape(s)}</span>', t] for s, t in chain]
        secs.append(_sec(n, "私の推しと、その連鎖",
                         f'<p class="lead">推す案は <b class="pickn">{_h.escape(letter)}</b> である。</p>'
                         + _table(["段", "中身"], rows, "chain")))

    n += 1
    secs.append(_sec(n, "あなたの見解",
                     '<div class="you">✏️　記号を選ぶ（どれでもなければ、そう言う）</div>'))
    n += 1
    secs.append(_sec(n, "決まり",
                     '<div class="done">選ばれた案が合意になり、次の論点へ</div>'))

    head = (f'<div class="hd"><div class="t">{_h.escape(theme)}'
            f'<small>色の付いた箇所を押すと、変更前と理由が開きます'
            f'（<span id="n">0</span>か所）</small></div>'
            f'<button id="all" type="button">すべて開く</button></div>')
    top = (f'<p class="eyebrow">論点 {no} / {total}</p>'
           f'<h1>{_h.escape(question)}</h1>'
           + (f'<div class="note">{note}</div>' if note else ""))
    return f'{head}<main>{top}{"".join(secs)}</main>{SCRIPT}'


CSS = """
:root{ --paper:#FBFAF7; --ink:#191C1F; --muted:#6C7076; --rule:#E3DFD7; --panel:#F4F1EA;
  --panelrule:#DAD4C8; --key:#2F4858; --add:#A6543A; --out:#8A8479;
  --mark:#F7E2BC; --markh:#F0CE92; --pop:#FDF6E9; --popline:#D9B77E; }
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#15171A; --ink:#E8E5DF; --muted:#9AA0A8; --rule:#2C3036; --panel:#1D2024;
  --panelrule:#333940; --key:#8FB4C8; --add:#E0A184; --out:#7E838B;
  --mark:#4A3826; --markh:#5F4830; --pop:#241D14; --popline:#6E5738; } }
:root[data-theme="dark"]{ --paper:#15171A; --ink:#E8E5DF; --muted:#9AA0A8; --rule:#2C3036;
  --panel:#1D2024; --panelrule:#333940; --key:#8FB4C8; --add:#E0A184; --out:#7E838B;
  --mark:#4A3826; --markh:#5F4830; --pop:#241D14; --popline:#6E5738; }
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-size:15.5px;line-height:1.85;
  font-family:"Noto Sans JP",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:53rem;margin:0 auto;padding:0 1.5rem 5rem}
.eyebrow{font-size:11px;letter-spacing:.16em;color:var(--muted);margin:1.6rem 0 .5rem}
h1{font-family:"Noto Serif JP",serif;font-weight:700;font-size:clamp(23px,3.4vw,31px);
  line-height:1.35;margin:0;padding-bottom:.6rem;border-bottom:2px solid var(--key);text-wrap:balance}
h2{font-family:"Noto Serif JP",serif;font-weight:600;font-size:1.2rem;margin:2.6rem 0 1rem;
  padding-bottom:.4rem;border-bottom:1px solid var(--rule);display:flex;align-items:baseline;gap:.6rem}
h2 .sn{font-family:ui-monospace,monospace;font-size:.72rem;color:var(--muted);font-weight:400}
p{margin:0 0 1rem}
.note{background:var(--panel);border:1px solid var(--panelrule);border-left:3px solid var(--key);
  border-radius:.3rem;padding:.9rem 1.1rem;margin:1.2rem 0 0;font-size:.9rem}
.lead{font-size:.92rem;margin-bottom:.7rem}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.86rem;margin:0}
th,td{text-align:left;vertical-align:top;padding:.6rem .7rem;border-bottom:1px solid var(--rule)}
th{font-weight:700;font-size:.72rem;letter-spacing:.05em;color:var(--muted);
  border-bottom:1.5px solid var(--rule);white-space:nowrap}
th:first-child,td:first-child{width:1.9rem;padding-right:0}
.n{font-family:ui-monospace,monospace;font-size:11px;color:var(--key);border:1px solid var(--key);
  border-radius:2px;padding:0 5px;line-height:1.7;display:inline-block}
.n.out{color:var(--out);border-color:var(--out)}
table.out td{color:var(--muted)}
table.out b{color:var(--out);text-decoration:line-through}
.cost{color:var(--muted)}
.st{font-size:.7rem;font-weight:700;letter-spacing:.06em;color:var(--add);border:1px solid var(--add);
  border-radius:2px;padding:.05em .45em;white-space:nowrap;display:inline-block}
table.chain th:first-child,table.chain td:first-child{width:6.5rem;padding-right:.6rem}
.pickn{font-family:ui-monospace,monospace;color:var(--key);border:1px solid var(--key);
  border-radius:2px;padding:0 .35em}
ul.found{margin:0;padding-left:1.1rem;font-size:.92rem}
ul.found li{margin-bottom:.5rem}
figure{margin:0 0 1.2rem}
figure+figure{margin-top:1.6rem;padding-top:1.4rem;border-top:1px dashed var(--rule)}
figure svg{display:block;width:100%;height:auto;color:var(--ink);
  border:1px solid var(--rule);border-radius:.35rem;background:var(--panel)}
figcaption{font-size:.83rem;line-height:1.75;color:var(--muted);margin-top:.5rem}
.you{border:1px dashed var(--key);border-radius:.3rem;padding:.9rem 1.1rem;color:var(--muted);
  font-size:.9rem;background:color-mix(in srgb,var(--key) 5%,var(--paper))}
.done{border:1px dashed var(--panelrule);border-radius:.3rem;padding:.9rem 1.1rem;
  color:var(--muted);font-size:.9rem}

mark.chg{background:var(--mark);color:var(--ink);border-radius:.15em;cursor:pointer;
  box-shadow:-.2em 0 0 var(--mark),.2em 0 0 var(--mark);border-bottom:2px solid var(--add)}
mark.chg:hover,mark.chg:focus{background:var(--markh);
  box-shadow:-.2em 0 0 var(--markh),.2em 0 0 var(--markh);outline:none}
mark.chg:focus-visible{outline:2px solid var(--add);outline-offset:2px}
mark.chg::after{content:"▸";font-size:.72em;color:var(--add);margin-left:.3em;font-weight:700}
mark.chg[aria-expanded="true"]::after{content:"▾"}
mark.chg.del{background:none;box-shadow:none;color:var(--out);border-bottom:1px dashed var(--out)}
mark.chg.del b{text-decoration:line-through}

.pop[hidden]{display:none}
.pop{display:block;background:var(--pop);border:1px solid var(--popline);
  border-left:3px solid var(--add);border-radius:.3rem;padding:.7rem .9rem;margin:.6rem 0 .2rem;
  font-size:.82rem;line-height:1.75;white-space:normal;font-weight:400}
.pop b{display:block;font-size:.66rem;letter-spacing:.14em;color:var(--add);margin-bottom:.3rem}
.pop .why{display:block;margin-top:.6rem;padding-top:.6rem;border-top:1px solid var(--popline)}
.pop .why b{color:var(--key)}

.hd{position:sticky;top:0;background:var(--paper);border-bottom:1px solid var(--rule);
  padding:.8rem 1.5rem;display:flex;align-items:center;gap:1rem;flex-wrap:wrap;z-index:9}
.hd .t{font-family:"Noto Serif JP",serif;font-weight:700;font-size:1rem;flex:1;min-width:12rem}
.hd .t small{display:block;font-family:"Noto Sans JP",sans-serif;font-weight:400;
  font-size:.78rem;color:var(--muted);margin-top:.1rem}
.hd button{font:inherit;font-size:.82rem;font-weight:700;padding:.35rem .9rem;border-radius:.3rem;
  cursor:pointer;background:var(--panel);color:var(--ink);border:1px solid var(--panelrule)}
.hd button:hover{background:var(--markh)}
.hd button:focus-visible{outline:2px solid var(--add);outline-offset:2px}
"""

SCRIPT = """
<script>
(function(){
  const marks = [...document.querySelectorAll('mark.chg')];
  document.getElementById('n').textContent = marks.length;
  function panel(m){
    const p = document.createElement('div');
    p.className = 'pop'; p.hidden = true;
    p.innerHTML = '<b>変更前</b>' + m.dataset.b +
                  '<span class="why"><b>なぜ変えたか</b>' + m.dataset.w + '</span>';
    (m.closest('td') || m.parentNode).appendChild(p);
    return p;
  }
  marks.forEach(m => {
    const p = panel(m);
    const toggle = () => {
      const open = p.hidden;
      p.hidden = !open;
      m.setAttribute('aria-expanded', String(open));
    };
    m.addEventListener('click', toggle);
    m.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    });
  });
  const all = document.getElementById('all');
  all.addEventListener('click', () => {
    const open = all.textContent === 'すべて開く';
    document.querySelectorAll('.pop').forEach(p => p.hidden = !open);
    marks.forEach(m => m.setAttribute('aria-expanded', String(open)));
    all.textContent = open ? 'すべて閉じる' : 'すべて開く';
  });
})();
</script>
"""

HEAD = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@600;700&display=swap">')


def write(body: str, path: str, title: str) -> str:
    """1枚を、そのまま公開できるHTMLとして書き出す。"""
    import pathlib
    page = f"<title>{_h.escape(title)}</title>{HEAD}<style>{CSS}</style>{body}"
    pathlib.Path(path).write_text(page, encoding="utf-8")
    return page
