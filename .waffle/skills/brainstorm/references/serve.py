#!/usr/bin/env python3
"""承認の画面を配り、押された回答を1件ずつファイルに落とす小さなサーバー。

    python3 serve.py <配るディレクトリ> [--port 8731] [--answers .waffle/answers]

画面からの POST /answer を受け、本文（JSON）を `<answers>/<日時>.json` に書く。
回答は消さない ── 何を差し戻したかが、あとから順に読めるようにするためである。

形は answer-sheet.schema.json が決めるが、ここでは**素の形だけ**を見る
（必須の欄が在るか、諾否が決められた値か）。中身が妥当かは機械には分からない。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERDICTS = {"approved", "returned", "unanswered"}
REASONS = {"もっと単純に", "前提が違う", "別の道も見たい"}


def _fault(body: dict) -> list[str]:
    """回答1件の素の形を見る。返るのは、直すべきことの一覧（空なら通る）。"""
    bad: list[str] = []
    if not isinstance(body, dict):
        return ["いちばん外側が object ではない"]
    for key in ("board", "answeredAt", "answers"):
        if key not in body:
            bad.append(f"{key} が無い")
    answers = body.get("answers")
    if not isinstance(answers, list) or not answers:
        bad.append("answers が、1件以上の配列ではない")
        return bad
    for i, a in enumerate(answers):
        where = f"answers[{i}]"
        if not isinstance(a, dict):
            bad.append(f"{where} が object ではない")
            continue
        if not a.get("questionId"):
            bad.append(f"{where}.questionId が無い")
        verdict = a.get("verdict")
        if verdict not in VERDICTS:
            bad.append(f"{where}.verdict が {sorted(VERDICTS)} のどれでもない（{verdict!r}）")
        reason = a.get("returnReason")
        if verdict == "returned" and reason not in REASONS:
            bad.append(f"{where}.returnReason が {sorted(REASONS)} のどれでもない（{reason!r}）")
        if verdict != "returned" and reason not in (None, ""):
            bad.append(f"{where}.returnReason は、差し戻し以外では空でなければならない")
    return bad


class Handler(SimpleHTTPRequestHandler):
    answers_dir: Path = Path(".waffle/answers")

    def end_headers(self) -> None:  # 文字コードを言わないと、日本語が化ける
        if self.path.endswith(".html") or self.path.endswith("/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):  # type: ignore[override]
        t = super().guess_type(path)
        return t + "; charset=utf-8" if t in ("text/html", "text/plain", "text/css") else t

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:  # noqa: N802  （標準ライブラリの綴りに合わせる）
        if self.path.rstrip("/") != "/answer":
            self._json(404, {"error": "そのあて先は受け付けていない", "path": self.path})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            self._json(400, {"error": "本文が空"})
            return
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self._json(400, {"error": "JSON として読めない", "detail": str(e)})
            return

        bad = _fault(body)
        if bad:
            self._json(422, {"error": "形が合っていない", "faults": bad})
            return

        self.answers_dir.mkdir(parents=True, exist_ok=True)
        name = datetime.now().strftime("%Y%m%dT%H%M%S") + ".json"
        out = self.answers_dir / name
        out.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n = len(body["answers"])
        self._json(200, {"saved": str(out), "count": n,
                         "next": "Claude に一言送ると、この回答が読まれます"})

    def log_message(self, fmt: str, *args) -> None:  # 配信のたびに1行出すのは、うるさい
        if self.command == "POST":
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".", help="画面を置いてあるディレクトリ")
    p.add_argument("--port", type=int, default=8731)
    p.add_argument("--answers", default=".waffle/answers", help="回答を積む先")
    a = p.parse_args()

    Handler.answers_dir = Path(a.answers).resolve()
    root = Path(a.root).resolve()
    if not root.is_dir():
        print(f"配るディレクトリが無い: {root}", file=sys.stderr)
        return 1

    handler = lambda *args, **kw: Handler(*args, directory=str(root), **kw)  # noqa: E731
    with ThreadingHTTPServer(("127.0.0.1", a.port), handler) as httpd:
        print(f"配る  : {root}")
        print(f"積む  : {Handler.answers_dir}")
        print(f"開く  : http://127.0.0.1:{a.port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n止めました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
