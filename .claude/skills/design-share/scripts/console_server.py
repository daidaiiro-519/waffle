#!/usr/bin/env python3
"""console_server.py — 作成者向け横断管理コンソール（localhostのみ・本番非公開）。

合意事項（ブレスト論点6・7）:
  - 本番AWS環境にはデプロイしない。Claude Code上でこのスクリプトを起動し、
    起動時に表示されるURL（乱数トークン付き）をブラウザで開く
  - 認証は開発者が既に持つAWS認証情報（aws cli）をそのまま使う
  - 全セッション・全パターンを横断して一覧し、無効化/エクスポート/ローテーションを行う

セキュリティ（advisor批評の反映）:
  - Hostヘッダー検証（DNSリバインディング対策）
  - 変更系APIは起動時乱数トークンを X-Console-Token ヘッダーで要求
    （カスタムヘッダー必須 = ブラウザのプリフライトが強制され、外部サイトからのCSRFを遮断）

使い方: python3 console_server.py  （design-share.env のあるディレクトリで実行）
"""
import http.server
import json
import os
import secrets
import subprocess
import sys
import urllib.parse

HOST, PORT = "127.0.0.1", 8787
ALLOWED_HOSTS = {f"{HOST}:{PORT}", f"localhost:{PORT}"}
CONSOLE_TOKEN = secrets.token_urlsafe(16)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


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
                conf[k.strip()] = v.strip()
    return conf


CONF = load_env()


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
        except subprocess.CalledProcessError:
            continue
    return sorted(patterns, key=lambda p: p.get("updatedAt", ""), reverse=True)


PAGE = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<title>design-share console</title>
<style>
body{font-family:system-ui,sans-serif;max-width:880px;margin:2rem auto;padding:0 1rem;color:#1a2126}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{text-align:left;padding:.55rem .7rem;border-bottom:1px solid #d7dcdb}
th{color:#5c6b70;font-size:.75rem;text-transform:uppercase}
.pill{font-size:.72rem;padding:.1rem .5rem;border-radius:999px}
.active{background:#e4eeee;color:#2f6f76}.disabled{background:#f6e6e4;color:#a5423a}
button{font:inherit;font-size:.8rem;padding:.25rem .7rem;margin-right:.3rem;cursor:pointer;
border:1px solid #d7dcdb;border-radius:5px;background:#fff}
button.danger{color:#a5423a}
pre{background:#f2f4f6;padding:.8rem;border-radius:6px;white-space:pre-wrap;font-size:.8rem}
</style></head><body>
<h1 style="font-size:1.2rem">design-share 横断管理コンソール</h1>
<p style="color:#5c6b70;font-size:.85rem">localhostのみ・本番非公開。操作はAWS認証情報で直接実行されます。</p>
<div id="app">読み込み中…</div>
<script>
const CONSOLE_TOKEN = new URLSearchParams(location.search).get('token') || '';
async function refresh(){
  const res = await fetch('/api/patterns'); const items = await res.json();
  const rows = items.map(p => `<tr>
    <td>${esc(p.name)}</td><td><code>${esc(p.slug)}</code></td>
    <td><span class="pill ${p.status === 'active' ? 'active' : 'disabled'}">${p.status === 'active' ? '公開中' : '無効化済み'}</span></td>
    <td>${esc((p.updatedAt||'').slice(0,10))}</td>
    <td>
      <button onclick="act('export','${esc(p.slug)}')">Export</button>
      <button onclick="act('rotate','${esc(p.slug)}')">Rotate token</button>
      <button class="danger" onclick="if(confirm('無効化しますか？（エクスポートを先に実行します）'))act('invalidate','${esc(p.slug)}')">Disable</button>
    </td></tr>`).join('');
  document.getElementById('app').innerHTML = items.length
    ? `<table><tr><th>パターン名</th><th>slug</th><th>状態</th><th>更新日</th><th>操作</th></tr>${rows}</table><pre id="log"></pre>`
    : '<p>まだデプロイされたパターンはありません。</p>';
}
function esc(s){const d=document.createElement('div');d.textContent=s??'';return d.innerHTML}
async function act(op, slug){
  const log = document.getElementById('log'); log.textContent = `${op} 実行中…`;
  const res = await fetch(`/api/${op}?slug=${encodeURIComponent(slug)}`,
    {method:'POST', headers:{'X-Console-Token': CONSOLE_TOKEN}});
  log.textContent = await res.text();
  refresh();
}
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
        elif path == "/api/patterns":
            self._send(200, json.dumps(list_patterns(), ensure_ascii=False),
                       "application/json; charset=utf-8")
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
        slug = urllib.parse.parse_qs(parsed.query).get("slug", [""])[0]
        if not slug or not slug.replace("-", "").replace("_", "").isalnum():
            self._send(400, "invalid slug")
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
    print("（このURLごと開いてください。tokenが無いと操作ボタンは403になります。Ctrl+Cで終了）")
    http.server.ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
