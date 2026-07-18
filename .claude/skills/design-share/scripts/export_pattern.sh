#!/usr/bin/env bash
# export_pattern.sh — パターンのHTML＋コメント一式をzipでエクスポートする（公開状態は変えない）
#
# 使い方: ./export_pattern.sh <slug> [出力先ディレクトリ=./exports]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

SLUG="${1:?usage: export_pattern.sh <slug> [outdir]}"
OUTDIR="${2:-./exports}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

aws s3 sync "s3://$BUCKET/p/$SLUG/" "$WORK/pattern/" --no-progress
aws s3 sync "s3://$BUCKET/comments/$SLUG/" "$WORK/comments/" --no-progress || true

mkdir -p "$OUTDIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
ZIP_PATH="$OUTDIR/design-share-$SLUG-$STAMP.zip"
# zip化は python3 標準の zipfile で行う（python3は元々必須要件。zipバイナリへの追加依存をなくす）
python3 - "$WORK" "$ZIP_PATH" <<'PY'
import os, sys, zipfile
work, zip_path = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _dirs, files in os.walk(work):
        for name in files:
            full = os.path.join(root, name)
            z.write(full, os.path.relpath(full, work))
PY

echo "エクスポート完了: $ZIP_PATH"
echo "  HTML    : $(find "$WORK/pattern" -type f | wc -l) ファイル"
echo "  コメント: $(find "$WORK/comments" -type f 2>/dev/null | wc -l) 件"
