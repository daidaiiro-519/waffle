// edge-gate.js — CloudFront Function (cf2, viewer-request)
//
// 責務（論点4・5・8の合意事項 + advisor批評の反映）:
//   1. 状態判定: KVS "token:{slug}" を1回だけ読む
//        通常値      = 現在有効なトークン
//        "DISABLED" = 無効化済み → 403
//        キー無し    = 未発行slug → 403
//      （KVS読み取りを1回に抑えるのはcf2の実行予算対策）
//   2. トークン照合: Cookie "share_{slug}" の値をKVS現在値と毎回直接比較する
//      （ローテーションはKVSの値を書き換えるだけで旧トークンが自動失効する）
//   3. トークン検証: GET /p/{slug}/verify (header: x-share-token) → 204 + Set-Cookie
//   4. メソッド・書き込み検査（多層防御）:
//        - コメントPUTは /comments/{slug}/{英数}.json かつ content-type: application/json のみ許可
//        - それ以外の変更系メソッド（DELETE/POST/PATCH等）は全経路で403
//   5. コメント一覧: /comments-list/{slug} → S3 ListObjectsV2 リクエストへ書き換え

import cf from 'cloudfront';

const kvs = cf.kvs();

const GATE_HTML = `<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>共有トークンの入力</title>
<style>*{box-sizing:border-box}body{font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;
min-height:100vh;margin:0;padding:1rem;background:#f5f6f4;color:#1a2126}
.card{background:#fff;border:1px solid #d7dcdb;border-radius:10px;padding:2rem 1.6rem;max-width:340px;
width:100%;text-align:center;box-shadow:0 8px 20px rgba(0,0,0,.08)}
.card h1{margin:0 0 .4rem}.card p{margin:.4rem 0 1rem}
input{display:block;font:inherit;text-align:center;letter-spacing:.08em;border:1px solid #d7dcdb;border-radius:6px;
padding:.55rem .7rem;width:100%;margin:0 0 .6rem}
button{display:block;font:inherit;font-weight:600;background:#2f6f76;color:#fff;border:none;border-radius:6px;
padding:.55rem .7rem;width:100%;cursor:pointer}
.err{display:none;color:#a5423a;font-size:.8rem;margin-top:.6rem}</style></head><body>
<div class="card"><h1 style="font-size:1.05rem">共有トークンを入力してください</h1>
<p style="color:#5c6b70;font-size:.88rem">このページを見るには、URLとは別に共有されたトークンが必要です。</p>
<input id="t" type="text" placeholder="トークンを入力" autocomplete="off">
<button id="go">アクセスする</button><p class="err" id="e">トークンが違います。もう一度お試しください。</p></div>
<script>
document.getElementById('go').addEventListener('click', async () => {
  const p = location.pathname;
  const m = p.match(/^\\/p\\/([A-Za-z0-9_-]+)/);
  const verify = p.indexOf('/gallery') === 0 ? '/gallery/verify' : '/p/' + (m ? m[1] : '') + '/verify';
  const r = await fetch(verify,
    { headers: { 'x-share-token': document.getElementById('t').value.trim() } });
  if (r.status === 204) location.reload();
  else document.getElementById('e').style.display = 'block';
});
</script></body></html>`;

const DISABLED_HTML = `<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>無効化されています</title>
<style>body{font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;
min-height:100vh;margin:0;background:#f5f6f4;color:#5c6b70;text-align:center}</style></head><body>
<div><p style="font-weight:700;color:#a5423a">403 DISABLED</p><h1 style="font-size:1.05rem;color:#1a2126">このURLは無効化されています</h1>
<p style="max-width:44ch">作成者によってこの共有は終了されました。内容を確認したい場合は作成者にお問い合わせください。</p></div>
</body></html>`;

function htmlResponse(status, body) {
  return {
    statusCode: status,
    statusDescription: status === 403 ? 'Forbidden' : 'Unauthorized',
    headers: {
      'content-type': { value: 'text/html; charset=utf-8' },
      'x-content-type-options': { value: 'nosniff' },
    },
    body: body,
  };
}

function deny(status) {
  return { statusCode: status, statusDescription: 'Forbidden' };
}

function getCookie(request, name) {
  const c = request.cookies[name];
  return c ? c.value : null;
}

// パスからslugを取り出す: /p/{slug}/..., /comments/{slug}/..., /comments-list/{slug}
function extractSlug(uri) {
  const m = uri.match(/^\/(?:p|comments|comments-list)\/([A-Za-z0-9_-]+)/);
  return m ? m[1] : null;
}

function setCookie(name, value) {
  return {
    statusCode: 204,
    statusDescription: 'No Content',
    cookies: {
      [name]: {
        value: value,
        attributes: 'Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=604800',
      },
    },
  };
}

// プロジェクト共通トークン（ギャラリー用）の現在値。未設定/取得失敗はnull。
async function projectToken() {
  try {
    const v = await kvs.get('project:token');
    return (v && v !== 'DISABLED') ? v : null;
  } catch (e) {
    return null;
  }
}

// ギャラリー経路（プロジェクト共通トークンで保護）。1URL＋1共通トークンで
// 公開中パターンを一覧・横断できるランディング。実体ファイルはS3の gallery/ 配下。
async function handleGallery(request, uri, method) {
  if (method !== 'GET' && method !== 'HEAD') {
    return deny(403);
  }
  const pt = await projectToken();
  if (!pt) {
    return htmlResponse(403, DISABLED_HTML); // ギャラリー未有効化 or 無効化済み
  }
  // 共通トークン検証: 成功で share_project Cookie を発行
  if (uri === '/gallery/verify') {
    const supplied = request.headers['x-share-token']
      ? request.headers['x-share-token'].value : '';
    if (supplied === pt) {
      return setCookie('share_project', pt);
    }
    return { statusCode: 401, statusDescription: 'Unauthorized' };
  }
  if (getCookie(request, 'share_project') !== pt) {
    return htmlResponse(401, GATE_HTML);
  }
  // /gallery または /gallery/ → gallery/index.html 補完
  if (uri === '/gallery' || uri === '/gallery/') {
    request.uri = '/gallery/index.html';
  }
  // /gallery/index.json 等はそのままS3のgallery/配下へ通す
  return request;
}

async function handler(event) {
  const request = event.request;
  const uri = request.uri;
  const method = request.method;

  // ルート直下はギャラリーへ寄せる
  if (uri === '/' || uri.indexOf('/gallery') === 0) {
    return await handleGallery(request, uri === '/' ? '/gallery/' : uri, method);
  }

  const slug = extractSlug(uri);
  if (!slug) {
    return deny(403);
  }

  // メソッド検査（多層防御: S3ポリシーだけに頼らない）
  const isCommentPut = method === 'PUT' && uri.startsWith('/comments/');
  if (method !== 'GET' && method !== 'HEAD' && !isCommentPut) {
    return deny(403);
  }

  // 状態取得（パターン別トークンのKVS読み取り）
  let expected;
  try {
    expected = await kvs.get('token:' + slug);
  } catch (e) {
    return htmlResponse(403, DISABLED_HTML); // 未発行slug
  }
  if (expected === 'DISABLED') {
    return htmlResponse(403, DISABLED_HTML);
  }

  // トークン検証エンドポイント（パターン別）
  if (uri === '/p/' + slug + '/verify') {
    const supplied = request.headers['x-share-token']
      ? request.headers['x-share-token'].value : '';
    if (supplied === expected) {
      return setCookie('share_' + slug, expected);
    }
    return { statusCode: 401, statusDescription: 'Unauthorized' };
  }

  // アクセス許可: パターン別Cookie一致 or プロジェクト共通Cookie一致のいずれか。
  // 共通トークンの照合はパターン別が一致しなかった場合のみ行う（通常はKVS読み取り1回に抑える）。
  let allowed = getCookie(request, 'share_' + slug) === expected;
  if (!allowed && getCookie(request, 'share_project')) {
    const pt = await projectToken();
    allowed = pt !== null && getCookie(request, 'share_project') === pt;
  }
  if (!allowed) {
    return htmlResponse(401, GATE_HTML);
  }

  // コメントPUTの形状検査: キーは {英数}.json のみ・content-typeはJSONのみ
  // （text/html等を置かせない = 配信ドメイン上のstored XSSを封じる）
  if (isCommentPut) {
    const keyOk = new RegExp('^/comments/' + slug + '/[A-Za-z0-9_-]+\\.json$').test(uri);
    const ct = request.headers['content-type'] ? request.headers['content-type'].value : '';
    if (!keyOk || ct.split(';')[0].trim() !== 'application/json') {
      return deny(403);
    }
    return request;
  }

  // コメント一覧: S3 ListObjectsV2 へ書き換え
  if (uri.startsWith('/comments-list/')) {
    request.uri = '/';
    request.querystring = {
      'list-type': { value: '2' },
      'prefix': { value: 'comments/' + slug + '/' },
    };
    return request;
  }

  // /p/{slug} または /p/{slug}/ → index.html 補完
  if (uri === '/p/' + slug || uri === '/p/' + slug + '/') {
    request.uri = '/p/' + slug + '/index.html';
  }

  return request;
}
