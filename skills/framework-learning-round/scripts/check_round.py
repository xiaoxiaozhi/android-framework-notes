#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查「一页三块 + 两段配套」是否符合 framework-learning-loop 的形状契约。

用法:  python check_round.py <round.md>
退出码: 0 全过 / 1 有失败项 / 2 用法错误
"""
import io
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ANCHOR = re.compile(r"[\w./-]+\.(?:java|kt|aidl|h|cpp|cc):\d+")
ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
BLOCK = re.compile(r"^#{1,4}.*([①②③④])")
HEADING = re.compile(r"^#{2,4}\s+\S")
ARROW = ("→", "<-", "←")
BRANCH = ("├", "└")
STEP = re.compile(r"^\s*(?:[-*+]\s*)?[①②③④⑤⑥⑦⑧]\s*\S")


def die_usage(msg):
    print("用法错误:", msg)
    print("用法: python check_round.py <round.md>")
    sys.exit(2)


def parse(text):
    blocks = {}
    current = None
    buf = []
    for line in text.splitlines():
        m = BLOCK.match(line)
        if m:
            if current is not None:
                blocks.setdefault(current, []).extend(buf)
            current = m.group(1)
            buf = []
            continue
        if HEADING.match(line) and current is not None:
            # 非 ①②③④ 的小标题（例如「骨架解说」）不属于任何编号块
            blocks.setdefault(current, []).extend(buf)
            current = None
            buf = []
            continue
        if current is not None and line.strip() in ("---", "***"):
            blocks.setdefault(current, []).extend(buf)
            current = None
            buf = []
            continue
        if current is not None:
            buf.append(line)
    if current is not None:
        blocks.setdefault(current, []).extend(buf)
    return blocks


def section(text, title):
    """返回某个二级标题下的正文（到下一个二级标题为止）。"""
    m = re.search(r"^##\s*%s.*$" % re.escape(title), text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^##\s+\S", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def items(lines):
    return [l for l in lines if ITEM.match(l)]


def main():
    if len(sys.argv) != 2:
        die_usage("需要且只需要一个文件参数")
    path = sys.argv[1]
    try:
        text = io.open(path, encoding="utf-8").read()
    except OSError as e:
        die_usage("读不到文件: %s" % e)

    fails = []

    if re.search(r"^#{1,4}.*④", text, re.M):
        fails.append("出现第 ④ 块：只允许 ①②③ 三块")

    blocks = parse(text)
    for tag, name in (("①", "骨架"), ("②", "决策点"), ("③", "3 个问题")):
        if tag not in blocks:
            fails.append("缺少第 %s 块（%s）" % (tag, name))

    # 骨架：凡带 文件:行号 的行即为骨架行
    sk = [l for l in blocks.get("①", []) if ANCHOR.search(l)]
    if not (3 <= len(sk) <= 18):
        fails.append("骨架 %d 行，要求 3–18 行" % len(sk))
    for i, l in enumerate(sk, 1):
        if not any(a in l for a in ARROW):
            fails.append("骨架第 %d 行没有 → 或 ←（只写了方法名不算骨架）—— %s"
                         % (i, l.strip()[:60]))
    if sk and not any(any(b in l for b in BRANCH) for l in sk):
        fails.append("骨架没有任何 ├─ / └─ 分支行：只写主链等于清单，不是骨架")

    # 骨架解说：3–8 行，一行一个标号
    ex = section(text, "骨架解说")
    if ex is None:
        fails.append("缺少「## 骨架解说（这段在讲什么）」：一行一个标号，3–8 行")
    else:
        steps = [l for l in ex.splitlines() if STEP.match(l)]
        if not (3 <= len(steps) <= 8):
            fails.append("骨架解说 %d 行标号，要求 3–8 行（一行一个标号）" % len(steps))
        if len(steps) == 1:
            fails.append("骨架解说把标号挤成一段了：必须一行一个标号")

    # 骨架阅读法：五行
    rd = section(text, "骨架阅读法")
    if rd is None:
        fails.append("缺少「## 骨架阅读法」：一句话定位 / 三个接力边界 / 最小验证命令 / 最贵的一行 / 可追问的名字")
    else:
        body = [l.strip(" -*\t") for l in rd.splitlines()
                if l.strip() and not l.strip().startswith(">")
                and l.strip() not in ("---", "***")]
        if len(body) < 5:
            fails.append("骨架阅读法只有 %d 行，要求 5 行" % len(body))
        joined = "\n".join(body)
        for kw in ("一句话定位", "接力", "命令", "最贵"):
            if kw not in joined:
                fails.append("骨架阅读法缺「%s」" % kw)
        if "追问" not in joined:
            fails.append("骨架阅读法缺「可追问的名字」")

    dp = items(blocks.get("②", []))
    if not (3 <= len(dp) <= 5):
        fails.append("决策点 %d 条，要求 3–5 条" % len(dp))
    for i, l in enumerate(dp, 1):
        if not ANCHOR.search(l):
            fails.append("决策点第 %d 条没有 文件:行号 —— %s" % (i, l.strip()[:60]))

    qs = items(blocks.get("③", []))
    if len(qs) != 3:
        fails.append("问题 %d 条，要求正好 3 条" % len(qs))

    if "基线" not in text:
        fails.append("缺少基线附注（骨架末尾需一行说明 AOSP 12/13 与未核实项）")

    if fails:
        print("FAIL %d 项：" % len(fails))
        for f in fails:
            print("  -", f)
        sys.exit(1)

    print("PASS：三块齐全 + 解说 %d 行 + 阅读法 %d 行；骨架 %d 行（含分支）、决策点 %d 条、问题 %d 条"
          % (len(steps), len(body), len(sk), len(dp), len(qs)))
    sys.exit(0)


if __name__ == "__main__":
    main()
