# -*- coding: utf-8 -*-
"""Android Framework 学习站本地服务：启动时同步上位路线图，然后提供静态服务。
用法: python serve_framework.py [port]
"""
import http.server
import os
import shutil
import socketserver
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(ROOT)  # D:\openclaw
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8090

# 启动时把上位路线图同步进来（对外只暴露本目录，故需副本）
for name in ("Android-Framework学习路线图.html", "Android-Framework学习路线图.md"):
    src = os.path.join(UP, name)
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(ROOT, name))
        print("synced:", name)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        # 学习资料经常改，禁用缓存，避免浏览器看到旧版
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def guess_type(self, path):
        # .md 当纯文本看（避免被下载）
        if str(path).endswith(".md"):
            return "text/plain; charset=utf-8"
        return super().guess_type(path)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("0.0.0.0", PORT), Handler) as httpd:
        print("serving %s at http://0.0.0.0:%d" % (ROOT, PORT))
        httpd.serve_forever()
