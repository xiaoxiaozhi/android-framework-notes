---
name: "md-html-pdf-artifact-resync"
description: "源 md 删改段落/订正事实后，同步重生成 HTML 与 PDF：清查引用文案、逐份核验残留字符串。"
---

# 源 md 改动后的多产物同步

一套文档（md + 生成脚本 + HTML + PDF）里改源文时，衍生文件和引用该段落的其它文案会一起过期；只改 md 等于没改完。

## 步骤

1. 只在源 md 里删改，再列出同目录的衍生产物与生成脚本（如 `build_html.py`、`index.html`、同名 `.pdf`），按 mtime 确认哪个是生成物、哪个是手写源。
2. 清查指向被删内容的引用，这步最容易被漏：文首版本行、`<title>`/页头徽章、侧栏标签、目录锚点、正文里“详见上文实测说明”之类。用被删段落的关键词跑一遍：
   ```powershell
   Select-String -Path *.md,build_html.py -Pattern '关键词1|关键词2' | Select-Object Path,LineNumber,Line
   ```
   生成脚本里的硬编码文案（侧栏日期标签、`链接已实测` 徽章）要一并改掉，否则 HTML 仍显示已不存在的事实。
3. 重新生成 HTML，确认 `index.html` 与主 HTML 字节数一致（两者内容相同才是同步的）。
4. 重新打印 PDF（headless Edge）：
   ```powershell
   $argstr = '--headless=new --disable-gpu --user-data-dir="D:\openclaw\tmp\edge-pdf" --print-to-pdf="D:\...\x.pdf" --no-pdf-header-footer "file:///..."'
   Start-Process -FilePath $edge -ArgumentList $argstr -Wait -PassThru | Select-Object ExitCode
   ```
   与 `html-headless-verify` 相同：单字符串传参、带 `--user-data-dir`、`EXIT=0` 且字节数非零才算成功。
5. 核验三份产物都干净：在 md、HTML、PDF 文本中搜被删字符串，全部应为空，并记录 PDF 页数与体积变化。
   ```python
   import pymupdf; d=pymupdf.open('x.pdf')
   print(d.page_count, sum('关键词' in p.get_text() for p in d))
   ```
6. 渲染改动页（`get_pixmap(dpi=90)` 存 png 后看图），确认删除处没有残留空行、断开的列表或跳号标题。
7. 汇报按产物列一张表（改了什么 / 是否重生成 / 体积页数变化），并说明保留了哪些同类措辞——用户常只想删一句网络说明而保留实测结论，删过头要往回补。

## 判据

- 被删关键词在 md、HTML、PDF 中命中数为 0；生成脚本中的对应硬编码文案已改。
- PDF 重新生成成功（页数与体积变化已记录），改动页渲染无空白断裂。
