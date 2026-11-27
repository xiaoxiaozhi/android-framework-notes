#!/usr/bin/env python3
"""Extract a series' inline CSS and theme script into a reusable draft template.

Usage:
  py -3.12 extract_series_style.py --source <existing-article.html> \
      --build-dir <series>/_build --storage-key adsp_theme

Writes base.html, css.txt, theme.txt into build-dir. base.html uses
{{TITLE}}, {{CSS}}, {{CONTENT}}, {{THEME}} placeholders.
"""
import argparse
import pathlib
import re


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--build-dir", required=True)
    ap.add_argument("--storage-key", default="series_theme")
    args = ap.parse_args()

    src = pathlib.Path(args.source).read_text(encoding="utf-8")
    css_match = re.search(r"<style>(.*?)</style>", src, re.S)
    if not css_match:
        raise SystemExit("no <style> block found")
    css = css_match.group(1)

    scripts = re.findall(r"<script>(.*?)</script>", src, re.S)
    theme = ""
    for s in scripts:
        if "localStorage" in s or "data-theme" in s:
            theme = s.strip()
    if not theme:
        raise SystemExit("no theme script found")

    theme = re.sub(r"STORAGE_KEY\s*=\s*'[^']*'", "STORAGE_KEY = '%s'" % args.storage_key, theme)

    # Symbol fallback keeps circled numbers / arrows from shrinking on Windows.
    css = css.replace('"Consolas",monospace', '"Consolas","Segoe UI Symbol","Apple Symbols",monospace')
    css = css.replace('"Noto Sans SC",sans-serif', '"Noto Sans SC","Segoe UI Symbol","Apple Symbols",sans-serif')

    base = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<style>
{{CSS}}
</style>
</head>
<body>
{{CONTENT}}
<script>
{{THEME}}
</script>
</body>
</html>
"""

    build = pathlib.Path(args.build_dir)
    build.mkdir(parents=True, exist_ok=True)
    (build / "base.html").write_text(base, encoding="utf-8")
    (build / "css.txt").write_text(css, encoding="utf-8")
    (build / "theme.txt").write_text(theme, encoding="utf-8")
    print("css", len(css), "theme", len(theme), "build", build)


if __name__ == "__main__":
    main()
