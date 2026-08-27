#!/usr/bin/env python3
"""図を含む成果物を、描いて1枚残らず見る前に提示させない。

検査が通ることと、絵として成立していることは別である。幾何検査が「崩れ0件」と
出している最中に、矢印が空白を指す・節点の名前が消える・輪が閉じて読めない・
暗色で文字が地に沈む、といった不備が実際に起きた。どれも画像を見ないと分からない。

そこで提示（Artifact）の直前に、その成果物について次の2つが揃っているかを見る。

    1. ページ撮影の道具を、その成果物に対して実行したか
    2. そのとき生成された画像を、1枚残らず Read で読み返したか

2の「1枚残らず」は、枚数を人が申告するのではなく、実行の結果に並んだ画像の名前を
そのまま突き合わせて確かめる。一部だけ見て残りを推測した実例（16枚のうち8枚だけ
見て報告し、残りに重なりがあった）があるため、1枚でも欠けていれば通さない。

SVG断片だけを描く道具では通さない。断片では、明暗の切り替わりや周囲との関係で
起きる不備が見えない（暗色でページに載せて初めて、図の中の文字が地に沈んでいると
分かった実例がある）。

最後にその成果物を書き換えた時点より後の実行・読み返しだけを数える。書き換える前に
見た画像は、いま提示しようとしている図ではない。
"""
from __future__ import annotations

import json
import os
import re
import sys

# ページ全体を撮る道具。SVG断片だけを描く道具はここに含めない。
_SHOOT = "tools/shoot.py"
_WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
_PNG_LINE = re.compile(r"(\S+\.png)\s*$", re.M)


def _events(transcript_path: str) -> list[tuple[str, str, dict, str]]:
    """記録に残った道具の呼び出しと、その結果を、打たれた順に並べる。

    Args:
        transcript_path: 会話の記録ファイルの場所。

    Returns:
        (道具の名前, 呼び出しの識別子, 渡された入力, 結果の文字列) の並び。
        結果がまだ無いものは空文字。読めない場合は空の並び。

    Raises:
        なし。
    """
    try:
        with open(transcript_path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return []

    calls: list[tuple[str, str, dict, str]] = []
    results: dict[str, str] = {}
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = event.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                calls.append((block.get("name", ""), block.get("id", ""),
                              block.get("input", {}) or {}, ""))
            elif block.get("type") == "tool_result":
                body = block.get("content")
                results[block.get("tool_use_id", "")] = (
                    body if isinstance(body, str) else json.dumps(body, ensure_ascii=False))
    return [(n, i, a, results.get(i, "")) for n, i, a, _ in calls]


def _has_diagram(path: str) -> bool:
    try:
        with open(path, encoding="utf-8") as f:
            return "<svg" in f.read()
    except OSError:
        return False


def check(payload: dict) -> str | None:
    """提示してよいかを判定する。

    Args:
        payload: フックへ渡された入力（対象の道具の引数と、記録の場所を含む）。

    Returns:
        提示を拒否する理由。通してよければ None。

    Raises:
        なし。
    """
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
    # 撮った画像は <成果物名>-<明暗>-<通し番号>.png という名前で出る
    belongs = re.compile(rf"/{re.escape(stem)}-[^/]*\.png$")

    expected: set[str] = set()
    seen: set[str] = set()
    for name, _id, args, result in _events(payload.get("transcript_path", "")):
        if name in _WRITE_TOOLS and os.path.basename(str(args.get("file_path", ""))) == basename:
            # 書き換えたので、それまでに撮った画像も見た形跡ももう別の図のもの
            expected.clear()
            seen.clear()
        elif name == "Bash":
            command = str(args.get("command", ""))
            if _SHOOT in command and basename in command:
                # 撮り直したら、前回撮ったものは無効になる（別の絵かもしれない）。
                # だから足し込まず、この回の分で置き換える。同じ出力先へ撮り直した
                # 場合に備えて、見た形跡のほうも同じ名前ぶんだけ捨てる。
                shot = {p for p in _PNG_LINE.findall(result) if belongs.search(p)}
                if shot:
                    expected = shot
                    seen -= shot
        elif name == "Read":
            path = str(args.get("file_path", ""))
            if belongs.search(path):
                seen.add(path)

    if expected and expected <= seen:
        return None

    if not expected:
        return (
            f"[Hook] {basename} は図を含みますが、提示する前にページを撮っていません。\n"
            "- `LD_LIBRARY_PATH=$HOME/.cache/waffle-shoot-libs uv run python "
            f"tools/shoot.py {target} --out-dir <一時ディレクトリ>` を実行してください"
            "（明暗の両方を、縦に分割して撮ります）\n"
            "- そのあと、出てきた PNG を Read で1枚残らず開いて、"
            "矢印の向き・輪が閉じて読めるか・詰まり・見切れが無いことを目で確認してください"
        )

    missing = sorted(expected - seen)
    listed = "\n".join(f"  - {os.path.basename(p)}" for p in missing[:12])
    more = f"\n  ほか {len(missing) - 12} 枚" if len(missing) > 12 else ""
    return (
        f"[Hook] {basename} は撮りましたが、{len(missing)}/{len(expected)} 枚が"
        "読み返されていません。\n"
        f"{listed}{more}\n"
        "一部だけ見て残りを推測しないでください。Read で1枚ずつ開いてから提示してください。\n"
        "崩れを直した場合は、撮り直して全部見直してください。"
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
