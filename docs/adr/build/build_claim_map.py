"""言い分 → 部品の対応表。**実装から導く。**

手で書くと間違える（実際、相関の座標の出どころと、時間変化の span を書き誤った）。
ここでは変換器の構文木から、言い分ごとに「どの部品へ、どの鍵に、どんな式で渡すか」を
そのまま取り出す。鍵の要否は目録から引き、目録に無い鍵があればその場で落ちる。

つまりこの表は、実装と目録の両方に照らして作られる。どちらかとずれたら作れない。
"""
import ast, sys, pathlib, html
S = "/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0, S)
sys.path.insert(0, "/home/daidaiiro/workspace/waffle/.claude/skills/design-svg")
from _common import CSS, sec, fold, tbl, extra
from svg_engine.catalog import catalog

CAT = catalog()["parts"]
SRC = pathlib.Path("/home/daidaiiro/workspace/waffle/.claude/skills/design-svg"
                   "/svg_engine/examples/all_claims.py").read_text(encoding="utf-8")
TREE = ast.parse(SRC)
CONVERT = next(n for n in ast.walk(TREE)
               if isinstance(n, ast.FunctionDef) and n.name == "convert")

# 族 ── 承認済みの仕様が定める並び。実装には無いので、ここだけは表が持つ
FAMILY = {c: "関係" for c in ("つながり", "階層", "包含", "順序", "循環", "やり取り", "対応")}
FAMILY.update({c: "量" for c in ("全体と部分", "量の大小", "順位", "時間変化", "分布",
                                 "偏差", "相関", "流量", "空間")})


def claims_of(test) -> list[str]:
    """条件式が受け持つ言い分を取り出す。`a == "x"` と `a in ("x", "y")` の2形。"""
    if isinstance(test, ast.Compare) and isinstance(test.ops[0], ast.Eq):
        return [test.comparators[0].value]
    if isinstance(test, ast.Compare) and isinstance(test.ops[0], ast.In):
        return [e.value for e in test.comparators[0].elts]
    return []


def call_in(node):
    """その枝が呼ぶ描画。(部品名 or None, {鍵: 式}) を返す。"""
    for n in ast.walk(node):
        if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Name):
            continue
        if n.func.id == "render_chart":
            kind = n.args[0].value
            args = {}
            if len(n.args) > 1 and isinstance(n.args[1], ast.Dict):
                for k, v in zip(n.args[1].keys, n.args[1].values):
                    args[k.value] = ast.unparse(v)
            return kind, args
        if n.func.id == "render_figure":
            kw = {k.arg: ast.unparse(k.value) for k in n.keywords if k.arg != "theme"}
            return None, kw
    return None, {}


rows, seen = [], set()
node = CONVERT
branches = [n for n in ast.walk(CONVERT) if isinstance(n, ast.If)]
for br in branches:
    for claim in claims_of(br.test):
        if claim in seen:
            continue
        seen.add(claim)
        part, args = call_in(br)
        if part is not None:
            props = CAT[part]["props"]
            unknown = [k for k in args if k not in props]
            assert not unknown, f"{claim}/{part}: 目録に無い鍵 {unknown}"
            need = [k for k, v in props.items() if v["required"] and k not in args]
            assert not need, f"{claim}/{part}: 必須の鍵を渡していない {need}"
            cell = "<br>".join(
                f"<code>{k}</code> <span class='sub'>"
                f"({'必須' if props[k]['required'] else '任意'})</span> ← "
                f"<code>{html.escape(v)}</code>" for k, v in args.items())
            out = f"絵 / <code>{part}</code>"
        else:
            cell = "<br>".join(f"<code>{k}</code> ← <code>{html.escape(v)}</code>"
                               for k, v in args.items()) or "<span class='sub'>—</span>"
            out = "絵 / 図として組む"
        rows.append(("keyrow" if part is None else "",
                     [claim, FAMILY.get(claim, "?"), out, cell]))

covered = set(seen)
ALL = set(FAMILY)
missing = sorted(ALL - covered)

body = "".join([
 '<header><p class="eyebrow">対応表</p>'
 '<h1>言い分から、部品と渡す値へ</h1>'
 '<p class="lede">仕様の側が持つ表。<b>実装の構文木から導いている</b>'
 ' ── 手で書くと間違えるためで、実際に一度、座標の出どころと区間の出どころを書き誤った。'
 '鍵の要否は目録から引き、<b>目録に無い鍵や、渡し漏れた必須の鍵があればこの表は作れない</b>。</p></header>',

 sec("01", "対応",
  f"実装が受け持つ {len(rows)} 件。式はそのまま載せる ── 言い換えると、そこで誤る。",
  tbl(["言い分", "族", "何になるか", "部品へ渡す値 ← 実装の式"], rows)),

 sec("02", "仕様との差", "承認済みの仕様が定める言い分と、実装が受け持つものを突き合わせる。",
  tbl(["仕様が定めるもの", "実装", "どうするか"],
      [("keyrow", ["<b>分布</b> ── <code>bins</code> と <code>axes</code> を1本",
                   "<code>bins</code> を読んでいない（<code>frame</code> から読むのは "
                   "<code>axes</code>・<code>baseline</code>・<code>groups</code> の3つだけ）",
                   "<b>仕様が必須と定めた欄が変換で落ちている。</b>"
                   "部品側に対応する鍵が品目の軸の名前しか無いので、そこへ渡すかどうかを決める"])]
      + [("", [c, "受け持っていない", "引っ越しのときに実装する"]) for c in missing]),
  fold("「対応」が表に出てこない理由を開く",
   '<p>実装は対応を常にSVGの表として描くので、1行として出る。'
   'だが後から「交点が図を持たなければ成果物の書式そのものへ」という分岐が決まっており、'
   'それは版に入れていない試作にしかない。<b>いまの実装から導く以上、この表には'
   '古いほうが載る</b> ── 引っ越しのときに実装を直せば、この表も一緒に直る。</p>')),
])
extra2 = extra + "\n.sub{font-weight:400;font-size:.82rem;color:var(--ink-faint)}\n"
out = ("<title>言い分から、部品と渡す値へ</title>"
       f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adapter-claim-map.html").write_text(out, encoding="utf-8")
print("書いた", len(out), "／ 実装が受け持つ", len(rows), "件／ 未実装", len(missing), "件:", missing)
