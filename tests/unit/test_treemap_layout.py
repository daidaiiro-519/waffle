"""treemap_layout の単体テスト。"""
from waffle.domain.services.treemap_layout import normalize_sizes, squarify


def test_normalize_sizesはキャンバス面積に比例配分する():
    sizes = normalize_sizes([1, 1, 2], 100, 100)
    assert sum(sizes) == 10000
    assert sizes == [2500.0, 2500.0, 5000.0]


def test_squarifyは矩形の面積合計がキャンバス面積と一致する():
    sizes = normalize_sizes([5, 3, 2, 1, 1], 400, 300)
    rects = squarify(sizes, 0, 0, 400, 300)
    total_area = sum(w * h for _, _, w, h in rects)
    assert abs(total_area - 400 * 300) < 1e-6


def test_squarifyは矩形が重ならずキャンバス内に収まる():
    sizes = normalize_sizes([10, 6, 4, 2], 300, 200)
    rects = squarify(sizes, 0, 0, 300, 200)
    for x, y, w, h in rects:
        assert x >= -1e-6
        assert y >= -1e-6
        assert x + w <= 300 + 1e-6
        assert y + h <= 200 + 1e-6
        assert w > 0
        assert h > 0


def test_squarifyは入力sizesの件数と同じ数の矩形を返す():
    sizes = normalize_sizes([3, 2, 1], 100, 100)
    rects = squarify(sizes, 0, 0, 100, 100)
    assert len(rects) == 3


def test_squarifyは空リストで空を返す():
    assert squarify([], 0, 0, 100, 100) == []
