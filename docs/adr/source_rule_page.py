"""出典の書き方（案C）を、原則と実例で1枚にする。

  python3 docs/adr/source_rule_page.py

数と照合の結果は実物から取る ── 手で書くと腐る。
"""
import html as H
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SK = HERE.parents[1] / ".waffle/skills/coding-skills"
sys.path.insert(0, str(SK / "scripts"))
sys.path.insert(0, str(HERE))
from _common import SOURCES, load_all, needle_scope  # noqa: E402
from srcfig import FALL, ONE  # noqa: E402

RAW = {p.name: p.read_text(encoding="utf-8", errors="replace")
       for p in SOURCES.iterdir()
       if p.is_file() and not p.name.endswith(".meta.json")}


def canon(n):
    return n[:-3] if n.endswith(".md") and n[:-3] in RAW else n


DOCS = {}
for _n, _t in RAW.items():
    DOCS[canon(_n)] = DOCS.get(canon(_n), "") + _t


def hits(term):
    return sum(1 for t in DOCS.values() if term in t)


def fig(pair):
    svg, cap = pair
    return f'<figure>{svg}<figcaption>{H.escape(cap)}</figcaption></figure>'


def needle(term, note=""):
    n = hits(term)
    cls = "ok" if n == 1 else "ng"
    tail = f'<span class="hit {cls}">実原文 {len(DOCS)} 本のうち <b>{n}</b> 本に当たる</span>'
    return f'<code>{H.escape(term)}</code>{tail}' + (
        f'<small>{note}</small>' if note else "")


def main():
    rows = needle_scope(load_all())
    loose = [r for r in rows
             if [d for d, t in DOCS.items()
                 if d != canon(pathlib.Path(r["where"]).name) and r["needle"] in t]]
    # 実測は needle_scope（ファイル単位）ではなく、二重取得を畳んだ数で取り直す
    loose_n = sum(1 for r in rows if hits(r["needle"]) > 1)

    page = f"""<title>出典は、規則1件に原典1本</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@700&display=swap">
<style>
:root{{
  --paper:#F6F7F8; --card:#FFFFFF; --ink:#161A1E; --muted:#66717D;
  --rule:#DFE4E8; --line:#7C8894; --key:#2B5F7E; --accent:#A5432A; --ok:#2B6B55;
  --code:#EEF1F4;
}}
@media (prefers-color-scheme:dark){{ :root:not([data-theme="light"]){{
  --paper:#131619; --card:#1A1E22; --ink:#E6E9EC; --muted:#96A0AB;
  --rule:#282E34; --line:#7C8894; --key:#7FB2CE; --accent:#E08A72; --ok:#6EBFA2;
  --code:#232930;
}} }}
:root[data-theme="dark"]{{
  --paper:#131619; --card:#1A1E22; --ink:#E6E9EC; --muted:#96A0AB;
  --rule:#282E34; --line:#7C8894; --key:#7FB2CE; --accent:#E08A72; --ok:#6EBFA2;
  --code:#232930;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Noto Sans JP",system-ui,sans-serif;font-size:15.5px;line-height:1.85}}
main{{max-width:56rem;margin:0 auto;padding:2.5rem 1.5rem 5rem;
  display:flex;flex-direction:column;gap:2.6rem}}
h1{{font-family:"Noto Serif JP",serif;font-size:clamp(24px,3.6vw,32px);margin:0;
  line-height:1.35;text-wrap:balance}}
h2{{font-family:"Noto Serif JP",serif;font-size:1.16rem;margin:0 0 1rem;
  padding-bottom:.45rem;border-bottom:1px solid var(--rule)}}
h3{{font-size:.95rem;margin:1.5rem 0 .5rem;color:var(--muted)}}
p{{margin:0 0 .9rem}}
.eyebrow{{font-size:11px;letter-spacing:.18em;color:var(--muted);margin:0 0 .5rem}}
.lede{{color:var(--muted);margin:.7rem 0 0}}
ol.rules{{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:.7rem;
  counter-reset:r}}
ol.rules li{{background:var(--card);border:1px solid var(--rule);border-left:3px solid var(--key);
  border-radius:.4rem;padding:.85rem 1.1rem .85rem 3rem;position:relative}}
ol.rules li::before{{counter-increment:r;content:counter(r);position:absolute;left:1.1rem;
  top:.85rem;font-family:ui-monospace,monospace;font-weight:700;color:var(--key)}}
ol.rules b{{display:block;margin-bottom:.15rem}}
ol.rules small{{color:var(--muted);font-size:.85rem;line-height:1.7;display:block}}
figure{{margin:0}}
figure svg{{display:block;width:100%;height:auto;background:var(--card);
  border:1px solid var(--rule);border-radius:.45rem}}
figcaption{{font-size:.83rem;color:var(--muted);margin-top:.5rem;line-height:1.7}}
figure+figure{{margin-top:1.6rem}}
.ex{{background:var(--card);border:1px solid var(--rule);border-radius:.45rem;overflow:hidden}}
.ex>.hd{{padding:.8rem 1.1rem;border-bottom:1px solid var(--rule)}}
.ex>.hd b{{font-family:ui-monospace,monospace;color:var(--key);font-size:.85rem}}
.ex>.hd span{{display:block;font-size:.95rem;margin-top:.1rem}}
.ba{{display:grid;grid-template-columns:1fr 1fr;gap:0}}
.ba>div{{padding:1rem 1.1rem}}
.ba>div+div{{border-left:1px solid var(--rule)}}
@media(max-width:44rem){{.ba{{grid-template-columns:1fr}}
  .ba>div+div{{border-left:none;border-top:1px solid var(--rule)}}}}
.ba .tag{{font-size:.72rem;font-weight:700;letter-spacing:.08em;color:var(--muted);
  display:block;margin-bottom:.5rem}}
.ba .after .tag{{color:var(--ok)}}
code{{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.82rem;
  background:var(--code);border-radius:.25rem;padding:.25em .5em;display:block;
  word-break:break-word;line-height:1.7}}
.hit{{display:block;font-size:.75rem;margin-top:.4rem;color:var(--accent)}}
.hit.ok{{color:var(--ok)}}
.hit b{{font-variant-numeric:tabular-nums}}
small{{display:block;color:var(--muted);font-size:.8rem;line-height:1.7;margin-top:.4rem}}
table{{border-collapse:collapse;width:100%;font-size:.86rem}}
th{{text-align:left;font-size:.72rem;letter-spacing:.05em;color:var(--muted);font-weight:700;
  padding:.45rem .6rem;border-bottom:1.5px solid var(--rule)}}
td{{padding:.55rem .6rem;border-bottom:1px solid var(--rule);vertical-align:top}}
.scroll{{overflow-x:auto}}
.note{{background:var(--card);border:1px solid var(--rule);border-left:3px solid var(--accent);
  border-radius:.4rem;padding:.9rem 1.1rem;font-size:.92rem}}
.foot{{color:var(--muted);font-size:.82rem;border-top:1px solid var(--rule);padding-top:1rem}}
</style>
<main>
<header>
  <p class="eyebrow">CODING-SKILLS ／ 出典の書き方</p>
  <h1>出典は、規則1件に原典1本</h1>
  <p class="lede">照合する文字列は「原典が変わったときに鳴る」ためにある。
  いま {len(rows)} 件のうち <b>{loose_n} 件</b>は、他の原文にも当たっていて鳴らない。
  書き方を3つの原則に絞り、実例で示す。</p>
</header>

<section>
  <h2>3つの原則</h2>
  <ol class="rules">
    <li><b>規則1件に、原典1本。</b>
      <small>2本目が欲しくなったら、規則の切り方が合っていない。
      規則を割るか、規則にしないかのどちらかである。</small></li>
    <li><b>照合する文字列は、原典がその考えを名づけている箇所から取る。</b>
      <small>名づけているならその見出し・その語を。名づけていないなら、
      考えを定義している一文を。<b>一般語を取らない</b> ──
      <code style="display:inline;padding:.05em .35em">errors</code> ・
      <code style="display:inline;padding:.05em .35em">naming</code> ・
      <code style="display:inline;padding:.05em .35em">interfaces</code>
      は、どの文書にも在る。</small></li>
    <li><b>照合が落ちても、規則が出典を失ったとは限らない。</b>
      <small>落ちたのは指し先である。原典を読み、その考えがまだ在るかを人が確かめる。</small></li>
  </ol>
</section>

<section>
  <h2>図で見る</h2>
  {fig(ONE)}
  {fig(FALL)}
</section>

<section>
  <h2>実例1　原典が2本欲しくなる ── 規則を割る</h2>
  <div class="ex">
    <div class="hd"><b>GO-ERR-01</b>
      <span>失敗は戻り値の最後の <code style="display:inline;padding:.05em .35em">error</code>
      で返し、<code style="display:inline;padding:.05em .35em">panic</code> で流さない</span></div>
    <div class="ba">
      <div><span class="tag">いま</span>
        {needle("errors",
                "Effective Go を指しているつもりだが、どの Go 文書にも当たる。"
                "しかもこの規則は<b>命題を2つ持っている</b> ── "
                "「error で返す」と「panic で流さない」は別のことで、原典の節も別である。")}
      </div>
      <div class="after"><span class="tag">直したあと ── 2件に割る</span>
        <p style="margin:0 0 .3rem;font-size:.9rem"><b>GO-ERR-01</b>　失敗は戻り値の
        <code style="display:inline;padding:.05em .35em">error</code> で返す</p>
        {needle("By convention, errors have type", "Effective Go / Errors")}
        <p style="margin:.9rem 0 .3rem;font-size:.9rem"><b>GO-ERR-06</b>　失敗を
        <code style="display:inline;padding:.05em .35em">panic</code> で流さない</p>
        {needle("usual way to report an error to a caller is to return an",
                "Effective Go / Panic ── 別の節が支えている")}
      </div>
    </div>
  </div>
  <p class="lede" style="margin-top:.9rem">2本目の原典を足すのではなく、規則を2件にする。
  <b>それぞれが1本ずつ持つ。</b></p>
</section>

<section>
  <h2>実例2　照合を、考えを名づけている箇所へ移す</h2>
  <div class="ex">
    <div class="hd"><b>DP-TB-01</b>
      <span>写し手は、生の入力とデータ契約の型だけで確かめられる</span></div>
    <div class="ba">
      <div><span class="tag">いま</span>
        {needle("because the code under test deals only with buffers of bytes for",
                "1本にしか当たらないので鳴りはする。ただし<b>本文の途中の一文</b>なので、"
                "言い換え1つで落ちる ── 考えが生きていても鳴る。")}
      </div>
      <div class="after"><span class="tag">直したあと</span>
        {needle("Simplicity, Testability, and Correctness",
                "sans-IO が<b>その考えに与えている節の見出し</b>。"
                "節ごと消えれば考えが消えたと判る。言い換えでは落ちない。")}
      </div>
    </div>
  </div>
</section>

<section>
  <h2>どの箇所から取るか</h2>
  <div class="scroll"><table>
    <tr><th>原典が考えを</th><th>取るもの</th><th>例</th></tr>
    <tr><td>名づけている</td><td>その見出し・その語</td>
      <td><code style="display:inline;padding:.1em .4em">Simplicity, Testability, and Correctness</code>
      ・<code style="display:inline;padding:.1em .4em">Ports and Adapters</code></td></tr>
    <tr><td>名づけていない</td><td>考えを定義している一文</td>
      <td><code style="display:inline;padding:.1em .4em">By convention, errors have type</code></td></tr>
    <tr><td>規則が識別子そのものを主張している</td><td>その識別子</td>
      <td><code style="display:inline;padding:.1em .4em">%w</code>
      ・<code style="display:inline;padding:.1em .4em">testing.Short</code>
      ── 消えたら規則が本当に壊れている。鳴るのが仕事</td></tr>
  </table></div>
  <div class="note" style="margin-top:1rem">
    <b>長い一文をそのまま取らない。</b>落とした原文は行が折り返されているので、
    文をまたぐ範囲は当たらない。実際
    <code style="display:inline;padding:.1em .4em">The usual way to report an error to a caller is to return an error as an extra return value</code>
    は 0 本に当たる ── 1行に収まる範囲を取る。
  </div>
</section>

<section>
  <h2>この形にすると要らなくなるもの</h2>
  <p><b>「依拠する考え」の列も節も足さない。</b>
  原典の言葉で名づける限り、考えの名前がそのまま照合する文字列になる。
  1つの規則が原典を1本しか持たないなら、考えを別に持つ理由も無い。</p>
  <p style="margin:0">考えを<b>単位として</b>切り出すかどうかは別の問いである ──
  <code style="display:inline;padding:.05em .35em">contract test</code> の考えは
  <code style="display:inline;padding:.05em .35em">arch.data-port</code> でも
  <code style="display:inline;padding:.05em .35em">arch.hexagonal</code> でも成り立ち、
  <b>置ける層が無い</b>。そこは軸の体系に手を入れる話なので、別の論点として立てる。</p>
</section>

<p class="foot">当たった数はすべて実物から取っている（実原文 {len(DOCS)} 本。
落としてあるファイル {len(RAW)} 本のうち {len(RAW) - len(DOCS)} 本は同じ頁の二重取得なので畳んだ）。
この頁は <code style="display:inline;padding:.1em .4em">docs/adr/source_rule_page.py</code> が書き出す。</p>
</main>
"""
    out = HERE / "source-rule.html"
    out.write_text(page, encoding="utf-8")
    print(f"{out} ── 照合 {len(rows)} 件 ／ 他にも当たる {loose_n} 件 ／ 実原文 {len(DOCS)} 本")


if __name__ == "__main__":
    main()
