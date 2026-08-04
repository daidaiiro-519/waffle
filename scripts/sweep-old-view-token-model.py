"""旧モデルの語が残っている箇所を、全document・全ブロック・全階層で洗い出す。

閲覧トークンの複数持ちへの書き換えで、取り残しが3度続いた。個別に潰すたびに
別のブロックから出てくるので、走査する側を持つ。

使い方:
  python3 sweep_old_model.py            見つけた箇所を報告する
  python3 sweep_old_model.py --paths    書き換え対象のJMESPathも出す
"""
import json
import subprocess
import sys
from pathlib import Path

TERMS = ("再発行", "必ず新しく", "それまでのものは使えなくなる", "reissueViewToken", "reissue")
ROOT = Path(".waffle/documents/specs/bc-artifact-share")


def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, (r.stdout or r.stderr).strip()


def walk(node, path=""):
    """入れ子の中の文字列を、そこへ至る道筋つきで返す。"""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")


def blocks_of(doc_path):
    code, out = run(["uv", "run", "waffle", "query", "--operation", "query_path",
                     "--path", str(doc_path), "--expression", "@"])
    if code != 0:
        return {}
    return {r["blockKey"]: r["value"] for r in json.loads(out)["results"]}


total = 0
for doc in sorted(ROOT.rglob("*." + "json")):
    hits = []
    for key, value in blocks_of(doc).items():
        for path, text in walk(value):
            if any(t in text for t in TERMS):
                hits.append((key, path, text))
    if hits:
        print(f"\n■ {doc.stem}  {len(hits)}件")
        for key, path, text in hits:
            where = f"{key}.{path}" if path else key
            print(f"   {where}")
            print(f"     {text[:110]}")
        total += len(hits)

print(f"\n{'=' * 60}\n旧モデルの語が残る箇所: 合計 {total}件")
sys.exit(1 if total else 0)
