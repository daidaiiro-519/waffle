#!/usr/bin/env bash
# smoke_test.sh — design-share 実機スモークテスト（デプロイ済みスタックに対して実行）
#
# 目的:
#   机上設計のまま残っている経路（特にOAC署名PUTでのコメント投稿と
#   ListObjectsV2書き換え）が実機で成立するかを自動で白黒つける。
#   使い捨てのテストパターンをデプロイ→ゲート挙動・コメント往復・
#   ローテーション・無効化を検証し、最後に無効化して後始末する。
#
# 前提:
#   - design-share.env を作成済み（DESIGN_SHARE_ENV に絶対パス、または本コマンドを
#     env のあるディレクトリで実行）。common.sh と同じ解決規則。
#   - edge-gate.js を deploy_function.sh で反映済み（未反映だと503が返る）。
#   - aws CLI v2 / python3 / curl が使えること。
#
# 使い方:
#   DESIGN_SHARE_ENV=/abs/design-share.env bash scripts/smoke_test.sh
#
# 終了コード: 0=全自動チェック成功 / 1=いずれか失敗（内容は標準出力に出す）
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

PASS=0; FAIL=0
ok()   { printf '  \033[32mPASS\033[0m %s\n' "$1"; PASS=$((PASS+1)); }
ng()   { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
info() { printf '\n\033[1m%s\033[0m\n' "$1"; }

BASE="https://$DISTRIBUTION_DOMAIN"
JAR="$(mktemp)"
TMPHTML="$(mktemp --suffix=.html)"
SLUG=""; TOKEN=""; NEWTOKEN=""
MARKER="smoke-$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null || echo run)-$$"

cleanup() {
  # テストパターンは無効化して痕跡を残さない（データはS3に残る＝安全側）。
  if [[ -n "$SLUG" ]]; then
    info "Cleanup: テストパターン $SLUG を無効化します（データはS3に残ります）"
    "$SCRIPT_DIR/invalidate_pattern.sh" "$SLUG" --no-export >/dev/null 2>&1 || true
  fi
  rm -f "$JAR" "$TMPHTML"
}
trap cleanup EXIT

sha256hex() { python3 -c "import hashlib,sys;print(hashlib.sha256(sys.argv[1].encode()).hexdigest())" "$1"; }

# poll <retries> <sleep秒> <説明> -- <コマンド...>
# コマンドが成功終了するまで最大 retries 回リトライ（エッジ反映待ち）。
poll() {
  local n="$1" s="$2" desc="$3"; shift 3; shift # drop "--"
  local i
  for ((i=1;i<=n;i++)); do
    if "$@"; then return 0; fi
    sleep "$s"
  done
  echo "    （$desc: ${n}回リトライしても条件を満たしませんでした）"
  return 1
}

# --- 0. 前提チェック -------------------------------------------------------
info "0. 前提チェック"
for bin in aws python3 curl; do
  command -v "$bin" >/dev/null 2>&1 && ok "$bin が使える" || { ng "$bin が無い"; }
done
[[ $FAIL -eq 0 ]] || { echo; echo "前提が満たされていないため中断します。"; exit 1; }

# --- 1. テストパターンをデプロイ -------------------------------------------
info "1. 使い捨てテストパターンをデプロイ"
cat > "$TMPHTML" <<HTML
<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>smoke</title></head>
<body><main>smoke test page $MARKER</main></body></html>
HTML
DEPLOY_OUT="$("$SCRIPT_DIR/deploy_pattern.sh" "$TMPHTML" "smoke-test $MARKER" 2>&1)" || true
SLUG="$(printf '%s\n' "$DEPLOY_OUT" | sed -n 's#.*/p/\([A-Za-z0-9_-]*\)/.*#\1#p' | head -1)"
TOKEN="$(printf '%s\n' "$DEPLOY_OUT" | sed -n 's/^.*トークン: *//p' | head -1)"
if [[ -n "$SLUG" && -n "$TOKEN" ]]; then ok "deploy 成功 slug=$SLUG"; else
  ng "deploy 失敗（URL/トークンを取得できず）"; echo "$DEPLOY_OUT"; exit 1; fi

# --- 2. デプロイのエッジ伝播を待つ（KVSは結果整合。数十秒かかりうる）------
# 直後は「キー未伝播→DISABLED扱い→403」になりうるため、verify=204（＝トークンが
# エッジに伝播完了）を確定シグナルとしてポーリングで待ってから以降を評価する。
info "2. デプロイのエッジ伝播を待つ（KVS結果整合）"
verify_code() { curl -s -o /dev/null -w '%{http_code}' -H "x-share-token: $TOKEN" "$BASE/p/$SLUG/verify"; }
# KVS収束は非単調（あるエッジサーバが204でも別サーバは未同期で403になりうる）。
# 単発の204では不十分なので、204が連続CONSEC回そろうまで待って「収束」とみなす。
wait_converged() {
  local streak=0 i code CONSEC=4
  for ((i=1;i<=50;i++)); do
    code="$(verify_code)"
    if [[ "$code" == "204" ]]; then streak=$((streak+1)); else streak=0; fi
    [[ $streak -ge $CONSEC ]] && return 0
    sleep 3
  done
  return 1
}
if wait_converged; then ok "トークンがエッジへ収束伝播（verify=204が連続）"; else
  ng "伝播待ちタイムアウト（verify=$(verify_code)）※edge-gate未反映(503)の可能性"; fi

# --- 3. 負の認証: トークン無し／誤トークンは通さない ----------------------
info "3. 負の認証（トークン無し・誤トークン）"
notoken="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/p/$SLUG/")"
[[ "$notoken" == "401" || "$notoken" == "403" ]] && ok "トークン無し → 拒否($notoken)" \
  || ng "トークン無しでページが通る（$notoken）"
wrong="$(curl -s -o /dev/null -w '%{http_code}' -H "x-share-token: WRONG-$MARKER" "$BASE/p/$SLUG/verify")"
[[ "$wrong" == "401" ]] && ok "誤トークン → 401" || ng "誤トークンで 401 以外（実際: $wrong）"

# --- 4. 正トークンでCookie発行 → 本体が見られる ---------------------------
info "4. Cookie発行とページ本体"
right="$(curl -s -c "$JAR" -o /dev/null -w '%{http_code}' -H "x-share-token: $TOKEN" "$BASE/p/$SLUG/verify")"
[[ "$right" == "204" ]] && ok "正トークン → 204" || ng "正トークンで 204 以外（実際: $right）"
grep -q "share_$SLUG" "$JAR" && ok "share_$SLUG Cookie が発行された" || ng "Cookie が発行されない"
# 伝播の裾で一時的に403が混じりうるので、200が取れるまで数回許容
page_ok() { curl -s -b "$JAR" "$BASE/p/$SLUG/" | grep -q "$MARKER"; }
if poll 6 5 "本体取得リトライ" -- page_ok; then ok "Cookie付き → ページ本体200（マーカー一致）" \
  ; else ng "Cookie付きでもページ本体を取得できない"; fi

# --- 5. コメントPUT（★OAC署名PUTの実機検証：最重要）----------------------
info "5. コメント投稿（OAC署名PUT）"
BODYJSON="$(python3 -c "import json,sys;print(json.dumps({'author':'smoke','body':sys.argv[1],'postedAt':'2026-01-01T00:00:00Z'}))" "$MARKER")"
KEY="comments/$SLUG/$(date -u +%s 2>/dev/null || echo 0)-smoke.json"
SHA="$(sha256hex "$BODYJSON")"
put_code() { curl -s -b "$JAR" -o /dev/null -w '%{http_code}' -X PUT \
  -H 'content-type: application/json' -H "x-amz-content-sha256: $SHA" \
  --data "$BODYJSON" "$BASE/$KEY"; }
put_ok() { [[ "$(put_code)" =~ ^2 ]]; }
if poll 6 5 "PUTリトライ(伝播裾)" -- put_ok; then ok "コメントPUT → 2xx（OAC署名PUT成立）"; else
  ng "コメントPUT失敗（$(put_code)）★これが失敗ならコメント投稿だけFunction URL等へ逃がす代替が必要"; fi

# --- 6. コメント一覧（ListObjectsV2書き換え）＋本文取得 -------------------
info "6. コメント一覧と本文取得"
# grepは <Key>…投稿キー…</Key> を厳密に見る（<Prefix>への誤マッチを避ける）
list_has_key() { curl -s -b "$JAR" "$BASE/comments-list/$SLUG" | grep -q "<Key>comments/$SLUG/"; }
if poll 10 3 "一覧反映待ち" -- list_has_key; then ok "comments-list に投稿キーが出る（ListObjectsV2書き換え成立）"; else
  ng "comments-list に投稿が現れない"; fi
got="$(curl -s -b "$JAR" "$BASE/$KEY")"
printf '%s' "$got" | grep -q "$MARKER" && ok "コメント本文を取得できる" || ng "コメント本文を取得できない"

# --- 7. ローテーション：旧トークンCookieは失効 -----------------------------
info "7. トークンローテーション"
ROT_OUT="$("$SCRIPT_DIR/rotate_token.sh" "$SLUG" 2>&1)" || true
NEWTOKEN="$(printf '%s\n' "$ROT_OUT" | sed -n 's/^.*トークン: *//p' | head -1)"
[[ -n "$NEWTOKEN" && "$NEWTOKEN" != "$TOKEN" ]] && ok "新トークン発行（旧と異なる）" || ng "新トークンを取得できない"
old_dead() { local c; c="$(curl -s -b "$JAR" -o /dev/null -w '%{http_code}' "$BASE/p/$SLUG/")"; [[ "$c" == "401" ]]; }
if poll 20 3 "旧トークン失効反映待ち" -- old_dead; then ok "旧トークンCookie → 401（即時失効）"; else
  ng "旧トークンCookieがまだ通る"; fi

# --- 8. 無効化：403 DISABLED だがエクスポートは可能（データは残る）--------
info "8. 無効化とデータ保全"
"$SCRIPT_DIR/invalidate_pattern.sh" "$SLUG" --no-export >/dev/null 2>&1 || true
disabled() { local c; c="$(curl -s -o /dev/null -w '%{http_code}' -H "x-share-token: $NEWTOKEN" "$BASE/p/$SLUG/verify")"; [[ "$c" == "403" ]]; }
if poll 20 3 "無効化反映待ち" -- disabled; then ok "無効化後は正トークンでも403"; else
  ng "無効化後もアクセスできる"; fi
EXPORT_DIR="$(mktemp -d)"
if "$SCRIPT_DIR/export_pattern.sh" "$SLUG" "$EXPORT_DIR" >/dev/null 2>&1 && ls "$EXPORT_DIR"/*.zip >/dev/null 2>&1; then
  ok "無効化後もエクスポート可能（データは削除されていない）"; else
  ng "無効化後にエクスポートできない（データ保全の前提が崩れている）"; fi
rm -rf "$EXPORT_DIR"
SLUG=""  # 後始末済み。trapでの二重無効化を避ける
rm -f "$JAR" "$TMPHTML"; trap - EXIT

# --- 結果 ------------------------------------------------------------------
info "自動チェック結果: PASS=$PASS FAIL=$FAIL"
cat <<'MANUAL'

--- 以下は自動化できないため、ブラウザで手動確認してください ---
[ ] XSS: コメント本文に <img src=x onerror=alert(1)> 等を投稿し、
        画面上でタグがそのまま文字列として表示される（実行されない）こと
[ ] Cookie属性: DevTools の Application > Cookies で share_{slug} が
        Secure / HttpOnly / SameSite=Strict になっていること
[ ] UI: パターンページのレイアウト・コメント欄・投稿フォームが
        Design.md のトークン通りに崩れず表示されること
[ ] 横断遷移: 別パターンのURLへ遷移でき、それぞれ独立にゲートされること
MANUAL

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
