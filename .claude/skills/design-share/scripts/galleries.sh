#!/usr/bin/env bash
# galleries.sh — 名前付きギャラリー（カテゴリ）の管理
#
# 名前付きギャラリーは 1つのURL(/g/{id}/)＋固有トークンで入る「カテゴリ」。所属はタグ式
# （1パターンが複数ギャラリーに所属可）。ギャラリーのトークンCookieは、そのギャラリーに
# 入っているパターンだけを開ける（スコープ）。全体ギャラリー(/gallery/)とは別物。
#
# 使い方:
#   ./galleries.sh create "<表示名>"          新規カテゴリを作成しURL＋トークンを発行
#   ./galleries.sh list                       カテゴリ一覧（id・名前・状態）
#   ./galleries.sh rotate <gslug>             共有トークンを再発行（URL不変・旧失効）
#   ./galleries.sh disable <gslug>            カテゴリを無効化（/g/{gslug}/ が403）
#   ./galleries.sh delete <gslug>             カテゴリを削除（所属も全解除。パターン自体は消えない）
#   ./galleries.sh add <gslug> <pattern-slug>     パターンをカテゴリに追加
#   ./galleries.sh remove <gslug> <pattern-slug>  パターンをカテゴリから外す
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

gurl() { echo "https://$DISTRIBUTION_DOMAIN/g/$1/"; }

require_gslug() { [[ "$1" =~ ^[A-Za-z0-9_-]+$ ]] || { echo "invalid gslug: $1" >&2; exit 1; }; }
require_pattern() { [[ "$1" =~ ^[A-Za-z0-9_-]+$ ]] || { echo "invalid pattern slug: $1" >&2; exit 1; }; }

cmd="${1:-help}"; shift || true
case "$cmd" in
  create)
    NAME="${1:?usage: galleries.sh create \"<表示名>\"}"
    GSLUG="$(new_gslug)"; TOKEN="$(new_token)"
    # 全カテゴリ共用のランディングページを配置（冪等）
    aws s3 cp "$SCRIPT_DIR/../references/templates/gallery-app.html" \
      "s3://$BUCKET/gallery/app.html" --content-type "text/html; charset=utf-8" >/dev/null
    gallery_meta_write "$GSLUG" "$NAME"
    kvs_put "g:$GSLUG" "$TOKEN"
    rebuild_gallery_index
    cat <<EOF

カテゴリ（名前付きギャラリー）を作成しました。
  名前  : $NAME
  URL   : $(gurl "$GSLUG")
  トークン: $TOKEN

このURLとトークンを渡した相手は、このカテゴリに入れたパターンだけを一覧・閲覧できます。
トークンはこの一度だけ表示。パターンの追加は ds.sh galleries add $GSLUG <pattern-slug> です。
EOF
    ;;
  list)
    keys="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "galleries/" --query "Contents[].Key" --output text 2>/dev/null || true)"
    [[ -n "$keys" && "$keys" != "None" ]] || { echo "カテゴリはまだありません。"; exit 0; }
    for k in $keys; do
      [[ -n "$k" && "$k" != "None" ]] || continue
      gs="$(basename "$k" .json)"
      name="$(gallery_meta_name "$gs")"
      tok="$(kvs_get "g:$gs")"
      if [[ "$tok" == "DISABLED" ]]; then st="無効"; elif [[ -n "$tok" && "$tok" != "None" ]]; then st="有効"; else st="トークン無し"; fi
      printf "[%s] %s  gslug=%s  %s\n" "$st" "${name:-$gs}" "$gs" "$(gurl "$gs")"
    done
    ;;
  rotate)
    GSLUG="${1:?usage: galleries.sh rotate <gslug>}"; require_gslug "$GSLUG"
    TOKEN="$(new_token)"; kvs_put "g:$GSLUG" "$TOKEN"
    cat <<EOF

共有トークンを再発行しました（URL不変）。
  URL     : $(gurl "$GSLUG")
  新トークン: $TOKEN
旧トークンはまもなく無効になります（エッジ反映まで数秒〜数十秒）。
EOF
    ;;
  disable)
    GSLUG="${1:?usage: galleries.sh disable <gslug>}"; require_gslug "$GSLUG"
    kvs_put "g:$GSLUG" "DISABLED"
    echo "カテゴリを無効化しました: $(gurl "$GSLUG") はまもなく403になります。"
    echo "所属パターンの個別URL・他カテゴリには影響しません。再有効化は ds.sh galleries rotate $GSLUG です。"
    ;;
  delete)
    GSLUG="${1:?usage: galleries.sh delete <gslug>}"; require_gslug "$GSLUG"
    # 全パターンから所属を外す
    metakeys="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "meta/" --query "Contents[].Key" --output text 2>/dev/null || true)"
    for k in $metakeys; do
      [[ -n "$k" && "$k" != "None" ]] || continue
      slug="$(basename "$k" .json)"
      cur="$(pattern_galleries "$slug")"
      if [[ " $cur " == *" $GSLUG "* ]]; then
        newlist="$(echo "$cur" | tr ' ' '\n' | grep -vx "$GSLUG" | tr '\n' ' ')"
        pattern_set_galleries "$slug" $newlist
      fi
    done
    # KVS・S3・登録metaを削除
    ETAG="$(kvs_etag)"; aws cloudfront-keyvaluestore delete-key --kvs-arn "$KVS_ARN" --key "g:$GSLUG" --if-match "$ETAG" >/dev/null 2>&1 || true
    aws s3 rm "s3://$BUCKET/g/$GSLUG/" --recursive >/dev/null 2>&1 || true
    aws s3 rm "s3://$BUCKET/galleries/$GSLUG.json" >/dev/null 2>&1 || true
    rebuild_gallery_index
    echo "カテゴリ $GSLUG を削除しました（所属パターン自体は残っています）。"
    ;;
  add|remove)
    GSLUG="${1:?usage: galleries.sh $cmd <gslug> <pattern-slug>}"; require_gslug "$GSLUG"
    SLUG="${2:?usage: galleries.sh $cmd <gslug> <pattern-slug>}"; require_pattern "$SLUG"
    [[ -n "$(gallery_meta_name "$GSLUG")" ]] || { echo "カテゴリが存在しません: $GSLUG" >&2; exit 1; }
    cur="$(pattern_galleries "$SLUG")"
    if [[ "$cmd" == "add" ]]; then
      newlist="$(printf '%s\n%s\n' "$cur" "$GSLUG" | tr ' ' '\n' | sed '/^$/d' | sort -u | tr '\n' ' ')"
    else
      newlist="$(echo "$cur" | tr ' ' '\n' | grep -vx "$GSLUG" | sed '/^$/d' | tr '\n' ' ')"
    fi
    pattern_set_galleries "$SLUG" $newlist
    echo "更新しました: $SLUG の所属カテゴリ = [ ${newlist}]"
    ;;
  help|*)
    grep '^#   ' "$0" | sed 's/^#   //'
    ;;
esac
