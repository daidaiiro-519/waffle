#!/usr/bin/env bash
# rename_pattern.sh — パターンの表示名を変更する（slug・トークン・公開状態は変えない）
#
# 使い方: ./rename_pattern.sh <slug> "<新しい表示名>"
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

SLUG="${1:?usage: rename_pattern.sh <slug> <new-name>}"
NEWNAME="${2:?usage: rename_pattern.sh <slug> <new-name>}"

# 現在の公開状態を保って名前だけ差し替える
STATUS="$(meta_status "$SLUG")"
[[ -n "$STATUS" ]] || STATUS="active"

meta_write "$SLUG" "$NEWNAME" "$STATUS"
rebuild_gallery_index  # 名称変更をギャラリー一覧へ反映

echo "名前を変更しました: $SLUG → $NEWNAME"
