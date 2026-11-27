#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""无头验证单文件学习文章：脚本执行、主题切换、章节数、占位符、截图。

用法:
  python verify_html.py 文章.html --sections 7 --shot verify.png

退出码: 0 全过 / 1 有失败 / 2 用法错误（文件或 Edge 缺失）
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
RESIDUE = re.compile(r"\{\{[A-Z0-9_]+\}\}|/\*__CSS__\*/")


def find_edge():
    for p in EDGE_CANDIDATES:
        if os.path.isfile(p):
            return p
    return shutil.which("msedge")


def run_edge(edge, profile, extra, uri, timeout=90):
    cmd = [edge, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + profile, "--virtual-time-budget=3000"] + extra + [uri]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return p.stdout or ""


def main():
    ap = argparse.ArgumentParser(description="headless verify a learning article")
    ap.add_argument("file")
    ap.add_argument("--sections", type=int, default=0, help="期望的 <section id=sN> 数量")
    ap.add_argument("--shot", default="", help="截图输出路径（可选）")
    ap.add_argument("--timeout", type=int, default=90)
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        print("用法错误: 读不到文件 %s" % args.file)
        return 2
    edge = find_edge()
    if not edge:
        print("用法错误: 找不到 msedge.exe")
        return 2

    work = tempfile.mkdtemp(prefix="aw-verify-")
    try:
        page = os.path.join(work, "page.html")
        shutil.copyfile(args.file, page)
        uri = "file:///" + page.replace("\\", "/")
        dom = run_edge(edge, os.path.join(work, "prof1"), ["--dump-dom"], uri, args.timeout)

        fails = []
        if 'data-ready="1"' not in dom:
            fails.append("脚本未执行（data-ready 缺失）——检查 JS 语法/异常")
        if not re.search(r"<title>[^<]+</title>", dom):
            fails.append("缺少非空 <title>")
        residue = sorted(set(RESIDUE.findall(dom)))
        if residue:
            fails.append("占位符残留: " + ", ".join(residue[:6]))
        if args.sections:
            n = len(re.findall(r'<section id="s\d+"', dom))
            if n != args.sections:
                fails.append("<section> 数量 %d，期望 %d" % (n, args.sections))

        with io.open(page, encoding="utf-8") as f:
            html = f.read()
        harness = html.replace("</body>", (
            "<script>var _b=document.getElementById('themeBtn')||document.getElementById('themeFab');"
            "if(!_b){document.documentElement.setAttribute('data-test','NO_BUTTON');}"
            "else{"
            "var _a=document.documentElement.getAttribute('data-theme');"
            "_b.click();"
            "var _c=document.documentElement.getAttribute('data-theme');"
            "_b.click();"
            "var _d=document.documentElement.getAttribute('data-theme');"
            "document.documentElement.setAttribute('data-test',_a+'>'+_c+'>'+_d);}"
            "</script></body>"))
        hpage = os.path.join(work, "harness.html")
        with io.open(hpage, "w", encoding="utf-8", newline="\n") as f:
            f.write(harness)
        huri = "file:///" + hpage.replace("\\", "/")
        hdom = run_edge(edge, os.path.join(work, "prof2"), ["--dump-dom"], huri, args.timeout)
        m = re.search(r'data-test="([^"]+)"', hdom)
        if not m:
            fails.append("主题按钮测试未产出 data-test")
        else:
            seq = [x for x in m.group(1).replace("&gt;", ">").split(">") if x]
            if len(seq) < 3 or len(set(seq)) < 2:
                fails.append("主题按钮连点两次主题未变化: %s" % m.group(1))

        if args.shot:
            shot = os.path.abspath(args.shot)
            shot_dir = os.path.dirname(shot)
            if shot_dir and not os.path.isdir(shot_dir):
                os.makedirs(shot_dir, exist_ok=True)
            run_edge(edge, os.path.join(work, "prof3"),
                     ["--hide-scrollbars", "--window-size=1400,2200",
                      "--screenshot=" + shot], uri, args.timeout)
            if not os.path.isfile(shot):
                fails.append("截图失败: %s" % shot)
            else:
                print("SHOT:", shot, os.path.getsize(shot), "bytes")

        if fails:
            print("FAIL:")
            for f in fails:
                print("  -", f)
            return 1

        print("PASS: ready / theme cycle / sections=%d / no residue"
              % (args.sections or len(re.findall(r'<section id="s\d+"', dom))))
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
