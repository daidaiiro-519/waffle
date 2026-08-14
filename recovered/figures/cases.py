"""15の主張を、記法で書く。題材はWaffle自身の実際の話に揃える。"""

CASES = [
 ("つながり", {
   "asserts": "つながり",
   "items": [{"name": "CLI"}, {"name": "MCP"}, {"name": "ユースケース", "role": "focus"},
             {"name": "業務サービス"}, {"name": "モデル"}],
   "links": [{"from": "CLI", "to": "ユースケース", "ends": "head:arrow"},
             {"from": "MCP", "to": "ユースケース", "ends": "head:arrow"},
             {"from": "ユースケース", "to": "業務サービス", "name": "呼ぶ", "ends": "head:arrow"},
             {"from": "業務サービス", "to": "モデル", "ends": "head:arrow"}]}),

 ("階層", {
   "asserts": "階層",
   "items": [{"name": "扱う業務", "children": [
       {"name": "業務領域", "role": "focus", "children": [
           {"name": "中核"}, {"name": "一般"}, {"name": "補完"}]},
       {"name": "区切られた文脈", "children": [{"name": "同じ言葉"}, {"name": "集約"}]}]}]}),

 ("包含", {
   "asserts": "包含",
   "items": [{"name": "受け口", "children": [{"name": "CLI"}, {"name": "MCP"}]},
             {"name": "領域", "children": [{"name": "業務サービス"}, {"name": "モデル"}]}],
   "links": [{"from": "受け口", "to": "領域", "ends": "head:arrow"}]}),

 ("順序", {
   "asserts": "順序",
   "items": [{"name": "調べる"}, {"name": "決める"}, {"name": "引き継ぐ"},
             {"name": "作る", "role": "focus"}]}),

 ("循環", {
   "asserts": "循環",
   "items": [{"name": "生成"}, {"name": "測定"}, {"name": "修正"}, {"name": "知識へ還元"}]}),

 ("対応", {
   "asserts": "対応",
   "items": [{"name": "受け入れ基準", "at": [0, 0]}, {"name": "保証シナリオ", "at": [1, 0]},
             {"name": "業務ユースケース", "at": [0, 1]}, {"name": "集約", "at": [0, 2]},
             {"name": "業務サービス", "at": [0, 3]}],
   "frame": {"axes": [{"unit": "仕様の要素"}, {"unit": "対応するもの"}]}}),

 ("全体と部分", {
   "asserts": "全体と部分",
   "items": [{"name": "文章の部品", "value": 10}, {"name": "図の部品", "value": 5}]}),

 ("量の大小", {
   "asserts": "量の大小",
   "items": [{"name": "v8", "value": 31}, {"name": "v9", "value": 10}, {"name": "v10", "value": 4}],
   "frame": {"axes": [{"unit": "版"}, {"unit": "仕様の件数"}]}}),

 ("順位", {
   "asserts": "順位",
   "items": [{"name": "条件による選択", "value": 62}, {"name": "やり取りの順序", "value": 49},
             {"name": "向きのある関係", "value": 30}, {"name": "区画への所属", "value": 21},
             {"name": "一列に並ぶ", "value": 7}]}),

 ("時間変化", {
   "asserts": "時間変化",
   "items": [{"name": "調べる", "span": [0, 3]}, {"name": "決める", "span": [3, 2]},
             {"name": "引き継ぐ", "span": [5, 1], "role": "focus"}, {"name": "作る", "span": [6, 5]}],
   "frame": {"axes": [{"unit": "日"}]}}),

 ("分布", {
   "asserts": "分布",
   "items": [{"name": "2-4", "value": 38}, {"name": "5-8", "value": 64},
             {"name": "9-12", "value": 15}, {"name": "13-16", "value": 8}],
   "frame": {"bins": "節点の数", "axes": [{"unit": "図の枚数"}]}}),

 ("偏差", {
   "asserts": "偏差",
   "items": [{"name": "受け入れ基準", "value": 12}, {"name": "保証シナリオ", "value": -8},
             {"name": "帰る先", "value": 5}, {"name": "操作保証", "value": -20}],
   "frame": {"baseline": 0, "axes": [{"unit": "前の版からの増減"}]}}),

 ("相関", {
   "asserts": "相関",
   "items": [{"name": "文書の検証", "at": [8, 7]}, {"name": "描画", "at": [5, 6]},
             {"name": "設定の読み込み", "at": [2, 2]}, {"name": "配置の検査", "at": [7, 3]}],
   "frame": {"axes": [{"unit": "差別化の大きさ"}, {"unit": "複雑さ"}]}}),

 ("流量", {
   "asserts": "流量",
   "items": [{"name": "構造化データ"}, {"name": "Markdown"}, {"name": "HTML"}],
   "links": [{"from": "構造化データ", "to": "Markdown", "weight": 7},
             {"from": "構造化データ", "to": "HTML", "weight": 3}]}),

 ("空間", {
   "asserts": "空間",
   "items": [{"name": "受け口", "at": [0, 0]}, {"name": "ユースケース", "at": [0, 1]},
             {"name": "業務サービス", "at": [0, 2], "role": "focus"}, {"name": "モデル", "at": [0, 3]}],
   "frame": {"ground": "層", "axes": [{"unit": "外側から内側へ"}]}}),
]