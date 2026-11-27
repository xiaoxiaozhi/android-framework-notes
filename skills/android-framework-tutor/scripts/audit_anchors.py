#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_anchors.py — 校验 HTML 里的源码锚点（File.java:行号 / 行号区间）是否在真实 AOSP 源码树中成立。

用法:
  python audit_anchors.py --html "<成品.html>" --root "<AOSP源码根>" [--window 6] [--json]

规则:
  - 识别  Name.ext:line  与  Name.ext:line-line   ext ∈ java/kt/cpp/cc/c/h/hpp
  - 每个锚点: 文件必须能在 --root 下找到；行号必须落在文件行数内；行附近内容非空。
  - 同一文本里若出现 Class#method / Class.method 且该锚点是 [File:line] 形式，
    额外要求 method 名出现在该行 ±window 范围内（抓“行号对不上方法”的错锚）。
  - 占位符 ??? / 000 / xxxx 一律判失败。

只索引一次源码树（basename -> 路径），不跨挂载盘扫描；--root 请给具体 AOSP 根。
退出码: 0 = 全部通过; 1 = 有失败; 2 = 用法/环境错误。
"""
import argparse, json, os, re, sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

EXTS = ('java', 'kt', 'cpp', 'cc', 'c', 'h', 'hpp')
PRUNE = {'.git', '.repo', 'out', 'build', 'dist', 'node_modules', '__pycache__', '.idea'}
ANCHOR_RE = re.compile(
    r'(?P<file>[\w$./-]+\.(?:' + '|'.join(EXTS) + r'))\s*[:：]\s*(?P<a>\d+)\s*(?:[-–—]\s*(?P<b>\d+))?'
)
PLACEHOLDER_RE = re.compile(r'\?\?\?|:000\b|xxxx', re.I)
# Class#method(  或  Class.method(  （取方法名）
METHOD_RE = re.compile(r'[A-Z]\w*[#.](?P<m>[a-zA-Z_]\w*)\s*\(')


def index_tree(root):
    idx = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in PRUNE and not d.startswith('.')]
        for fn in filenames:
            if fn.lower().endswith(tuple('.' + e for e in EXTS)):
                idx.setdefault(fn, []).append(os.path.join(dirpath, fn))
    return idx


def strip_tags(text):
    text = re.sub(r'(?s)<(script|style).*?</\1>', ' ', text)
    text = re.sub(r'(?s)<!--.*?-->', ' ', text)
    text = re.sub(r'(?s)<[^>]+>', ' ', text)
    return text


def pick_file(idx, name):
    base = os.path.basename(name)
    cands = idx.get(base, [])
    if not cands:
        return None, []
    if len(cands) == 1:
        return cands[0], cands
    tail = name.replace('/', os.sep).replace('\\', os.sep)
    exact = [c for c in cands if c.endswith(tail)]
    return (exact[0] if exact else cands[0]), cands


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', required=True)
    ap.add_argument('--root', required=True)
    ap.add_argument('--window', type=int, default=6)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    if not os.path.isfile(args.html):
        print('ERROR: html 不存在: %s' % args.html, file=sys.stderr); return 2
    if not os.path.isdir(args.root):
        print('ERROR: 源码根不存在: %s' % args.root, file=sys.stderr); return 2

    raw = open(args.html, encoding='utf-8').read()
    text = strip_tags(raw)

    print('索引源码树（首次较慢）… %s' % args.root, file=sys.stderr)
    idx = index_tree(args.root)
    print('索引到 %d 个源码文件名' % len(idx), file=sys.stderr)

    # 预读缓存
    cache = {}
    def lines_of(path):
        if path not in cache:
            try:
                with open(path, encoding='utf-8', errors='replace') as f:
                    cache[path] = f.read().splitlines()
            except OSError:
                cache[path] = None
        return cache[path]

    results = []
    # 用去重集合，同一锚点多次出现只报一次
    seen = set()
    for m in ANCHOR_RE.finditer(text):
        key = (m.group('file'), m.group('a'), m.group('b') or '')
        if key in seen:
            continue
        seen.add(key)
        name, a, b = m.group('file'), int(m.group('a')), int(m.group('b') or m.group('a'))
        rec = {'anchor': m.group(0).strip(), 'file': name, 'from': a, 'to': b,
               'ok': True, 'problems': []}

        if PLACEHOLDER_RE.search(m.group(0)):
            rec['ok'] = False; rec['problems'].append('含占位符(???/000/xxxx)')
        if b < a:
            rec['ok'] = False; rec['problems'].append('行号区间倒置')

        path, cands = pick_file(idx, name)
        if not path:
            rec['ok'] = False; rec['problems'].append('源码树中找不到文件')
        else:
            if len(cands) > 1:
                rec['problems'].append('同名文件 %d 个，已按路径匹配: %s' %
                                       (len(cands), os.path.basename(os.path.dirname(path))))
            ls = lines_of(path)
            if ls is None:
                rec['ok'] = False; rec['problems'].append('文件无法读取')
            else:
                if not (1 <= a <= len(ls)) or b > len(ls):
                    rec['ok'] = False
                    rec['problems'].append('行号越界(文件共 %d 行)' % len(ls))
                else:
                    window_text = '\n'.join(ls[max(0, a-1-args.window): b+args.window])
                    if not window_text.strip():
                        rec['ok'] = False; rec['problems'].append('锚点附近为空行')
                    # 反向校验：锚点前 60 字符内若给了 Class#method，方法名应落在窗口里
                    pre = text[max(0, m.start()-80):m.start()]
                    mm = list(METHOD_RE.finditer(pre))
                    if mm:
                        method = mm[-1].group('m')
                        if method not in window_text:
                            rec['ok'] = False
                            rec['problems'].append(
                                "方法 %s() 未出现在 %s:%d±%d" % (method, os.path.basename(name), a, args.window))
        results.append(rec)

    total, passed = len(results), sum(1 for r in results if r['ok'])
    if args.json:
        print(json.dumps({'passed': passed, 'total': total, 'results': results},
                         ensure_ascii=False, indent=2))
    else:
        for r in results:
            mark = 'OK ' if r['ok'] else 'FAIL'
            print('[%s] %s' % (mark, r['anchor']))
            for p in r['problems']:
                print('       - ' + p)
        print('\n通过 %d/%d' % (passed, total))

    return 0 if passed == total and total > 0 else (1 if total > 0 else 1)


if __name__ == '__main__':
    sys.exit(main())
