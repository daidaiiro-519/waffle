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
import re
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


@dataclass
class Topic:
    """1つの論点。deck() に並べると、タブ1枚になる。

    ブレストは複数の論点が絡むので、決着した論点も同じ1枚に置く ── 別々の
    ページに散らすと、後の論点が前の決着を前提にしていることが見えなくなる。

    status は「未」「新規」「決着」のいずれか。決着した論点は kept を持たず、
    decision（決定・理由・次にすること）と、必要なら extras（節の見出しと中身）だけを持つ。
    """
    no: int
    label: str
    question: str
    status: str = "未"
    answer: str = ""
    note: str | None = None
    figures: list[tuple[str, str]] = field(default_factory=list)
    kept: list[Option] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    dropped: list[tuple[str, str]] = field(default_factory=list)
    found: list[str] = field(default_factory=list)
    pick: tuple[str, list[tuple[str, str]]] | None = None
    decision: list[tuple[str, str]] = field(default_factory=list)
    extras: list[tuple[str, str]] = field(default_factory=list)


def _sections(t: Topic) -> str:
    """論点1つぶんの節を、番号を振って組む。"""
    if len(t.kept) == 1:
        raise ValueError(f"論点{t.no}: 反証を通過した案が1つしかない。論点の立て方を見直す "
                         "── 1つしか残らないなら、それは選択ではない。"
                         "まだ案を出していない論点は、案を空にして置く")
    secs, n = [], 0
    figs = "".join(f'<figure>{svg}<figcaption>{cap}</figcaption></figure>'
                   for svg, cap in t.figures)
    if t.figures and not t.pick:
        n += 1
        secs.append(_sec(n, "図で見る", figs))
    if t.kept:
        n += 1
        rows = []
        for i, o in enumerate(t.kept):
            name = f"<b>{o.name}</b>"
            if o.before and o.why:
                name = _mark(name, o.before, o.why)
            rows.append([_key(LETTERS[i]), name, o.gist, f'<span class="cost">{o.cost}</span>'])
        secs.append(_sec(n, "反証を通過した案", _table(["", "案", "中身", "代償"], rows, "opts")))
    for tb in t.tables:
        n += 1
        lead = f'<p class="lead">{tb.lead}</p>' if tb.lead else ""
        rows = [[_key(k)] + list(v) for k, v in tb.rows.items()]
        secs.append(_sec(n, tb.caption, lead + _table([""] + tb.columns, rows)))
    if t.dropped:
        n += 1
        rows = [[_key("×", "out"),
                 _mark(f"<b>{d}</b>", "この案は残っていた", w, deleted=True), w]
                for d, w in t.dropped]
        secs.append(_sec(n, "落とした案と、その理由",
                         _table(["", "案", "落とした理由"], rows, "out")))
    if t.found:
        n += 1
        secs.append(_sec(n, "反証で分かったこと",
                         "<ul class='found'>" + "".join(f"<li>{f}</li>" for f in t.found) + "</ul>"))
    if t.pick:
        n += 1
        letter, chain = t.pick
        # 記号はバッジが持つので、本文の「A ── 」は落とす
        conc = [re.sub(r'^(<b>)?[A-H]\s*──\s*', r'\1', txt)
                for st, txt in chain if st == "結論"]
        why = [(st, txt) for st, txt in chain if st in ("測った", "確かめていない", "定義から",
                                                       "だから", "一方で", "合わせると")]
        cost = [txt for st, txt in chain if st == "引き受ける"]
        weak = [(st, txt) for st, txt in chain if st in ("反証", "崩れる条件")]
        body = (f'<div class="concl"><span class="n big">{_h.escape(letter)}</span>'
                f'<div>{"".join(f"<p>{c}</p>" for c in conc)}</div></div>')
        if why:
            if not any(st in ("測った", "確かめていない", "定義から") for st, _ in why):
                raise ValueError(f"論点{t.no}: 根拠に前提が無い。「だから」「一方で」は"
                                 "前の段から次へ渡す接続であって、それ自体は事実ではない ── "
                                 "「測った」「定義から」「確かめていない」のどれかを最低1つ置く")
            # 種別は書き手の規律であって、読み手に覚えさせる記号ではない。
            # 接続だけを、ふつうの日本語として文の頭へ置く。
            lead = {"だから": "だから、", "一方で": "一方で、", "合わせると": "合わせると、",
                    "確かめていない": "確かめていないが、"}
            body += ('<h3>なぜそう言えるか</h3><ol class="why">'
                     + "".join(f'<li>{lead.get(st, "")}{txt}</li>' for st, txt in why)
                     + '</ol>')
        if figs:
            body += f'<h3>図で見る</h3>{figs}'
        if cost:
            body += ('<h3>引き受けること</h3><ul class="found">'
                     + "".join(f"<li>{c}</li>" for c in cost) + "</ul>")
        if weak:
            body += ('<h3>まだ崩れうるところ</h3><ul class="found">'
                     + "".join(f"<li><span class='st'>{_h.escape(st)}</span>　{txt}</li>"
                               for st, txt in weak) + "</ul>")
        secs.append(_sec(n, "私の推し", body))
    for title, body in t.extras:
        n += 1
        secs.append(_sec(n, title, body))
    if t.decision:
        n += 1
        secs.append(_sec(n, "決まり", _table(["", ""], [
            [f'<span class="st done">{_h.escape(k)}</span>', v] for k, v in t.decision], "chain")))
    else:
        n += 1
        secs.append(_sec(n, "あなたの見解",
                         '<div class="you">✏️　記号を選ぶ（どれでもなければ、そう言う）</div>'))
        n += 1
        secs.append(_sec(n, "決まり",
                         '<div class="next">選ばれた案が合意になり、次の論点へ</div>'))
    head = (f'<p class="eyebrow">論点 {t.no}</p><h1>{_h.escape(t.question)}</h1>'
            + (f'<div class="note">{t.note}</div>' if t.note else ""))
    return head + "".join(secs)


def deck(theme: str, topics: list[Topic], intro: str | None = None,
         extras: list[tuple[str, str]] | None = None) -> str:
    """複数の論点を、タブで1枚にまとめる。

    先頭のタブは「現在地」── どの論点が決着し、どれが開いているかの一覧である。
    ブレストは論点が互いに前提になるので、別ページへ散らさない。
    """
    rows = [[f'<span class="n">{t.no}</span>', _h.escape(t.question),
             f'<span class="st {"done" if t.status == "決着" else "open"}">{_h.escape(t.status)}</span>',
             t.answer] for t in topics]
    now = (f'<p class="eyebrow">現在地</p><h1>{_h.escape(theme)}</h1>'
           + (f'<div class="note">{intro}</div>' if intro else "")
           + _sec(1, "論点の現在地", _table(["#", "論点", "状態", "いまの答え"], rows))
           + "".join(_sec(i, ti, bo) for i, (ti, bo) in enumerate(extras or [], start=2)))
    tabs = ['<button role="tab" aria-selected="true" data-t="p0">現在地</button>']
    panels = [f'<section id="p0" role="tabpanel">{now}</section>']
    for i, t in enumerate(topics, start=1):
        cls = "done" if t.status == "決着" else "open"
        tabs.append(f'<button role="tab" aria-selected="false" data-t="p{i}">'
                    f'<span class="tn">{t.no}</span>{_h.escape(t.label)}'
                    f'<span class="st {cls}">{_h.escape(t.status)}</span></button>')
        panels.append(f'<section id="p{i}" role="tabpanel" hidden>{_sections(t)}</section>')
    head = (f'<div class="hd"><div class="t">{_h.escape(theme)}'
            f'<small>色の付いた箇所を押すと、変更前と理由が開きます'
            f'（<span id="n">0</span>か所）</small></div>'
            f'<button id="all" type="button">すべて開く</button></div>'
            f'<div class="tabs" role="tablist">{"".join(tabs)}</div>')
    return f'{head}<main>{"".join(panels)}</main>{SCRIPT}'


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
        pick: (推す案の記号, 理由の連鎖)。連鎖は (その文が何であるか, 一文) の並び。
            「測った」は出所のある観測、「定義から」は語の定義や既に合意した決定から
            従うこと、「確かめていない」は検証していない前提、
            「だから」「一方で」「合わせると」は前の段から次へ渡す接続、
            「結論」は推す案、「引き受ける」は代償、「反証」は既に観測されている
            不利な事実である。**接続だけを並べない** ── 前提が無い推論になるので、
            「測った」「定義から」「確かめていない」のどれかを最低1つ置く。
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
                     '<div class="next">選ばれた案が合意になり、次の論点へ</div>'))

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
  --mark:#F7E2BC; --markh:#F0CE92; --pop:#FDF6E9; --popline:#D9B77E;
  --soft:#8FA3AE; --del:#8A8479; }
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#15171A; --ink:#E8E5DF; --muted:#9AA0A8; --rule:#2C3036; --panel:#1D2024;
  --panelrule:#333940; --key:#8FB4C8; --add:#E0A184; --out:#7E838B;
  --mark:#4A3826; --markh:#5F4830; --pop:#241D14; --popline:#6E5738;
  --soft:#5D6B75; --del:#7E838B; } }
:root[data-theme="dark"]{ --paper:#15171A; --ink:#E8E5DF; --muted:#9AA0A8; --rule:#2C3036;
  --panel:#1D2024; --panelrule:#333940; --key:#8FB4C8; --add:#E0A184; --out:#7E838B;
  --mark:#4A3826; --markh:#5F4830; --pop:#241D14; --popline:#6E5738;
  --soft:#5D6B75; --del:#7E838B; }
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
ol.why{margin:0;padding-left:1.4rem;font-size:.92rem}
ol.why li{margin-bottom:.55rem;line-height:1.85}
.pickn{font-family:ui-monospace,monospace;color:var(--key);border:1px solid var(--key);
  border-radius:2px;padding:0 .35em}
.concl{display:flex;gap:.9rem;align-items:flex-start;background:color-mix(in srgb,var(--key) 6%,var(--paper));
  border:1px solid var(--panelrule);border-left:3px solid var(--key);border-radius:.3rem;padding:1rem 1.1rem;margin:0 0 1.4rem}
.concl p{margin:0;font-size:1.02rem;line-height:1.75;font-weight:700}
.concl p+p{margin-top:.5rem;font-weight:400;font-size:.92rem;color:var(--muted)}
.n.big{font-size:1rem;padding:.15em .6em;border-width:2px;flex:none}
h3{font-size:.95rem;font-weight:700;margin:1.8rem 0 .6rem;color:var(--muted)}
ul.found{margin:0;padding-left:1.1rem;font-size:.92rem}
ul.found li{margin-bottom:.5rem}
figure{margin:0 0 1.2rem}
figure+figure{margin-top:1.6rem;padding-top:1.4rem;border-top:1px dashed var(--rule)}
figure svg{display:block;width:100%;height:auto;color:var(--ink);
  border:1px solid var(--rule);border-radius:.35rem;background:var(--panel)}
figcaption{font-size:.83rem;line-height:1.75;color:var(--muted);margin-top:.5rem}
.you{border:1px dashed var(--key);border-radius:.3rem;padding:.9rem 1.1rem;color:var(--muted);
  font-size:.9rem;background:color-mix(in srgb,var(--key) 5%,var(--paper))}
.next{border:1px dashed var(--panelrule);border-radius:.3rem;padding:.9rem 1.1rem;
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

/* 論点のタブ。ブレストは論点が互いの前提になるので、1枚に束ねる */
.tabs{position:sticky;top:3.4rem;background:var(--paper);border-bottom:1px solid var(--rule);
  padding:.45rem 1.5rem;display:flex;gap:.4rem;overflow-x:auto;z-index:8;scrollbar-width:thin}
.tabs button{font:inherit;font-size:.82rem;padding:.35rem .8rem;border-radius:.3rem;cursor:pointer;
  background:none;color:var(--muted);border:1px solid transparent;white-space:nowrap;
  display:flex;align-items:center;gap:.4rem}
.tabs button:hover{background:var(--panel);color:var(--ink)}
.tabs button[aria-selected="true"]{background:var(--panel);color:var(--ink);
  border-color:var(--panelrule);font-weight:700}
.tabs button[aria-selected="true"] .tn{color:var(--key)}
.tabs .tn{font-family:ui-monospace,monospace;font-size:.72rem;color:var(--muted)}
.tabs button:focus-visible{outline:2px solid var(--add);outline-offset:2px}
.st.done{color:var(--key);border-color:var(--key)}
.st.open{color:var(--add);border-color:var(--add)}
section[role="tabpanel"][hidden]{display:none}
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
  const tabs = [...document.querySelectorAll('.tabs button')];
  function show(id){
    tabs.forEach(b => {
      const on = b.dataset.t === id;
      b.setAttribute('aria-selected', String(on));
      document.getElementById(b.dataset.t).hidden = !on;
    });
    history.replaceState(null, '', '#' + id);
    window.scrollTo({top: 0});
  }
  tabs.forEach((b, i) => {
    b.addEventListener('click', () => show(b.dataset.t));
    b.addEventListener('keydown', e => {
      const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (d) { e.preventDefault(); const t = tabs[(i + d + tabs.length) % tabs.length];
               t.focus(); show(t.dataset.t); }
    });
  });
  if (tabs.length && document.getElementById(location.hash.slice(1))) show(location.hash.slice(1));

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
