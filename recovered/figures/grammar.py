"""図の記法 ── 書ける形を先に決める。

HTMLが「入れ子の要素＋属性」、CSSが「性質: 値」であるように、
ここでも書ける形は固定で、その中で自由に組む。種類ごとに別の形を
与えない——種類の数だけ形が増えると、それは記法ではなく品揃えになる。

宣言は常に4つの欄だけを持つ:

    asserts   何を主張するか（15のうち1つ）
    items     置くもの。名前・値・位置・役割・入れ子
    links     つなぐもの。から・へ・名前・端の意味・太さ
    frame     読む枠。軸・尺度・区間・基準・既知の座標

どの欄が要り、どの欄を書いてはいけないかは asserts が決める。
これが「決められたルール」の本体であり、描き方はここから従属して決まる。
"""

# 主張 → 書いてよい欄（+ は必須、- は書いてはいけない、? は任意）
RULES = {
    # ── 関係を主張する ──────────────────────────
    "つながり": {"items": "+", "links": "+", "frame": "-",
                 "note": "誰と誰が結ばれているか。位置に意味は無い"},
    "階層":     {"items": "+", "links": "-", "frame": "-",
                 "note": "親子。結びは入れ子から導かれるので書かない"},
    "包含":     {"items": "+", "links": "?", "frame": "-",
                 "note": "どれがどの区画に属するか。入れ子が区画を表す"},
    "順序":     {"items": "+", "links": "?", "frame": "-",
                 "note": "何の後に何が来るか。items の並びが順序そのもの"},
    "循環":     {"items": "+", "links": "-", "frame": "-",
                 "note": "終わりが始まりへ戻る。並びが閉じる"},
    "対応":     {"items": "+", "links": "?", "frame": "?",
                 "note": "どれとどれが対応するか。面をまたぐ／格子で交わる"},

    # ── 量を主張する ───────────────────────────
    "全体と部分": {"items": "+", "links": "-", "frame": "-",
                   "note": "値の合計が全体。軸は要らない"},
    "量の大小":   {"items": "+", "links": "-", "frame": "+",
                   "note": "値そのものを比べる。軸が要る"},
    "順位":       {"items": "+", "links": "-", "frame": "?",
                   "note": "並び順が主張。値は添え物"},
    "時間変化":   {"items": "+", "links": "-", "frame": "+",
                   "note": "枠が時間の軸を持つ。items は区間か点"},
    "分布":       {"items": "+", "links": "-", "frame": "+",
                   "note": "枠が区間を持ち、items はその度数"},
    "偏差":       {"items": "+", "links": "-", "frame": "+",
                   "note": "枠が基準を持ち、items はそこからの差"},
    "相関":       {"items": "+", "links": "-", "frame": "+",
                   "note": "枠が2本の軸を持ち、items は座標を持つ"},
    "流量":       {"items": "+", "links": "+", "frame": "-",
                   "note": "結びが太さを持つ。太さが量"},
    "空間":       {"items": "+", "links": "?", "frame": "+",
                   "note": "枠が既に知られている座標。位置が意味を運ぶ"},
}

# 欄の中で書けるもの（ここも固定。種類ごとに増やさない）
FIELDS = {
    "items": ["name", "value", "at", "role", "children", "span"],
    "links": ["from", "to", "name", "ends", "weight"],
    "frame": ["axes", "bins", "baseline", "ground", "unit"],
}


def check(fig):
    """宣言が規則に合っているかを見る。合わない形は描く前に落とす。"""
    a = fig.get("asserts")
    if a not in RULES:
        return [f"主張 '{a}' は語彙に無い"]
    bad = []
    for slot, need in RULES[a].items():
        if slot == "note":
            continue
        has = bool(fig.get(slot))
        if need == "+" and not has:
            bad.append(f"{a}: {slot} が要る")
        if need == "-" and has:
            bad.append(f"{a}: {slot} は書けない（{RULES[a]['note']}）")
    for slot, allowed in FIELDS.items():
        for one in fig.get(slot) if isinstance(fig.get(slot), list) else []:
            for k in one:
                if k not in allowed:
                    bad.append(f"{a}: {slot} に '{k}' は書けない")
        if slot == "frame" and isinstance(fig.get("frame"), dict):
            for k in fig["frame"]:
                if k not in allowed:
                    bad.append(f"{a}: frame に '{k}' は書けない")
    return bad


if __name__ == "__main__":
    print(f"主張 {len(RULES)} 種 / 欄 {len(FIELDS)} 個 / 欄の中身 "
          f"{sum(len(v) for v in FIELDS.values())} 個\n")
    for name, r in RULES.items():
        need = " ".join(f"{k}{v}" for k, v in r.items() if k != "note")
        print(f"  {name:<6} {need:<28} {r['note']}")