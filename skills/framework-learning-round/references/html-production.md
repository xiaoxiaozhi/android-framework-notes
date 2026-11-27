# 文章落盘（HTML）

> 只在第 6 步读。目标：每个学习轮次都产出**同款视觉**的单文件 HTML，且能机械验证。

## 1. 视觉基线（不许自创）

一律使用 `android-source-html-analyzer` 的设计系统；CSS 已固化在 `assets/article.css`，**不要**再手写一套。

必须有的特征：

- 暖纸色浅色 `#faf8f5` / 低对比深色 `#1a1a1e`，全部走 CSS 变量 + `data-theme`
- 22:00–07:00 自动深色，其余浅色；右下角悬浮按钮三态切换（自动 🌓 → 浅色 ☀️ → 深色 🌙），`localStorage` 记忆
- 代码块：文件名条 + 圆点 + 复制按钮；关键字/函数/注释三种色
- 重点标注：`✦ ✦ ✦` 金框；基线/未核实用青框
- 吸顶导航 + 滚动进度条；编号章节；表格与卡片统一圆角阴影
- 打印时隐藏按钮/导航

## 2. 结构（单文件，离线可开）

```
_build/<主题>/
├── p1.html   <head> + <style>/*__CSS__*/</style> + hero + nav
├── p2.html   ① 骨架 + 解说 + ② 决策点 + ③ 三问 + 阅读法 + 关键代码
└── p3.html   L0 题 + 白话对照 + 12→13 漂移 + footer + <script>
```

- p1 的 `<style>` 里只留占位符 `/*__CSS__*/`；CSS 只有 `assets/article.css` 一份。
- 章节 `<section id="s1">…` 数量固定，导航里的锚点必须一一对应。
- 单块 ≤ 8KB；不要把整份 HTML 贴进聊天回复。

## 3. 构建

```bash
python scripts/build_article.py \
  --parts "_build/<主题>/p1.html" "_build/<主题>/p2.html" "_build/<主题>/p3.html" \
  --css assets/article.css \
  --out "D:\\openclaw\\Android framework\\学习XXX\\<主题>学习轮次-AOSP13.html"
```

脚本负责：注入 CSS、按顺序拼接、写 UTF-8 无 BOM、检查占位符残留与标签闭合。非 0 不许交付。

## 4. 验证（必做）

```bash
python scripts/verify_html.py "<文章.html>" --sections 7 --shot verify.png
```

必须全绿：

1. `data-ready="1"` —— 脚本真的跑完了
2. `data-theme` 存在，且点击一次后值发生变化
3. `<section>` 数量等于 `--sections`
4. 无 `/*__CSS__*/`、`{{` 占位符残留
5. 截图能打开，肉眼确认：标题/骨架/解说/表格四处没有错位或溢出

截图放在工作区，打开看一眼再删；只跑断言不看图，等于没验证。

## 5. 清单（逐条勾）

- [ ] 三块顺序正确，解说一行一个标号，阅读法五行
- [ ] 每个锚点在基线树成立（`check_anchors.py` 无 error）
- [ ] CSS 来自 `assets/article.css`，没有第二份
- [ ] 深浅色、自动时段、按钮三态都试过
- [ ] 代码块复制按钮可用（点一次看到“已复制”）
- [ ] 表格在 390px 宽度下可横向滚动，不撑破页面
- [ ] 文件 UTF-8 无 BOM，`grep` 得到第一条锚点
- [ ] `_build/` 保留分块，方便下一轮补内容

## 6. 旧文章重刷（legacy）

老文章若已有自己的布局（如侧边 TOC + 流程表），**不要为了统一而重排内容**：

- 新文章一律走 `article-template.html`；旧文章只做“视觉对齐”：替换/覆盖 CSS 变量为 `assets/article.css` 的同一套 token、标题统一衬线、补进度条、复用三态主题脚本。
- 不新造第二套色板；旧布局的组件（`.flow-row`、`.tbl`）可以保留，但颜色只能引用同一组变量。
- 重刷后同样跑 `verify_html.py`：`data-ready`、主题切换、section 数、无占位符，再截图确认。
