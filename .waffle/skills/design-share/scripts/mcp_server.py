#!/usr/bin/env python3
"""mcp_server.py — design-share ローカルMCPサーバ（stdio・依存パッケージなし）。

MCPクライアント（Claude Code等）から管理操作をツールとして呼べるようにする薄い層。
実処理はすべて scripts/ の各シェルスクリプトへ委譲する（CLI/Web UIと同一の実体）。

Claude Codeへの登録例（.mcp.json）:
  {
    "mcpServers": {
      "design-share": {
        "command": "python3",
        "args": [".claude/skills/design-share/scripts/mcp_server.py"],
        "env": { "DESIGN_SHARE_ENV": "/absolute/path/to/design-share.env" }
      }
    }
  }
"""
import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(SCRIPT_DIR, "ds.py")

TOOLS = [
    {
        "name": "list_patterns",
        "description": "デプロイ済みUIパターンの一覧（公開中/無効化済み・slug・更新日）を返す",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "deploy_pattern",
        "description": "UIパターンHTMLをデプロイし、共有URL＋トークンを発行する（トークンは応答に一度だけ含まれる）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "html_path": {"type": "string", "description": "デプロイするHTMLファイルの絶対パス"},
                "display_name": {"type": "string", "description": "パターンの表示名"},
            },
            "required": ["html_path", "display_name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "redeploy_pattern",
        "description": "既存パターンの内容だけを差し替える（URL・トークン・既存コメントはそのまま維持される）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string"},
                "html_path": {"type": "string", "description": "差し替えるHTMLファイルの絶対パス"},
            },
            "required": ["slug", "html_path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "export_pattern",
        "description": "パターンのHTML＋コメント一式をzipエクスポートする（公開状態は変えない）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string"},
                "outdir": {"type": "string", "description": "省略時は ./exports"},
            },
            "required": ["slug"],
            "additionalProperties": False,
        },
    },
    {
        "name": "rotate_token",
        "description": "トークンを再発行する（旧トークン失効・URL不変。無効化済みなら再公開になる）",
        "inputSchema": {
            "type": "object",
            "properties": {"slug": {"type": "string"}},
            "required": ["slug"],
            "additionalProperties": False,
        },
    },
    {
        "name": "disable_pattern",
        "description": "パターンURLを無効化する（既定でzipエクスポートを先に実行。データは削除しない）",
        "inputSchema": {
            "type": "object",
            "properties": {"slug": {"type": "string"}},
            "required": ["slug"],
            "additionalProperties": False,
        },
    },
]


def run_ds(*args: str) -> tuple[bool, str]:
    proc = subprocess.run(["uv", "run", "--script", DS, *args], capture_output=True, text=True)
    return proc.returncode == 0, proc.stdout + proc.stderr


REQUIRED_ARGS = {
    "deploy_pattern": ("html_path", "display_name"),
    "redeploy_pattern": ("slug", "html_path"),
    "export_pattern": ("slug",),
    "rotate_token": ("slug",),
    "disable_pattern": ("slug",),
}


def call_tool(name: str, arguments: dict) -> tuple[bool, str]:
    # 必須引数の欠落はエラーとして返す（KeyErrorでサーバを落とさない）
    missing = [k for k in REQUIRED_ARGS.get(name, ()) if not str(arguments.get(k, "")).strip()]
    if missing:
        return False, f"missing required argument(s): {', '.join(missing)}"
    slug = str(arguments.get("slug", ""))
    if "slug" in arguments and not slug.replace("-", "").replace("_", "").isalnum():
        return False, "invalid slug"
    if name == "list_patterns":
        return run_ds("list")
    if name == "deploy_pattern":
        return run_ds("deploy", str(arguments["html_path"]), str(arguments["display_name"]))
    if name == "redeploy_pattern":
        return run_ds("redeploy", slug, str(arguments["html_path"]))
    if name == "export_pattern":
        extra = [str(arguments["outdir"])] if arguments.get("outdir") else []
        return run_ds("export", slug, *extra)
    if name == "rotate_token":
        return run_ds("rotate", slug)
    if name == "disable_pattern":
        return run_ds("disable", slug)
    return False, f"unknown tool: {name}"


def reply(msg_id, result=None, error=None) -> None:
    res: dict = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        res["error"] = error
    else:
        res["result"] = result
    sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method", "")
        msg_id = msg.get("id")
        if method == "initialize":
            reply(msg_id, {
                "protocolVersion": msg.get("params", {}).get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "design-share", "version": "0.1.0"},
            })
        elif method == "notifications/initialized":
            continue  # 通知には応答しない
        elif method == "tools/list":
            reply(msg_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = msg.get("params", {})
            ok, output = call_tool(params.get("name", ""), params.get("arguments", {}) or {})
            reply(msg_id, {
                "content": [{"type": "text", "text": output.strip() or "(no output)"}],
                "isError": not ok,
            })
        elif msg_id is not None:
            reply(msg_id, error={"code": -32601, "message": f"method not found: {method}"})


if __name__ == "__main__":
    main()
