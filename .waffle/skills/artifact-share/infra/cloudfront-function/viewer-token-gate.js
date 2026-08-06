// 閲覧者のトークンを照合する閲覧ゲート（CloudFront Functions・閲覧の面に載せる）
//
// 担うこと:
//   1. トークンの照合。KVS の "token:{artifactId}" に、現在の値・有効期限・世代番号を持つ。
//      期限切れ・世代違いはその場で拒む。値が "DISABLED" なら公開停止。
//   2. 交差条件の判定。プロジェクトのトークンで開けるのは、そのまとめに入っており、かつ
//      アーティファクト自身が公開されているものだけ。片方だけを見ると、公開を止めたはずの
//      ものがプロジェクトのトークンで開ける欠陥になる。
//   3. 書き込みの検査。反応の記録は、キーの形・content-type・大きさに加えて
//      「既存が無いこと」の宣言を要求する。宣言の無い書き込みは拒む。
//      閲覧画面の側だけで宣言しても、宣言を省いた直接の書き込みを防げないため。
//   4. 反応の一覧を、保管の列挙要求へ書き換える。
//
// 担わないこと:
//   - トークンの発行・書き込み。ここは読むだけで、書き手は管理APIひとつに限る。
//   - アーティファクトの中身の検査。中身は隔離された枠に入るため、ここでは触れない。
//   - 認証が要る面の判定。あちらは別の配信の口に載り、この閲覧ゲートを通らない。
//
// KVS の読み取り回数（実行予算に影響する）:
//   - アーティファクトごとのトークンで通る通常経路 = 1回
//   - プロジェクトのトークン経由 = + 所属の読み取り + 該当するまとめの読み取り（所属は3件まで）
//   最悪でおよそ5回。予算を超えると関数がエラーになり配信側が5xxを返す（安全側に倒れる）。

import cf from 'cloudfront';
import crypto from 'crypto';

const kvs = cf.kvs();

// Cookie 名の接頭辞。ブラウザ側で Domain 属性の付与を禁じ、Secure と Path=/ を強制する。
// 配信の出所を分ける前提が外部の静的な一覧に依存しているため、その依存をこの接頭辞で外す。
const COOKIE_PREFIX = '__Host-';
const ARTIFACT_COOKIE = COOKIE_PREFIX + 'as_a_';   // アーティファクトごとのトークン
const PROJECT_COOKIE = COOKIE_PREFIX + 'as_p_';    // まとめごとのトークン

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

// トークンを発行済みの相手へ渡す。__Host- の条件（Secure・Path=/・Domain属性なし）を満たす。
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

// 保管された記録を読む。
//   形式: "{照合の形}|{期限のエポック秒}" を ";" でつないだもの（期限0は期限なし）
//   "DISABLED" は公開停止。空は「誰にも渡していない」で、公開は止まっていない。
// 1つの対象に複数の閲覧トークンを渡せる。ここにある記録をすべて見るだけなので、
// 本数の上限は知らない——先頭から決まった数しか読まない実装にすると、書き手が
// 上限を伝え忘れたときに閲覧者だけが開けない状態になる。
// 期限切れはここで失効させる。保管の書き換えを待たずに効く。
async function readKey(kvsKey) {
  let raw;
  try {
    raw = await kvs.get(kvsKey);
  } catch (e) {
    return null;                       // 未発行
  }
  if (raw === 'DISABLED') {
    return { disabled: true };         // 公開停止
  }
  if (!raw) {
    return { values: [], disabled: false };   // 誰にも渡していない
  }
  const now = Math.floor(Date.now() / 1000);
  const values = [];
  let anyExpired = false;
  for (const record of raw.split(';')) {
    if (!record) continue;
    const parts = record.split('|');
    const expires = parts.length > 1 ? parseInt(parts[1], 10) : 0;
    if (expires > 0 && now > expires) { anyExpired = true; continue; }
    values.push(parts[0]);
  }
  if (values.length === 0 && anyExpired) {
    return { expired: true };
  }
  return { values: values, disabled: false };
}

// 閲覧者が持つ値と、保管された記録のどれかが一致するか。
// 1本ずつが独立しているので、他の記録が入れ替わっても手元の値は効き続ける。
function matches(cookieValue, record) {
  if (!cookieValue || !record || !record.values) return false;
  return record.values.indexOf(cookieValue) >= 0;
}

function extractArtifactId(uri) {
  const m = uri.match(/^\/(?:p|comments|comments-list)\/([A-Za-z0-9_-]+)/);
  return m ? m[1] : null;
}

function extractProject(uri) {
  const m = uri.match(/^\/proj\/([A-Za-z0-9_-]+)/);
  return m ? m[1] : null;
}

// 渡されたトークンを、保管に残した形へ変えて突き合わせる。
// 保管にはトークンそのものを置かず、照合できる形だけを置いているため、
// 平文のまま比べても永久に一致しない。
function fingerprint(token) {
  return crypto.createHash('sha256').update(token).digest('hex').slice(0, 32);
}

// プロジェクトの経路。入っているものの一覧を配る。
async function handleProject(request, pid, uri, method) {
  if (method !== 'GET' && method !== 'HEAD') {
    return deny(403);
  }
  const record = await readKey('proj:' + pid);
  if (!record || record.disabled || record.expired) {
    return htmlResponse(403, DISABLED_HTML);
  }
  if (uri === '/proj/' + pid + '/verify') {
    const supplied = request.headers['x-share-token'] ? request.headers['x-share-token'].value.trim() : '';
    if (supplied && matches(fingerprint(supplied), record)) {
      return setCookie(PROJECT_COOKIE + pid, fingerprint(supplied));
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

// プロジェクトのトークンで、このアーティファクトを開けるか。
// 所属していることと、アーティファクト自身が公開されていることの両方が要る。
// アーティファクト側の公開状態は呼び出し元で既に確かめてあるため、ここでは所属だけを見る。
async function allowedByProject(request, artifactId) {
  let member = null;
  try {
    member = await kvs.get('pp:' + artifactId);
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

  const artifactId = extractArtifactId(uri);
  if (!artifactId) {
    return deny(403);
  }

  // 変更を伴う要求は、反応の記録の書き込みだけを通す
  const isCommentPut = method === 'PUT' && uri.startsWith('/comments/');
  if (method !== 'GET' && method !== 'HEAD' && !isCommentPut) {
    return deny(403);
  }

  // アーティファクト自身の状態。公開が止まっていれば、プロジェクトのトークンを持っていても開かせない
  const record = await readKey('token:' + artifactId);
  if (!record) {
    return htmlResponse(403, DISABLED_HTML);   // 未発行
  }
  if (record.disabled) {
    return htmlResponse(403, DISABLED_HTML);   // 公開停止
  }
  if (record.expired) {
    return htmlResponse(401, GATE_HTML);       // 期限切れ。渡し直せば開ける
  }

  if (uri === '/p/' + artifactId + '/verify') {
    const supplied = request.headers['x-share-token'] ? request.headers['x-share-token'].value.trim() : '';
    if (supplied && matches(fingerprint(supplied), record)) {
      return setCookie(ARTIFACT_COOKIE + artifactId, fingerprint(supplied));
    }
    return { statusCode: 401, statusDescription: 'Unauthorized' };
  }

  // 開けるのは、アーティファクトごとのトークンが一致するか、所属するまとめのトークンが一致するとき
  let allowed = matches(getCookie(request, ARTIFACT_COOKIE + artifactId), record);
  if (!allowed) {
    allowed = await allowedByProject(request, artifactId);
  }
  if (!allowed) {
    return htmlResponse(401, GATE_HTML);
  }

  // 反応の記録の書き込み。形・種類・大きさに加えて、既存を上書きしない宣言を要求する。
  // 宣言を省いた直接の書き込みをここで拒むことで、他人の記録を壊せなくする。
  if (isCommentPut) {
    const keyOk = new RegExp('^/comments/' + artifactId + '/[A-Za-z0-9_-]+\\.json$').test(uri);
    const ct = request.headers['content-type'] ? request.headers['content-type'].value : '';
    const len = request.headers['content-length']
      ? parseInt(request.headers['content-length'].value, 10) : 0;
    const ifNoneMatch = request.headers['if-none-match']
      ? request.headers['if-none-match'].value.trim() : '';

    if (!keyOk) return deny(403);
    // 差し替えの区切りは仕組みだけが残す。閲覧者がこの鍵で書けると、
    // 嘘の「ここで中身が差し替えられました」を並びに差し込める。
    // 本文では防げない——ここは要求の本文を読めないため（infra/contract/comment-entries.json）
    if (uri.endsWith('-replaced.json')) return deny(403);
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
      'prefix': { value: 'comments/' + artifactId + '/' },
    };
    return request;
  }

  // /p/{artifactId} と /p/{artifactId}/ は閲覧画面へ寄せる
  if (uri === '/p/' + artifactId || uri === '/p/' + artifactId + '/') {
    request.uri = '/p/' + artifactId + '/index.html';
  }

  return request;
}
