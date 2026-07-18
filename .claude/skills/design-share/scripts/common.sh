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

# --- meta helpers ---
# 真実源の割り当て（reconcile_projections がこの前提で投影を再生成する）:
#   秘密トークン         → KVS が権威（token:{slug} / g:{gslug} / project:token）。S3には残さない
#   構造・状態・名前・所属 → S3 の meta/{slug}.json が権威
#   投影(再生成可・非権威) → KVS pg:{slug}、gallery/index.json、g/*/index.json、token:のDISABLED overlay
meta_write() { # meta_write <slug> <name> <status>  （既存のgalleries[]所属は保持する）
  # 既存galleries[]の保持は、metaが「読めた」ときだけ行う。読めない場合:
  #   - オブジェクトが存在しない（新規デプロイ）→ galleries=[] で新規作成してよい
  #   - 存在するのに読めない（一時失敗）→ 上書きを中止（galleries[]の消失を防ぐ）
  local existing cur
  if cur="$(aws s3 cp "s3://$BUCKET/meta/$1.json" - 2>/dev/null)" && [[ -n "$cur" ]]; then
    # 既存metaは丸ごと保持し、管理するキーだけ上書きする（galleries[]・type・project・designSource等の
    # このシートが直接管理しないフィールドを、rename/rotate等の後続書き込みで消さないため）
    existing="$cur"
    printf '%s' "$cur" | python3 -c "import json,sys; json.load(sys.stdin)" >/dev/null 2>&1 \
      || { echo "meta_write: 既存metaの解析に失敗したため上書きを中止: $1" >&2; return 1; }
  elif aws s3api head-object --bucket "$BUCKET" --key "meta/$1.json" >/dev/null 2>&1; then
    echo "meta_write: 既存metaが存在するのに読めなかったため上書きを中止（所属消失防止）: $1" >&2
    return 1
  else
    existing='{}'  # 本当に新規
  fi
  # 確定値を組み立ててから書く（pythonが失敗しても空でmetaを上書きしない）
  local out
  out="$(python3 - "$1" "$2" "$3" "$existing" <<'PY'
import json, sys, datetime
slug, name, status, existing = sys.argv[1:5]
try:
    base = json.loads(existing)
    if not isinstance(base, dict): base = {}
except Exception:
    base = {}
base.setdefault("galleries", [])
base.update({"slug": slug, "name": name, "status": status,
             "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps(base, ensure_ascii=False))
PY
)" || { echo "meta_write: metaの生成に失敗: $1" >&2; return 1; }
  [[ -n "$out" ]] || { echo "meta_write: 生成結果が空のため書き込み中止: $1" >&2; return 1; }
  printf '%s' "$out" | aws s3 cp - "s3://$BUCKET/meta/$1.json" --content-type application/json >/dev/null
}

meta_patch() { # meta_patch <slug> <json-object>  既存metaへ任意フィールドをマージする（既存キー保持）
  local slug="$1" patch="$2" cur
  cur="$(aws s3 cp "s3://$BUCKET/meta/$slug.json" - 2>/dev/null)" \
    || { echo "meta_patch: metaが読めません: $slug" >&2; return 1; }
  [[ -n "$cur" ]] || { echo "meta_patch: metaが空です: $slug" >&2; return 1; }
  local out
  out="$(python3 - "$cur" "$patch" <<'PY'
import json, sys, datetime
cur = json.loads(sys.argv[1])
patch = json.loads(sys.argv[2])
if not isinstance(cur, dict): raise SystemExit("meta is not an object")
cur.update(patch)
cur["updatedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
print(json.dumps(cur, ensure_ascii=False))
PY
)" || { echo "meta_patch: マージに失敗: $slug" >&2; return 1; }
  [[ -n "$out" ]] || { echo "meta_patch: 生成結果が空のため中止: $slug" >&2; return 1; }
  printf '%s' "$out" | aws s3 cp - "s3://$BUCKET/meta/$slug.json" --content-type application/json >/dev/null
}

meta_name() { # meta_name <slug>（無ければslugを返す）
  aws s3 cp "s3://$BUCKET/meta/$1.json" - 2>/dev/null \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('name',''))" || true
}

meta_status() { # meta_status <slug>（無ければ空。通常は active / disabled）
  aws s3 cp "s3://$BUCKET/meta/$1.json" - 2>/dev/null \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" || true
}

new_token() { # 暗号学的乱数のトークン（URL安全な22文字）
  python3 -c "import secrets; print(secrets.token_urlsafe(16))"
}

new_slug() { # 推測困難なslug（16文字。誕生日衝突を実質排除）
  python3 -c "import secrets; print(secrets.token_hex(8))"
}

# --- ギャラリー ---
# 全体ギャラリー: KVS project:token（値 or "DISABLED"）で入る全部入りランディング（/gallery/）。
# 名前付きギャラリー（カテゴリ）: KVS g:{gslug}（値 or "DISABLED"）で入る /g/{gslug}/。
#   所属はタグ式（1パターンが複数ギャラリーに所属可）。metaのgalleries[]が真実で、
#   エッジのスコープ判定用に pg:{slug}（空白区切りのgslug一覧）をKVSに鏡像として持つ。
# 一覧はいずれも集約JSON（gallery/index.json と g/{gslug}/index.json）を都度再生成して持つ
#   （閲覧側は1ファイルfetchで済み、edge側でListBucket権限を要求しない）。
gallery_enabled() { # 全体ギャラリーが有効なら共通トークン、無効/未設定なら空を返す
  local v; v="$(kvs_get "project:token")"
  [[ -n "$v" && "$v" != "DISABLED" && "$v" != "None" ]] && printf '%s' "$v" || printf ''
}

new_gslug() { python3 -c "import secrets; print(secrets.token_hex(6))"; }  # 名前付きギャラリーのid

gallery_meta_write() { # <gslug> <name>
  python3 - "$1" "$2" <<'PY' | aws s3 cp - "s3://$BUCKET/galleries/$1.json" --content-type application/json
import json, sys, datetime
gslug, name = sys.argv[1:3]
print(json.dumps({"gslug": gslug, "name": name,
                  "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()}, ensure_ascii=False))
PY
}

gallery_meta_name() { # <gslug>
  aws s3 cp "s3://$BUCKET/galleries/$1.json" - 2>/dev/null \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('name',''))" || true
}

# パターンの所属ギャラリーを設定し、meta.galleries・pg:{slug}(KVS)・各indexを更新する。
# 途中で失敗しても meta を空で上書きしないよう、確定値を組み立ててから書き込む。
MAX_PATTERN_GALLERIES=3   # edge-gate.js のスコープ判定が先頭N件のみ照合するため、書き込み側で強制
pattern_set_galleries() { # <slug> <gslug...>（0個で全所属解除）
  local slug="$1"; shift; local list="$*"
  # 所属カテゴリ数の上限を強制（超過を黙って切り捨てず、書き込み時点で拒否する）
  local -a arr=($list)
  if (( ${#arr[@]} > MAX_PATTERN_GALLERIES )); then
    echo "所属カテゴリは最大 ${MAX_PATTERN_GALLERIES} 件までです（指定: ${#arr[@]} 件）: $slug" >&2
    return 1
  fi
  local cur new
  cur="$(aws s3 cp "s3://$BUCKET/meta/$slug.json" - 2>/dev/null)"
  [[ -n "$cur" ]] || { echo "meta not found or empty: $slug" >&2; return 1; }
  new="$(printf '%s' "$cur" | python3 -c "import json,sys
meta=json.load(sys.stdin)
meta['galleries']=[x for x in sys.argv[1].split() if x]
print(json.dumps(meta,ensure_ascii=False))" "$list")" || { echo "meta更新に失敗: $slug" >&2; return 1; }
  [[ -n "$new" ]] || { echo "meta結果が空: $slug" >&2; return 1; }
  printf '%s' "$new" | aws s3 cp - "s3://$BUCKET/meta/$slug.json" --content-type application/json >/dev/null
  kvs_put "pg:$slug" "$list"   # エッジのスコープ判定用の鏡像（空白区切り）
  rebuild_gallery_index
}

pattern_galleries() { # <slug> 現在の所属gslugを空白区切りで返す
  aws s3 cp "s3://$BUCKET/meta/$1.json" - 2>/dev/null \
    | python3 -c "import json,sys; print(' '.join(json.load(sys.stdin).get('galleries',[])))" 2>/dev/null || true
}

rebuild_gallery_index() { # 全meta+galleriesを集約し gallery/index.json と各 g/{gslug}/index.json を再生成
  local metakeys galkeys
  metakeys="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "meta/" --query "Contents[].Key" --output text 2>/dev/null)" || return 0
  galkeys="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "galleries/" --query "Contents[].Key" --output text 2>/dev/null || true)"
  {
    echo "@@METAS"
    for k in $metakeys; do [[ -n "$k" && "$k" != "None" ]] || continue; aws s3 cp "s3://$BUCKET/$k" - 2>/dev/null; echo; done
    echo "@@GALLERIES"
    for k in $galkeys; do [[ -n "$k" && "$k" != "None" ]] || continue; aws s3 cp "s3://$BUCKET/$k" - 2>/dev/null; echo; done
  } | BUCKET="$BUCKET" python3 -c "
import json, sys, os, subprocess
bucket = os.environ['BUCKET']
mode = None; metas = []; gals = []
for line in sys.stdin:
    s = line.strip()
    if s == '@@METAS': mode = 'm'; continue
    if s == '@@GALLERIES': mode = 'g'; continue
    if not s: continue
    try: obj = json.loads(s)
    except Exception: continue
    (metas if mode == 'm' else gals).append(obj)
def put(key, data):
    subprocess.run(['aws','s3','cp','-','s3://%s/%s' % (bucket, key),'--content-type','application/json'],
                   input=json.dumps(data, ensure_ascii=False), text=True, stdout=subprocess.DEVNULL)
def slim(r):
    return {'slug': r.get('slug',''), 'name': r.get('name',''), 'status': r.get('status','active'), 'updatedAt': r.get('updatedAt','')}
put('gallery/index.json', [slim(r) for r in metas])
for g in gals:
    gs = g.get('gslug','')
    if not gs: continue
    items = [slim(r) for r in metas if gs in (r.get('galleries') or [])]
    put('g/%s/index.json' % gs, {'name': g.get('name',''), 'gslug': gs, 'items': items})
"
}

# reconcile: S3のmeta（構造・状態・所属の真実源）から、KVSの投影(pg:{slug})・status overlay・
# 各index.jsonをすべて再生成する。乖離（pg:とmeta.galleriesの不一致、token:のDISABLEDとmeta.status
# の不一致）を直せる唯一の経路。書き込みが途中失敗して投影がずれても、これで真実源から回復できる。
#   真実源: 秘密トークン=KVS(token:/g:/project:token)、構造・状態・所属=S3 meta。
#   投影(再生成可): pg:{slug}、gallery/index.json、g/*/index.json、token:のDISABLED overlay。
reconcile_projections() {
  local keys slug gl st tok n=0 warned=0
  keys="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "meta/" --query "Contents[].Key" --output text 2>/dev/null)" \
    || { echo "meta一覧の取得に失敗（認証・権限・バケット名を確認）" >&2; return 1; }
  for k in $keys; do
    [[ -n "$k" && "$k" != "None" ]] || continue
    slug="$(basename "$k" .json)"
    gl="$(pattern_galleries "$slug")"
    kvs_put "pg:$slug" "$gl"                       # 所属ミラーをmetaから再生成
    st="$(meta_status "$slug")"
    tok="$(kvs_get "token:$slug")"
    if [[ "$st" == "disabled" ]]; then
      [[ "$tok" == "DISABLED" ]] || kvs_put "token:$slug" "DISABLED"   # 無効化overlayを保証（秘密は触らない）
    elif [[ "$tok" == "DISABLED" ]]; then
      echo "  ⚠ $slug: metaはactiveだがKVSがDISABLED。トークンは秘密でmetaから復元不可 → ds.sh rotate $slug で再発行を" >&2
      warned=$((warned+1))
    fi
    n=$((n+1))
  done
  rebuild_gallery_index
  echo "reconcile完了: ${n}パターンの投影(pg:/index/status overlay)をmetaから再生成しました（要対応: ${warned}件）。"
}
