// 合鍵の照合の振る舞いを、仕様のシナリオに沿って確かめる。
//
// 実行:  node infra/cloudfront-function/tests/viewer-token-gate.test.mjs
//
// 配信側の関数は import と KVS の取得を伴うため、そのままでは手元で動かない。
// この検証では両方を差し替えて読み込む（関数本体には手を入れない）。

import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, '..', 'viewer-token-gate.js'), 'utf-8')
  .replace("import cf from 'cloudfront';", '')
  .replace('const kvs = cf.kvs();', 'const kvs = globalThis.__KVS;')
  + '\nexport { handler };\n';
const work = join(mkdtempSync(join(tmpdir(), 'as-gate-')), 'gate.mjs');
writeFileSync(work, source, 'utf-8');

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

// 表示物A: 公開中(値 k1・世代 1)、まとめPに所属。表示物B: 公開停止。
store.set('token:aaa', 'k1|0|1');
store.set('token:bbb', 'DISABLED');
store.set('proj:ppp', 'pk1|0|1');
store.set('pp:aaa', 'ppp');
store.set('pp:bbb', 'ppp');

console.log('■ 仕様のシナリオ');
await t('個別の合鍵で開く',            req('/p/aaa/', { cookies: { [A+'aaa']: 'k1.1' } }), 'pass-through');
await t('まとめの合鍵で開く',          req('/p/aaa/', { cookies: { [P+'ppp']: 'pk1.1' } }), 'pass-through');
await t('公開停止はまとめの合鍵でも開けない', req('/p/bbb/', { cookies: { [P+'ppp']: 'pk1.1' } }), 'status:403');
await t('所属していないものは開けない', req('/p/ccc/', { cookies: { [P+'ppp']: 'pk1.1' } }), 'status:403');
await t('合鍵なしは入力画面へ',        req('/p/aaa/'), 'status:401');

console.log('■ 再発行と期限');
store.set('token:aaa', 'k2|0|2');   // 再発行（値と世代が変わる）
await t('再発行前の合鍵では開けない',  req('/p/aaa/', { cookies: { [A+'aaa']: 'k1.1' } }), 'status:401');
await t('値だけ合っても世代違いは弾く', req('/p/aaa/', { cookies: { [A+'aaa']: 'k2.1' } }), 'status:401');
await t('新しい合鍵では開ける',        req('/p/aaa/', { cookies: { [A+'aaa']: 'k2.2' } }), 'pass-through');
store.set('token:ddd', 'k9|1000000000|1');  // 期限切れ（2001年）
await t('期限切れは入力画面へ',        req('/p/ddd/', { cookies: { [A+'ddd']: 'k9.1' } }), 'status:401');

console.log('■ 反応の書き込み');
const put = (h) => req('/comments/aaa/1234-abcd.json', { method: 'PUT', cookies: { [A+'aaa']: 'k2.2' }, headers: h });
await t('条件つきの書き込みは通る',    put({ 'content-type': 'application/json', 'content-length': 100, 'if-none-match': '*' }), 'pass-through');
await t('条件なしの書き込みは拒む',    put({ 'content-type': 'application/json', 'content-length': 100 }), 'status:403');
await t('種類が違えば拒む',            put({ 'content-type': 'text/html', 'content-length': 100, 'if-none-match': '*' }), 'status:403');
await t('大きすぎれば拒む',            put({ 'content-type': 'application/json', 'content-length': 20000, 'if-none-match': '*' }), 'status:403');
await t('削除は拒む',                  req('/p/aaa/', { method: 'DELETE', cookies: { [A+'aaa']: 'k2.2' } }), 'status:403');

console.log(`\n通過 ${pass} / 失敗 ${fail}`);
process.exit(fail ? 1 : 0);
