# 文章视觉层与树-only 改造

## 触发

- 用户说「设计美观 / 排版太素 / 背景纯黑难看 / 只要调用树 / 不要代码块」。
- 长文落盘后做最后一轮视觉与结构收口。

## 树-only 改造

用户明确「不要代码块，只要调用树」时执行；否则保留代码块。

1. 备份整篇到 `_build\backup-<日期>\`。
2. 删除代码块：Python 读 UTF-8，`re.subn(r'<div class="code-block">.*?</pre></div>\s*', '', s, flags=re.S)`；打印删除数，要求剩余 `class="code-block"` 为 0。
3. 提取树：`re.finditer(r'<div class="tree">.*?</div>', s, re.S)`；数量必须等于功能章节数。
4. 按章节顺序替换树。每行节点后写 `// 这一层做什么`；渲染时按第一个 `//` 切开，左侧 `html.escape(..., quote=False)`，右侧包 `<span class="cm">`，保留缩进。
5. 校验脚本：
   - 每棵树的非空行 `//` 缺失数必须为 0：
     ```python
     text = html.unescape(re.sub(r'<[^>]+>', '', tree))
     missing = [l for l in text.splitlines() if l.strip() and '//' not in l]
     ```
   - HTMLParser 栈 0 错；
   - TOC `href` 与 `id` 全命中；
   - `class="code-block"` 计数 0；
   - `audit_anchors.py` 仍 n/n（树行保留 `[文件:行号]`）。
6. 树-only 文章不再写 `.filename`、`<pre>`；正文段落围绕「这一层做什么 / 为什么这样设计」，不要加「这段在干什么：」「设计意图：」标签。

## 摘要卡

长文在 `0.0 名词表` 之后、第一章之前放：

```html
<h2 id="abstract">摘要</h2>
<div class="card">
<p><strong>主线：</strong>一句话把起点→模型→分发→消费串起来。</p>
<ul>
<li><strong>采样：</strong>...</li>
<li><strong>模型：</strong>...</li>
<li><strong>分发：</strong>...</li>
<li><strong>消费：</strong>...</li>
<li><strong>两条相位：</strong>...</li>
</ul>
</div>
```

TOC 加 `<a href="#abstract">摘要</a>`。摘要写结论，不写目录复述；4-6 条，每条一个机制。

## 视觉组件

CSS 变量：

- 浅色：`--tree-bg:#f7f2e7; --tree-text:#2c2c2c; --tree-border:#ddd3c3; --tree-comment:#5f7f5a;`
- 深色：`--tree-bg:#2f3540; --tree-text:#ece7de; --tree-border:#4a5260; --tree-comment:#a8c98a;`

完整可复制样式见 [templates/article-polish.css](../templates/article-polish.css)。

- 树块禁止纯黑；用左侧 4px accent 边、圆角 12px、`padding:30px 20px 18px`、`::before content:"调用树"`。
- h1/h2/h3 用衬线回退（`"Source Han Serif SC","Noto Serif SC","Songti SC",SimSun,Georgia,serif`）；h2 左侧 4px 渐变条 + 底部渐变线；`scroll-margin-top:24px`。
- TOC 桌面 `display:grid; grid-template-columns:repeat(2,minmax(0,1fr))`；移动单栏；hover 左侧强调线。
- 卡片圆角 14px、soft shadow、hover 抬升 1px；摘要卡 `#abstract + .card` 加左边框和渐变底。
- 表格斑马纹；暗色 `rgba(255,255,255,.025)`；表头首尾圆角。
- 顶部 3px 阅读进度条；右下角 `#top-btn` 滚动 >600px 显示；`html{scroll-behavior:smooth}`。
- 640px 断点缩小 h1/h2、card/tree padding，按钮 `right:18px`；打印隐藏 toc/按钮/进度条，白底黑字，card/tree/table `break-inside:avoid`。
- 所有 CSS 内联，不依赖外部资源；JS 放 `</body>` 前，确保元素已存在。

## 渲染验证

- 复制到无空格路径 `D:\openclaw\tmp\shotpage.html`；Edge headless `--window-size=1280,6000 --screenshot=...`。
- 用 PIL 裁 2200-4200 / 4200-6000 两条带，检查：树块不是纯黑、注释不被截断、表格不溢出、首屏标题/目录不挤。
- 暗色在 22:00 后自动生效；要查浅色主题时，复制一份把 `currentMode` 设为 `'light'` 再截图。
