#!/usr/bin/env bash
# confirm_design.sh — レビューを経たDESIGN.mdを正式な配置場所へ確定配置する
#
# 使い方: ./confirm_design.sh <slug> [--to <配置先ディレクトリ>] [--no-export]
#
#   design-review としてデプロイしたスペックシート（ds.sh deploy --design ...）に対して実行する。
#   deploy時にS3(design/{slug}.md)へ保存した権威コピーを、プロジェクト直下の DESIGN.md として配置する。
#
#   --to <dir>    : 配置先ディレクトリ（既定: カレントディレクトリ）。<dir>/DESIGN.md に置く
#   --no-export   : 確定時にレビューコメントのzipエクスポートを行わない（既定は行う＝決定の記録を残す）
#
# 設計:
#   - 1プロジェクト = 1 DESIGN.md（プロジェクトが所有）。確定＝正式な配置場所へ置くこと。UIモックの生成は行わない
#   - 既存のDESIGN.mdがある場合は上書き前にタイムスタンプ付きバックアップを取る（不可逆操作の保護）
#   - 確定した事実は meta の confirmedAt / confirmedTo に記録する（管理コンソールが「確定済み」を表示できる）
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

SLUG=""; TO_DIR="."; DO_EXPORT=1
while (( $# )); do
  case "$1" in
    --to)         TO_DIR="${2:?--to にはディレクトリが必要です}"; shift 2 ;;
    --no-export)  DO_EXPORT=0; shift ;;
    -*)           echo "error: 不明なオプション: $1" >&2; exit 1 ;;
    *)            SLUG="$1"; shift ;;
  esac
done
[[ -n "$SLUG" ]] || { echo "usage: confirm_design.sh <slug> [--to <dir>] [--no-export]" >&2; exit 1; }

# metaを読み、design-reviewであること・designSourceがあることを確認する
META="$(aws s3 cp "s3://$BUCKET/meta/$SLUG.json" - 2>/dev/null)" \
  || { echo "error: metaが読めません（slugを確認してください）: $SLUG" >&2; exit 1; }
read -r MTYPE MSRC MNAME < <(printf '%s' "$META" | python3 -c "
import json,sys
m=json.load(sys.stdin)
print(m.get('type','mock'), m.get('designSource',''), (m.get('name','') or '-').replace(' ',' '))")
if [[ "$MTYPE" != "design-review" ]]; then
  echo "error: このslugはDESIGN.mdレビューではありません（type=$MTYPE）。confirm-designの対象外です: $SLUG" >&2
  exit 1
fi
[[ -n "$MSRC" ]] || { echo "error: このレビューにはDESIGN.md本体が保存されていません（deploy時に --design を付けていない）: $SLUG" >&2; exit 1; }

# 権威コピー（S3）を取得
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
aws s3 cp "s3://$BUCKET/$MSRC" "$TMP" >/dev/null \
  || { echo "error: DESIGN.md本体の取得に失敗: s3://$BUCKET/$MSRC" >&2; exit 1; }
[[ -s "$TMP" ]] || { echo "error: 取得したDESIGN.mdが空です: $MSRC" >&2; exit 1; }

mkdir -p "$TO_DIR"
DEST="$TO_DIR/DESIGN.md"

# 既存があれば上書き前にバックアップ（不可逆操作の保護）
if [[ -f "$DEST" ]]; then
  if cmp -s "$TMP" "$DEST"; then
    echo "既存の $DEST は確定内容と同一でした（変更なし）。"
  else
    BAK="$DEST.bak-$(date +%Y%m%d-%H%M%S)"
    cp "$DEST" "$BAK"
    echo "既存の $DEST を $BAK に退避しました。"
  fi
fi
cp "$TMP" "$DEST"

# 確定の事実をmetaへ記録
ABS_DEST="$(cd "$TO_DIR" && pwd)/DESIGN.md"
meta_patch "$SLUG" "$(python3 -c "import json,datetime,sys; print(json.dumps({'confirmedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'confirmedTo': sys.argv[1]}))" "$ABS_DEST")"

echo
echo "確定しました: ${MNAME//$' '/ }"
echo "  配置先: $ABS_DEST"

# 決定の記録としてレビューコメントを同伴エクスポート（既定）
if (( DO_EXPORT )); then
  echo
  echo "レビューコメントを記録としてエクスポートします..."
  "$SCRIPT_DIR/export_pattern.sh" "$SLUG" || echo "（エクスポートはスキップされました）" >&2
fi

cat <<EOF

次のステップ:
  - このDESIGN.mdを単一の源として、対話でUIモックを生成できます（confirm-designはモックを生成しません）。
  - レビュー用スペックシート自体が不要になったら ds.sh disable $SLUG で公開を止められます（データは残ります）。
EOF
