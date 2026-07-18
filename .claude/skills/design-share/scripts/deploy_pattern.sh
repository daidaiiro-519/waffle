#!/usr/bin/env bash
# deploy_pattern.sh — UIパターンHTML（またはDESIGN.md視覚スペックシート）をデプロイし、slug＋トークンを発行する
#
# 使い方: ./deploy_pattern.sh [--type mock|design-review] [--design <DESIGN.mdパス>] <HTMLファイル> "<表示名>"
#
#   --type design-review : 管理画面上でUIモックと区別する（DESIGN.mdレビュー用スペックシート）
#   --design <path>      : レビュー対象のDESIGN.md本体。deploy時にS3(design/{slug}.md)へ保存し、
#                          後で ds.sh confirm-design が正式な配置場所へ置くための権威コピーにする
#
# 合意事項（ブレスト論点4・5・8）:
#   - 共有単位はパターン1件 = 1URL（slug単位）
#   - トークンはここでローカル生成し、KVSにのみ保存。平文をファイルに残さない
#   - URL・トークンはこの場で一度だけ表示する
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

TYPE="mock"; DESIGN_SRC=""
POS=()
while (( $# )); do
  case "$1" in
    --type)   TYPE="${2:?--type には値が必要です}"; shift 2 ;;
    --design) DESIGN_SRC="${2:?--design には値が必要です}"; shift 2 ;;
    *)        POS+=("$1"); shift ;;
  esac
done
HTML_FILE="${POS[0]:?usage: deploy_pattern.sh [--type ..] [--design ..] <html-file> <display-name>}"
DISPLAY_NAME="${POS[1]:?usage: deploy_pattern.sh [--type ..] [--design ..] <html-file> <display-name>}"
[[ -f "$HTML_FILE" ]] || { echo "error: HTMLファイルが見つかりません: $HTML_FILE" >&2; exit 1; }
[[ "$TYPE" == "mock" || "$TYPE" == "design-review" ]] || { echo "error: --type は mock か design-review: $TYPE" >&2; exit 1; }
if [[ -n "$DESIGN_SRC" ]]; then
  [[ -f "$DESIGN_SRC" ]] || { echo "error: DESIGN.mdが見つかりません: $DESIGN_SRC" >&2; exit 1; }
  TYPE="design-review"  # --design を伴う場合は明示的にレビュー扱い
fi

SLUG="$(new_slug)"
TOKEN="$(new_token)"

# HTML内の {{スラッグ}} プレースホルダーを実slugへ置換してアップロード
python3 - "$HTML_FILE" "$SLUG" <<'PY' | aws s3 cp - "s3://$BUCKET/p/$SLUG/index.html" --content-type "text/html; charset=utf-8"
import sys
html = open(sys.argv[1], encoding="utf-8").read()
sys.stdout.write(html.replace("{{スラッグ}}", sys.argv[2]))
PY

kvs_put "token:$SLUG" "$TOKEN"
meta_write "$SLUG" "$DISPLAY_NAME" "active"
if [[ -n "$DESIGN_SRC" ]]; then
  # レビュー対象のDESIGN.md本体をS3へ権威コピーとして保存（confirm-designが参照する）
  aws s3 cp "$DESIGN_SRC" "s3://$BUCKET/design/$SLUG.md" --content-type "text/markdown; charset=utf-8" >/dev/null
fi
[[ "$TYPE" == "mock" ]] || meta_patch "$SLUG" "$(printf '{"type":"%s","designSource":"%s"}' "$TYPE" "${DESIGN_SRC:+design/$SLUG.md}")"
rebuild_gallery_index  # ギャラリー集約インデックスを最新化（有効時に一覧へ反映される）

cat <<EOF

デプロイ完了: $DISPLAY_NAME$([[ "$TYPE" == "design-review" ]] && echo "  [DESIGN.mdレビュー]")
  URL   : https://$DISTRIBUTION_DOMAIN/p/$SLUG/
  トークン: $TOKEN

トークンはこの一度しか表示されません。URLとは別のチャネルで共有相手に渡してください。
紛失した場合は ds.sh rotate $SLUG で再発行できます。
$([[ "$TYPE" == "design-review" ]] && cat <<REV

これはDESIGN.mdのレビュー用スペックシートです。関係者のコメントで合意できたら、
  ds.sh confirm-design $SLUG [--to <配置先ディレクトリ>]
でDESIGN.mdを正式な配置場所（既定: ./DESIGN.md）へ配置してください。
REV
)

補足: デプロイ直後の数十秒はエッジへのトークン伝播（KVSの結果整合）が済むまで
      403（無効化済みの表示）に見えることがあります。少し待ってから再読み込みしてください。
EOF
