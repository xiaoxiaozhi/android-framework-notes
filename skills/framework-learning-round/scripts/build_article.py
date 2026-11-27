#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把分块 HTML + 共享 CSS 拼成单文件文章。

用法:
  python build_article.py --parts p1.html p2.html p3.html --css article.css --out out.html

退出码: 0 成功 / 1 校验失败 / 2 用法错误
"""
import argparse
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PLACEHOLDER = "/*__CSS__*/"
RESIDUE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser(description="assemble article from parts")
    ap.add_argument("--parts", nargs="+", required=True)
    ap.add_argument("--css", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-residue", action="store_true",
                    help="允许模板占位符残留（默认不允许）")
    args = ap.parse_args()

    missing = [p for p in args.parts + [args.css] if not os.path.isfile(p)]
    if missing:
        print("用法错误: 找不到文件: " + ", ".join(missing))
        return 2

    css = read(args.css).strip() + "\n"
    if PLACEHOLDER not in read(args.parts[0]):
        print("用法错误: 第一块里没有 %s 占位符" % PLACEHOLDER)
        return 2

    chunks = []
    for i, path in enumerate(args.parts):
        text = read(path)
        if i == 0:
            text = text.replace(PLACEHOLDER, css)
        chunks.append(text.rstrip())

    html = "\n".join(chunks) + "\n"

    fails = []
    if PLACEHOLDER in html:
        fails.append("CSS 占位符仍未替换")
    if not args.allow_residue:
        left = sorted(set(RESIDUE.findall(html)))
        if left:
            fails.append("模板占位符残留: " + ", ".join(left[:8]))
    for tag in ("section", "html", "body"):
        opens = len(re.findall(r"<%s[\s>]" % tag, html))
        closes = len(re.findall(r"</%s>" % tag, html))
        if opens != closes:
            fails.append("<%s> 不配对: %d 开 / %d 闭" % (tag, opens, closes))
    if "<style>" not in html or "</style>" not in html:
        fails.append("缺少 <style> 块")

    if fails:
        print("FAIL:")
        for f in fails:
            print("  -", f)
        return 1

    with io.open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    size = os.path.getsize(args.out)
    print("PASS: %s (%d bytes, %d parts + css %d bytes)"
          % (args.out, size, len(args.parts), len(css)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
