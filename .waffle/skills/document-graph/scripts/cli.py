#!/usr/bin/env python3
"""cli.py — document-graph CLIエントリポイント。

  document-graph add <path> [--alias ALIAS] [--format md|html]
  document-graph list
  document-graph remove <alias>
  document-graph serve [--port 4173]

config.jsonは手作業編集を前提とせず、このCLIの操作結果として作成・変更される
（brainstorm-document-graph-skill.md 論点2の合意決定）。
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as config_mod  # noqa: E402
import graph_index  # noqa: E402
import server as server_mod  # noqa: E402


def cmd_add(args: argparse.Namespace) -> int:
    config_path = config_mod.DEFAULT_CONFIG_PATH
    sources_dir = config_mod.DEFAULT_SOURCES_DIR
    try:
        result = config_mod.add_source(
            args.path, alias=args.alias, fmt=args.format, config_path=config_path, sources_dir=sources_dir
        )
    except config_mod.ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"追加しました: alias={result['alias']} format={result['format']} path={result['path']}")
    print(f"  symlink同期: {result['syncStatus']}")

    config = config_mod.load_config(config_path)
    graph = graph_index.scan_sources(sources_dir, config["sources"])
    missing = graph["contractMissing"].get(result["alias"], 0)
    total = graph["contractTotal"].get(result["alias"], 0)
    print(f"  契約チェック: frontmatter/meta未検出 {missing}/{total} 件")
    for w in graph["warnings"]:
        print(f"  warning: {w}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    sources = config_mod.list_sources(config_mod.DEFAULT_CONFIG_PATH)
    if not sources:
        print("登録済みのソースはありません。`document-graph add <path>` で追加してください。")
        return 0
    for s in sources:
        print(f"{s['alias']}\t{s['format']}\t{s['path']}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    ok = config_mod.remove_source(
        args.alias, config_path=config_mod.DEFAULT_CONFIG_PATH, sources_dir=config_mod.DEFAULT_SOURCES_DIR
    )
    if not ok:
        print(f"error: alias '{args.alias}' は登録されていません", file=sys.stderr)
        return 1
    print(f"削除しました: alias={args.alias}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    server_mod.serve(port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="document-graph")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="ソース（フォルダ/ファイル）を登録する")
    p_add.add_argument("path")
    p_add.add_argument("--alias", default=None)
    p_add.add_argument("--format", choices=["md", "html"], default=None)
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="登録済みソースを一覧する")
    p_list.set_defaults(func=cmd_list)

    p_remove = sub.add_parser("remove", help="ソースを削除する")
    p_remove.add_argument("alias")
    p_remove.set_defaults(func=cmd_remove)

    p_serve = sub.add_parser("serve", help="ローカルサーバーを起動する")
    p_serve.add_argument("--port", type=int, default=server_mod.DEFAULT_PORT)
    p_serve.set_defaults(func=cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
