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
    """反証を通過した案。代償を必ず添える ── 代償が無いと選べない。"""
    name: str
    gist: str
    cost: str


def _blk(label: str, body: str, tone: str = "") -> str:
    return (f'<div class="blk {tone}"><div class="blk-h">{_h.escape(label)}</div>'
            f'<div class="blk-b">{body}</div></div>')


def _opt(letter: str, name: str, gist: str, cost: str, out: bool = False) -> str:
    return (f'<div class="opt{" out" if out else ""}"><span class="n">{letter}</span>'
            f'<span class="t"><b>{name}</b>{"　" + gist if gist else ""}'
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
        _opt(LETTERS[i], o.name, o.gist, o.cost) for i, o in enumerate(kept))))
    if dropped:
        parts.append(_blk("落とした案と、その理由", "".join(
            _opt("×", n, "", why, out=True) for n, why in dropped), "out"))
    if found:
        parts.append(_blk("反証で分かったこと", found, "found"))
    if pick:
        parts.append(_blk("私の推し", f"<b>{pick[0]}</b>　{pick[1]}", "mine"))
    parts.append(_blk("あなた", '<span class="ph">記号を選ぶ'
                      '（どれでもなければ、そう言う）</span>', "you"))
    parts.append(_blk("決まり", '<span class="ph">選ばれた案が合意になり、次の論点へ</span>', "done"))
    return (f'<div class="wrap"><p class="eyebrow">{_h.escape(theme)}</p>'
            f'<h1>{_h.escape(question)}</h1>'
            f'<div class="spec">{"".join(parts)}</div></div>')


CSS = """
:root{ --ground:#F6F8F7; --surface:#FFFFFF; --ink:#171B23; --muted:#69737E;
       --accent:#16636B; --rule:#DFE5E4; --soft:#F1F5F4; --warn:#9A4A21; --out:#98A0A8; }
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --ground:#11161A; --surface:#191F24; --ink:#E7ECF0; --muted:#8C979F;
  --accent:#7FD1D9; --rule:#2A3239; --soft:#1E252B; --warn:#D9A382; --out:#6B747C; } }
:root[data-theme="dark"]{ --ground:#11161A; --surface:#191F24; --ink:#E7ECF0; --muted:#8C979F;
  --accent:#7FD1D9; --rule:#2A3239; --soft:#1E252B; --warn:#D9A382; --out:#6B747C; }
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-size:15px;line-height:1.85;
  font-family:"Noto Sans JP",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:52rem;margin:0 auto;padding:56px 24px 80px}
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
