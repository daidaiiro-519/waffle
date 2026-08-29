"""スタイルの解決 ── CSSのカスケードに相当する。

出どころは3段。テーマの既定値 → role によるクラス的な上書き → その場限りの
インライン上書き。後のものが前のものに勝つ。role の中身もテーマが持つので
（`role.focus.color.box-fill` のような平らな名前）、テーマを差し替えれば
「どんな役割があるか」ごと入れ替わる。トークンの値がさらに別のトークン名を
指していたら、指し先の値へ解決する（`color.box-fill: "color.accent-bg"` のように）。

値に妥当な範囲があるトークン(TOKEN_RANGES参照)は、解決のたびにその範囲へ
照らして検査する。範囲外の値を渡すレンダリングが崩れて気づくのではなく、
その場で例外にする。
"""
from __future__ import annotations

from typing import Any

from .tokens import DEFAULT_THEME, PLAIN, ROLE_PREFIX, TOKEN_RANGES


class TokenRangeError(ValueError):
    """範囲付きトークンに、範囲外の値が渡されたときに送出する。"""


class UnknownRoleError(ValueError):
    """テーマが知らない役割を渡されたときに送出する。

    黙って既定で描くと、綴り違いに気づけない ── 実際、旧世代の図が
    'added'/'removed' という表に無い役割を渡し、色が付かないまま描かれていた。
    範囲外のトークン値はその場で例外にしているのだから、ここだけ素通りに
    しない。"""


def _deref(value, theme):
    """値がトークン名を指していたら、指し先の値へたどる（1段だけ。循環はしない前提）。"""
    if isinstance(value, str) and value in theme:
        return theme[value]
    return value


def _check_ranges(resolved: dict) -> None:
    for key, (lo, hi) in TOKEN_RANGES.items():
        if key not in resolved:
            continue
        v = resolved[key]
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        if not (lo <= v <= hi):
            raise TokenRangeError(
                f"トークン '{key}' の値 {v} が妥当な範囲 [{lo}, {hi}] の外にある")


def resolve_style(role: str = "plain", overrides: dict | None = None,
                   theme: dict | None = None) -> dict[str, Any]:
    """role とインライン上書きから、実際に使う値の辞書を組み立てる。

    Args:
        role: コンポーネントに与える意味役割。テーマが `role.<名前>.` で
            定義しているものだけを受け付ける（"plain" は常に有効）。
        overrides: 呼び出し側がその場で指定する上書き（インラインstyleに相当）。
        theme: 差し替えるテーマ。省略時は DEFAULT_THEME。

    Returns:
        トークン名 → 解決済みの値、の辞書。値の型は鍵ごとに決まっている
        （色は文字列、寸法は数、系列の色は文字列の並び）が、鍵が122個ある
        ことと、その場の上書きが何でも入れられることから、型では書き分け
        ない。使う側はどの鍵が何を返すかを知っている ── ここを型で縛るのは
        規約2（段ごとに型が変わる）の仕事で、そのとき Style 型に置き換わる。

    Raises:
        TokenRangeError: 範囲を持つトークンに、範囲外の値が渡されたとき。
        UnknownRoleError: テーマが知らない役割を渡されたとき。
    """
    theme = theme or DEFAULT_THEME
    prefix = f"{ROLE_PREFIX}{role}."
    role_over = {k[len(prefix):]: v for k, v in theme.items() if k.startswith(prefix)}
    if role != PLAIN and not role_over:
        known = sorted({k[len(ROLE_PREFIX):].split(".")[0]
                        for k in theme if k.startswith(ROLE_PREFIX)} | {PLAIN})
        raise UnknownRoleError(
            f"テーマが知らない役割 '{role}' が渡された。使えるのは {known}。"
            f"新しい役割は、テーマへ 'role.{role}.<トークン名>' を足すと増える")
    merged = {k: v for k, v in theme.items() if not k.startswith(ROLE_PREFIX)}
    merged.update(role_over)
    if overrides:
        merged.update(overrides)
    resolved = {k: _deref(v, theme) for k, v in merged.items()}
    _check_ranges(resolved)
    return resolved
