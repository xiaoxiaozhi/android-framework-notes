#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_html.py — 成稿 HTML 结构校验：标签配对、TOC/页内锚点、站内 .html 链接、模板占位符残留。

用法:
  python check_html.py --html "<成品.html>" [--json]
退出码: 0 = 0 错误; 1 = 有错误; 2 = 用法错误。
"""
import argparse, json, os, re, sys
from html.parser import HTMLParser

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
PLACEHOLDER_RE = re.compile(r'\{\{[^}]+\}\}')


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = set()
        self.anchor_hrefs = []   # #xxx
        self.local_links = []    # xxx.html / a/b.html
        self.has_title = False
        self._in_title = False
        self._title = ''

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'id' in d:
            if d['id'] in self.ids:
                self.errors.append('重复 id: #%s (行 %d)' % (d['id'], self.getpos()[0]))
            self.ids.add(d['id'])
        if tag == 'title':
            self._in_title = True
        if tag == 'a' and 'href' in d:
            href = d['href'].strip()
            if href.startswith('#'):
                self.anchor_hrefs.append((href[1:], self.getpos()[0]))
            elif not re.match(r'^[a-zA-Z][\w+.-]*:', href) and not href.startswith('//'):
                # 去掉 query/hash
                local = href.split('#', 1)[0].split('?', 1)[0]
                if local:
                    self.local_links.append((href, local, self.getpos()[0]))
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append('多余闭合标签 </%s> (行 %d)' % (tag, self.getpos()[0]))
            return
        # 向上找匹配
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for unclosed in reversed(self.stack[i + 1:]):
                    self.errors.append('标签未闭合 <%s> (开于行 %d)' % unclosed)
                del self.stack[i:]
                return
        self.errors.append('无匹配闭合 </%s> (行 %d)' % (tag, self.getpos()[0]))

    def handle_data(self, data):
        if self._in_title:
            self._title += data

    def handle_startendtag(self, tag, attrs):
        d = dict(attrs)
        if 'id' in d:
            self.ids.add(d['id'])

    def handle_endtag_marker(self):
        self._in_title = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', required=True)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    if not os.path.isfile(args.html):
        print('ERROR: %s 不存在' % args.html, file=sys.stderr); return 2

    raw = open(args.html, encoding='utf-8').read()
    # title 结束标记单独处理
    class C(Checker):
        def handle_endtag(self, tag):
            if tag == 'title':
                self._in_title = False
                self.has_title = bool(self._title.strip())
            super().handle_endtag(tag)

    p = C()
    try:
        p.feed(raw)
        p.close()
    except Exception as e:
        p.errors.append('HTMLParser 异常: %r' % e)

    errors = list(p.errors)
    for tag, line in p.stack:
        errors.append('文件结束仍未闭合 <%s> (开于行 %d)' % (tag, line))

    if not p.has_title:
        errors.append('缺少非空 <title>')

    # TOC/页内锚点
    for frag, line in p.anchor_hrefs:
        if frag and frag not in p.ids:
            errors.append('页内链接 #%s 无对应 id (行 %d)' % (frag, line))

    # 站内文件链接
    base = os.path.dirname(os.path.abspath(args.html))
    for href, local, line in p.local_links:
        if local.lower().endswith(('.html', '.htm')):
            target = os.path.normpath(os.path.join(base, local.replace('/', os.sep)))
            if not os.path.isfile(target):
                errors.append('站内链接目标不存在: %s (行 %d)' % (href, line))

    # 模板占位符
    for i, line_txt in enumerate(raw.splitlines(), 1):
        for ph in PLACEHOLDER_RE.findall(line_txt):
            errors.append('模板占位符残留 %s (行 %d)' % (ph, i))

    if args.json:
        print(json.dumps({'errors': errors, 'ids': sorted(p.ids)}, ensure_ascii=False, indent=2))
    else:
        if errors:
            for e in errors:
                print('FAIL ' + e)
        else:
            print('OK 标签配对 / TOC 锚点 / 站内链接 / 占位符 全部通过')
        print('错误 %d 处；id %d 个；页内锚点 %d 个；站内链接 %d 个' %
              (len(errors), len(p.ids), len(p.anchor_hrefs), len(p.local_links)))
    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
