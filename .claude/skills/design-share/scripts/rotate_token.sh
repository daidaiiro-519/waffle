#!/usr/bin/env bash
# rotate_token.sh — トークンを再発行する。旧トークンは失効（URLは変わらない）
#
# 合意事項（ブレスト論点8）:
#   - edge-gateはCookie値とKVSの現在値を毎回直接比較するため、
#     KVSの値を書き換えるだけで旧トークン保持者はアクセス不能になる（エッジ反映まで数秒〜数十秒）
#   - 無効化済み（DISABLED）のパターンに対して実行すると再公開になる
#   - 新トークンはこの場で一度だけ表示。平文の永続保存はしない
#
# 使い方: ./rotate_token.sh <slug>
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

SLUG="${1:?usage: rotate_token.sh <slug>}"
TOKEN="$(new_token)"

WAS="$(kvs_get "token:$SLUG")"
kvs_put "token:$SLUG" "$TOKEN"

if [[ "$WAS" == "DISABLED" ]]; then
  NAME="$(meta_name "$SLUG")"
  meta_write "$SLUG" "${NAME:-$SLUG}" "active"
  rebuild_gallery_index  # 再公開をギャラリー一覧へ反映
  echo "無効化済みパターンを再公開しました。"
fi

cat <<MSG

トークンを再発行しました: $SLUG
  URL     : https://$DISTRIBUTION_DOMAIN/p/$SLUG/ （変更なし）
  新トークン: $TOKEN

旧トークンはまもなく無効になります（エッジ反映まで数秒〜数十秒）。新トークンを配布し直してください。
MSG
