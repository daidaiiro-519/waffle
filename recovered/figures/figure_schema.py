"""図の宣言の JSON Schema（案）。

document.json は schema に従って埋められる。だから記法は、まず
JSON Schema として書けなければならない。書けない規則は、別の場所で
守る必要がある——それを先に見つけるために、描画より先にこれを書く。
"""

CLAIMS_RELATION = ["つながり", "階層", "包含", "順序", "循環", "やり取り", "対応"]
CLAIMS_AMOUNT = ["全体と部分", "量の大小", "順位", "時間変化",
                 "分布", "偏差", "相関", "流量", "空間"]
CLAIMS = CLAIMS_RELATION + CLAIMS_AMOUNT

# 主張ごとの、欄の必須・禁止。任意はここに書かない
NEED = {
    "つながり":   {"+": ["items", "links"], "-": ["frame"]},
    "階層":       {"+": ["items"],          "-": ["links", "frame"]},
    "包含":       {"+": ["items"],          "-": ["links", "frame"]},
    "順序":       {"+": ["items"],          "-": ["frame"]},
    "循環":       {"+": ["items"],          "-": ["links", "frame"]},
    "やり取り":   {"+": ["items", "links"], "-": []},
    "対応":       {"+": ["items"],          "-": []},
    "全体と部分": {"+": ["items"],          "-": ["links", "frame"]},
    "量の大小":   {"+": ["items", "frame"], "-": ["links"]},
    "順位":       {"+": ["items"],          "-": ["links"]},
    "時間変化":   {"+": ["items", "frame"], "-": ["links"]},
    "分布":       {"+": ["items", "frame"], "-": ["links"]},
    "偏差":       {"+": ["items", "frame"], "-": ["links"]},
    "相関":       {"+": ["items", "frame"], "-": ["links"]},
    "流量":       {"+": ["items", "links"], "-": ["frame"]},
    "空間":       {"+": ["items", "frame"], "-": []},
}

def build(depth=3):
    """深さを有界にした図の宣言のschemaを組む。

    再帰は $ref ではなく、深さのぶんだけ展開する。集約の不変条件
    「再帰は常に有界である」を、schema の構造そのもので満たすため。
    """
    def figure(level):
        inner = {"$comment": "深さの上限に達したので、これ以上は入れ子にできない"} \
            if level == 0 else figure(level - 1)
        item = {
            "type": "object", "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name":  {"type": "string"},
                "value": {"type": "number"},
                "at":    {"type": "array", "items": {"type": "number"},
                          "minItems": 1, "maxItems": 2},
                "span":  {"type": "array", "items": {"type": "number"},
                          "minItems": 2, "maxItems": 2},
                "role":  {"enum": ["plain", "focus", "muted", "start", "end"]},
                "children": {"type": "array", "items": {"$dynamicRef": "#item"}},
                "figure": inner,
            },
        }
        # children は同じ item の形。展開して有界にする
        def item_at(lv):
            it = {k: v for k, v in item.items()}
            it["properties"] = dict(item["properties"])
            it["properties"]["figure"] = ({"$comment": "上限"} if lv == 0
                                          else figure(lv - 1))
            it["properties"]["children"] = ({"type": "array", "maxItems": 0}
                                            if lv == 0 else
                                            {"type": "array", "items": item_at(lv - 1)})
            return it

        base = {
            "type": "object", "additionalProperties": False,
            "required": ["asserts", "reading"],
            "properties": {
                "asserts": {"enum": CLAIMS},
                "reading": {"type": "string"},
                "items": {"type": "array", "items": item_at(level)},
                "links": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["from", "to"],
                    "properties": {
                        "from": {"type": "string"}, "to": {"type": "string"},
                        "name": {"type": "string"}, "ends": {"type": "string"},
                        "weight": {"type": "number"}}}},
                "frame": {"type": "object", "additionalProperties": False,
                          "properties": {
                              "axes": {"type": "array", "items": {
                                  "type": "object", "additionalProperties": False,
                                  "properties": {"unit": {"type": "string"}}}},
                              "bins": {"type": "string"},
                              "baseline": {"type": "number"},
                              "ground": {"type": "string"}}},
                "notes": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["anchor", "note"],
                    "properties": {"anchor": {"type": "string"},
                                   "note": {"type": "string"}}}},
            },
            "allOf": [],
        }
        for claim, rule in NEED.items():
            then = {}
            if rule["+"]:
                then["required"] = rule["+"]
            if rule["-"]:
                then["not"] = {"anyOf": [{"required": [k]} for k in rule["-"]]}
            base["allOf"].append({
                "if": {"properties": {"asserts": {"const": claim}},
                       "required": ["asserts"]},
                "then": then})
        return base
    return figure(depth)


if __name__ == "__main__":
    import json
    s = build()
    print("主張", len(CLAIMS), "種 / 深さの上限 3")
    print("トップの鍵:", list(s["properties"]))
    print("置くものの鍵:", list(s["properties"]["items"]["items"]["properties"]))
    print("条件付きの規則:", len(s["allOf"]), "件")
    print("schemaの大きさ:", len(json.dumps(s)), "bytes")