"""スタイルの解決 ── CSSのカスケードに相当する。

出どころは3段。テーマの既定値 → role によるクラス的な上書き → その場限りの
インライン上書き。後のものが前のものに勝つ。トークンの値がさらに別のトークン名を
指していたら、指し先の値へ解決する（`color.box-fill: "color.accent-bg"` のように）。

値に妥当な範囲があるトークン(TOKEN_RANGES参照)は、解決のたびにその範囲へ
照らして検査する。範囲外の値を渡すレンダリングが崩れて気づくのではなく、
その場で例外にする。
"""
from __future__ import annotations

from .tokens import DEFAULT_THEME, ROLE_OVERRIDES, TOKEN_RANGES


class TokenRangeError(ValueError):
    """範囲付きトークンに、範囲外の値が渡されたときに送出する。"""


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
                   theme: dict | None = None) -> dict:
    """role とインライン上書きから、実際に使う値の辞書を組み立てる。

    Args:
        role: "plain" / "focus" / "muted" など、コンポーネントに与える意味役割。
        overrides: 呼び出し側がその場で指定する上書き（インラインstyleに相当）。
        theme: 差し替えるテーマ。省略時は DEFAULT_THEME。

    Returns:
        トークン名 → 解決済みの値、の辞書。

    Raises:
        TokenRangeError: 範囲を持つトークンに、範囲外の値が渡されたとき。
    """
    theme = theme or DEFAULT_THEME
    merged = dict(theme)
    merged.update(ROLE_OVERRIDES.get(role, {}))
    if overrides:
        merged.update(overrides)
    resolved = {k: _deref(v, theme) for k, v in merged.items()}
    _check_ranges(resolved)
    return resolved
