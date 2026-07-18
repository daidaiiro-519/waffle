#!/usr/bin/env bash
# invalidate_pattern.sh — パターンURLを無効化する（エクスポート同伴、データは削除しない）
#
# 合意事項（ブレスト論点4・8）:
#   - 無効化は token:{slug} を "DISABLED" に書き換えるだけ。S3のデータは削除しない
#   - 再公開したい場合は rotate_token.sh（新トークン発行）で行う
#   - 「無効化したがエクスポートを忘れた」を構造的に防ぐため、既定でエクスポートを先に実行する
#
# 使い方: ./invalidate_pattern.sh <slug> [--no-export]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

SLUG="${1:?usage: invalidate_pattern.sh <slug> [--no-export]}"

if [[ "${2:-}" != "--no-export" ]]; then
  "$SCRIPT_DIR/export_pattern.sh" "$SLUG"
fi

kvs_put "token:$SLUG" "DISABLED"

NAME="$(meta_name "$SLUG")"
meta_write "$SLUG" "${NAME:-$SLUG}" "disabled"

echo "無効化しました: https://$DISTRIBUTION_DOMAIN/p/$SLUG/ はまもなく403を返します（エッジ反映まで数秒〜数十秒）。"
echo "データはS3に残っています。再エクスポートは ds.sh export $SLUG、再公開は ds.sh rotate $SLUG で可能です。"
