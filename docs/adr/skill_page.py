"""CodingSkills の全文を、前の版からの変更つきで1枚にする。

  python3 docs/adr/skill_page.py

**差分は git から取る。**手で書くと、写した側が正になる。
「なぜ変えたか」だけを人が書き、どのファイルがどの変更に当たるかは
パターンで割り当てる ── 61ファイルぶんの理由を1つずつ書くと、必ずずれる。
"""
import html as H
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from counts import rows as counts  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SK = ROOT / ".waffle/skills/coding-skills"
REL = ".waffle/skills/coding-skills"
BASE = "9d99557"          # 第1版（CodingSkills を Skill として据える）

# ── 変更の束。ファイルの当たり方はパターンで決める ──────────────
GROUPS = [
    ("承認の記録", r"^(constraints|templates)/.*\.md$",
     "前置きに <code>approved_by</code> と <code>approved_at</code> を足した。",
     "承認を定めていたのに、記録する場所がどこにも無かった。"
     "承認済みと未承認を、記録から区別できない状態だった。"),
    ("出典の追加", r"^constraints/(arch\.hexagonal/test-boundaries|lang\.rust/concurrency|"
     r"lang\.go/(failure|style)|lang\.go\+arch\.hexagonal/test-placement|"
     r"purpose\.(hook|mcp-server|backend-api)/acceptance|purpose\.hook/test-strategy|"
     r"arch\.data-port/test-boundaries)\.md$",
     "出典の行を14行足した。",
     "66件の規則のうち23件に出典が無いのに、検査が通っていた。"
     "検査が出典の表を回っていたので、行が1つも無い規則を見逃していた。"),
    ("照合の差し替え", r"^constraints/(purpose\.hook/acceptance|purpose\.mcp-server/acceptance|"
     r"lang\.go\+arch\.hexagonal/test-placement|purpose\.backend-api/acceptance)\.md$",
     "照合する文字列を差し替えた（6件）。",
     "原文に在るだけで、規則を裏づけていなかった ── "
     "<code>Exit code</code> は28か所、<code>stdout</code> は3か所に当たる。"
     "入れ子のバッククォートで検査の解釈が壊れるものもあった。"),
    ("規則の組み替え", r"^constraints/(lang\.rust\+arch\.(data-port|hexagonal)/test-placement|"
     r"arch\.data-port/test-boundaries|purpose\.hook/acceptance|purpose\.mcp-server/acceptance)\.md$",
     "規則を割った・新設した・外した。",
     "1文に2つの命題が入っていたものを割り、外部に原典が無いものを"
     "「委譲する判断」へ移した。出典を持たない言明は規則ではない、という定めをそのまま当てた。"),
    ("テストの置き場所", r"^constraints/(lang\.rust\+arch\.(hexagonal|data-port)/test-placement|"
     r"purpose\.(hook|mcp-server)/acceptance)\.md$",
     "テストの置き場所を組み替えた。",
     "<code>include_str!</code> は「そのマクロを書いたソースファイルからの相対」で解決されるので、"
     "単体テストが <code>src/</code> に在るのに実物入力を <code>tests/</code> へ置くと届かなかった。"
     "あわせて <code>tests/</code> を「公開する境界から叩くもの」だけに絞った。"),
    ("参照文書の定め", r"^references/",
     "定めを足した ── 出典の取り方・承認の記録・規則の印・数の扱い。",
     "検査を足すには、守る宣言が先に要る。"
     "「同じ層で印は一意」は検査だけが先に在り、宣言がどこにも無かった。"),
    ("scripts の作り直し", r"^scripts/",
     "読み取り層を1か所へ畳み、検査に宣言を持たせ、テストを足した。",
     "検査ごとに正規表現を書いていて、3か所が<b>落ちずに</b>壊れていた ── "
     "出典の照合が78行すべて素通り、<code>JSON</code> を規則と誤検出、"
     "照合文字列の入れ子で別の語を拾う。"),
    ("索引の作り直し", r"^constraints/INDEX\.md$",
     "数を書き出すようにした。",
     "参照文書に手で書いた数が腐っていた（落とした原文41本のまま）。"
     "索引と同じく、数も生成物にした。"),
]

SKIP = re.compile(r"^(sources/|__pycache__|scripts/__pycache__)")


def git_show(path):
    r = subprocess.run(["git", "show", f"{BASE}:{REL}/{path}"],
                       cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def files():
    out = []
    for p in sorted(SK.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(SK))
        if SKIP.match(rel) or rel.endswith((".pyc", ".bak")):
            continue
        out.append(rel)
    order = {"README.md": 0, "SKILL.md": 1}
    return sorted(out, key=lambda r: (order.get(r, 2), not r.startswith("references/"),
                                      not r.startswith("templates/"),
                                      not r.startswith("scripts/"), r))


# ── Markdown を、最小限だけ HTML にする ────────────────────────

def inline(s):
    s = H.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = s.replace("&lt;br&gt;", "<br>").replace("&lt;small&gt;", "<small>") \
         .replace("&lt;/small&gt;", "</small>")
    return s


def md2html(text):
    out, lines, i = [], text.splitlines(), 0
    if lines and lines[0] == "---":
        j = lines.index("---", 1) if "---" in lines[1:] else 0
        if j:
            out.append('<pre class="fm">' + H.escape("\n".join(lines[1:j])) + "</pre>")
            i = j + 1
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre><code>" + H.escape("\n".join(lines[i + 1:j])) + "</code></pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,4}) (.+)$", ln)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n+1}>{inline(m.group(2))}</h{n+1}>")
            i += 1
            continue
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-: |]+\|$", lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            tb = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                         for r in rows)
            out.append(f'<div class="scroll"><table><tr>{th}</tr>{tb}</table></div>')
            i = j
            continue
        if re.match(r"^[-*] ", ln):
            items, j = [], i
            while j < len(lines) and re.match(r"^[-*] ", lines[j]):
                items.append(f"<li>{inline(lines[j][2:])}</li>")
                j += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            i = j
            continue
        if ln.strip() == "":
            i += 1
            continue
        if ln.strip() == "---":
            out.append("<hr>")
            i += 1
            continue
        para, j = [], i
        while j < len(lines) and lines[j].strip() and not lines[j].startswith(("|", "#", "```", "- ")):
            para.append(inline(lines[j]))
            j += 1
        out.append("<p>" + "<br>".join(para) + "</p>")
        i = j
    return "".join(out)


def code2html(text):
    return "<pre><code>" + H.escape(text) + "</code></pre>"


def diff_html(old, new, path):
    import difflib
    d = list(difflib.unified_diff(old.splitlines(), new.splitlines(),
                                  fromfile=f"第1版/{path}", tofile=f"第2版/{path}",
                                  lineterm="", n=2))
    if not d:
        return ""
    body = []
    for ln in d:
        cls = ("a" if ln.startswith("+") and not ln.startswith("+++") else
               "d" if ln.startswith("-") and not ln.startswith("---") else
               "h" if ln.startswith("@@") else "")
        body.append(f'<span class="{cls}">{H.escape(ln)}</span>')
    add = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
    rm = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
    return (f'<details class="dif"><summary>変更を見る'
            f'<span class="cnt">＋{add} ／ −{rm}</span></summary>'
            f'<pre class="diff">{"".join(body)}</pre></details>')


CSS = """
:root{ --paper:#FBFAF7; --ink:#1C1A17; --muted:#6B665D; --panel:#F2EFE8;
  --line:#D8D3C7; --key:#2F6F5E; --add:#9A5B2C; --del:#8A3A3A; --code:#E7E3D9; }
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#16150F; --ink:#ECE7DC; --muted:#98918A; --panel:#211F18;
  --line:#38342A; --key:#6FBFA4; --add:#D99B62; --del:#D97B7B; --code:#2B281F; } }
:root[data-theme="dark"]{ --paper:#16150F; --ink:#ECE7DC; --muted:#98918A; --panel:#211F18;
  --line:#38342A; --key:#6FBFA4; --add:#D99B62; --del:#D97B7B; --code:#2B281F; }
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);line-height:1.85;font-size:15px;
  font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",system-ui,sans-serif}
.hd{position:sticky;top:0;z-index:9;background:var(--panel);border-bottom:2px solid var(--add);
  padding:.6rem 1.2rem;display:flex;gap:.9rem;align-items:baseline;flex-wrap:wrap}
.hd b{font-size:1.02rem}
.hd small{color:var(--muted);font-size:.82rem}
.tabs{position:sticky;top:3.1rem;z-index:8;background:var(--paper);border-bottom:1px solid var(--line);
  padding:.4rem 1.2rem;display:flex;gap:.35rem;overflow-x:auto;scrollbar-width:thin}
.tabs button{font:inherit;font-size:.8rem;padding:.3rem .7rem;border-radius:.25rem;cursor:pointer;
  background:none;border:1px solid transparent;color:var(--muted);white-space:nowrap}
.tabs button:hover{background:var(--panel);color:var(--ink)}
.tabs button[aria-selected="true"]{background:var(--panel);color:var(--ink);
  border-color:var(--line);font-weight:700}
.tabs .chg{color:var(--add);font-weight:700;margin-left:.3rem}
.tabs button:focus-visible{outline:2px solid var(--add);outline-offset:2px}
main{max-width:56rem;margin:0 auto;padding:1.4rem 1.2rem 5rem}
section[hidden]{display:none}
h1{font-size:1.42rem;margin:0 0 .8rem;letter-spacing:.01em}
h2{font-size:1.1rem;margin:2.1rem 0 .7rem;padding-bottom:.3rem;border-bottom:1px solid var(--line)}
h3{font-size:.98rem;margin:1.5rem 0 .5rem;color:var(--key)}
h4,h5{font-size:.92rem;margin:1.2rem 0 .4rem}
p{margin:0 0 .9rem}
.path{font-family:ui-monospace,monospace;font-size:.82rem;color:var(--muted);
  border-bottom:1px solid var(--line);padding-bottom:.4rem;margin-bottom:1rem}
.why{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--add);
  border-radius:.3rem;padding:.75rem 1rem;margin:0 0 1.1rem;font-size:.88rem}
.why b.t{display:block;color:var(--add);font-size:.72rem;letter-spacing:.1em;margin-bottom:.3rem}
.why .g{display:block;margin-top:.5rem}
.why .g em{font-style:normal;font-weight:700;color:var(--key)}
.none{color:var(--muted);font-size:.85rem;margin:0 0 1.1rem}
table{border-collapse:collapse;width:100%;font-size:.86rem;margin:.6rem 0}
th,td{border:1px solid var(--line);padding:.4rem .6rem;text-align:left;vertical-align:top}
th{background:var(--code);font-weight:700}
.scroll{overflow-x:auto}
code{background:var(--code);border-radius:.2rem;padding:.06em .3em;font-size:.88em;
  font-family:ui-monospace,SFMono-Regular,monospace}
pre{background:var(--code);border-radius:.3rem;padding:.6rem .8rem;overflow-x:auto;
  font-size:.8rem;line-height:1.7;margin:.5rem 0}
pre code{background:none;padding:0}
pre.fm{color:var(--muted);border-left:3px solid var(--line)}
ul{margin:0 0 .9rem;padding-left:1.2rem}
li{margin-bottom:.3rem}
hr{border:0;border-top:1px solid var(--line);margin:1.6rem 0}
details.dif{margin:.6rem 0 1.4rem;border:1px solid var(--line);border-radius:.3rem;
  background:var(--panel);padding:.5rem .8rem}
details.dif summary{cursor:pointer;font-size:.84rem;font-weight:700;color:var(--add)}
details.dif summary:focus-visible{outline:2px solid var(--add);outline-offset:2px}
.cnt{font-family:ui-monospace,monospace;font-weight:400;color:var(--muted);margin-left:.6rem}
pre.diff span{display:block;white-space:pre-wrap;word-break:break-word}
pre.diff .a{color:var(--key)}
pre.diff .d{color:var(--del)}
pre.diff .h{color:var(--muted)}
.sum td:first-child{white-space:nowrap;font-weight:700;color:var(--add)}
"""

SCRIPT = """
<script>
(function(){
  const tabs=[...document.querySelectorAll('.tabs button')];
  function show(id){
    tabs.forEach(b=>{const on=b.dataset.t===id;b.setAttribute('aria-selected',String(on));
      document.getElementById(b.dataset.t).hidden=!on;});
    history.replaceState(null,'','#'+id); window.scrollTo({top:0});
  }
  tabs.forEach((b,i)=>{
    b.addEventListener('click',()=>show(b.dataset.t));
    b.addEventListener('keydown',e=>{const d=e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0;
      if(d){e.preventDefault();const t=tabs[(i+d+tabs.length)%tabs.length];t.focus();show(t.dataset.t);}});
  });
  if(document.getElementById(location.hash.slice(1))) show(location.hash.slice(1));
  const all=document.getElementById('all');
  all.addEventListener('click',()=>{
    const open=all.textContent==='変更をすべて開く';
    document.querySelectorAll('details.dif').forEach(d=>d.open=open);
    all.textContent=open?'変更をすべて閉じる':'変更をすべて開く';
  });
})();
</script>
"""


def label(rel):
    if rel in ("README.md", "SKILL.md"):
        return rel
    d, _, n = rel.rpartition("/")
    n = n.removesuffix(".md").removesuffix(".py")
    return f"{d.split('/')[0][:12]}／{n}" if d else n


def main():
    rels = files()
    tabs, panes, changed, rows = [], [], 0, []
    hits = {g[0]: 0 for g in GROUPS}

    for k, rel in enumerate(rels, start=1):
        cur = (SK / rel).read_text(encoding="utf-8")
        old = git_show(rel)
        gs = [g for g in GROUPS if re.search(g[1], rel) and old is not None and old != cur]
        for g in gs:
            hits[g[0]] += 1
        dif = diff_html(old, cur, rel) if old is not None and old != cur else ""
        is_new = old is None
        if dif or is_new:
            changed += 1

        if is_new:
            why = ('<div class="why"><b class="t">この版で足した</b>'
                   'このファイルは第1版に無い。</div>')
        elif gs:
            why = ('<div class="why"><b class="t">変えたところ</b>'
                   + "".join(f'<span class="g"><em>{H.escape(g[0])}</em>　{g[2]}<br>'
                             f'<small>{g[3]}</small></span>' for g in gs) + "</div>")
        elif dif:
            why = ('<div class="why"><b class="t">変えたところ</b>'
                   '生成物として作り直した。</div>')
        else:
            why = '<p class="none">第1版から変えていない。</p>'

        body = code2html(cur) if rel.endswith(".py") else md2html(cur)
        panes.append(f'<section id="f{k}" hidden><p class="path">{H.escape(rel)}</p>'
                     f'{why}{dif}{body}</section>')
        tabs.append(f'<button data-t="f{k}" aria-selected="false">{H.escape(label(rel))}'
                    + ('<span class="chg">変</span>' if (dif or is_new) else "") + "</button>")

    for name, _, what, why in GROUPS:
        rows.append(f"<tr><td>{H.escape(name)}</td><td>{what}</td>"
                    f"<td>{why}</td><td>{hits[name]} 本</td></tr>")

    top = (f'<h1>CodingSkills（第2版）</h1>'
           f'<p>第1版（<code>{BASE}</code>）から、<b>{changed} ファイル</b>が変わった。'
           f'各タブの先頭に「変えたところ」と、git から取った差分を置いてある ── '
           f'<b>差分は手で書いていない。</b></p>'
           f'<h2>変更の束</h2>'
           f'<div class="scroll"><table class="sum"><tr><th>束</th><th>何をしたか</th>'
           f'<th>なぜ</th><th>当たるファイル</th></tr>{"".join(rows)}</table></div>'
           f'<h2>この版で決まったこと</h2>'
           f'<p>決定と、その根拠は<b>ブレストの盤面にある</b>（論点13〜17）。'
           f'ここに在るのは、決まったことの<b>結果</b>である。</p>'
           f'<div class="scroll"><table><tr><th>数えたもの</th>'
           f'<th>第1版</th><th>第2版</th></tr>'
           + "".join(f'<tr><td>{k}</td><td>{a}</td><td><b>{b}</b></td></tr>'
                     for k, a, b in counts())
           + '</table></div>'
           '<p class="none">第1版の <code>references/file-catalog.md</code> は'
           '「落とした原文 41」と書いていた。実際は 81 本で、'
           '<b>手で書いた数が既に腐っていた</b>。この表は両方の版から数えている。</p>')

    tabs.insert(0, '<button data-t="f0" aria-selected="true">変更の一覧</button>')
    panes.insert(0, f'<section id="f0">{top}</section>')

    page = (f'<title>CodingSkills（第2版）</title><style>{CSS}</style>'
            f'<div class="hd"><b>CodingSkills（第2版）</b>'
            f'<small>第1版から {changed} ファイルが変わった</small>'
            f'<button id="all" type="button" style="font:inherit;font-size:.8rem;'
            f'padding:.25rem .7rem;border:1px solid var(--add);border-radius:.25rem;'
            f'background:none;color:var(--add);cursor:pointer;margin-left:auto">'
            f'変更をすべて開く</button></div>'
            f'<div class="tabs" role="tablist">{"".join(tabs)}</div>'
            f'<main>{"".join(panes)}</main>{SCRIPT}')
    out = HERE / "coding-skills-v2.html"
    out.write_text(page, encoding="utf-8")
    print(f"{out} ── {len(rels)} ファイル（変更 {changed}）")


if __name__ == "__main__":
    main()
