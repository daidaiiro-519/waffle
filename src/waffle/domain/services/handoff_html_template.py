"""handoff_html_template — HandoffSchemaの確定デザイン（Pattern G）を、
実際の値を差し込んだ自己完結HTMLとして生成する。uc-render-handoff-templateが使う
（tech-lead-advisorの助言により、固定テンプレートはコード内定数として持つ。
schema側には技術詳細を持たせない）。
"""
from __future__ import annotations

from html import escape as _e

from waffle.domain.services.completion_image_layout import MARGIN_LEFT, NODE_HEIGHT

_LABEL_MARGIN_PAD = 14
_LABEL_WIDTH = MARGIN_LEFT - _LABEL_MARGIN_PAD - 6

_CSS = """
@font-face { font-family: "Ledger Slab"; src: local("Roboto Slab"), local("Georgia"); }
:root {
  --paper: #f3f1ec; --ink: #23241f; --ink-dim: #63645a; --ink-faint: #8c8d80;
  --line: #ddd9cd; --surface: #ffffff; --surface-sunken: #faf9f5;
  --accent: #2f5c46; --accent-soft: #e6f0ea; --accent-ink: #ffffff;
  --shadow: 0 1px 2px rgba(35,36,31,0.04), 0 4px 14px rgba(35,36,31,0.05);
  --mono: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;
  --sans: -apple-system, "Segoe UI", "Hiragino Sans", "Yu Gothic", sans-serif;
  --serif: "Ledger Slab", "Hiragino Mincho ProN", Georgia, serif;
}
:root[data-theme="dark"] {
  --paper: #1b1c18; --ink: #eceae2; --ink-dim: #b0af9f; --ink-faint: #7c7b6d;
  --line: #37382f; --surface: #232420; --surface-sunken: #1f201c;
  --accent: #82c4a4; --accent-soft: #1c332a; --accent-ink: #14211b;
  --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 6px 18px rgba(0,0,0,0.25);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #1b1c18; --ink: #eceae2; --ink-dim: #b0af9f; --ink-faint: #7c7b6d;
    --line: #37382f; --surface: #232420; --surface-sunken: #1f201c;
    --accent: #82c4a4; --accent-soft: #1c332a; --accent-ink: #14211b;
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 6px 18px rgba(0,0,0,0.25);
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--sans); line-height: 1.7; -webkit-font-smoothing: antialiased; }
.wrap { max-width: 780px; margin: 0 auto; padding: 3rem 1.5rem 6rem; }
header.masthead { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: var(--shadow); padding: 1.6rem 1.8rem; margin-bottom: 2rem; }
.masthead .kicker { font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-faint); }
h1 { font-family: var(--serif); font-size: clamp(1.5rem, 3.6vw, 2.05rem); font-weight: 600; margin: 0.35rem 0 0.7rem; text-wrap: balance; }
.masthead dl { display: grid; grid-template-columns: auto 1fr; gap: 0.25rem 1rem; font-family: var(--mono); font-size: 0.78rem; color: var(--ink-faint); margin-top: 0.6rem; }
.masthead dt { white-space: nowrap; }
.masthead dd { margin: 0; color: var(--ink-dim); overflow-wrap: anywhere; }
.table-scroll { overflow-x: auto; }
.table-scroll table { border-collapse: collapse; width: 100%; min-width: max-content; }
section { margin-bottom: 1.6rem; }
h2 { font-family: var(--mono); font-size: 0.74rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-faint); margin: 0 0 0.9rem 0.2rem; }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: var(--shadow); padding: 1.5rem 1.6rem; }
.flow-card { overflow-x: auto; }
.flow-card svg { display: block; min-width: 660px; }
.flow-box rect { fill: var(--surface-sunken); stroke: var(--line); stroke-width: 1.3; rx: 10; }
.flow-box.new rect { fill: var(--accent-soft); stroke: var(--accent); stroke-width: 1.4; stroke-dasharray: 3 3; }
.flow-box.new .flow-html .title { font-weight: 700; color: var(--accent); }
.flow-arrow { stroke: var(--ink-faint); stroke-width: 1.4; fill: none; marker-end: url(#arrow); }
.flow-arrow.dep { stroke: var(--accent); stroke-dasharray: 4 3; }
.flow-num circle { fill: var(--accent-soft); stroke: var(--accent); stroke-width: 1.2; }
.flow-num text { font-family: var(--mono); font-size: 10px; font-weight: 700; fill: var(--accent); }
.flow-caption-svg { font-family: var(--mono); font-size: 9.5px; fill: var(--ink-faint); text-anchor: middle; }
.flow-caption-html { height: 100%; display: flex; align-items: center; font-family: var(--mono); font-size: 9.5px; line-height: 1.3; color: var(--ink-faint); text-align: left; overflow-wrap: break-word; word-break: break-word; }
.flow-split { stroke: var(--ink-faint); stroke-width: 1.2; stroke-dasharray: 2 3; }
.flow-html { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: var(--mono); font-size: 11px; line-height: 1.4; color: var(--ink); text-align: center; overflow-wrap: break-word; word-break: break-word; padding: 0 4px; }
.flow-html .title { font-weight: 600; }
.flow-html .sub { color: var(--ink-faint); font-size: 9.5px; margin-top: 2px; }
.legend { display: flex; gap: 1.4rem; margin-top: 1rem; font-family: var(--mono); font-size: 0.72rem; color: var(--ink-faint); flex-wrap: wrap; }
.legend span { display: inline-flex; align-items: center; gap: 0.4rem; }
.legend .swatch { width: 0.9rem; height: 0.9rem; border-radius: 3px; }
.legend .swatch.existing { background: var(--surface-sunken); border: 1.3px solid var(--line); }
.legend .swatch.new { background: var(--accent-soft); border: 1.4px dashed var(--accent); }
.progress-rail { display: flex; align-items: center; margin-bottom: 1.3rem; }
.rail-step { display: flex; flex-direction: column; align-items: center; flex: 1; min-width: 0; }
.rail-step .dot { width: 1.3rem; height: 1.3rem; border-radius: 50%; background: var(--surface-sunken); border: 1.5px solid var(--line); flex-shrink: 0; }
.rail-step.done .dot { background: var(--ink-faint); border-color: var(--ink-faint); }
.rail-step.current .dot { background: var(--accent); border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-soft); }
.rail-step .label { font-family: var(--mono); font-size: 0.68rem; color: var(--ink-faint); margin-top: 0.5rem; text-align: center; }
.rail-step.current .label { color: var(--accent); font-weight: 600; }
.rail-connector { flex: 1.4; height: 1.5px; background: var(--line); margin-bottom: 1.3rem; }
.rail-connector.done { background: var(--ink-faint); }
.coverage-list { border-top: 1px solid var(--line); padding-top: 1rem; }
.review-row { display: flex; align-items: baseline; justify-content: space-between; gap: 0.5rem 1.2rem; flex-wrap: wrap; padding: 0.55rem 0; }
.review-row .who { font-family: var(--mono); font-size: 0.85rem; color: var(--ink); flex-shrink: 0; }
.review-row .detail { font-family: var(--mono); font-size: 0.77rem; color: var(--ink-faint); font-variant-numeric: tabular-nums; text-align: right; overflow-wrap: anywhere; }
.tabs-card { padding: 0; overflow: hidden; }
.tabs input { position: absolute; opacity: 0; pointer-events: none; }
.tab-labels { display: flex; flex-wrap: wrap; gap: 0.4rem; padding: 0.9rem 1rem 0; }
.tab-labels label { padding: 0.55rem 1.1rem; border-radius: 999px; font-family: var(--mono); font-size: 0.78rem; letter-spacing: 0.02em; color: var(--ink-dim); cursor: pointer; background: var(--surface-sunken); border: 1px solid var(--line); overflow-wrap: anywhere; text-align: center; }
#tab1:checked ~ .tab-labels label[for="tab1"], #tab2:checked ~ .tab-labels label[for="tab2"], #tab3:checked ~ .tab-labels label[for="tab3"] { color: var(--accent-ink); background: var(--accent); border-color: var(--accent); }
.tab-panel { display: none; padding: 1.5rem 1.7rem 1.8rem; }
#tab1:checked ~ .tab-panels #panel1, #tab2:checked ~ .tab-panels #panel2, #tab3:checked ~ .tab-panels #panel3 { display: block; }
.entry { border-top: 1px solid var(--line); padding: 1.1rem 0; max-width: 60ch; }
.entry:first-child { border-top: none; padding-top: 0; }
.entry-head { display: flex; gap: 0.4rem; margin-bottom: 0.55rem; }
.entry-head .badge { font-family: var(--mono); font-size: 0.7rem; padding: 0.15rem 0.6rem; border-radius: 999px; background: var(--surface-sunken); border: 1px solid var(--line); color: var(--ink-dim); }
.entry-viewpoint { font-weight: 600; margin-bottom: 0.5rem; line-height: 1.55; overflow-wrap: anywhere; }
.entry-consideration { color: var(--ink-dim); font-size: 0.93rem; line-height: 1.75; overflow-wrap: anywhere; }
.empty-state { font-size: 0.9rem; color: var(--ink-faint); font-style: italic; }
.constraint-item { display: flex; gap: 0.9rem; align-items: baseline; max-width: 60ch; padding: 0.9rem 0; border-top: 1px solid var(--line); }
.constraint-item:first-child { border-top: none; padding-top: 0; }
.constraint-item .num { font-family: var(--mono); color: var(--accent); background: var(--accent-soft); font-size: 0.72rem; flex-shrink: 0; width: 1.7rem; height: 1.7rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.constraint-item p { margin: 0; color: var(--ink-dim); font-size: 0.93rem; line-height: 1.75; overflow-wrap: anywhere; }
.reading-card { margin-top: 0.9rem; }
.reading-card h3 { font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-faint); margin: 0 0 0.9rem; }
.reading-steps { list-style: none; margin: 0; padding: 0; counter-reset: step; }
.reading-steps li { counter-increment: step; display: flex; gap: 0.85rem; align-items: baseline; padding: 0.65rem 0; border-top: 1px solid var(--line); max-width: 62ch; }
.reading-steps li:first-child { border-top: none; padding-top: 0; }
.reading-steps li::before { content: counter(step); font-family: var(--mono); font-size: 0.72rem; color: var(--accent); background: var(--accent-soft); flex-shrink: 0; width: 1.5rem; height: 1.5rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.reading-steps p { margin: 0; font-size: 0.9rem; color: var(--ink-dim); line-height: 1.7; }
.reading-steps strong { color: var(--ink); font-weight: 600; }
a:focus-visible, label:focus-within { outline: 2px solid var(--accent); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""

_RAIL_STEPS = ["ブレスト提案", "advisor<br>レビュー", "ブレスト完了<br>サマリー", "spec作成", "Handoff記録", "実装"]

_KIND_LABELS = {
    "specToImplementation": {
        "kicker": "Handoff Record",
        "spec_dt": "引き継ぎ元spec",
        "tabs": ("spec作成の結論", "実装方針", "実装への申し送り"),
        "rail_current_index": 4,  # Handoff記録
        "section00_suffix": " — 予定される実装配置",
        "new_legend": "新設（今回の実装対象）",
        "review_detail": "viewpoints",
    },
    "brainstormToSpec": {
        "kicker": "ブレスト→specハンドオフ",
        "spec_dt": "これから書くspec",
        "tabs": ("ブレストの結論", "仕様方針", "仕様への申し送り"),
        "rail_current_index": 2,  # ブレスト完了サマリー
        "section00_suffix": " — 予定されるDDD上の配置",
        "new_legend": "新設（今回のブレストの帰結）",
        "review_detail": "classification",
    },
}


def _render_rail(current_index: int) -> str:
    parts = []
    for i, label in enumerate(_RAIL_STEPS):
        state = "done" if i < current_index else ("current" if i == current_index else "")
        parts.append(f'<div class="rail-step {state}"><div class="dot"></div><div class="label">{label}</div></div>')
        if i < len(_RAIL_STEPS) - 1:
            connector_state = "done" if i < current_index else ""
            parts.append(f'<div class="rail-connector {connector_state}"></div>')
    return "\n        ".join(parts)


def _render_svg_nodes(nodes: list[dict]) -> str:
    parts = []
    for i, n in enumerate(nodes, start=1):
        status_class = "new" if n["status"] == "new" else ""
        cx, cy = n["x"], n["y"]
        parts.append(f"""
        <g class="flow-box {status_class}" transform="translate({cx:.1f},{cy:.1f})">
          <rect width="{n['width']:.1f}" height="{n['height']}" rx="10"/>
          <foreignObject x="4" y="4" width="{n['width'] - 8:.1f}" height="{n['height'] - 8}">
            <div xmlns="http://www.w3.org/1999/xhtml" class="flow-html">
              <div class="title">{_e(n['title'])}</div>
              <div class="sub">{_e(n['sub'])}</div>
            </div>
          </foreignObject>
          <g class="flow-num"><circle cx="0" cy="0" r="10"/><text x="0" y="4" text-anchor="middle">{i}</text></g>
        </g>""")
    return "".join(parts)


def _connector_points(from_node: dict, to_node: dict) -> tuple[float, float, float, float]:
    """2ノードを繋ぐ直線の始点・終点を、実際の箱の辺（中心ではない）から求める。
    同じ行（yが同じ）なら左右の辺同士、異なる行なら上下の辺同士を繋ぐ。"""
    fcx = from_node["x"] + from_node["width"] / 2
    fcy = from_node["y"] + from_node["height"] / 2
    tcx = to_node["x"] + to_node["width"] / 2
    tcy = to_node["y"] + to_node["height"] / 2
    if from_node["y"] == to_node["y"]:
        if fcx < tcx:
            return from_node["x"] + from_node["width"], fcy, to_node["x"], tcy
        return from_node["x"], fcy, to_node["x"] + to_node["width"], tcy
    if fcy < tcy:
        return fcx, from_node["y"] + from_node["height"], tcx, to_node["y"]
    return fcx, from_node["y"], tcx, to_node["y"] + to_node["height"]


def _render_svg_arrows(layout: dict) -> str:
    nodes_by_id = {n["id"]: n for n in layout["nodes"]}
    parts = []
    for arrow in layout["containment_arrows"]:
        fx, fy, tx, ty = _connector_points(nodes_by_id[arrow["from_id"]], nodes_by_id[arrow["to_id"]])
        parts.append(f'<path class="flow-arrow" d="M{fx:.1f},{fy:.1f} L{tx:.1f},{ty:.1f}"/>')
    for arrow in layout["relationship_arrows"]:
        fx, fy, tx, ty = _connector_points(nodes_by_id[arrow["from_id"]], nodes_by_id[arrow["to_id"]])
        label_x = (fx + tx) / 2
        label_y = (fy + ty) / 2 - 6
        if arrow["kind"] == "split":
            parts.append(
                f'<path class="flow-split" d="M{fx:.1f},{fy:.1f} L{tx:.1f},{ty:.1f}"/>'
                f'<text class="flow-caption-svg" x="{label_x:.1f}" y="{label_y:.1f}">{_e(arrow["label"])}</text>'
            )
        else:
            parts.append(
                f'<path class="flow-arrow dep" d="M{fx:.1f},{fy:.1f} L{tx:.1f},{ty:.1f}" marker-end="url(#arrow-accent)"/>'
                f'<text class="flow-caption-svg" x="{label_x:.1f}" y="{label_y:.1f}">{_e(arrow["label"])}</text>'
            )
    return "\n        ".join(parts)


def _render_layer_labels(layer_labels: list[dict], viewbox_width: float) -> str:
    parts = []
    for ll in layer_labels:
        top = ll["y"] - NODE_HEIGHT / 2
        parts.append(
            f'<foreignObject class="flow-caption-fo" x="{_LABEL_MARGIN_PAD}" y="{top:.1f}" '
            f'width="{_LABEL_WIDTH}" height="{NODE_HEIGHT}">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" class="flow-caption-html">{_e(ll["label"])}</div>'
            f"</foreignObject>"
        )
    for prev, nxt in zip(layer_labels, layer_labels[1:]):
        divider_y = (prev["y"] + nxt["y"]) / 2
        parts.append(f'<path class="flow-split" d="M0,{divider_y:.1f} H{viewbox_width}"/>')
    return "\n        ".join(parts)


def _render_reading_steps(layers: list[dict], usage_examples: list[str]) -> str:
    if not layers and not usage_examples:
        return ""
    items = []
    for layer in layers:
        items.append(
            f'<li><p><strong>{_e(layer["label"])}</strong>: {_e(layer["description"])}</p></li>'
        )
    reading_ol = f'<ol class="reading-steps">{"".join(items)}</ol>' if items else ""
    reading_h3 = "<h3>読み方</h3>" if items else ""
    return (
        '<div class="card reading-card">'
        f"{reading_h3}{reading_ol}"
        f"{_render_usage_examples(usage_examples)}"
        "</div>"
    )


def _render_legend(nodes: list[dict], new_legend: str) -> str:
    if not any(n["status"] == "new" for n in nodes):
        return ""
    return (
        '<div class="legend">'
        '<span><span class="swatch existing"></span>既存</span>'
        f'<span><span class="swatch new"></span>{_e(new_legend)}</span>'
        "</div>"
    )


def _render_coverage(review_counts: list[dict], review_detail: str) -> str:
    rows = []
    for rc in review_counts:
        if review_detail == "classification":
            total = rc["design"] + rc["impl"]
            detail = f"分類判断 {total}件" if total else "0件"
        else:
            detail_parts = []
            if rc["design"]:
                detail_parts.append(f"設計観点 {rc['design']}件")
            if rc["impl"]:
                detail_parts.append(f"実装観点 {rc['impl']}件")
            detail = "／".join(detail_parts) if detail_parts else "0件"
        rows.append(
            f'<div class="review-row"><span class="who">{_e(rc["advisor"])}</span>'
            f'<span class="detail">{_e(detail)}</span></div>'
        )
    rows.append('<div class="review-row"><span class="who">未解決事項</span><span class="detail">0件</span></div>')
    return "\n        ".join(rows)


def _render_usage_examples(items: list[str]) -> str:
    if not items:
        return ""
    entries = "".join(f"<li><p>{_e(text)}</p></li>" for text in items)
    return (
        '<h3 style="margin-top:1.3rem">使われ方（実際の呼び出し例）</h3>'
        f'<ol class="reading-steps">{entries}</ol>'
    )


def _render_entries(items: list[dict]) -> str:
    if not items:
        return '<p class="empty-state">記録なし。</p>'
    parts = []
    for item in items:
        parts.append(f"""
            <div class="entry">
              <div class="entry-head"><span class="badge">{_e(item['advisor'])}</span></div>
              <div class="entry-viewpoint">{_e(item['viewpoint'])}</div>
              <div class="entry-consideration">{_e(item['consideration'])}</div>
            </div>""")
    return "".join(parts)


def _render_constraints(items: list[str]) -> str:
    if not items:
        return '<p class="empty-state">既知の制約・トレードオフなし。</p>'
    parts = []
    for i, text in enumerate(items, start=1):
        parts.append(f"""
            <div class="constraint-item">
              <span class="num">{i}</span>
              <p>{_e(text)}</p>
            </div>""")
    return "".join(parts)


def render_handoff_html(
    title: str,
    document_id: str,
    spec_ref: str,
    layout: dict,
    layers: list[dict],
    review_counts: list[dict],
    design_viewpoints: list[dict],
    implementation_viewpoints: list[dict],
    constraints: list[str],
    handoff_kind: str = "specToImplementation",
    usage_examples: list[str] | None = None,
) -> str:
    """Handoffの値を、確定済みの固定HTMLテンプレート（Pattern G）へ差し込んだ自己完結HTMLを返す。"""
    svg_width = layout["viewbox_width"]
    svg_height = layout["viewbox_height"]
    kind_labels = _KIND_LABELS[handoff_kind]
    tab1_label, tab2_label, tab3_label = kind_labels["tabs"]
    usage_examples = usage_examples or []
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{_e(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <div class="kicker">{_e(kind_labels["kicker"])}</div>
    <h1>{_e(title)}</h1>
    <dl>
      <dt>{_e(kind_labels["spec_dt"])}</dt><dd>{_e(spec_ref)}</dd>
      <dt>documentId</dt><dd>{_e(document_id)}</dd>
    </dl>
  </header>

  <section>
    <h2>00 完成イメージ{_e(kind_labels["section00_suffix"])}</h2>
    <div class="card flow-card">
      <svg viewBox="0 0 {svg_width} {svg_height}" width="100%" height="{svg_height}">
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 z" fill="var(--ink-faint)"/>
          </marker>
          <marker id="arrow-accent" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 z" fill="var(--accent)"/>
          </marker>
        </defs>
        {_render_layer_labels(layout["layer_labels"], svg_width)}
        {_render_svg_arrows(layout)}
        {_render_svg_nodes(layout["nodes"])}
      </svg>
      {_render_legend(layout["nodes"], kind_labels["new_legend"])}
    </div>
    {_render_reading_steps(layers, usage_examples)}
  </section>

  <section>
    <h2>01 レビュー状況</h2>
    <div class="card">
      <div class="progress-rail">
        {_render_rail(kind_labels["rail_current_index"])}
      </div>
      <div class="coverage-list">
        {_render_coverage(review_counts, kind_labels["review_detail"])}
      </div>
    </div>
  </section>

  <section>
    <h2>02 詳細</h2>
    <div class="card tabs-card">
      <div class="tabs">
        <input type="radio" name="tabs" id="tab1" checked>
        <input type="radio" name="tabs" id="tab2">
        <input type="radio" name="tabs" id="tab3">
        <div class="tab-labels">
          <label for="tab1">{_e(tab1_label)}</label>
          <label for="tab2">{_e(tab2_label)}</label>
          <label for="tab3">{_e(tab3_label)}</label>
        </div>
        <div class="tab-panels">
          <div class="tab-panel" id="panel1">{_render_entries(design_viewpoints)}</div>
          <div class="tab-panel" id="panel2">{_render_entries(implementation_viewpoints)}</div>
          <div class="tab-panel" id="panel3">{_render_constraints(constraints)}</div>
        </div>
      </div>
    </div>
  </section>
</div>
</body>
</html>
"""
