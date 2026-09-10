#!/usr/bin/env python3
"""承認の画面から届いた回答のうち、まだ読んでいないものを文脈へ入れる。

Claude Code は自分からターンを始められない。だから回答がファイルに落ちても、
利用者が次に何か書くまで誰も読まない。このHookは、その「次に何か書いたとき」に
未読の回答だけを渡す ── 毎回「回答を読んで」と書かせないためである。

回答はブレストごとに `.brainstorm/<ブレスト>/answers/` へ積まれる。
既読の管理は各 answers の `.read` で行い、回答そのものは消さず書き換えもしない。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".brainstorm"


def _answer_dirs() -> list[Path]:
    """ブレストごとの回答置き場。回答はそのブレストの持ち物である。"""
    if not ROOT.is_dir():
        return []
    return sorted(d for d in ROOT.glob("*/answers") if d.is_dir())


def _read_marks(mark: Path) -> set[str]:
    if not mark.exists():
        return set()
    return {line.strip() for line in mark.read_text(encoding="utf-8").splitlines() if line.strip()}


def _line(a: dict) -> str:
    verdict = {"approved": "承認", "returned": "差し戻し", "unanswered": "未回答"}.get(
        a.get("verdict"), a.get("verdict", "?"))
    head = f"  - {a.get('questionId', '?')} {a.get('title', '')}（{a.get('topic', '')}）: {verdict}"
    if a.get("returnReason"):
        head += f"／理由: {a['returnReason']}"
    if a.get("note"):
        head += f"\n    書き足し: {a['note']}"
    return head


def main() -> int:
    fresh: list[Path] = []
    for d in _answer_dirs():
        seen = _read_marks(d / ".read")
        fresh.extend(p for p in sorted(d.glob("*.json")) if p.name not in seen)
    if not fresh:
        return 0

    out: list[str] = ["[承認の画面からの回答]まだ読んでいないものがあります。"]
    used: list[Path] = []
    for p in fresh:
        try:
            body = json.loads(p.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            out.append(f"- {p.name}: JSON として読めないので飛ばしました")
            used.append(p)
            continue
        answers = body.get("answers") or []
        out.append(f"- {p.parent.parent.name} / {p.name}　時刻: {body.get('answeredAt', '?')}")
        out.extend(_line(a) for a in answers if isinstance(a, dict))
        used.append(p)

    out.append("承認されたものは決まりとして盤面へ記録し、"
               "差し戻されたものは理由と書き足しを材料に、直した答えを1つ出してください。")
    print("\n".join(out))

    for p in used:
        mark = p.parent / ".read"
        with mark.open("a", encoding="utf-8") as f:
            f.write(p.name + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
