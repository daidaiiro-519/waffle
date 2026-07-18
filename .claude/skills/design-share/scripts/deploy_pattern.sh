#!/usr/bin/env bash
# deploy_pattern.sh — UIパターンHTMLをデプロイし、slug＋トークンを発行する
#
# 使い方: ./deploy_pattern.sh <パターンHTMLファイル> "<パターン表示名>"
#
# 合意事項（ブレスト論点4・5・8）:
#   - 共有単位はパターン1件 = 1URL（slug単位）
#   - トークンはここでローカル生成し、KVSにのみ保存。平文をファイルに残さない
#   - URL・トークンはこの場で一度だけ表示する
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

HTML_FILE="${1:?usage: deploy_pattern.sh <html-file> <display-name>}"
DISPLAY_NAME="${2:?usage: deploy_pattern.sh <html-file> <display-name>}"
[[ -f "$HTML_FILE" ]] || { echo "error: HTMLファイルが見つかりません: $HTML_FILE" >&2; exit 1; }

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

cat <<EOF

デプロイ完了: $DISPLAY_NAME
  URL   : https://$DISTRIBUTION_DOMAIN/p/$SLUG/
  トークン: $TOKEN

トークンはこの一度しか表示されません。URLとは別のチャネルで共有相手に渡してください。
紛失した場合は ds.sh rotate $SLUG で再発行できます。

補足: デプロイ直後の数十秒はエッジへのトークン伝播（KVSの結果整合）が済むまで
      403（無効化済みの表示）に見えることがあります。少し待ってから再読み込みしてください。
EOF
