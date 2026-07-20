"""handoff_html_template の単体テスト（SVG矢印生成の正しさに焦点）。"""
from waffle.domain.services.completion_image_layout import compute_layout
from waffle.domain.services.handoff_html_template import render_handoff_html


def _base_kwargs(layout, layers=None, handoff_kind="specToImplementation", usage_examples=None):
    return dict(
        title="タイトル", document_id="handoff-x", spec_ref="uc-x", layout=layout, layers=layers or [],
        review_counts=[], design_viewpoints=[], implementation_viewpoints=[], constraints=[],
        handoff_kind=handoff_kind, usage_examples=usage_examples or [],
    )


def test_層をまたぐ関係矢印は始点と終点のy座標が異なる():
    """
    Given 異なる層に属する2ノード間のrelationships
    When render_handoff_htmlを呼ぶ
    Then 生成されるpathの始点と終点のy座標が一致しない（層をまたいで正しく接続される）
    """
    layers = [
        {"label": "上", "nodes": [{"id": "a", "title": "A", "sub": "", "status": "existing"}]},
        {"label": "下", "nodes": [{"id": "b", "title": "B", "sub": "", "status": "new"}]},
    ]
    layout = compute_layout(layers, [{"from": "a", "to": "b", "kind": "dependency", "label": "依存"}])
    html = render_handoff_html(**_base_kwargs(layout))
    import re
    m = re.search(r'class="flow-arrow dep" d="M([\d.]+),([\d.]+) L([\d.]+),([\d.]+)"', html)
    assert m is not None
    _, fy, _, ty = m.groups()
    assert fy != ty


def test_層ラベルがマージンに描画される():
    """
    Given ラベル付きの2層のlayers
    When render_handoff_htmlを呼ぶ
    Then 各層のlabelテキストがSVG内に出力される
    """
    layers = [
        {"label": "呼出口", "nodes": [{"id": "a", "title": "A", "sub": "", "status": "existing"}]},
        {"label": "コア", "nodes": [{"id": "b", "title": "B", "sub": "", "status": "new"}]},
    ]
    layout = compute_layout(layers, [])
    html = render_handoff_html(**_base_kwargs(layout))
    assert "呼出口" in html
    assert ">コア<" in html


def test_長い層ラベルは折り返し用のforeignObjectで描画されノード列の外に留まる():
    """
    Given ノード領域まで収まらない長さの層ラベル
    When render_handoff_htmlを呼ぶ
    Then ラベルはノードと同じ折り返し可能なforeignObjectで描画され、マージン幅を超えて配置されない
    """
    layers = [
        {"label": "境界づけられたコンテキスト", "nodes": [{"id": "a", "title": "A", "sub": "", "status": "existing"}]},
    ]
    layout = compute_layout(layers, [])
    html = render_handoff_html(**_base_kwargs(layout))
    assert "境界づけられたコンテキスト" in html
    import re
    m = re.search(r'<foreignObject class="flow-caption-fo"[^>]*width="([\d.]+)"[^>]*>', html)
    assert m is not None
    assert float(m.group(1)) <= 96.0


def test_読み方セクションに層ごとの番号付き説明が出力される():
    """
    Given labelとdescriptionを持つ2層のlayers
    When render_handoff_htmlを呼ぶ
    Then 読み方セクションに層ごとの番号付き項目（label＋description）が出力される
    """
    layers = [
        {"label": "呼出口", "description": "CLIとMCPから呼ぶ。", "nodes": [{"id": "a", "title": "A", "sub": "", "status": "existing"}]},
        {"label": "コア", "description": "業務ロジック本体。", "nodes": [{"id": "b", "title": "B", "sub": "", "status": "new"}]},
    ]
    layout = compute_layout(layers, [])
    html = render_handoff_html(**_base_kwargs(layout, layers=layers))
    assert "読み方" in html
    assert "reading-steps" in html
    assert "CLIとMCPから呼ぶ。" in html
    assert "業務ロジック本体。" in html


def test_brainstormToSpec種別ではタブラベルとkickerが切り替わる():
    """
    Given handoff_kind=brainstormToSpec
    When render_handoff_htmlを呼ぶ
    Then ブレスト→spec用のタブラベル・kickerが出力され、spec向けラベルは出力されない
    """
    layout = compute_layout([], [])
    html = render_handoff_html(**_base_kwargs(layout, handoff_kind="brainstormToSpec"))
    assert "ブレストの結論" in html
    assert "ブレスト→specハンドオフ" in html
    assert "実装への申し送り" not in html


def test_split種別の関係は矢印なしの分離線として描画される():
    """
    Given kind=splitのrelationshipsを持つ同じ層の2ノード
    When render_handoff_htmlを呼ぶ
    Then 生成されるpathはflow-splitクラスでmarker-endを持たない
    """
    layers = [{"label": "コア", "nodes": [
        {"id": "a", "title": "A", "sub": "", "status": "existing"},
        {"id": "b", "title": "B", "sub": "", "status": "new"},
    ]}]
    layout = compute_layout(layers, [{"from": "a", "to": "b", "kind": "split", "label": "関心事が異なるため分離"}])
    html = render_handoff_html(**_base_kwargs(layout))
    assert 'class="flow-split"' in html
    assert "関心事が異なるため分離" in html
    assert 'class="flow-arrow dep"' not in html


def test_00見出しはkindごとの接尾辞を持つ():
    """
    Given handoff_kindがspecToImplementation/brainstormToSpecそれぞれ
    When render_handoff_htmlを呼ぶ
    Then 00見出しにkindごとの接尾辞が付く
    """
    layout = compute_layout([], [])
    html_impl = render_handoff_html(**_base_kwargs(layout, handoff_kind="specToImplementation"))
    html_brainstorm = render_handoff_html(**_base_kwargs(layout, handoff_kind="brainstormToSpec"))
    assert "00 完成イメージ — 予定される実装配置" in html_impl
    assert "00 完成イメージ — 予定されるDDD上の配置" in html_brainstorm


def test_凡例の新設表記はkindごとに説明が付く():
    """
    Given 新設ノードを含むlayersとhandoff_kind
    When render_handoff_htmlを呼ぶ
    Then 凡例の「新設」にkindごとの説明が付く
    """
    layers = [{"label": "コア", "nodes": [{"id": "a", "title": "A", "sub": "", "status": "new"}]}]
    layout = compute_layout(layers, [])
    html_impl = render_handoff_html(**_base_kwargs(layout, handoff_kind="specToImplementation"))
    html_brainstorm = render_handoff_html(**_base_kwargs(layout, handoff_kind="brainstormToSpec"))
    assert "新設（今回の実装対象）" in html_impl
    assert "新設（今回のブレストの帰結）" in html_brainstorm


def test_レビュー状況に未解決事項の行が常に出力される():
    """
    Given 任意のreview_counts
    When render_handoff_htmlを呼ぶ
    Then レビュー状況に「未解決事項」の行が出力される
    """
    layout = compute_layout([], [])
    html = render_handoff_html(**_base_kwargs(layout))
    assert '<span class="who">未解決事項</span>' in html
    assert "0件" in html


def test_brainstormToSpec種別のレビュー行は分類判断件数で表示される():
    """
    Given handoff_kind=brainstormToSpecで設計観点・実装観点を持つreview_counts
    When render_handoff_htmlを呼ぶ
    Then レビュー行は「分類判断 N件」（design+implの合計）で表示される
    """
    layout = compute_layout([], [])
    kwargs = _base_kwargs(layout, handoff_kind="brainstormToSpec")
    kwargs["review_counts"] = [{"advisor": "ddd-advisor", "design": 2, "impl": 0}]
    html = render_handoff_html(**kwargs)
    assert "分類判断 2件" in html
    assert "設計観点" not in html


def test_使われ方セクションはitemsがある場合のみ出力される():
    """
    Given usage_examplesを持つ場合と持たない場合
    When render_handoff_htmlを呼ぶ
    Then itemsがある場合のみ「使われ方」セクションが出力される
    """
    layout = compute_layout([], [])
    html_with = render_handoff_html(**_base_kwargs(layout, usage_examples=["waffle x --y z のように呼ぶ。"]))
    html_without = render_handoff_html(**_base_kwargs(layout))
    assert "使われ方（実際の呼び出し例）" in html_with
    assert "waffle x --y z のように呼ぶ。" in html_with
    assert "使われ方" not in html_without


def test_同じ行の関係矢印は始点と終点のy座標が一致する():
    """
    Given 同じ層に属する2ノード間のrelationships
    When render_handoff_htmlを呼ぶ
    Then 生成されるpathの始点と終点のy座標が一致する（水平接続）
    """
    layers = [{"label": "コア", "nodes": [
        {"id": "a", "title": "A", "sub": "", "status": "existing"},
        {"id": "b", "title": "B", "sub": "", "status": "new"},
    ]}]
    layout = compute_layout(layers, [{"from": "b", "to": "a", "kind": "dependency", "label": "再利用"}])
    html = render_handoff_html(**_base_kwargs(layout))
    import re
    m = re.search(r'class="flow-arrow dep" d="M([\d.]+),([\d.]+) L([\d.]+),([\d.]+)"', html)
    assert m is not None
    _, fy, _, ty = m.groups()
    assert fy == ty


def test_headにdocument_graph契約準拠のmetaタグが出力される():
    """
    Given description・tagsを持つHandoff
    When render_handoff_htmlを呼ぶ
    Then headにid/type/title/description/tagsのmetaタグが出力される
    """
    layout = compute_layout([], [])
    kwargs = _base_kwargs(layout)
    kwargs["description"] = "説明文です"
    kwargs["tags"] = ["context:waffle", "kind:handoff"]
    html = render_handoff_html(**kwargs)
    assert '<meta name="id" content="handoff-x">' in html
    assert '<meta name="type" content="Handoff">' in html
    assert '<meta name="title" content="タイトル">' in html
    assert '<meta name="description" content="説明文です">' in html
    assert '<meta name="tags" content="context:waffle, kind:handoff">' in html


def test_descriptionとtagsが無い場合はmetaタグを空文字で出力する():
    """
    Given description・tagsを渡さないHandoff
    When render_handoff_htmlを呼ぶ
    Then エラーにならず、空文字のmetaタグが出力される
    """
    layout = compute_layout([], [])
    html = render_handoff_html(**_base_kwargs(layout))
    assert '<meta name="description" content="">' in html
    assert '<meta name="tags" content="">' in html
