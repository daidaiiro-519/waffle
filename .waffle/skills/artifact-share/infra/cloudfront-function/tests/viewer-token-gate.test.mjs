// トークンの照合の振る舞いを、仕様のシナリオに沿って確かめる。
//
// 実行:  node infra/cloudfront-function/tests/viewer-token-gate.test.mjs
//
// 配信側の関数は import と KVS の取得を伴うため、そのままでは手元で動かない。
// この検証では両方を差し替えて読み込む（関数本体には手を入れない）。
//
// 保管に置く形は infra/contract/token-records.json が正で、公開する側
// （Python）の検証も同じ表を読む。ここで規則を書き直さないのは、書き直すと
// 同じ規則の写しが増えるだけで、突き合わせにならないため。
//
// 当初この検証は保管の値を平文として置いており、関数側も平文と比べていた。
// 両方が同じ誤解で揃って通り、実環境で初めて「正しいトークンでも開けない」
// として現れた。表を挟むのは、その再発を止めるため。

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

// 両側の唯一の共通点。ここに書かれた値をそのまま使い、規則を書き直さない
const contract = JSON.parse(
  readFileSync(join(here, '..', '..', 'contract', 'token-records.json'), 'utf-8'));
const vector = (name) => {
  const c = contract['ケース'].find((x) => x['名前'] === name);
  if (!c) throw new Error(`契約に「${name}」がありません`);
  return c;
};

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

// アーティファクトA: 公開中（契約の1件目）、プロジェクトPに所属。
// アーティファクトB: 公開停止。
const v1 = vector('無期限・初回発行');       // 世代1
const v2 = vector('再発行して世代が上がった状態');  // 世代2
const vx = vector('期限つき（発行時刻＋有効期間が期限になる）');

store.set('token:aaa', v1['保管の記録']);
store.set('token:bbb', contract['形式']['無効の印']);
store.set('proj:ppp', v1['保管の記録']);
store.set('pp:aaa', 'ppp');
store.set('pp:bbb', 'ppp');

console.log('■ 仕様のシナリオ');
await t('個別のトークンで開く',            req('/p/aaa/', { cookies: { [A+'aaa']: v1['手元の記録'] } }), 'pass-through');
await t('プロジェクトのトークンで開く',          req('/p/aaa/', { cookies: { [P+'ppp']: v1['手元の記録'] } }), 'pass-through');
await t('公開停止はプロジェクトのトークンでも開けない', req('/p/bbb/', { cookies: { [P+'ppp']: v1['手元の記録'] } }), 'status:403');
await t('所属していないものは開けない', req('/p/ccc/', { cookies: { [P+'ppp']: v1['手元の記録'] } }), 'status:403');
await t('トークンなしは入力画面へ',        req('/p/aaa/'), 'status:401');

console.log('■ 再発行と期限');
store.set('token:aaa', v2['保管の記録']);   // 再発行（値と世代が変わる）
await t('再発行前のトークンでは開けない',  req('/p/aaa/', { cookies: { [A+'aaa']: v1['手元の記録'] } }), 'status:401');
await t('値だけ合っても世代違いは弾く', req('/p/aaa/', { cookies: { [A+'aaa']: v2['保管の記録'].split('|')[0] + '.1' } }), 'status:401');
await t('新しいトークンでは開ける',        req('/p/aaa/', { cookies: { [A+'aaa']: v2['手元の記録'] } }), 'pass-through');
store.set('token:ddd', vx['保管の記録']);  // 期限つき
await t('期限切れは入力画面へ',        req('/p/ddd/', { cookies: { [A+'ddd']: vx['手元の記録'] } }), 'status:401');

console.log('■ 合言葉を示して入る');
const verify = (id, token) => req('/p/' + id + '/verify', { headers: { 'x-share-token': token } });
await t('正しい合言葉なら手元の記録が渡る', verify('aaa', v2['合言葉']), 'status:204');
await t('違う合言葉は拒む',               verify('aaa', v1['合言葉']), 'status:401');
await t('空の合言葉は拒む',               verify('aaa', ''),   'status:401');

console.log('■ 所属の上限');
const limit = contract['所属の記録']['上限'];
const many = contract['所属の記録']['ケース'].find((c) => c['名前'] === '上限ちょうど');
store.set('pp:eee', many['記録']);
store.set('token:eee', v1['保管の記録']);
for (const pid of many['プロジェクト']) store.set('proj:' + pid, v1['保管の記録']);
for (let i = 0; i < limit; i++) {
  const pid = many['プロジェクト'][i];
  await t(`所属${i + 1}件目のトークンで開ける`,
    req('/p/eee/', { cookies: { [P + pid]: v1['手元の記録'] } }), 'pass-through');
}

console.log('■ 反応の書き込み');
const put = (h) => req('/comments/aaa/1234-abcd.json', { method: 'PUT', cookies: { [A+'aaa']: v2['手元の記録'] }, headers: h });
await t('条件つきの書き込みは通る',    put({ 'content-type': 'application/json', 'content-length': 100, 'if-none-match': '*' }), 'pass-through');
await t('条件なしの書き込みは拒む',    put({ 'content-type': 'application/json', 'content-length': 100 }), 'status:403');
await t('種類が違えば拒む',            put({ 'content-type': 'text/html', 'content-length': 100, 'if-none-match': '*' }), 'status:403');
await t('大きすぎれば拒む',            put({ 'content-type': 'application/json', 'content-length': 20000, 'if-none-match': '*' }), 'status:403');
await t('削除は拒む',                  req('/p/aaa/', { method: 'DELETE', cookies: { [A+'aaa']: v2['手元の記録'] } }), 'status:403');

console.log(`\n通過 ${pass} / 失敗 ${fail}`);
process.exit(fail ? 1 : 0);
