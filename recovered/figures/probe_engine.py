"""いまのレンダラに、関門1の図を描かせてみる。上限は主張ではなく出力で示す。"""
import sys
sys.path.insert(0, "src")
from waffle.domain.services.completion_image_layout import compute_layout

# 関門1の図が言いたいこと（囲み・左右2面は、そもそも渡す口が無い）
layers = [
    {"label": "問題空間", "nodes": [
        {"id": "biz", "title": "事業領域", "sub": "新設", "status": "new"},
        {"id": "sd", "title": "業務領域", "sub": "移設", "status": "new"}]},
    {"label": "解決空間", "nodes": [
        {"id": "bc", "title": "区切られた文脈", "sub": "既存", "status": "existing"},
        {"id": "uc", "title": "業務ユースケース", "sub": "既存", "status": "existing"},
        {"id": "agg", "title": "集約", "sub": "既存", "status": "existing"}]},
]
rel = [{"from": "uc", "to": "sd", "kind": "dependency", "label": "対応"}]
out = compute_layout(layers, rel)
print("viewBox:", out["viewbox_width"], "x", out["viewbox_height"])
for n in out["nodes"]:
    print(f"  {n['id']:5} x={n['x']:6.1f} y={n['y']:5.1f} w={n['width']:6.1f} h={n['height']}")
print("自動で引かれた包含の矢印:", [(a["from_id"], a["to_id"]) for a in out["containment_arrows"]])
print("宣言した関係の矢印:", [(a["from_id"], a["to_id"], a["kind"]) for a in out["relationship_arrows"]])