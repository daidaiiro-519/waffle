#!/usr/bin/env bash
# dg.sh — document-graph CLIラッパー（design-shareのds.shと同じ立て付け）
#
# 使い方:
#   ./dg.sh add <path> [--alias ALIAS] [--format md|html]   ソースを登録する
#   ./dg.sh list                                            登録済みソース一覧
#   ./dg.sh remove <alias>                                  ソースを削除する
#   ./dg.sh serve [--port 4173]                              ローカルサーバーを起動する
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/cli.py" "$@"
