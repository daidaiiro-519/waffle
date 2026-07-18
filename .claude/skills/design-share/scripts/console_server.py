#!/usr/bin/env python3
"""console_server.py — 作成者向け横断管理コンソール（localhostのみ・本番非公開）。

合意事項（ブレスト論点6・7）:
  - 本番AWS環境にはデプロイしない。Claude Code上でこのスクリプトを起動し、
    起動時に表示されるURL（乱数トークン付き）をブラウザで開く
  - 認証は開発者が既に持つAWS認証情報（aws cli）をそのまま使う
  - 全セッション・全パターンを横断して一覧し、操作は行ごとの「⋯」メニューから行う
    （エクスポート/名前変更/トークン再発行/無効化・再公開）。共有ギャラリーの
    有効化/共通トークン再発行/無効化も同画面から行える

セキュリティ（advisor批評の反映）:
  - Hostヘッダー検証（DNSリバインディング対策）
  - 変更系APIは起動時乱数トークンを X-Console-Token ヘッダーで要求
    （カスタムヘッダー必須 = ブラウザのプリフライトが強制され、外部サイトからのCSRFを遮断）

使い方: python3 console_server.py  （design-share.env のあるディレクトリで実行、
        または DESIGN_SHARE_ENV に絶対パスを設定）
"""
import http.server
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.parse

HOST, PORT = "127.0.0.1", 8787
ALLOWED_HOSTS = {f"{HOST}:{PORT}", f"localhost:{PORT}"}
CONSOLE_TOKEN = secrets.token_urlsafe(16)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def resolve_env_path() -> str:
    env_path = os.path.abspath(os.environ.get("DESIGN_SHARE_ENV", "./design-share.env"))
    if not os.path.exists(env_path):
        sys.exit(f"error: {env_path} がありません。CloudFormation Outputsから作成してください。")
    return env_path


ENV_PATH = resolve_env_path()


def load_env() -> dict:
    conf = {}
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if k.startswith("export "):  # `export AWS_PROFILE=dev` 形式に対応
                    k = k[len("export "):].strip()
                conf[k] = v
    return conf


CONF = load_env()
# env内のAWS認証情報（SSO名前付きプロファイル等）をこのプロセスのaws呼び出しにも適用する。
# これがないと、シェルにAWS_PROFILEを export せずに起動した場合に一覧が空になる。
for _k in ("AWS_PROFILE", "AWS_REGION", "AWS_DEFAULT_REGION"):
    if CONF.get(_k):
        os.environ.setdefault(_k, CONF[_k])

GALLERY_URL = f"https://{CONF.get('DISTRIBUTION_DOMAIN', '')}/gallery/"


def aws(*args: str) -> str:
    return subprocess.run(["aws", *args], check=True, capture_output=True, text=True).stdout


def run_script(name: str, *args: str) -> tuple[bool, str]:
    # bash側はDESIGN_SHARE_ENVを絶対パスで受け取るため、cwdに依存しない
    env = {**os.environ, "DESIGN_SHARE_ENV": ENV_PATH}
    proc = subprocess.run(
        ["bash", os.path.join(SCRIPT_DIR, name), *args],
        capture_output=True, text=True, cwd=os.getcwd(), env=env,
    )
    return proc.returncode == 0, proc.stdout + proc.stderr


def list_patterns() -> list[dict]:
    try:
        out = aws("s3api", "list-objects-v2", "--bucket", CONF["BUCKET"],
                  "--prefix", "meta/", "--query", "Contents[].Key", "--output", "json")
        keys = json.loads(out) or []
    except subprocess.CalledProcessError:
        return []
    patterns = []
    for key in keys:
        try:
            patterns.append(json.loads(aws("s3", "cp", f"s3://{CONF['BUCKET']}/{key}", "-")))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
    return sorted(patterns, key=lambda p: p.get("updatedAt", ""), reverse=True)


def gallery_status() -> str:
    try:
        v = aws("cloudfront-keyvaluestore", "get-key", "--kvs-arn", CONF["KVS_ARN"],
                "--key", "project:token", "--query", "Value", "--output", "text").strip()
    except subprocess.CalledProcessError:
        return "unset"
    if not v or v == "None":
        return "unset"
    return "disabled" if v == "DISABLED" else "enabled"


def state() -> dict:
    return {"patterns": list_patterns(),
            "gallery": {"status": gallery_status(), "url": GALLERY_URL}}


PAGE = r"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>design-share console</title>
<style>
:root{--ground:#F1F4F6;--surface:#FFFFFF;--surface-2:#F7F9FA;--ink:#1C2733;--muted:#5A6B7A;--faint:#8494A1;
--line:#E1E5EA;--accent:#2F6F76;--accent-ink:#FFF;--pos-bg:#E2F0E8;--pos-fg:#1E7A50;--crit-bg:#F6E5E3;--crit-fg:#B23A30;
--shadow:0 1px 2px rgba(28,39,51,.06),0 8px 24px rgba(28,39,51,.06);--radius:10px;
--mono:ui-monospace,"SF Mono","IBM Plex Mono",Menlo,monospace;--sans:system-ui,-apple-system,"Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif}
@media(prefers-color-scheme:dark){:root{--ground:#10161C;--surface:#19222B;--surface-2:#1E2831;--ink:#E7EDF1;--muted:#9DAAB5;
--faint:#6E7E8B;--line:#2A353F;--accent:#52A2A9;--accent-ink:#06171A;--pos-bg:#16332A;--pos-fg:#67C79A;--crit-bg:#3A211F;--crit-fg:#E58B80;
--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35)}}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);line-height:1.5;padding:clamp(1rem,4vw,2.4rem) 1rem 4rem}
.wrap{max-width:940px;margin:0 auto}
header.top{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem 1rem;margin-bottom:.3rem}
header.top h1{font-size:1.3rem;font-weight:650;margin:0;letter-spacing:-.01em}
.env{font-family:var(--mono);font-size:.72rem;color:var(--muted);background:var(--surface-2);border:1px solid var(--line);border-radius:999px;padding:.15rem .6rem}
.sub{color:var(--muted);font-size:.85rem;margin:.1rem 0 1.3rem}
.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem;margin-bottom:1.2rem}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:.8rem 1rem;box-shadow:var(--shadow)}
.stat .n{font-size:1.6rem;font-weight:650;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.stat .k{font-family:var(--mono);font-size:.66rem;letter-spacing:.04em;text-transform:uppercase;color:var(--faint);margin-top:.1rem}
.stat.pos .n{color:var(--pos-fg)}.stat.crit .n{color:var(--crit-fg)}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:1.2rem}
.panel .ph{display:flex;align-items:center;gap:.6rem;padding:.7rem 1.1rem;border-bottom:1px solid var(--line);background:var(--surface-2);border-radius:var(--radius) var(--radius) 0 0}
.panel .ph h2{font-size:.78rem;font-weight:600;letter-spacing:.03em;text-transform:uppercase;color:var(--muted);margin:0;flex:1}
.gwrap{display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;padding:.9rem 1.1rem}
.gwrap .gurl{font-family:var(--mono);font-size:.78rem;color:var(--accent);word-break:break-all;flex:1;min-width:12rem}
.gwrap .goff{font-size:.82rem;color:var(--muted);flex:1;min-width:12rem}
table{width:100%;border-collapse:collapse}
thead th{text-align:left;font-family:var(--mono);font-size:.66rem;letter-spacing:.03em;text-transform:uppercase;color:var(--faint);font-weight:600;padding:.7rem 1.1rem;border-bottom:1px solid var(--line)}
tbody td{padding:.8rem 1.1rem;border-bottom:1px solid var(--line);vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
.name{font-weight:600}.slug{font-family:var(--mono);font-size:.78rem;color:var(--muted)}
.date{font-family:var(--mono);font-size:.78rem;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
.pill{display:inline-flex;align-items:center;gap:.35rem;font-size:.72rem;font-weight:600;padding:.18rem .6rem;border-radius:999px;white-space:nowrap}
.pill::before{content:"";width:.45rem;height:.45rem;border-radius:50%;background:currentColor}
.pill.active{background:var(--pos-bg);color:var(--pos-fg)}.pill.disabled{background:var(--crit-bg);color:var(--crit-fg)}
.pill.unset{background:var(--surface-2);color:var(--faint)}
td.c-actions{text-align:right}
.menu-wrap{position:relative;display:inline-block}
button.kebab{font:inherit;cursor:pointer;width:2rem;height:2rem;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--muted);transition:background .12s,border-color .12s,color .12s}
button.kebab:hover,button.kebab[aria-expanded=true]{background:var(--surface-2);border-color:var(--accent);color:var(--ink)}
button.kebab:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button.kebab svg{width:1.1rem;height:1.1rem;display:block}
.menu{position:absolute;right:0;top:calc(100% + .35rem);z-index:40;min-width:13rem;background:var(--surface);border:1px solid var(--line);border-radius:10px;box-shadow:0 6px 16px rgba(28,39,51,.14),0 12px 40px rgba(28,39,51,.18);padding:.35rem;display:none;text-align:left}
.menu.open{display:block;animation:pop .1s ease-out}
@keyframes pop{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
.menu button.item{font:inherit;font-size:.82rem;width:100%;text-align:left;cursor:pointer;display:flex;align-items:center;gap:.6rem;padding:.5rem .6rem;border:none;border-radius:7px;background:transparent;color:var(--ink);transition:background .1s}
.menu button.item .ic{width:1.05rem;text-align:center;color:var(--muted);flex:none}
.menu button.item:hover,.menu button.item:focus-visible{background:var(--surface-2);outline:none}
.menu button.item.danger{color:var(--crit-fg)}.menu button.item.danger .ic{color:var(--crit-fg)}
.menu button.item.danger:hover,.menu button.item.danger:focus-visible{background:var(--crit-bg)}
.menu button.item.good{color:var(--pos-fg)}.menu button.item.good .ic{color:var(--pos-fg)}
.menu .sep{height:1px;background:var(--line);margin:.3rem .2rem}
.console h2{font-family:var(--mono);font-size:.7rem;letter-spacing:.04em;text-transform:uppercase;color:var(--faint);margin:0 0 .4rem}
pre.log{font-family:var(--mono);font-size:.78rem;line-height:1.6;margin:0;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:.9rem 1.1rem;min-height:3.4rem;white-space:pre-wrap;word-break:break-word;color:var(--muted);box-shadow:var(--shadow)}
pre.log .ok{color:var(--pos-fg)}pre.log .warn{color:var(--crit-fg)}
@media(max-width:640px){
table,thead,tbody,tr,td{display:block}thead{display:none}
tbody tr{position:relative;border-bottom:1px solid var(--line);padding:.9rem 1.1rem}tbody tr:last-child{border-bottom:none}
tbody td{border:none;padding:.18rem 0}tbody td.c-name{font-size:1rem;padding-right:2.6rem}
tbody td.c-actions{position:absolute;top:.7rem;right:.9rem;margin:0;padding:0}
td[data-k]:not(.c-actions)::before{content:attr(data-k) "  ";font-family:var(--mono);font-size:.66rem;text-transform:uppercase;letter-spacing:.03em;color:var(--faint)}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style></head><body>
<div class="wrap">
<header class="top"><h1>design-share 管理コンソール</h1><span class="env" id="env"></span></header>
<p class="sub">公開中の全パターンを横断管理します。localhostのみ・本番非公開。操作はAWS認証情報で直接実行されます。</p>
<div class="summary">
<div class="stat"><div class="n" id="s-total">–</div><div class="k">総パターン</div></div>
<div class="stat pos"><div class="n" id="s-active">–</div><div class="k">公開中</div></div>
<div class="stat crit"><div class="n" id="s-disabled">–</div><div class="k">無効化済み</div></div>
</div>
<div class="panel"><div class="ph"><h2>共有ギャラリー</h2><span id="g-actions"></span></div>
<div class="gwrap" id="g-body"></div></div>
<div class="panel"><div class="ph"><h2>パターン一覧</h2></div>
<table><thead><tr><th>パターン名</th><th>slug</th><th>状態</th><th>更新日</th><th>操作</th></tr></thead>
<tbody id="rows"><tr><td colspan="5" style="padding:1rem 1.1rem;color:var(--muted)">読み込み中…</td></tr></tbody></table></div>
<div class="console"><h2>操作ログ</h2><pre class="log" id="log">操作を選ぶと結果をここに表示します。</pre></div>
</div>
<script>
const TOKEN=new URLSearchParams(location.search).get('token')||'';
const $=(id)=>document.getElementById(id);
const KEBAB='<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="3" r="1.5" fill="currentColor"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/><circle cx="8" cy="13" r="1.5" fill="currentColor"/></svg>';
let openMenu=null;
function closeMenu(){if(!openMenu)return;openMenu.menu.classList.remove('open');openMenu.trigger.setAttribute('aria-expanded','false');openMenu=null;}
document.addEventListener('click',closeMenu);
document.addEventListener('keydown',(e)=>{if(e.key==='Escape')closeMenu();});
function log(t,cls){const l=$('log');l.textContent='';const s=document.createElement('span');if(cls)s.className=cls;s.textContent=t;l.appendChild(s);}
async function api(path,opts){const r=await fetch(path,Object.assign({method:'POST',headers:{'X-Console-Token':TOKEN}},opts||{}));return{ok:r.ok,text:await r.text()};}
async function doOp(path,label){closeMenu();log(label+' 実行中…');const {ok,text}=await api(path);log(text.trim()||(ok?'完了':'失敗'),ok?'ok':'warn');refresh();}
function item(icon,label,cls,disabled,onClick){const b=document.createElement('button');b.type='button';b.className='item'+(cls?' '+cls:'');b.setAttribute('role','menuitem');if(disabled)b.disabled=true;
const ic=document.createElement('span');ic.className='ic';ic.textContent=icon;const lb=document.createElement('span');lb.textContent=label;b.append(ic,lb);
if(!disabled)b.addEventListener('click',(e)=>{e.stopPropagation();onClick();});return b;}
function menuButton(aria,items){const wrap=document.createElement('div');wrap.className='menu-wrap';
const trig=document.createElement('button');trig.type='button';trig.className='kebab';trig.innerHTML=KEBAB;
trig.setAttribute('aria-haspopup','true');trig.setAttribute('aria-expanded','false');trig.setAttribute('aria-label',aria);
const menu=document.createElement('div');menu.className='menu';menu.setAttribute('role','menu');items.forEach(x=>menu.appendChild(x));
trig.addEventListener('click',(e)=>{e.stopPropagation();const isOpen=openMenu&&openMenu.menu===menu;closeMenu();if(!isOpen){menu.classList.add('open');trig.setAttribute('aria-expanded','true');openMenu={menu,trigger:trig};}});
menu.addEventListener('click',(e)=>e.stopPropagation());wrap.append(trig,menu);return wrap;}
function sep(){const d=document.createElement('div');d.className='sep';return d;}

function patternMenu(p){const items=[];
items.push(item('↓','エクスポート','',false,()=>doOp('/api/export?slug='+encodeURIComponent(p.slug),'export')));
items.push(item('✎','名前を変更','',false,()=>renamePattern(p)));
if(p.status==='active'){
items.push(item('⟳','トークンを再発行','',false,()=>doOp('/api/rotate?slug='+encodeURIComponent(p.slug),'rotate')));
items.push(sep());
items.push(item('⦸','無効化する','danger',false,()=>{if(confirm('「'+p.name+'」を無効化しますか？\n（先にエクスポートを実行します。データは残り、あとで再公開できます）'))doOp('/api/invalidate?slug='+encodeURIComponent(p.slug),'disable');}));
}else{
items.push(sep());
items.push(item('▲','再公開する（新トークン）','good',false,()=>doOp('/api/rotate?slug='+encodeURIComponent(p.slug),'republish')));
}
return menuButton(p.name+' の操作メニュー',items);}

function renamePattern(p){closeMenu();const name=prompt('新しい表示名を入力してください',p.name);if(name===null)return;const t=name.trim();if(!t){log('名前が空です。変更を中止しました。','warn');return;}
doOp('/api/rename?slug='+encodeURIComponent(p.slug)+'&name='+encodeURIComponent(t),'rename');}

function galleryControls(g){
const box=$('g-actions');box.textContent='';const body=$('g-body');body.textContent='';
const pill=document.createElement('span');pill.className='pill '+(g.status==='enabled'?'active':g.status==='disabled'?'disabled':'unset');
pill.textContent=g.status==='enabled'?'有効':g.status==='disabled'?'無効化済み':'未設定';box.appendChild(pill);
const items=[];
if(g.status==='enabled'){
const url=document.createElement('span');url.className='gurl';url.textContent=g.url;body.appendChild(url);
items.push(item('⟳','共通トークンを再発行','',false,()=>doOp('/api/gallery?op=rotate','gallery rotate')));
items.push(sep());
items.push(item('⦸','ギャラリーを無効化','danger',false,()=>{if(confirm('共有ギャラリーを無効化しますか？\n（各パターンの個別URLには影響しません）'))doOp('/api/gallery?op=disable','gallery disable');}));
}else{
const msg=document.createElement('span');msg.className='goff';msg.textContent=g.status==='disabled'?'無効化済み。有効化すると同じURLで再開します。':'未設定。有効化すると1つのURL＋共通トークンで全パターンを横断閲覧できます。';body.appendChild(msg);
items.push(item('▲','ギャラリーを有効化','good',false,()=>doOp('/api/gallery?op=init','gallery init')));
}
$('g-actions').appendChild(menuButton('共有ギャラリーの操作メニュー',items));
}

function renderRows(patterns){const tb=$('rows');tb.textContent='';
if(!patterns.length){const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=5;td.style.padding='1rem 1.1rem';td.style.color='var(--muted)';td.textContent='まだデプロイされたパターンはありません。';tr.appendChild(td);tb.appendChild(tr);return;}
patterns.forEach(p=>{const tr=document.createElement('tr');
const n=document.createElement('td');n.className='c-name name';n.textContent=p.name||p.slug;
const s=document.createElement('td');s.className='slug';s.dataset.k='slug';s.textContent=p.slug;
const st=document.createElement('td');st.dataset.k='状態';const pill=document.createElement('span');pill.className='pill '+(p.status==='active'?'active':'disabled');pill.textContent=p.status==='active'?'公開中':'無効化済み';st.appendChild(pill);
const d=document.createElement('td');d.className='date';d.dataset.k='更新';d.textContent=(p.updatedAt||'').slice(0,10);
const a=document.createElement('td');a.className='c-actions';a.dataset.k='操作';a.appendChild(patternMenu(p));
tr.append(n,s,st,d,a);tb.appendChild(tr);});}

async function refresh(){const r=await fetch('/api/state');const data=await r.json();
$('env').textContent='env: '+((data.gallery.url||'').replace('https://','').replace('/gallery/',''));
const ps=data.patterns||[];$('s-total').textContent=ps.length;
$('s-active').textContent=ps.filter(p=>p.status==='active').length;
$('s-disabled').textContent=ps.filter(p=>p.status!=='active').length;
galleryControls(data.gallery||{status:'unset',url:''});renderRows(ps);}
refresh();
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, status: int, body: str, ctype: str = "text/plain; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _host_ok(self) -> bool:
        return self.headers.get("Host", "") in ALLOWED_HOSTS

    def do_GET(self) -> None:
        if not self._host_ok():
            self._send(403, "forbidden")
            return
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif path == "/api/state":
            self._send(200, json.dumps(state(), ensure_ascii=False), "application/json; charset=utf-8")
        else:
            self._send(404, "not found")

    def do_POST(self) -> None:
        if not self._host_ok():
            self._send(403, "forbidden")
            return
        if self.headers.get("X-Console-Token", "") != CONSOLE_TOKEN:
            self._send(403, "invalid console token")
            return
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)
        slug = q.get("slug", [""])[0]

        # 共有ギャラリー操作（slug不要）
        if parsed.path == "/api/gallery":
            op = q.get("op", [""])[0]
            if op not in {"init", "rotate", "disable"}:
                self._send(400, "invalid gallery op")
                return
            ok, output = run_script("gallery.sh", op)
            self._send(200 if ok else 500, output)
            return

        # 以降はパターン単位の操作。slug必須。
        if not SLUG_RE.match(slug):
            self._send(400, "invalid slug")
            return
        if parsed.path == "/api/rename":
            name = q.get("name", [""])[0].strip()
            if not name or len(name) > 80 or any(ord(c) < 0x20 for c in name):
                self._send(400, "invalid name")
                return
            ok, output = run_script("rename_pattern.sh", slug, name)
            self._send(200 if ok else 500, output)
            return
        actions = {
            "/api/export": ("export_pattern.sh", [slug]),
            "/api/rotate": ("rotate_token.sh", [slug]),
            "/api/invalidate": ("invalidate_pattern.sh", [slug]),
        }
        if parsed.path not in actions:
            self._send(404, "not found")
            return
        script, args = actions[parsed.path]
        ok, output = run_script(script, *args)
        self._send(200 if ok else 500, output)

    def log_message(self, fmt: str, *args) -> None:  # 静かに
        pass


if __name__ == "__main__":
    print(f"design-share console: http://{HOST}:{PORT}/?token={CONSOLE_TOKEN}")
    print("（このURLごと開いてください。tokenが無いと操作は403になります。Ctrl+Cで終了）")
    http.server.ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
