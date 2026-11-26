#!/usr/bin/env python3
"""AOSP 模拟器屏幕镜像（Windows 侧）。

- GET /            -> 自动刷新的页面
- GET /shot.png    -> 最新一帧（缓存 ~0.6s，避免并发过多 screencap）
- GET /tap?x=&y=   -> adb input tap
- GET /key?k=back|home|recent -> adb input keyevent
- GET /type?t=...  -> adb input text
- GET /devices     -> adb devices

依赖 WSL 里的 adb（模拟器在 WSL 内）。
"""
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

PORT = int(os.environ.get("EMU_VIEW_PORT", "8124"))
WSL = ["wsl", "-d", "Ubuntu", "--", "bash", "-lc"]

_cache = {"t": 0.0, "data": b""}
_lock = threading.Lock()


def run_adb(args, binary=False, timeout=25):
    cmd = WSL + ["adb " + args]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return out.stdout if binary else out.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return b"" if binary else "(timeout)\n"


def grab_screen(max_age=0.6):
    with _lock:
        now = time.time()
        if now - _cache["t"] < max_age and _cache["data"]:
            return _cache["data"]
        data = run_adb("exec-out screencap -p", binary=True)
        if data.startswith(b"\x89PNG"):
            _cache["data"] = data
            _cache["t"] = now
        return _cache["data"]


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>AOSP 13 模拟器</title>
<style>
 :root { color-scheme: dark; }
 body { margin:0; background:#14161a; color:#e6e9ef;
        font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
        display:flex; flex-direction:column; align-items:center; }
 header { display:flex; gap:8px; align-items:center; padding:10px 14px; width:100%;
           box-sizing:border-box; background:#1b1e24; border-bottom:1px solid #2a2f38; }
 button { background:#2a2f38; color:#e6e9ef; border:1px solid #3a4150; border-radius:8px;
           padding:6px 12px; cursor:pointer; font-size:13px; }
 button:hover { background:#343b47; }
 button.on { background:#2563eb; border-color:#2563eb; }
 #wrap { padding:12px; }
 img { display:block; max-height:calc(100vh - 90px); width:auto; border-radius:10px;
        box-shadow:0 8px 30px rgba(0,0,0,.5); cursor:crosshair; background:#000; }
 #stat { margin-left:auto; font-size:12px; color:#8b93a1; }
 .spacer { flex:1; }
</style></head>
<body>
<header>
  <button id="btnLive" class="on">自动刷新</button>
  <button onclick="shot(true)">刷新一次</button>
  <button data-k="back">返回</button>
  <button data-k="home">Home</button>
  <button data-k="recent">最近</button>
  <span id="stat">–</span>
</header>
<div id="wrap"><img id="scr" src="/shot.png" alt="emulator screen"></div>
<script>
let live = true, timer = null;
const img = document.getElementById('scr');
const stat = document.getElementById('stat');
img.addEventListener('load', () => {
  stat.textContent = new Date().toLocaleTimeString() + ' · ' + img.naturalWidth + '×' + img.naturalHeight;
});
img.addEventListener('error', () => { stat.textContent = '取帧失败（模拟器未就绪？）'; });
function shot(force) {
  const t = Date.now();
  img.src = '/shot.png?t=' + t;
}
function tick() { if (live) shot(); }
document.getElementById('btnLive').onclick = (e) => {
  live = !live;
  e.target.classList.toggle('on', live);
  e.target.textContent = live ? '自动刷新' : '已暂停';
};
setInterval(tick, 1200);
document.querySelectorAll('button[data-k]').forEach(b => {
  b.onclick = () => fetch('/key?k=' + b.dataset.k).then(() => shot(true));
});
img.addEventListener('click', (ev) => {
  const r = img.getBoundingClientRect();
  const x = Math.round((ev.clientX - r.left) * img.naturalWidth / r.width);
  const y = Math.round((ev.clientY - r.top) * img.naturalHeight / r.height);
  fetch('/tap?x=' + x + '&y=' + y).then(() => setTimeout(() => shot(true), 250));
});
</script>
</body></html>
"""

KEYMAP = {"back": "4", "home": "3", "recent": "187", "power": "26", "enter": "66"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if u.path == "/shot.png":
            data = grab_screen()
            if not data:
                return self._send(503, b"no frame")
            return self._send(200, data, "image/png")
        if u.path == "/tap":
            x = q.get("x", ["0"])[0]
            y = q.get("y", ["0"])[0]
            run_adb(f"shell input tap {x} {y}")
            return self._send(200, "ok")
        if u.path == "/key":
            k = q.get("k", [""])[0]
            code = KEYMAP.get(k, k)
            run_adb(f"shell input keyevent {code}")
            return self._send(200, "ok")
        if u.path == "/type":
            t = q.get("t", [""])[0]
            run_adb("shell input text " + quote(t, safe=""))
            return self._send(200, "ok")
        if u.path == "/devices":
            return self._send(200, run_adb("devices"))
        return self._send(404, "not found")


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"emu view on http://127.0.0.1:{PORT}/")
    srv.serve_forever()
