#!/usr/bin/env bash
# deploy_function.sh — edge-gate.js の本体コードをCloudFront Functionへ反映・公開する
#
# CloudFormationはプレースホルダー関数（503を返す）でFunctionを作成するため、
# 【初回構築後に必ず1回】と、edge-gate.js 変更時に実行する。
#
# 使い方: ./deploy_function.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

: "${FUNCTION_NAME:?design-share.env に FUNCTION_NAME が必要です}"
CODE_FILE="$SCRIPT_DIR/../infra/cloudfront-function/edge-gate.js"

ETAG="$(aws cloudfront describe-function --name "$FUNCTION_NAME" --query ETag --output text)"

aws cloudfront update-function \
  --name "$FUNCTION_NAME" \
  --if-match "$ETAG" \
  --function-config "Comment=design-share edge-gate,Runtime=cloudfront-js-2.0,KeyValueStoreAssociations={Quantity=1,Items=[{KeyValueStoreARN=$KVS_ARN}]}" \
  --function-code "fileb://$CODE_FILE" > /dev/null

ETAG="$(aws cloudfront describe-function --name "$FUNCTION_NAME" --query ETag --output text)"
aws cloudfront publish-function --name "$FUNCTION_NAME" --if-match "$ETAG" > /dev/null

echo "edge-gate を更新・公開しました: $FUNCTION_NAME"
