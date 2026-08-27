"""会話の記録から、書いたきり消えた作業ファイルを取り出す。

一時ディレクトリへ書いたスクリプトはセッションをまたいで消えるが、
書いた内容そのものは記録（jsonl）に残っている。Write の入力と、
Bash のヒアドキュメント（cat > path <<'X' ... X）の本文を拾う。
同じ名前で複数回書かれているものは、いちばん長いものを採る。
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HEREDOC = re.compile(
    r"cat\s+>\s*(?P<path>[^\s<>|;&]+)\s*<<\s*'?(?P<tag>[A-Za-z_][A-Za-z0-9_]*)'?\s*\n"
    r"(?P<body>.*?)\n(?P=tag)\s*$",
    re.S | re.M,
)


def _walk(node):
    """記録の1行から tool_use の入力だけを取り出す。"""
    if isinstance(node, dict):
        if node.get("type") == "tool_use" and isinstance(node.get("input"), dict):
            yield node["name"], node["input"]
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def collect(transcript: pathlib.Path, suffix: str = ".py") -> dict[str, str]:
    """記録を走査し、ファイル名ごとにいちばん長い本文を返す。"""
    best: dict[str, str] = {}

    def offer(path: str, body: str) -> None:
        name = pathlib.PurePosixPath(path).name
        if not name.endswith(suffix):
            return
        if len(body) > len(best.get(name, "")):
            best[name] = body

    with transcript.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            for tool, params in _walk(rec):
                if tool == "Write" and isinstance(params.get("content"), str):
                    offer(str(params.get("file_path", "")), params["content"])
                elif tool == "Bash" and isinstance(params.get("command"), str):
                    for m in HEREDOC.finditer(params["command"]):
                        offer(m.group("path"), m.group("body"))
    return best


def main(argv: list[str]) -> int:
    """記録から取り出して、指定のディレクトリへ書き出す。"""
    if len(argv) < 3:
        print("使い方: recover_from_transcript.py <記録のjsonl> <書き出す先> [名前の正規表現]")
        return 2
    transcript, out = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    keep = re.compile(argv[3]) if len(argv) > 3 else None
    out.mkdir(parents=True, exist_ok=True)

    found = collect(transcript)
    for name, body in sorted(found.items()):
        if keep and not keep.search(name):
            continue
        (out / name).write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
        print(f"{len(body):>7}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
