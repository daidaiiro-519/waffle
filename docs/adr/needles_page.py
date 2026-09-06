"""照合する文字列が、その原文を特定できているかを1枚にする。

  python3 docs/adr/needles_page.py

数は実物から取る ── 手で書くと腐る。
"""
import html as H
import pathlib
import re
import sys

SK = pathlib.Path(__file__).resolve().parents[2] / ".waffle/skills/coding-skills"
sys.path.insert(0, str(SK / "scripts"))
from _common import load_all, needle_scope, sections, tables  # noqa: E402


def statements():
    out = {}
    for s in load_all():
        for name, body in sections(s.body).items():
            if name == "出典":
                continue
            for tb in tables(body):
                if not tb.has("ID"):
                    continue
                key = "規則" if tb.has("規則") else ("振る舞い" if tb.has("振る舞い") else None)
                if key:
                    for r in tb.rows:
                        out[(s.where, r["ID"])] = r[key]
    return out


def ids_for(where, needle):
    for s in load_all():
        if s.where != where:
            continue
        for tb in tables(sections(s.body).get("出典", "")):
            if not tb.has("照合する文字列"):
                continue
            for r in tb.rows:
                if r["照合する文字列"].strip().strip("`") == needle:
                    return r.get("ID", "")
    return ""


def docs_row(hit_others, total, w=250, h=30):
    """落としてある原文を1本ずつの目盛にし、当たったものを塗る。"""
    n = min(total, 52)
    cw = w / n
    bars = "".join(
        f'<rect x="{i * cw:.2f}" y="0" width="{max(cw - 1.2, 1.2):.2f}" height="{h}" '
        f'rx="1" fill="var({"--hit" if i < hit_others + 1 else "--strip"})"/>'
        for i in range(n))
    return (f'<svg viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="落としてある原文のうち、この文字列に当たる本数">{bars}</svg>')


def main():
    rows = needle_scope(load_all())
    stmt = statements()
    for r in rows:
        r["rid"] = ids_for(r["where"], r["needle"])
        r["stmt"] = stmt.get((r["where"], r["rid"]), "")
        r["short"] = r["where"].replace("constraints/", "")
    total_src = len({r["own"] for r in rows}) and len(
        [p for p in (SK / "sources").iterdir()
         if p.is_file() and not p.name.endswith(".meta.json")])

    pinned = [r for r in rows if not r["others"]]
    loose = sorted([r for r in rows if r["others"]],
                   key=lambda r: -len(r["others"]))
    blind = [r for r in loose if r["own"] == 1]
    noisy = sorted([r for r in pinned if r["own"] > 1], key=lambda r: -r["own"])

    good = next(r for r in pinned if r["own"] == 1 and r["rid"])
    bad = loose[0]

    def table(rs, cap):
        body = "".join(f'''<tr>
          <td class="id">{H.escape(r["rid"] or "宣言")}</td>
          <td class="st">{H.escape(r["stmt"] or "（規則ではなく、宣言に付いた出典）")}
            <small>{H.escape(r["short"])}</small></td>
          <td class="nd"><code>{H.escape(r["needle"])}</code></td>
          <td class="ct"><b>{len(r["others"])}</b> 本<small>自 {r["own"]} か所</small></td>
        </tr>''' for r in rs)
        return (f'<div class="scroll"><table><caption>{cap}</caption>'
                f'<tr><th>規則</th><th>言明</th><th>照合する文字列</th>'
                f'<th>他に当たる原文</th></tr>{body}</table></div>')

    tiles = "".join(
        f'<div class="tile{c}"><span class="k">{k}</span><span class="v">{v}</span>'
        f'<span class="d">{d}</span></div>'
        for k, v, d, c in [
            ("その原文だけに当たる", len(pinned), "版が変われば鳴る", " good"),
            ("他の原文にも当たる", len(loose), "原文が差し替わっても鳴らない", " weak"),
            ("うち、自分の原文には1か所", len(blind),
             "当たった数では見つからない", " weak"),
            ("当たった数は多いが特定できている", len(noisy),
             "数だけ見ると誤って疑う", "")])

    page = f"""<title>照合する文字列は、原文を特定できているか</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@700&display=swap">
<style>
:root{{
  --paper:#F7F8F9; --card:#FFFFFF; --ink:#171A1D; --muted:#68727E;
  --rule:#E1E5E9; --key:#2E5D7A; --weak:#A83E28; --good:#2C6A57;
  --strip:#E4E8EC; --hit:#A83E28; --barbg:#EDF0F2;
}}
@media (prefers-color-scheme:dark){{ :root:not([data-theme="light"]){{
  --paper:#14171A; --card:#1B1F23; --ink:#E7E9EC; --muted:#98A2AE;
  --rule:#2A3037; --key:#7FB0CC; --weak:#E08A72; --good:#6FBFA3;
  --strip:#2A3138; --hit:#E08A72; --barbg:#242A30;
}} }}
:root[data-theme="dark"]{{
  --paper:#14171A; --card:#1B1F23; --ink:#E7E9EC; --muted:#98A2AE;
  --rule:#2A3037; --key:#7FB0CC; --weak:#E08A72; --good:#6FBFA3;
  --strip:#2A3138; --hit:#E08A72; --barbg:#242A30;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Noto Sans JP",system-ui,sans-serif;font-size:15.5px;line-height:1.85;
  -webkit-font-smoothing:antialiased}}
main{{max-width:58rem;margin:0 auto;padding:2.5rem 1.5rem 5rem;
  display:flex;flex-direction:column;gap:2.6rem}}
h1{{font-family:"Noto Serif JP",serif;font-size:clamp(24px,3.6vw,33px);line-height:1.35;
  margin:0;text-wrap:balance}}
h2{{font-family:"Noto Serif JP",serif;font-size:1.18rem;margin:0 0 1rem;
  padding-bottom:.45rem;border-bottom:1px solid var(--rule)}}
p{{margin:0 0 .9rem}}
.lede{{color:var(--muted);margin:.7rem 0 0;font-size:1rem}}
.eyebrow{{font-size:11px;letter-spacing:.18em;color:var(--muted);margin:0 0 .5rem}}
.role{{background:var(--card);border:1px solid var(--rule);border-left:3px solid var(--key);
  border-radius:.4rem;padding:1rem 1.2rem;font-size:.95rem}}
.role q{{font-style:normal;font-weight:700}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(17rem,1fr));gap:1.1rem}}
.ex{{background:var(--card);border:1px solid var(--rule);border-radius:.45rem;padding:1.1rem}}
.ex.g{{border-color:var(--good)}} .ex.b{{border-color:var(--weak)}}
.ex h3{{margin:.15rem 0 .1rem;font-size:.93rem}}
.ex .verdict{{font-size:.76rem;font-weight:700;letter-spacing:.05em}}
.ex.g .verdict{{color:var(--good)}} .ex.b .verdict{{color:var(--weak)}}
.ex code{{display:block;margin:.55rem 0 .5rem;font-size:.8rem;word-break:break-all}}
.ex svg{{display:block;width:100%;height:30px;margin:.3rem 0}}
.ex small{{color:var(--muted);font-size:.79rem;line-height:1.7;display:block}}
code{{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.86em;
  background:var(--barbg);border-radius:.2rem;padding:.08em .4em}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(11.5rem,1fr));gap:.8rem}}
.tile{{background:var(--card);border:1px solid var(--rule);border-radius:.45rem;
  padding:.9rem 1rem;display:flex;flex-direction:column;gap:.15rem}}
.tile.weak{{border-color:var(--weak);border-width:1.5px}}
.tile.good{{border-color:var(--good)}}
.tile .k{{font-size:.75rem;color:var(--muted);line-height:1.6}}
.tile .v{{font-size:1.9rem;font-weight:700;line-height:1.2;font-variant-numeric:tabular-nums}}
.tile.weak .v{{color:var(--weak)}} .tile.good .v{{color:var(--good)}}
.tile .d{{font-size:.77rem;color:var(--muted);line-height:1.6}}
.scroll{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:.86rem}}
caption{{text-align:left;font-size:.82rem;color:var(--muted);padding-bottom:.5rem}}
th{{text-align:left;font-size:.72rem;letter-spacing:.05em;color:var(--muted);font-weight:700;
  padding:.45rem .6rem;border-bottom:1.5px solid var(--rule);white-space:nowrap}}
td{{padding:.6rem;border-bottom:1px solid var(--rule);vertical-align:top}}
td.id{{font-family:ui-monospace,monospace;font-size:.78rem;color:var(--key);white-space:nowrap}}
td.st small,td.ct small{{display:block;color:var(--muted);font-size:.74rem;margin-top:.15rem}}
td.nd{{max-width:19rem}}
td.ct{{white-space:nowrap;font-variant-numeric:tabular-nums}}
td.ct b{{color:var(--weak);font-size:1.05rem}}
ul{{margin:0;padding-left:1.15rem}} li{{margin-bottom:.45rem}}
.foot{{color:var(--muted);font-size:.82rem;border-top:1px solid var(--rule);padding-top:1rem}}
</style>
<main>
<header>
  <p class="eyebrow">CODING-SKILLS ／ 出典の点検</p>
  <h1>照合する文字列は、原文を特定できているか</h1>
  <p class="lede">規約の規則には出典が付き、「原文にこの文字列が在る」ことで確かめている。
  <b>その文字列が、他の原文にも当たっていないかを測った。</b>当たっているなら、
  原文が別物に差し替わっても、その確認は通ってしまう。</p>
</header>

<section>
  <h2>照合する文字列は、何のために在るか</h2>
  <div class="role">
    <p style="margin:0 0 .5rem">規約が、この印の役割をこう定めている。</p>
    <p style="margin:0"><q>版が上がったら、照合する文字列がまだ原文に在るかを確かめる。
    無ければ、その規則は出典を失っている。</q>
    <small style="color:var(--muted)">── references/sources.md</small></p>
  </div>
  <p style="margin-top:1rem"><b>つまりこの印は、原典が変わったときに鳴るためのものである。</b>
  鳴らない印は、付いていないのと同じである。</p>
</section>

<section>
  <h2>鳴る印と、鳴らない印</h2>
  <p>目盛は落としてある原文 {total_src} 本。赤は、その文字列が当たる原文である。</p>
  <div class="two">
    <div class="ex g">
      <span class="verdict">その1本だけ ── 鳴る</span>
      <h3>{H.escape(good["rid"])}　{H.escape(good["stmt"][:24])}</h3>
      <code>{H.escape(good["needle"])}</code>
      {docs_row(0, total_src)}
      <small>この文字列は、出典に指定した原文にしか当たらない。
      原文が書き換われば、その場で落ちる。</small>
    </div>
    <div class="ex b">
      <span class="verdict">他に {len(bad["others"])} 本 ── 鳴らない</span>
      <h3>{H.escape(bad["rid"] or "宣言")}　{H.escape((bad["stmt"] or bad["short"])[:24])}</h3>
      <code>{H.escape(bad["needle"])}</code>
      {docs_row(len(bad["others"]), total_src)}
      <small>落としてある原文のうち {len(bad["others"]) + 1} 本に当たる。
      <b>出典をまったく別の文書に差し替えても、この確認は通る。</b></small>
    </div>
  </div>
</section>

<section>
  <h2>{len(rows)} 件の内訳</h2>
  <div class="tiles">{tiles}</div>
</section>

<section>
  <h2>当たった数では見つからない</h2>
  <p>はじめは「原文に何か所当たるか」で測った。<b>その測り方は両方向に外す。</b></p>
  {table(blind, f"自分の原文には1か所しか当たらないのに、他の原文にも当たる {len(blind)} 件"
                "　── 数で測ると「良い」と判定される")}
  <p class="lede" style="margin-top:1.2rem">逆に、当たった数が多くても特定できているものが
  {len(noisy)} 件ある（<code>{H.escape(noisy[0]["needle"])}</code> は自 {noisy[0]["own"]} か所だが、
  他の原文には1本も当たらない）。<b>数は、この問いの答えになっていない。</b></p>
</section>

<section>
  <h2>他の原文にも当たる {len(loose)} 件</h2>
  {table(loose[:24], "他に当たる原文の多い順（上位24件）")}
</section>

<section>
  <h2>機械に決められないこと</h2>
  <p>ここで測ったのは<b>「その文字列が、その原文を特定できているか」だけ</b>である。
  特定できていても、<b>その箇所が規則を支えているかは決められない</b> ──
  それは人が読んで判断する（<code>check.py --contracts</code> が
  「機械では裁けない」として並べている3件の1つ）。</p>
</section>

<section>
  <h2>どうするか</h2>
  <ul>
    <li><b>A</b>　{len(loose)} 件すべて、原文から取り直す ── 印が鳴るようになる</li>
    <li><b>B</b>　他に当たる本数の多いものから直す（<code>errors</code> ・
      <code>Short</code> ・ <code>internal</code> …）</li>
    <li><b>C</b>　いまは直さず、この測定を記録として残す</li>
  </ul>
</section>

<p class="foot">数はすべて実物から取っている（<code>python3 scripts/check.py --needles</code>）。
この頁は <code>docs/adr/needles_page.py</code> が書き出す ── 手で書いた数は腐るためである。</p>
</main>
"""
    out = pathlib.Path(__file__).parent / "needles.html"
    out.write_text(page, encoding="utf-8")
    print(f"{out} ── 照合 {len(rows)} 件 ／ 特定できている {len(pinned)} ／ "
          f"できていない {len(loose)}（うち数では見つからない {len(blind)}）")


if __name__ == "__main__":
    main()
