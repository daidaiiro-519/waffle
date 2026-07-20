#!/usr/bin/env bash
# ds.sh — design-share 統一CLI（薄いラッパー。実体は ds.py。uv run --script が
# PEP723のインラインメタデータ(boto3/awscrt)を隔離環境へ自動導入する）
#
# 使い方は ds.py の docstring（uv run ds.py help、または引数なし実行）を参照。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec uv run --script "$SCRIPT_DIR/ds.py" "$@"
