"""論点を、見て選べる1枚へ組む。

文字だけで案を説明すると、読み手が頭の中で像を作ることになり、そこで解釈がぶれる。
だから案は成果物として組む ── 読み手は像を補完せず、見えているものだけで決められる。

使い方:
    from build_board import board, Option, write
    html = board(
        theme="ADR の構造",
        no=1, total=3,
        question="ADR の節の並びを、どういう順にするか",
        kept=[Option("決定を先頭のまま、反証の節を足す",
                     "決定 → それが間違っているとしたら何か → 実測 → 残る弱点",
                     "書き手が自分の決定を攻めることになり、書くのが重い")],
        dropped=[("判断の経路をたどる形", "承認の場で読み飛ばされる。経路は折りたたみで既に読める")],
        found="3案が2案になり、軸が変わった",
        pick=("A", "押し返されなければ承認されていた誤りが4件あった"))
    write(html, "/path/to/board.html")
"""
from __future__ import annotations

import html as _h
from dataclasses import dataclass

LETTERS = "ABCDEFGH"


@dataclass
class Option:
    """反証を通過した案。代償を必ず添える ── 代償が無いと選べない。

    対話の途中で案が変わったら、before と why を添える。そうすると案の名前が
    印になり、押すと「変更前」と「なぜ変えたか」が開く ── 履歴を別の場所へ
    追い出すと、いまの盤面と突き合わせながら読むことになる。変わった当人の
    すぐ隣に置けば、その手間が要らない。
    """
    name: str
    gist: str
    cost: str
    before: str | None = None
    why: str | None = None


def _blk(label: str, body: str, tone: str = "") -> str:
    return (f'<div class="blk {tone}"><div class="blk-h">{_h.escape(label)}</div>'
            f'<div class="blk-b">{body}</div></div>')


def _mark(text: str, before: str, why: str, deleted: bool = False) -> str:
    """変わった箇所の印。押すと、変更前と理由が開く。"""
    return (f'<mark class="chg{" del" if deleted else ""}" tabindex="0" role="button" '
            f'aria-expanded="false" data-b="{_h.escape(before, quote=True)}" '
            f'data-w="{_h.escape(why, quote=True)}">{text}</mark>')


def _opt(letter: str, name: str, gist: str, cost: str, out: bool = False,
         before: str | None = None, why: str | None = None) -> str:
    label = f"<b>{name}</b>"
    if before and why:
        label = _mark(label, before, why)
    return (f'<div class="opt{" out" if out else ""}"><span class="n">{letter}</span>'
            f'<span class="t">{label}{"　" + gist if gist else ""}'
            f'<span class="cost">{cost}</span></span></div>')


def board(theme: str, no: int, total: int, question: str,
          kept: list[Option], dropped: list[tuple[str, str]] | None = None,
          found: str | None = None, pick: tuple[str, str] | None = None) -> str:
    """論点1つを1枚に組む。

    Args:
        theme: このブレスト全体のテーマ。
        no / total: いま何番目の論点か。
        question: 論点そのもの。
        kept: 反証を通過した案。2つ以上あること ── 1つしか残らないなら、
            それは論点の立て方が誤っている。
        dropped: (落とした案の名前, 落とした理由) の並び。黙って消さない。
        found: 反証で軸そのものが変わったなら、その内容。無ければ省く。
        pick: (推す案の記号, その根拠)。

    Returns:
        1枚ぶんのHTML。

    Raises:
        ValueError: 残った案が2つ未満のとき。
    """
    if len(kept) < 2:
        raise ValueError("反証を通過した案が2つ未満。論点の立て方を見直す "
                         "── 1つしか残らないなら、それは選択ではない")
    parts = [_blk(f"論点 {no} / {total}", f"<b>{_h.escape(question)}</b>")]
    parts.append(_blk("反証を通過した案", "".join(
        _opt(LETTERS[i], o.name, o.gist, o.cost, before=o.before, why=o.why)
        for i, o in enumerate(kept))))
    if dropped:
        parts.append(_blk("落とした案と、その理由", "".join(
            _opt("×", _mark(f"<b>{n}</b>", "この案は残っていた", why, deleted=True), "", why,
                 out=True) for n, why in dropped), "out"))
    if found:
        parts.append(_blk("反証で分かったこと", found, "found"))
    if pick:
        parts.append(_blk("私の推し", f"<b>{pick[0]}</b>　{pick[1]}", "mine"))
    parts.append(_blk("あなた", '<span class="ph">記号を選ぶ'
                      '（どれでもなければ、そう言う）</span>', "you"))
    parts.append(_blk("決まり", '<span class="ph">選ばれた案が合意になり、次の論点へ</span>', "done"))
    return (f'<div class="hd"><div class="t">{_h.escape(theme)}'
            f'<small>色の付いた箇所を押すと、変更前と理由が開きます'
            f'（<span id="n">0</span>か所）</small></div>'
            f'<button id="all" type="button">すべて開く</button></div>'
            f'<div class="wrap"><h1>{_h.escape(question)}</h1>'
            f'<div class="spec">{"".join(parts)}</div></div>{SCRIPT}')


CSS = """
:root{ --ground:#F6F8F7; --surface:#FFFFFF; --ink:#171B23; --muted:#69737E;
       --accent:#16636B; --rule:#DFE5E4; --soft:#F1F5F4; --warn:#9A4A21; --out:#98A0A8;
       --mark:#F7E2BC; --markh:#F0CE92; --pop:#FDF6E9; --popline:#D9B77E; }
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --ground:#11161A; --surface:#191F24; --ink:#E7ECF0; --muted:#8C979F;
  --accent:#7FD1D9; --rule:#2A3239; --soft:#1E252B; --warn:#D9A382; --out:#6B747C;
  --mark:#4A3826; --markh:#5F4830; --pop:#241D14; --popline:#6E5738; } }
:root[data-theme="dark"]{ --ground:#11161A; --surface:#191F24; --ink:#E7ECF0; --muted:#8C979F;
  --accent:#7FD1D9; --rule:#2A3239; --soft:#1E252B; --warn:#D9A382; --out:#6B747C;
  --mark:#4A3826; --markh:#5F4830; --pop:#241D14; --popline:#6E5738; }
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-size:15px;line-height:1.85;
  font-family:"Noto Sans JP",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:52rem;margin:0 auto;padding:28px 24px 80px}
.eyebrow{font-size:11px;letter-spacing:.16em;color:var(--muted);margin:0 0 10px}
h1{font-family:"Shippori Mincho B1",serif;font-weight:600;font-size:clamp(24px,3.6vw,34px);
  line-height:1.35;margin:0;text-wrap:balance}
.spec{margin-top:34px;padding:22px;background:var(--soft);border:1px solid var(--rule);
  border-radius:4px;display:flex;flex-direction:column;gap:12px}
.blk{background:var(--surface);border:1px solid var(--rule);border-radius:3px;
  border-left:3px solid var(--rule);padding:12px 15px}
.blk.you{border-left-color:var(--accent);background:color-mix(in srgb,var(--accent) 5%,var(--surface))}
.blk.mine{border-left-color:var(--muted)}
.blk.found{border-left-color:var(--warn)}
.blk.out{border-left-color:var(--out)}
.blk.done{border-left-color:var(--accent)}
.blk-h{font-size:11px;letter-spacing:.1em;color:var(--muted);margin-bottom:6px}
.blk-b{font-size:13.5px;line-height:1.8}
.opt{display:flex;gap:10px;padding:7px 0;align-items:baseline}
.opt+.opt{border-top:1px dashed var(--rule)}
.opt .n{font-family:ui-monospace,monospace;font-size:11px;color:var(--accent);
  border:1px solid var(--accent);border-radius:2px;padding:0 5px;flex:none;line-height:1.7}
.opt.out .n{color:var(--out);border-color:var(--out)}
.opt.out b{color:var(--out);text-decoration:line-through}
.opt .t{font-size:13px;line-height:1.75}
.opt .cost{display:block;color:var(--muted);font-size:12px;margin-top:3px}
.ph{color:var(--muted);border-bottom:1px dashed var(--rule);padding-bottom:1px}

/* 変わった箇所の印。押すと開く */
mark.chg{background:var(--mark);color:var(--ink);border-radius:.15em;cursor:pointer;
  box-shadow:-.2em 0 0 var(--mark),.2em 0 0 var(--mark);border-bottom:2px solid var(--warn)}
mark.chg:hover,mark.chg:focus{background:var(--markh);
  box-shadow:-.2em 0 0 var(--markh),.2em 0 0 var(--markh);outline:none}
mark.chg:focus-visible{outline:2px solid var(--warn);outline-offset:2px}
mark.chg::after{content:"▸";font-size:.72em;color:var(--warn);margin-left:.3em;font-weight:700}
mark.chg[aria-expanded="true"]::after{content:"▾"}
mark.chg.del{background:none;box-shadow:none;color:var(--out);border-bottom:1px dashed var(--out)}
mark.chg.del b{text-decoration:line-through}

.pop[hidden]{display:none}
.pop{display:block;background:var(--pop);border:1px solid var(--popline);
  border-left:3px solid var(--warn);border-radius:.3rem;padding:.7rem .9rem;margin:.6rem 0 .2rem;
  font-size:12.5px;line-height:1.75;white-space:normal}
.pop b{display:block;font-size:10.5px;letter-spacing:.14em;color:var(--warn);margin-bottom:.3rem}
.pop .why{display:block;margin-top:.6rem;padding-top:.6rem;border-top:1px solid var(--popline)}
.pop .why b{color:var(--accent)}

.hd{position:sticky;top:0;background:var(--ground);border-bottom:1px solid var(--rule);
  padding:.8rem 24px;display:flex;align-items:center;gap:1rem;flex-wrap:wrap;z-index:9}
.hd .t{font-family:"Shippori Mincho B1",serif;font-weight:600;font-size:15px;flex:1;min-width:12rem}
.hd .t small{display:block;font-family:"Noto Sans JP",sans-serif;font-weight:400;
  font-size:12px;color:var(--muted);margin-top:.1rem}
.hd button{font:inherit;font-size:12.5px;font-weight:500;padding:.3rem .85rem;border-radius:.3rem;
  cursor:pointer;background:var(--surface);color:var(--ink);border:1px solid var(--rule)}
.hd button:hover{background:var(--markh)}
.hd button:focus-visible{outline:2px solid var(--warn);outline-offset:2px}
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
    m.closest('.opt, .blk-b').appendChild(p);
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
        'family=Noto+Sans+JP:wght@400;500&family=Shippori+Mincho+B1:wght@600&display=swap">')


def write(body: str, path: str, title: str) -> str:
    """1枚を、そのまま公開できるHTMLとして書き出す。"""
    import pathlib
    page = f"<title>{_h.escape(title)}</title>{HEAD}<style>{CSS}</style>{body}"
    pathlib.Path(path).write_text(page, encoding="utf-8")
    return page
