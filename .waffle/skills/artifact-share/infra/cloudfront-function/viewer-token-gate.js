// 閲覧者の合鍵を照合する関門（CloudFront Functions・合鍵で見る面に載せる）
//
// 担うこと:
//   1. 合鍵の照合。KVS の "token:{slug}" に、現在の値・有効期限・世代番号を持つ。
//      期限切れ・世代違いはその場で拒む。値が "DISABLED" なら公開停止。
//   2. 交差条件の判定。まとめの合鍵で開けるのは、そのまとめに入っており、かつ
//      表示物自身が公開されているものだけ。片方だけを見ると、公開を止めたはずの
//      ものがまとめの合鍵で開ける欠陥になる。
//   3. 書き込みの検査。反応の記録は、キーの形・content-type・大きさに加えて
//      「既存が無いこと」の宣言を要求する。宣言の無い書き込みは拒む。
//      閲覧画面の側だけで宣言しても、宣言を省いた直接の書き込みを防げないため。
//   4. 反応の一覧を、保管の列挙要求へ書き換える。
//
// 担わないこと:
//   - 合鍵の発行・書き込み。ここは読むだけで、書き手は公開の受け口ひとつに限る。
//   - 表示物の中身の検査。中身は隔離された枠に入るため、ここでは触れない。
//   - 認証が要る面の判定。あちらは別の配信の口に載り、この関門を通らない。
//
// KVS の読み取り回数（実行予算に影響する）:
//   - 表示物ごとの合鍵で通る通常経路 = 1回
//   - まとめの合鍵経由 = + 所属の読み取り + 該当するまとめの読み取り（所属は3件まで）
//   最悪でおよそ5回。予算を超えると関数がエラーになり配信側が5xxを返す（安全側に倒れる）。

import cf from 'cloudfront';

const kvs = cf.kvs();

// Cookie 名の接頭辞。ブラウザ側で Domain 属性の付与を禁じ、Secure と Path=/ を強制する。
// 配信の出所を分ける前提が外部の静的な一覧に依存しているため、その依存をこの接頭辞で外す。
const COOKIE_PREFIX = '__Host-';
const ARTIFACT_COOKIE = COOKIE_PREFIX + 'as_a_';   // 表示物ごとの合鍵
const PROJECT_COOKIE = COOKIE_PREFIX + 'as_p_';    // まとめごとの合鍵

const GATE_HTML = `<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>共有トークンの入力</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f4f2ee;color:#1b2027;
font-family:-apple-system,"Segoe UI",system-ui,"Hiragino Sans","Yu Gothic",sans-serif;padding:24px}
.box{width:100%;max-width:392px;text-align:center}h1{font-size:1.3rem;font-weight:600;margin:0 0 .4rem}
p{font-size:.86rem;color:#5b6472;margin:0 0 1.4rem;line-height:1.7}
input{width:100%;font:inherit;font-size:1rem;text-align:center;letter-spacing:.08em;padding:.7rem;
border:1px solid #dcd8d0;border-radius:9px;background:#fff;color:#1b2027;
font-family:ui-monospace,Menlo,monospace;margin-bottom:.6rem}
button{width:100%;font:inherit;font-size:.9rem;font-weight:600;padding:.7rem;border-radius:9px;
border:1px solid #2f5d63;background:#2f5d63;color:#fff;cursor:pointer}
.note{font-size:.72rem;color:#68737e;margin-top:1rem}.err{color:#b3261e;font-size:.8rem;min-height:1.2em}
@media(prefers-color-scheme:dark){body{background:#16191c;color:#e8e5df}p{color:#a9b0ba}
input{background:#1f2327;border-color:#343a3f;color:#e8e5df}.note{color:#8b939d}}</style></head><body>
<div class="box"><h1>共有トークンの入力</h1>
<p>この内容を見るには、共有された相手から渡されたトークンが必要です。</p>
<input id="t" type="text" placeholder="0000-0000-0000" autocomplete="off" spellcheck="false" aria-label="共有トークン">
<button id="b" type="button">開く</button><p class="err" id="e"></p>
<p class="note">アカウント登録は不要です。<br>トークンが分からない場合は、URLを渡してくれた相手にお尋ねください。</p></div>
<script>
var b=document.getElementById('b'),t=document.getElementById('t'),e=document.getElementById('e');
function go(){e.textContent='';b.disabled=true;
fetch(location.pathname.replace(/\\/?$/,'/')+'verify',{headers:{'x-share-token':t.value.trim()}})
.then(function(r){if(r.ok){location.reload();return;}e.textContent='トークンが違うか、期限が切れています。';b.disabled=false;})
.catch(function(){e.textContent='通信に失敗しました。時間をおいてお試しください。';b.disabled=false;});}
b.addEventListener('click',go);t.addEventListener('keydown',function(ev){if(ev.key==='Enter')go();});
</script></body></html>`;

const DISABLED_HTML = `<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>公開されていません</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f4f2ee;color:#1b2027;
font-family:-apple-system,"Segoe UI",system-ui,"Hiragino Sans","Yu Gothic",sans-serif;padding:24px;text-align:center}
h1{font-size:1.05rem;font-weight:600;margin:.3rem 0 .4rem}
p{font-size:.85rem;color:#5b6472;margin:0;line-height:1.7}
.code{font-family:ui-monospace,Menlo,monospace;font-size:.72rem;color:#a1503f;font-weight:700}
@media(prefers-color-scheme:dark){body{background:#16191c;color:#e8e5df}p{color:#a9b0ba}}</style></head><body>
<div><p class="code">403</p><h1>このURLは公開されていません</h1>
<p>公開が止められているか、URLが誤っている可能性があります。<br>渡してくれた相手にお尋ねください。</p></div>
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

// 合鍵を発行済みの相手へ渡す。__Host- の条件（Secure・Path=/・Domain属性なし）を満たす。
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

// 保管された合鍵の記録を読む。
//   形式: "{値}|{期限のエポック秒}|{世代番号}"（期限0は無期限）
//   "DISABLED" は公開停止。読めない場合は未発行として扱う。
// 期限切れはここで失効させる。保管の書き換えを待たずに効く。
async function readKey(kvsKey) {
  let raw;
  try {
    raw = await kvs.get(kvsKey);
  } catch (e) {
    return null;                       // 未発行
  }
  if (!raw || raw === 'DISABLED') {
    return { disabled: true };         // 公開停止
  }
  const parts = raw.split('|');
  const value = parts[0];
  const expires = parts.length > 1 ? parseInt(parts[1], 10) : 0;
  const generation = parts.length > 2 ? parts[2] : '1';
  if (expires > 0 && Math.floor(Date.now() / 1000) > expires) {
    return { expired: true };
  }
  return { value: value, generation: generation, disabled: false };
}

// 閲覧者が持つ合鍵と、保管された記録が一致するか。
// 値だけでなく世代番号も突き合わせる（再発行のたびに世代が上がる）。
function matches(cookieValue, record) {
  if (!cookieValue || !record || !record.value) return false;
  const sep = cookieValue.lastIndexOf('.');
  if (sep < 0) return false;
  const value = cookieValue.slice(0, sep);
  const generation = cookieValue.slice(sep + 1);
  return value === record.value && generation === record.generation;
}

function extractSlug(uri) {
  const m = uri.match(/^\/(?:p|comments|comments-list)\/([A-Za-z0-9_-]+)/);
  return m ? m[1] : null;
}

function extractProject(uri) {
  const m = uri.match(/^\/proj\/([A-Za-z0-9_-]+)/);
  return m ? m[1] : null;
}

// まとめて見せる単位の経路。入っているものの一覧を配る。
async function handleProject(request, pid, uri, method) {
  if (method !== 'GET' && method !== 'HEAD') {
    return deny(403);
  }
  const record = await readKey('proj:' + pid);
  if (!record || record.disabled || record.expired) {
    return htmlResponse(403, DISABLED_HTML);
  }
  if (uri === '/proj/' + pid + '/verify') {
    const supplied = request.headers['x-share-token'] ? request.headers['x-share-token'].value : '';
    if (supplied === record.value) {
      return setCookie(PROJECT_COOKIE + pid, record.value + '.' + record.generation);
    }
    return { statusCode: 401, statusDescription: 'Unauthorized' };
  }
  if (!matches(getCookie(request, PROJECT_COOKIE + pid), record)) {
    return htmlResponse(401, GATE_HTML);
  }
  if (uri === '/proj/' + pid || uri === '/proj/' + pid + '/') {
    request.uri = '/proj/' + pid + '/index.html';
  }
  return request;
}

// まとめの合鍵で、この表示物を開けるか。
// 所属していることと、表示物自身が公開されていることの両方が要る。
// 表示物側の公開状態は呼び出し元で既に確かめてあるため、ここでは所属だけを見る。
async function allowedByProject(request, slug) {
  let member = null;
  try {
    member = await kvs.get('pp:' + slug);
  } catch (e) {
    return false;
  }
  if (!member) return false;

  const pids = member.split(' ');
  for (let i = 0; i < pids.length && i < 3; i++) {
    const pid = pids[i];
    if (!pid) continue;
    const cookie = getCookie(request, PROJECT_COOKIE + pid);
    if (!cookie) continue;
    const record = await readKey('proj:' + pid);
    if (record && !record.disabled && !record.expired && matches(cookie, record)) {
      return true;
    }
  }
  return false;
}

async function handler(event) {
  const request = event.request;
  const uri = request.uri;
  const method = request.method;

  const pid = extractProject(uri);
  if (pid) {
    return await handleProject(request, pid, uri, method);
  }

  const slug = extractSlug(uri);
  if (!slug) {
    return deny(403);
  }

  // 変更を伴う要求は、反応の記録の書き込みだけを通す
  const isCommentPut = method === 'PUT' && uri.startsWith('/comments/');
  if (method !== 'GET' && method !== 'HEAD' && !isCommentPut) {
    return deny(403);
  }

  // 表示物自身の状態。公開が止まっていれば、まとめの合鍵を持っていても開かせない
  const record = await readKey('token:' + slug);
  if (!record) {
    return htmlResponse(403, DISABLED_HTML);   // 未発行
  }
  if (record.disabled) {
    return htmlResponse(403, DISABLED_HTML);   // 公開停止
  }
  if (record.expired) {
    return htmlResponse(401, GATE_HTML);       // 期限切れ。渡し直せば開ける
  }

  if (uri === '/p/' + slug + '/verify') {
    const supplied = request.headers['x-share-token'] ? request.headers['x-share-token'].value : '';
    if (supplied === record.value) {
      return setCookie(ARTIFACT_COOKIE + slug, record.value + '.' + record.generation);
    }
    return { statusCode: 401, statusDescription: 'Unauthorized' };
  }

  // 開けるのは、表示物ごとの合鍵が一致するか、所属するまとめの合鍵が一致するとき
  let allowed = matches(getCookie(request, ARTIFACT_COOKIE + slug), record);
  if (!allowed) {
    allowed = await allowedByProject(request, slug);
  }
  if (!allowed) {
    return htmlResponse(401, GATE_HTML);
  }

  // 反応の記録の書き込み。形・種類・大きさに加えて、既存を上書きしない宣言を要求する。
  // 宣言を省いた直接の書き込みをここで拒むことで、他人の記録を壊せなくする。
  if (isCommentPut) {
    const keyOk = new RegExp('^/comments/' + slug + '/[A-Za-z0-9_-]+\\.json$').test(uri);
    const ct = request.headers['content-type'] ? request.headers['content-type'].value : '';
    const len = request.headers['content-length']
      ? parseInt(request.headers['content-length'].value, 10) : 0;
    const ifNoneMatch = request.headers['if-none-match']
      ? request.headers['if-none-match'].value.trim() : '';

    if (!keyOk) return deny(403);
    if (ct.split(';')[0].trim() !== 'application/json') return deny(403);
    if (!(len > 0) || len > 16384) return deny(403);      // 16KBまで
    if (ifNoneMatch !== '*') return deny(403);            // 上書きの宣言が無いものは通さない
    return request;
  }

  // 反応の一覧を、保管の列挙要求へ書き換える
  if (uri.startsWith('/comments-list/')) {
    request.uri = '/';
    request.querystring = {
      'list-type': { value: '2' },
      'prefix': { value: 'comments/' + slug + '/' },
    };
    return request;
  }

  // /p/{slug} と /p/{slug}/ は閲覧画面へ寄せる
  if (uri === '/p/' + slug || uri === '/p/' + slug + '/') {
    request.uri = '/p/' + slug + '/index.html';
  }

  return request;
}
