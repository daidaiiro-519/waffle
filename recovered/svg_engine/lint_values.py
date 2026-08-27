"""値の出どころを見る検査 ── 生の数値がコードに残っていないかを機械が探す。

幾何検査は「重なっているか」しか見ない。生の数値で置いた寸法でも、たまたま
重ならなければ緑になる。だから寸法の出どころは、規律だけが支えていた ──
そして実際に、量系の部品だけで9箇所の生値が見逃されたまま残っていた。

採用済みの規律では、コードに現れる数値は3つに分かれる。

    1. 設計上の選択（余白・線幅・書体の大きさ）  → トークンから注入する
    2. データから決まる量（文字幅・箱の大きさ）  → 毎回計算する
    3. 勘で置いた閾値                            → 存在してはいけない

この検査は3を探す。1と2はコードに数値として現れないので、**現れた数値は
原則すべて疑わしい**という立場を取る。構造上どうしても現れるもの（0・1・2、
添字、角度の360/180、半分の2）だけを除く。

使い方:
    python3 -m svg_engine.lint_values          # 一覧を出す
    from svg_engine.lint_values import findings  # 検査として使う
"""
from __future__ import annotations

import ast
import pathlib

# 構造上どうしても現れる数。これ以外の数値は報告する。
_STRUCTURAL = {0, 1, 2, -1, -2}
# 角度と割合。座標系そのものが決めている数で、選んだ値ではない。
_GEOMETRIC = {90, 180, 270, 360, 100}


class _Finder(ast.NodeVisitor):
    """関数ごとに、生の数値を集める。"""

    def __init__(self, src: str):
        self.lines = src.splitlines()
        self.func: list[str] = []
        self.found: list[tuple[int, str, str]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.func.append(node.name)
        self.generic_visit(node)
        self.func.pop()

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # 添字（points[-1] など）の数は構造。中身だけ辿る
        self.visit(node.value)

    def visit_Call(self, node: ast.Call) -> None:
        name = getattr(node.func, "id", "")
        if name == "range":
            for a in node.args:
                if not isinstance(a, ast.Constant):
                    self.visit(a)
            return
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        # 平方根（** 0.5）は数学の書き方であって、選んだ値ではない
        if (isinstance(node.op, ast.Pow) and isinstance(node.right, ast.Constant)
                and node.right.value == 0.5):
            self.visit(node.left)
            return
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        v = node.value
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return
        if v in _STRUCTURAL or v in _GEOMETRIC:
            return
        if isinstance(v, float) and 0 < abs(v) < 1e-6:
            return   # 数値誤差の許容値。座標の設計ではない
        line = self.lines[node.lineno - 1].strip() if node.lineno <= len(self.lines) else ""
        self.found.append((node.lineno, self.func[-1] if self.func else "(直下)", line))


def findings(root: pathlib.Path | None = None) -> list[tuple[str, int, str, str]]:
    """エンジンの各ファイルから、生の数値を探す。

    Args:
        root: 探すディレクトリ。省略するとこのパッケージ自身。

    Returns:
        (ファイル名, 行, 関数名, その行) の並び。行の昇順。

    Raises:
        なし。
    """
    root = root or pathlib.Path(__file__).parent
    out: list[tuple[str, int, str, str]] = []
    for path in sorted(root.glob("*.py")):
        if path.name in ("lint_values.py", "tokens.py", "__init__.py"):
            continue  # トークンの定義そのものは、値が書かれている場所である
        src = path.read_text(encoding="utf-8")
        f = _Finder(src)
        f.visit(ast.parse(src))
        for lineno, func, line in f.found:
            out.append((path.name, lineno, func, line))
    return out


def main() -> None:
    """一覧を印字する。

    Returns:
        なし。

    Raises:
        なし。
    """
    rows = findings()
    by_file: dict[str, int] = {}
    for name, _, _, _ in rows:
        by_file[name] = by_file.get(name, 0) + 1
    print(f"生の数値: {len(rows)} 箇所")
    for name, n in sorted(by_file.items(), key=lambda kv: -kv[1]):
        print(f"  {name:<26}{n:>3}")
    print()
    for name, lineno, func, line in rows:
        print(f"{name}:{lineno} [{func}] {line[:88]}")


if __name__ == "__main__":
    main()
