#!/usr/bin/env bash
# gallery.sh — プロジェクト共通トークンで入る「共有ギャラリー」を管理する
#
# ギャラリーは 1つのランディングURL＋1つの共通トークンで、公開中の全パターンを
# 一覧・横断閲覧できる面。共通トークンのCookie(share_project)は各 /p/{slug}/ の
# 横断キーも兼ねる（一度入場すれば各案を再入力なしで開ける）。パターン別トークンとは併用可能。
#
# 使い方:
#   ./gallery.sh init      共通トークンを発行し、ギャラリーページ＋集約インデックスを配置する
#   ./gallery.sh rotate    共通トークンを再発行する（旧共通トークンは失効・URL不変）
#   ./gallery.sh disable   ギャラリーを無効化する（/gallery/ が403。パターン別URLは影響なし）
#   ./gallery.sh url       ギャラリーのURLを表示する（トークンは表示しない）
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

GALLERY_HTML="$SCRIPT_DIR/../references/templates/gallery-page.html"
GALLERY_URL="https://$DISTRIBUTION_DOMAIN/gallery/"

upload_page() { # ギャラリーページ本体を gallery/index.html として配置
  [[ -f "$GALLERY_HTML" ]] || { echo "error: gallery-page.html が見つかりません: $GALLERY_HTML" >&2; exit 1; }
  aws s3 cp "$GALLERY_HTML" "s3://$BUCKET/gallery/index.html" \
    --content-type "text/html; charset=utf-8" >/dev/null
}

cmd="${1:-help}"
case "$cmd" in
  init)
    TOKEN="$(new_token)"
    upload_page
    rebuild_gallery_index
    kvs_put "project:token" "$TOKEN"
    cat <<EOF

共有ギャラリーを有効化しました。
  URL       : $GALLERY_URL
  共通トークン: $TOKEN

このURLと共通トークンを渡した相手は、公開中の全パターンを一覧・横断閲覧できます。
共通トークンはこの一度しか表示されません。URLとは別チャネルで共有相手に渡してください。
再発行は ds.sh gallery rotate、無効化は ds.sh gallery disable で行えます。
EOF
    ;;
  rotate)
    [[ -n "$(gallery_enabled)" ]] || { echo "ギャラリーは未有効化です。先に ds.sh gallery init を実行してください。" >&2; exit 1; }
    TOKEN="$(new_token)"
    kvs_put "project:token" "$TOKEN"
    cat <<EOF

共通トークンを再発行しました（URLは変更なし）。
  URL         : $GALLERY_URL
  新共通トークン: $TOKEN

旧共通トークンはまもなく無効になります（エッジ反映まで数秒〜数十秒）。
EOF
    ;;
  disable)
    kvs_put "project:token" "DISABLED"
    echo "ギャラリーを無効化しました: $GALLERY_URL はまもなく403を返します（エッジ反映まで数秒〜数十秒）。"
    echo "各パターンの個別URL＋個別トークンでのアクセスには影響しません。再有効化は ds.sh gallery init です。"
    ;;
  url)
    echo "$GALLERY_URL"
    ;;
  help|*)
    grep '^#   ' "$0" | sed 's/^#   //'
    ;;
esac
