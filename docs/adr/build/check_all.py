"""生成した頁を、3つの検査へまとめて通す。

  1. 表   ── 見出しとセルの数が合っているか
  2. 整合 ── 他の決定への言及に付けた状態、落とすと決めた語の残り
  3. 図   ── 文字が箱からはみ出していないか

図の「線と文字の衝突」だけは機械で見ていない。そこは PNG を目で見る。
"""
from __future__ import annotations

import pathlib
import sys

S = pathlib.Path(__file__).parent
sys.path.insert(0, str(S))

import check_tables      # noqa: E402
import check_consistency  # noqa: E402
import check_fig_text    # noqa: E402


def main(argv: list[str]) -> int:
    paths = [pathlib.Path(a) for a in argv[1:]]
    if not paths:
        # 既定は「生きている頁」だけ。廃止・取り下げ済みは直さないので見ない
        paths = [S.parent / f"{n}.html" for n in check_consistency.LIVE]
        paths = [p for p in paths if p.exists()]

    print("■ 表 ── 見出しとセルの数")
    tbl = 0
    for p in paths:
        n = check_tables.check(p, verbose=False)
        if n:
            print(f"   × {p.name}: 列ずれ {n}")
            tbl += n
    print(f"   {'合っている' if not tbl else f'列ずれ {tbl} 件'}\n")

    print("■ 図 ── 文字のはみ出し")
    fig = sum(check_fig_text.check(p) for p in paths)
    print(f"   {'はみ出し無し' if not fig else f'はみ出し {fig} 件'}\n")

    print("■ 整合 ── 状態の言及と、落とした語")
    con = check_consistency.main()

    total = tbl + fig + con
    print(f"\n合計: {total} 件")
    print("※ 図の線と文字の衝突は機械で見ていない。PNG を目で確かめること。")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
