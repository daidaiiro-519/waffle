"""HTMLページを画像にする ── 出す前に自分で見るための道具。

自動検査は「壊れていない」ことしか言えない。詰まり・読みにくさ・図と本文の
食い違い・明暗への追随は、描いた結果を見ないと分からない。このリポジトリには
SVG断片をPNGにする道具(render_svg_check.py)はあったが、HTMLページ全体を
見る手段が無く、その結果ADRや成果物を「見ないまま」提示していた。

使い方:
    uv run python tools/shoot.py <HTMLパス> [--out-dir DIR]
                                [--width 1280] [--themes light,dark]
                                [--slice 2000]

出力: 出力先に <名前>-<テーマ>-<通し番号>.png を書き、そのパスを1行ずつ出す。
      縦に長いページは --slice の高さで分割するので、Read で1枚ずつ開ける。
"""
from __future__ import annotations

import argparse
import pathlib
import sys


def shoot(path: pathlib.Path, out_dir: pathlib.Path, width: int,
          themes: list[str], slice_h: int) -> list[pathlib.Path]:
    """1つのHTMLを、テーマごと・縦の区切りごとの画像にする。

    Args:
        path: 撮るHTMLファイル。
        out_dir: 画像の出力先。無ければ作る。
        width: 画面の横幅（画素）。
        themes: "light" / "dark" の並び。ページの明暗の指定に使う。
        slice_h: 1枚あたりの縦の高さ（画素）。ページがこれより高ければ分割する。

    Returns:
        書き出した画像のパスの並び。

    Raises:
        RuntimeError: ブラウザが入っていないとき。
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:                       # pragma: no cover
        raise RuntimeError("playwright が入っていません: uv sync --dev") from e

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = path.stem
    written: list[pathlib.Path] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for theme in themes:
            page = browser.new_page(viewport={"width": width, "height": slice_h},
                                    color_scheme=theme,
                                    device_scale_factor=1)
            page.goto(path.resolve().as_uri())
            # 明暗をページ側の指定でも固定する。既定(system)のままだと、
            # ページが data-theme を見る作りのとき片方しか撮れない。
            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
            page.wait_for_timeout(300)
            total = page.evaluate("Math.ceil(document.documentElement.scrollHeight)")
            n = max(1, -(-total // slice_h))
            for i in range(n):
                # 表示領域ぶんスクロールして、そのまま撮る。
                # full_page と clip を併用すると、実在しない要素が写り込む
                # （実測：ページ最上部に、下のほうにある図の一部が現れた）。
                # 検査対象の絵に嘘が混じるので、この方式は使わない。
                top = min(i * slice_h, max(total - slice_h, 0))
                page.evaluate("y => window.scrollTo(0, y)", top)
                page.wait_for_timeout(120)
                dest = out_dir / f"{stem}-{theme}-{i:02d}.png"
                page.screenshot(path=str(dest))
                written.append(dest)
            page.close()
        browser.close()
    return written


def main() -> None:
    """コマンドとして呼ばれたときの入口。

    Returns:
        なし。

    Raises:
        SystemExit: 対象のHTMLが見つからないとき。
    """
    ap = argparse.ArgumentParser(description="HTMLページを画像にする")
    ap.add_argument("html", type=pathlib.Path)
    ap.add_argument("--out-dir", type=pathlib.Path, default=None)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--themes", default="light,dark")
    ap.add_argument("--slice", dest="slice_h", type=int, default=2000)
    a = ap.parse_args()

    if not a.html.exists():
        raise SystemExit(f"見つかりません: {a.html}")
    out = a.out_dir or a.html.parent / "shots"
    paths = shoot(a.html, out, a.width, [t.strip() for t in a.themes.split(",") if t.strip()],
                  a.slice_h)
    for p in paths:
        print(p)
    print(f"{len(paths)} 枚。全部開いて見ること ── 枚数を報告に書く。", file=sys.stderr)


if __name__ == "__main__":
    main()
