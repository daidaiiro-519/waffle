"""図の見た目と寸法を、1箇所に集める。

CSSに書くもの（色・太さ・書体）と、座標計算に要るもの（余白・行の高さ）を
分けて持つ。散らばっていると、直すたびに探し回ることになる。
"""

# 座標の計算に使う寸法。Python側が知る必要があるもの
GEOM = {
    "box_pad_x": 18, "box_pad_y": 10,          # 箱の内側の余白
    "head_h": 24, "row_h": 16,                 # 区画の見出しと行
    "node_sep": 0.5, "rank_sep": 0.75,         # 節点と段の間隔（インチ）
    "sym_len": 13,                             # 端の記号の長さ
    "font_name": 12, "font_row": 11, "font_edge": 10,
    "seq_col": 170, "seq_row": 42, "seq_head": 46, "seq_note": 34,
    "lane_label": 110, "lane_track": 460, "lane_row": 30,
    "pad": 16,
}

# CSSに渡す見た目。ページ側のトークンを参照し、ここでは対応づけだけを持つ
LOOK = """
  :root{
    --fig-line:var(--rule);
    --fig-line-w:1.2px;
    --fig-sym:var(--ink-faint);
    --fig-sym-w:1.4px;
    --fig-box-fill:var(--surface-2);
    --fig-box-stroke:var(--rule);
    --fig-box-radius:5px;
    --fig-accent:var(--acc);
    --fig-accent-bg:var(--acc-bg);
    --fig-warn:var(--warn);
    --fig-warn-bg:var(--warn-bg);
    --fig-text:var(--ink);
    --fig-text-soft:var(--ink-soft);
    --fig-text-faint:var(--ink-faint);
    --fig-font:var(--sans);
    --fig-font-mono:var(--mono);
    --fig-size-name:12px;
    --fig-size-row:11px;
    --fig-size-edge:10px;
    --fig-size-small:9px;
    --fig-group-stroke:var(--acc);
    --fig-group-dash:5 4;
    --fig-track:var(--rule-soft);
    --fig-tone-0:var(--acc);
    --fig-tone-1:var(--warn);
    --fig-tone-2:#7A4368;
    --fig-tone-3:#8A8F98;
  }
"""