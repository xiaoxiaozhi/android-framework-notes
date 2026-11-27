#!/usr/bin/env python3
"""Build stage-one HTML drafts from body modules and a shared base template.

Usage:
  py -3.12 build_series_drafts.py --build-dir <series>/_build \
      --out-dir <series>/_draft [--date 2026-10-21] [--prefix draft]

Expected in build-dir: base.html, css.txt, theme.txt, and one or more
bodies_*.py modules. Each module exports ARTICLES = [{order, slug, title,
subtitle, series, toc, body}]. Each body may use common.py helpers `code`,
`details`, `table`, `tree`; `code` must html-escape source text.

Output filenames carry no series number: <prefix>-<date>-<slug>.html.
"""
import argparse
import datetime
import importlib
import pathlib
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--prefix", default="draft")
    args = ap.parse_args()

    build = pathlib.Path(args.build_dir).resolve()
    out = pathlib.Path(args.out_dir).resolve()
    sys.path.insert(0, str(build))

    articles = []
    for path in sorted(build.glob("bodies_*.py")):
        mod = importlib.import_module(path.stem)
        articles.extend(mod.ARTICLES)
    if not articles:
        raise SystemExit("no ARTICLES found in bodies_*.py")
    articles.sort(key=lambda a: a["order"])

    base = (build / "base.html").read_text(encoding="utf-8")
    css = (build / "css.txt").read_text(encoding="utf-8")
    theme = (build / "theme.txt").read_text(encoding="utf-8")
    out.mkdir(parents=True, exist_ok=True)

    for art in articles:
        toc = "".join('<a href="#%s">%s</a>' % (i, label) for i, label in art["toc"])
        content = (
            '<div class="container">\n'
            + "<h1>" + art["title"] + "</h1>\n"
            + '<p class="subtitle">' + art["subtitle"] + "</p>\n"
            + '<p class="series">' + art["series"] + "</p>\n"
            + '<button id="theme-btn" title="切换主题">🌓</button>\n'
            + '<div class="toc"><strong style="color:var(--accent)">📖 目录</strong>'
            + toc
            + "</div>\n"
            + art["body"]
            + '\n<footer style="margin-top:40px;padding-top:18px;border-top:1px solid var(--border);color:var(--text2);font-size:.85rem;">'
            + "临时稿 · 未分配系列编号 · 基于 AOSP 12（SP1A）源码 · 待审阅修改后正式落盘"
            + "</footer>\n</div>"
        )
        doc = (
            base.replace("{{TITLE}}", art["title"] + " — Android 12 源码深度分析")
            .replace("{{CSS}}", css)
            .replace("{{CONTENT}}", content)
            .replace("{{THEME}}", theme)
        )
        fn = out / ("%s-%s-%s.html" % (args.prefix, args.date, art["slug"]))
        fn.write_text(doc, encoding="utf-8")
        print("wrote", fn.name, len(doc))
    print("total", len(articles))


if __name__ == "__main__":
    main()
