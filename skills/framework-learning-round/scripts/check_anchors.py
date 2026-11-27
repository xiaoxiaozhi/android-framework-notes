#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对 round/文章里每个 `文件:行号` 在基线源码树里真的成立。

- error: 文件找不到、行号超出文件长度、区间倒置
- warning: 骨架行上，锚点 ±3 行内找不到该行提到的任何符号（疑似行号漂移）
- --strict: warning 也算失败

支持 `File.java:1683/:1789-1790` 这种同一文件的续写行号。

用法:
  python check_anchors.py round.md --root /home/book/aosp13
  python check_anchors.py round.md --root D:\\aosp13 --strict

退出码: 0 无 error / 1 有 error（或 strict 下有 warning）/ 2 用法错误
"""
import argparse
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ANCHOR = re.compile(r"([A-Za-z0-9_$]+\.(?:java|kt|aidl|cpp|h|cc)):(\d+)(?:-(\d+))?")
CONT = re.compile(r"\s*/\s*:(\d+)(?:-(\d+))?")
TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
ARROWS = ("→", "←", "<-", "├", "└")

KEYWORDS = {
    "java", "public", "private", "protected", "static", "final", "void", "class",
    "return", "true", "false", "null", "this", "super", "new", "import", "package",
    "extends", "implements", "override", "interface", "abstract", "synchronized",
}


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return p.returncode, p.stdout, p.stderr


def sh_quote(s):
    return "'" + s.replace("'", "'\\''") + "'"


def is_wsl_path(root):
    return root.startswith("/")


def resolve_wsl(root, names):
    names = sorted(names)
    cond = " -o ".join("-name %s" % sh_quote(n) for n in names)
    cmd = ("cd %s && find frameworks packages system -type f \\( %s \\) "
           "-not -path '*/out/*' -not -path '*/.repo/*' 2>/dev/null | head -80"
           % (sh_quote(root), cond))
    rc, out, _ = run(["wsl", "bash", "-lc", cmd])
    mapping = {}
    for line in out.splitlines():
        line = line.strip()
        if line:
            mapping.setdefault(os.path.basename(line), line)
    return mapping


def resolve_local(root, names):
    mapping = {}
    wanted = set(names)
    for sub in ("frameworks", "packages", "system"):
        base_dir = os.path.join(root, sub)
        if not os.path.isdir(base_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(base_dir):
            dirnames[:] = [d for d in dirnames if d not in ("out", ".repo", "obj")]
            for fn in filenames:
                if fn in wanted and fn not in mapping:
                    mapping[fn] = os.path.join(dirpath, fn)
            if len(mapping) == len(wanted):
                return mapping
    return mapping


def candidates(text):
    out = []
    for m in TOKEN.finditer(ANCHOR.sub(" ", text)):
        tok = m.group(0)
        if tok in KEYWORDS or tok.lower() in ("http", "https", "www"):
            continue
        if tok.endswith((".java", ".md", ".html", ".py")):
            continue
        # 类名本身不是判据；取点号最后一段作为方法/字段名
        if "." in tok:
            for part in tok.split("."):
                if part and part not in KEYWORDS and len(part) > 3 and part not in out:
                    out.append(part)
            continue
        if tok[0].isupper():      # ActivityThread 这类类名跳过
            continue
        if "_" in tok or re.search(r"[a-z][A-Z]", tok) or len(tok) > 5:
            out.append(tok)
    return out[:8]


def main():
    ap = argparse.ArgumentParser(description="verify file:line anchors against AOSP tree")
    ap.add_argument("file")
    ap.add_argument("--root", default="/home/book/aosp13")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--window", type=int, default=3, help="符号核对的行窗口（默认 ±3）")
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        print("用法错误: 读不到文件 %s" % args.file)
        return 2
    local = not is_wsl_path(args.root)
    if local:
        if not os.path.isdir(args.root):
            print("用法错误: 找不到源码根 %s" % args.root)
            return 2

    text = io.open(args.file, encoding="utf-8").read()
    lines = text.splitlines()

    found = []   # (md_lineno, text, name, start, end)
    for i, line in enumerate(lines, 1):
        for m in ANCHOR.finditer(line):
            found.append((i, line, m.group(1), int(m.group(2)),
                          int(m.group(3)) if m.group(3) else int(m.group(2))))
            tail = line[m.end():]
            for c in CONT.finditer(tail):
                found.append((i, line, m.group(1), int(c.group(1)),
                              int(c.group(2)) if c.group(2) else int(c.group(1))))

    if not found:
        print("FAIL: 没有找到任何 文件:行号 锚点")
        return 1

    names = {f[2] for f in found}
    mapping = resolve_local(args.root, names) if local else resolve_wsl(args.root, names)

    cache = {}   # name -> list[str]

    def load(name):
        if name in cache:
            return cache[name]
        rel = mapping.get(name)
        if not rel:
            cache[name] = None
            return None
        if local:
            try:
                with io.open(rel, encoding="utf-8", errors="replace") as f:
                    cache[name] = f.read().splitlines()
            except OSError:
                cache[name] = None
        else:
            rc, out, _ = run(["wsl", "bash", "-lc",
                              "cat %s" % sh_quote(args.root.rstrip("/") + "/" + rel)])
            cache[name] = out.splitlines() if rc == 0 else None
        return cache[name]

    errors, warnings = [], []
    per_line = {}      # md_line -> (line_text, [window_text])
    for md_line, line, name, start, end in found:
        body = load(name)
        if body is None:
            errors.append("L%d 找不到/读不到 %s" % (md_line, name))
            continue
        if start < 1 or end > len(body) or start > end:
            errors.append("L%d %s:%d-%d 越界（文件 %d 行）"
                          % (md_line, name, start, end, len(body)))
            continue
        lo = max(0, start - 1 - args.window)
        hi = min(len(body), end + args.window)
        entry = per_line.setdefault(md_line, (line, []))
        entry[1].append("\n".join(body[lo:hi]))

    # 只在骨架行做符号核对；同一行多个锚点取并集，避免误报
    for md_line in sorted(per_line):
        line, windows = per_line[md_line]
        if not any(a in line for a in ARROWS):
            continue
        cands = candidates(line)
        if not cands:
            continue
        joined = "\n".join(windows)
        if not any(c in joined for c in cands):
            warnings.append("L%d 锚点附近未见 %s" % (md_line, "/".join(cands[:3])))

    print("锚点 %d 个，文件 %d 个，基线 %s"
          % (len(found), len(mapping), args.root))
    for w in warnings:
        print("WARN", w)
    for e in errors:
        print("ERROR", e)

    if errors or (args.strict and warnings):
        print("FAIL: %d error / %d warning" % (len(errors), len(warnings)))
        return 1
    print("PASS: 无 error（%d warning）" % len(warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
