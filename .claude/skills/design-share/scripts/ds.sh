#!/usr/bin/env bash
# ds.sh — design-share 統一CLIディスパッチャ
#
# 使い方:
#   ./ds.sh list                          公開中/無効化済みパターンの一覧
#   ./ds.sh deploy <html> "<表示名>"      パターンをデプロイ（slug＋トークン発行）
#   ./ds.sh export <slug> [outdir]        zipエクスポート（公開状態は変えない）
#   ./ds.sh rotate <slug>                 トークン再発行（DISABLEDなら再公開）
#   ./ds.sh disable <slug> [--no-export]  無効化（既定でエクスポート同伴）
#   ./ds.sh console                       Web管理コンソールをlocalhostで起動
#   ./ds.sh update-function               edge-gate.jsをCloudFront Functionへ反映
#   ./ds.sh gallery <init|rotate|disable|url>  共有ギャラリー（共通トークンで横断閲覧）を管理
#   ./ds.sh smoke                         実機スモークテスト（使い捨てパターンで往復検証）
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cmd="${1:-help}"
shift || true

case "$cmd" in
  list)
    source "$SCRIPT_DIR/common.sh"
    # 認証・権限エラーを「0件」と誤認しないよう、まずlistの成否をstderr込みで確認する
    if ! keys="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "meta/" \
      --query "Contents[].Key" --output text 2>&1)"; then
      echo "パターン一覧の取得に失敗しました（認証・権限・バケット名を確認してください）:" >&2
      echo "$keys" >&2
      exit 1
    fi
    printf '%s\n' "$keys" | tr '\t' '\n' | while read -r key; do
      [[ -n "$key" && "$key" != "None" ]] || continue
      aws s3 cp "s3://$BUCKET/$key" - 2>/dev/null
      echo
    done | python3 -c "
import json, sys
rows = [json.loads(l) for l in sys.stdin if l.strip()]
if not rows:
    print('デプロイ済みパターンはありません。'); raise SystemExit
rows.sort(key=lambda r: r.get('updatedAt',''), reverse=True)
w = max(len(r.get('name','')) for r in rows)
for r in rows:
    mark = '公開中 ' if r.get('status') == 'active' else '無効化'
    print(f\"[{mark}] {r.get('name',''):<{w}}  slug={r.get('slug','')}  updated={r.get('updatedAt','')[:10]}\")"
    ;;
  deploy)          exec "$SCRIPT_DIR/deploy_pattern.sh" "$@" ;;
  export)          exec "$SCRIPT_DIR/export_pattern.sh" "$@" ;;
  rotate)          exec "$SCRIPT_DIR/rotate_token.sh" "$@" ;;
  disable)         exec "$SCRIPT_DIR/invalidate_pattern.sh" "$@" ;;
  console)         exec python3 "$SCRIPT_DIR/console_server.py" ;;
  update-function) exec "$SCRIPT_DIR/deploy_function.sh" ;;
  gallery)         exec "$SCRIPT_DIR/gallery.sh" "$@" ;;
  smoke)           exec "$SCRIPT_DIR/smoke_test.sh" ;;
  help|*)
    grep '^#   ' "$0" | sed 's/^#   //'
    ;;
esac
