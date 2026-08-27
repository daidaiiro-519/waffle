"""層1 ── 見た目の解決。カスケードの優先順と、範囲外の値を弾くこと。"""
from __future__ import annotations

import pytest

from svg_engine.registry import known_kinds, render_component
from svg_engine.style import TokenRangeError, resolve_style
from svg_engine.tokens import DEFAULT_THEME, TOKEN_RANGES


class TestCascade:
    def test_何も指定しなければテーマの値が出る(self):
        s = resolve_style()
        assert s["font.size"] == DEFAULT_THEME["font.size"]

    def test_役割はテーマより強い(self):
        assert resolve_style("focus") != resolve_style("plain")

    def test_その場の上書きは役割より強い(self):
        s = resolve_style("focus", {"size.stroke-width": 3.0})
        assert s["size.stroke-width"] == 3.0

    def test_差し替えたテーマが土台になる(self):
        theme = dict(DEFAULT_THEME, **{"font.size": 20.0})
        assert resolve_style(theme=theme)["font.size"] == 20.0

    def test_トークン名を指す値は指し先までたどる(self):
        s = resolve_style(overrides={"color.ink": "color.accent"})
        assert s["color.ink"] == DEFAULT_THEME["color.accent"]


class TestRanges:
    @pytest.mark.parametrize("key", sorted(TOKEN_RANGES))
    def test_範囲の下と上を外れたら描く前に例外になる(self, key):
        lo, hi = TOKEN_RANGES[key]
        with pytest.raises(TokenRangeError):
            resolve_style(overrides={key: lo - 1})
        with pytest.raises(TokenRangeError):
            resolve_style(overrides={key: hi + 1})

    @pytest.mark.parametrize("key", sorted(TOKEN_RANGES))
    def test_範囲の中の値は通る(self, key):
        lo, hi = TOKEN_RANGES[key]
        assert resolve_style(overrides={key: (lo + hi) / 2})[key] == (lo + hi) / 2

    def test_既定のテーマ自身が範囲を守っている(self):
        resolve_style()


class TestRegistry:
    def test_台帳に無い部品は名前を挙げて断る(self):
        with pytest.raises(KeyError):
            render_component("そんな部品はない", {}, resolve_style())

    def test_例のファイルを読み込まなくても基本の部品は登録済み(self):
        assert {"box", "edge", "frame"} <= set(known_kinds())
