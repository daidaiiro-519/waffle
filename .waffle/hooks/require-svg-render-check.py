#!/usr/bin/env python3
"""図を含む成果物を、描いて見る前に提示させない。

手で座標を書いたSVGは、描くまで崩れているかどうかが分からない。座標が数値として
正しく見えることと、絵として成立していることは別で、実際に静的な座標検査を通った図が
囲みを跨いだり辺に密着したりしていた。

そこで提示（Artifact）の直前に、その成果物について次の2つが揃っているかを見る。

    1. render_svg_check.py を、その成果物に対して実行したか
    2. 出てきた画像を Read で読み返したか

1だけでは足りない。スクリプトが報告できるのは規則として書ける崩れだけで、線と文字の
衝突や、そもそも図として伝わらないことは画像を見ないと分からない。2は「見た」ことの
唯一の痕跡である。

最後にその成果物を書き換えた時点より後の実行・読み返しだけを数える。書き換える前に
見た画像は、いま提示しようとしている図ではない。
"""
from __future__ import annotations

import json
import os
import re
import sys

_CHECK_SCRIPT = "render_svg_check.py"
_WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def _events(transcript_path: str) -> list[tuple[str, dict]]:
    """記録に残った道具の呼び出しを、打たれた順に並べる。

    Args:
        transcript_path: 会話の記録ファイルの場所。

    Returns:
        (道具の名前, 渡された入力) の並び。読めない場合は空。

    Raises:
        なし。
    """
    try:
        with open(transcript_path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return []

    found: list[tuple[str, dict]] = []
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = event.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                found.append((block.get("name", ""), block.get("input", {}) or {}))
    return found


def _has_diagram(path: str) -> bool:
    try:
        with open(path, encoding="utf-8") as f:
            return "<svg" in f.read()
    except OSError:
        return False


def check(payload: dict) -> str | None:
    tool_input = payload.get("tool_input", {}) or {}
    if tool_input.get("action") == "list":
        return None
    target = tool_input.get("file_path")
    if not isinstance(target, str) or not target.endswith(".html"):
        return None
    if not _has_diagram(target):
        return None

    stem = os.path.splitext(os.path.basename(target))[0]
    basename = os.path.basename(target)
    # 描いた画像は <成果物名>-<通し番号>.png という名前で出る
    image = re.compile(rf"{re.escape(stem)}-\d+\.png$")

    rendered = False
    looked = False
    for name, args in _events(payload.get("transcript_path", "")):
        if name in _WRITE_TOOLS and os.path.basename(str(args.get("file_path", ""))) == basename:
            # 書き換えたので、それまでに見た画像はもう別の図
            rendered = False
            looked = False
        elif name == "Bash":
            command = str(args.get("command", ""))
            if _CHECK_SCRIPT in command and basename in command:
                rendered = True
        elif name == "Read" and image.search(str(args.get("file_path", ""))):
            looked = True

    if rendered and looked:
        return None

    missing = []
    if not rendered:
        missing.append(
            "図を描いていません。"
            "`uv run --no-project --with resvg-py --with fonttools python3 "
            f".claude/skills/design-structured-html/scripts/render_svg_check.py {target} "
            "--out-dir <一時ディレクトリ>` を実行してください"
        )
    if not looked:
        missing.append(
            "描いた画像を読み返していません。出力された PNG を Read で1枚ずつ開いて、"
            "線と文字の衝突・詰まり・見切れが無いことを目で確認してください"
        )

    return (
        f"[Hook] {basename} は図を含みますが、提示する前の確認が済んでいません。\n"
        + "\n".join(f"- {m}" for m in missing)
        + "\n崩れを直した場合は、描き直して画像をもう一度見てください。"
    )


def main() -> None:
    payload = json.load(sys.stdin)
    message = check(payload)
    if message:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
            }
        }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
