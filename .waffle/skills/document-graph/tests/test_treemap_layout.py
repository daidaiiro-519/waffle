import treemap_layout as tl


def test_normalize_sizes_proportional_to_area():
    sizes = tl.normalize_sizes([1, 1, 2], 100, 100)
    assert sum(sizes) == 10000
    assert sizes[2] == 5000


def test_normalize_sizes_zero_total_returns_zeros():
    assert tl.normalize_sizes([0, 0], 100, 100) == [0.0, 0.0]


def test_squarify_single_size_fills_canvas():
    rects = tl.squarify([100.0], 0, 0, 10, 10)
    assert rects == [(0, 0, 10.0, 10.0)]


def test_squarify_covers_total_area():
    sizes = tl.normalize_sizes([3, 1, 1, 1], 40, 40)
    rects = tl.squarify(sizes, 0, 0, 40, 40)
    covered = sum(w * h for _, _, w, h in rects)
    assert round(covered) == 1600


def test_squarify_empty_sizes_returns_empty():
    assert tl.squarify([], 0, 0, 10, 10) == []
