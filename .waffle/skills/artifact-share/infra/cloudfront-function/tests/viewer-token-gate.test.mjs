// トークンの照合の振る舞いを、仕様のシナリオに沿って確かめる。
//
// 実行:  node infra/cloudfront-function/tests/viewer-token-gate.test.mjs
//
// 配信側の関数は import と KVS の取得を伴うため、そのままでは手元で動かない。
// この検証では両方を差し替えて読み込む（関数本体には手を入れない）。
//
// 保管に置くのは合言葉そのものではなく、照合できる形（sha256の先頭32文字）。
// 当初この検証は平文を置いており、関数側も平文と比べていたため、両方が
// 同じ誤解で揃って通っていた。実環境で初めて「正しいトークンでも開けない」
// として現れた。ここでは実際の形を作って置く。

import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, '..', 'viewer-token-gate.js'), 'utf-8')
  .replace("import cf from 'cloudfront';", '')
  .replace("import crypto from 'crypto';", "import crypto from 'node:crypto';")
  .replace('const kvs = cf.kvs();', 'const kvs = globalThis.__KVS;')
  + '\nexport { handler };\n';
const work = join(mkdtempSync(join(tmpdir(), 'as-gate-')), 'gate.mjs');
writeFileSync(work, source, 'utf-8');

// 公開のときに保管へ残す形（lambda/admin_api/publish.py の token_record と同じ）
const fingerprint = (token) =>
  createHash('sha256').update(token).digest('hex').slice(0, 32);
const record = (token, { expires = 0, generation = 1 } = {}) =>
  `${fingerprint(token)}|${expires}|${generation}`;

const store = new Map();
globalThis.__KVS = { get: async (k) => { if (!store.has(k)) throw new Error('no key'); return store.get(k); } };
const { handler } = await import(work);

const req = (uri, { cookies = {}, method = 'GET', headers = {} } = {}) => ({
  request: {
    uri, method,
    cookies: Object.fromEntries(Object.entries(cookies).map(([k, v]) => [k, { value: v }])),
    headers: Object.fromEntries(Object.entries(headers).map(([k, v]) => [k, { value: String(v) }])),
    querystring: {},
  },
});
const A = '__Host-as_a_', P = '__Host-as_p_';
let pass = 0, fail = 0;
const t = async (name, fn, expect) => {
  const r = await handler(fn);
  const got = r.statusCode ? `status:${r.statusCode}` : 'pass-through';
  if (got === expect) { console.log(`OK   ${name}`); pass++; }
  else { console.log(`NG   ${name}  期待:${expect} 実際:${got}`); fail++; }
};

// アーティファクトA: 公開中（合言葉 k1・世代 1）、プロジェクトPに所属。
// アーティファクトB: 公開停止。
store.set('token:aaa', record('k1'));
store.set('token:bbb', 'DISABLED');
store.set('proj:ppp', record('pk1'));
store.set('pp:aaa', 'ppp');
store.set('pp:bbb', 'ppp');

console.log('■ 仕様のシナリオ');
await t('個別のトークンで開く',            req('/p/aaa/', { cookies: { [A+'aaa']: fingerprint('k1') + '.1' } }), 'pass-through');
await t('プロジェクトのトークンで開く',          req('/p/aaa/', { cookies: { [P+'ppp']: fingerprint('pk1') + '.1' } }), 'pass-through');
await t('公開停止はプロジェクトのトークンでも開けない', req('/p/bbb/', { cookies: { [P+'ppp']: fingerprint('pk1') + '.1' } }), 'status:403');
await t('所属していないものは開けない', req('/p/ccc/', { cookies: { [P+'ppp']: fingerprint('pk1') + '.1' } }), 'status:403');
await t('トークンなしは入力画面へ',        req('/p/aaa/'), 'status:401');

console.log('■ 再発行と期限');
store.set('token:aaa', record('k2', { generation: 2 }));   // 再発行（値と世代が変わる）
await t('再発行前のトークンでは開けない',  req('/p/aaa/', { cookies: { [A+'aaa']: fingerprint('k1') + '.1' } }), 'status:401');
await t('値だけ合っても世代違いは弾く', req('/p/aaa/', { cookies: { [A+'aaa']: fingerprint('k2') + '.1' } }), 'status:401');
await t('新しいトークンでは開ける',        req('/p/aaa/', { cookies: { [A+'aaa']: fingerprint('k2') + '.2' } }), 'pass-through');
store.set('token:ddd', record('k9', { expires: 1000000000 }));  // 期限切れ（2001年）
await t('期限切れは入力画面へ',        req('/p/ddd/', { cookies: { [A+'ddd']: fingerprint('k9') + '.1' } }), 'status:401');

console.log('■ 合言葉を示して入る');
const verify = (id, token) => req('/p/' + id + '/verify', { headers: { 'x-share-token': token } });
await t('正しい合言葉なら手元の記録が渡る', verify('aaa', 'k2'), 'status:204');
await t('違う合言葉は拒む',               verify('aaa', 'k1'), 'status:401');
await t('空の合言葉は拒む',               verify('aaa', ''),   'status:401');

console.log('■ 反応の書き込み');
const put = (h) => req('/comments/aaa/1234-abcd.json', { method: 'PUT', cookies: { [A+'aaa']: fingerprint('k2') + '.2' }, headers: h });
await t('条件つきの書き込みは通る',    put({ 'content-type': 'application/json', 'content-length': 100, 'if-none-match': '*' }), 'pass-through');
await t('条件なしの書き込みは拒む',    put({ 'content-type': 'application/json', 'content-length': 100 }), 'status:403');
await t('種類が違えば拒む',            put({ 'content-type': 'text/html', 'content-length': 100, 'if-none-match': '*' }), 'status:403');
await t('大きすぎれば拒む',            put({ 'content-type': 'application/json', 'content-length': 20000, 'if-none-match': '*' }), 'status:403');
await t('削除は拒む',                  req('/p/aaa/', { method: 'DELETE', cookies: { [A+'aaa']: fingerprint('k2') + '.2' } }), 'status:403');

console.log(`\n通過 ${pass} / 失敗 ${fail}`);
process.exit(fail ? 1 : 0);
