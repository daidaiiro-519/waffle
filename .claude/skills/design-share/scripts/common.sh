#!/usr/bin/env bash
# common.sh — design-share scripts 共通設定・KVSヘルパー
#
# 設定は以下の優先順で解決する:
#   1. 環境変数 DESIGN_SHARE_ENV（絶対パス推奨）
#   2. 呼び出し元カレントディレクトリの design-share.env
# 各スクリプトはcdしないため、相対パス引数は呼び出し元基準で解決される。
#
# design-share.env の必須キー（CloudFormation Outputsから作成する）:
#   BUCKET=my-design-share-bucket
#   DISTRIBUTION_DOMAIN=xxxx.cloudfront.net
#   KVS_ARN=arn:aws:cloudfront::123456789012:key-value-store/xxxx
#   FUNCTION_NAME=my-design-share-edge-gate
set -euo pipefail

ENV_FILE="${DESIGN_SHARE_ENV:-$PWD/design-share.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "error: 設定ファイルが見つかりません: $ENV_FILE" >&2
  echo "CloudFormationスタックのOutputsをもとに design-share.env を作成し、" >&2
  echo "そのディレクトリで実行するか DESIGN_SHARE_ENV に絶対パスを設定してください。" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

: "${BUCKET:?design-share.env に BUCKET が必要です}"
: "${DISTRIBUTION_DOMAIN:?design-share.env に DISTRIBUTION_DOMAIN が必要です}"
: "${KVS_ARN:?design-share.env に KVS_ARN が必要です}"

# --- KeyValueStore helpers -------------------------------------------------
# token:{slug} が唯一の状態キー:
#   通常値       = 現在有効なトークン
#   "DISABLED"  = 無効化済み（rotate_token.sh の再発行で再公開できる）
# キーを1つに保つのは、edge-gateのKVS読み取りを1回に抑えるため（cf2実行予算対策）
kvs_etag() {
  aws cloudfront-keyvaluestore describe-key-value-store \
    --kvs-arn "$KVS_ARN" --query ETag --output text
}

kvs_put() { # kvs_put <key> <value>
  aws cloudfront-keyvaluestore put-key \
    --kvs-arn "$KVS_ARN" --key "$1" --value "$2" \
    --if-match "$(kvs_etag)" > /dev/null
}

kvs_get() { # kvs_get <key>（無ければ空文字）
  aws cloudfront-keyvaluestore get-key \
    --kvs-arn "$KVS_ARN" --key "$1" --query Value --output text 2>/dev/null || true
}

# --- meta helpers（横断管理コンソール・CLI一覧が読む表示用キャッシュ。真実はKVS） ---
meta_write() { # meta_write <slug> <name> <status>
  python3 - "$1" "$2" "$3" <<'PY' | aws s3 cp - "s3://$BUCKET/meta/$1.json" --content-type application/json
import json, sys, datetime
slug, name, status = sys.argv[1:4]
print(json.dumps({"slug": slug, "name": name, "status": status,
                  "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()},
                 ensure_ascii=False))
PY
}

meta_name() { # meta_name <slug>（無ければslugを返す）
  aws s3 cp "s3://$BUCKET/meta/$1.json" - 2>/dev/null \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('name',''))" || true
}

new_token() { # 暗号学的乱数のトークン（URL安全な22文字）
  python3 -c "import secrets; print(secrets.token_urlsafe(16))"
}

new_slug() { # 推測困難なslug（16文字。誕生日衝突を実質排除）
  python3 -c "import secrets; print(secrets.token_hex(8))"
}

# --- ギャラリー（プロジェクト共通トークンで入る横断ランディング） ---
# 共通トークンは KVS の唯一のキー project:token に保持（値 or "DISABLED"）。
# 一覧は全 meta/*.json を集約した gallery/index.json を都度再生成して持つ
# （閲覧側は1ファイルfetchで済み、edge側でListBucket権限を要求しない）。
gallery_enabled() { # 有効なら現在の共通トークン、無効/未設定なら空を返す
  local v; v="$(kvs_get "project:token")"
  [[ -n "$v" && "$v" != "DISABLED" && "$v" != "None" ]] && printf '%s' "$v" || printf ''
}

rebuild_gallery_index() { # 全meta/*.jsonを集約して gallery/index.json を再生成・配置
  local keys
  keys="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "meta/" \
    --query "Contents[].Key" --output text 2>/dev/null)" || return 0
  {
    for key in $keys; do
      [[ -n "$key" && "$key" != "None" ]] || continue
      aws s3 cp "s3://$BUCKET/$key" - 2>/dev/null
      echo
    done
  } | python3 -c "
import json, sys
rows = [json.loads(l) for l in sys.stdin if l.strip()]
rows = [{'slug': r.get('slug',''), 'name': r.get('name',''),
         'status': r.get('status','active'), 'updatedAt': r.get('updatedAt','')} for r in rows]
sys.stdout.write(json.dumps(rows, ensure_ascii=False))
" | aws s3 cp - "s3://$BUCKET/gallery/index.json" --content-type "application/json" >/dev/null
}
