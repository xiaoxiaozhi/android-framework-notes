---
name: "android-source-html-analyzer"
description: "分析 Android 源码并生成带深色/浅色主题、时间自动切换、悬浮按钮、重点标注和中文注释的 HTML 文档"
---

# Android 源码 HTML 分析文档生成器

## 概述
分析 Android 源码（Java/C++）中的关键方法、执行流程、类结构，并生成带深色/浅色模式、时间自动切换、悬浮切换按钮、重点标注和中文注释的 HTML 文档。

## 触发词
- 分析这份源码并生成 HTML
- 生成源码分析文档
- android source to html

## 工作流程

### Step 1: 读取源码文件
源码在 WSL `/home/book/aosp12/`(例如 wm 源码目录 `frameworks/base/services/core/java/com/android/server/wm/`)。先 `wsl -e bash -lc` 里跑 `grep -n` / `sed -n 'a,bp'` 定位关键方法,文档引用的行号必须这样现查现核,不要凭记忆写。
**引号坑**:外层 PowerShell 已用双引号包住整条 bash 命令时,内层不能再出现 `\"` 转义(会把外层字符串提前终止,报「字符串缺少终止符」);内层一律只用单引号,或者把多段命令写进临时 `.sh`/`.ps1` 文件再执行。
**定位文件**:不要用跨 `/mnt`、`/home`、`/root` 的大 `find` 搜全盘(扫 Windows 挂载盘会卡死,需 kill);源码根已知是 `/home/book/aosp12`,直接拼完整路径 `ls` 验证文件存在,再对该文件 `grep -n` 定位。

### Step 2: 源码分析
- 识别类声明、构造函数、关键方法（main/run/init/start/systemReady 等）
- 标注方法的作用和调用链
- 识别常量、枚举、关键设计模式
- 标注异常处理、同步块、系统调用等关键点
- 对 C++ JNI 文件，标注 `JNINativeMethod` 注册表和对应 Java 方法

### Step 3: 生成 HTML 文档
生成包含以下特性的完整 HTML 文件：

#### 3.1 深色/浅色切换
- 为浅色模式使用柔和配色（`#faf8f5` 背景，暖色调强调色）
- 深色模式使用低对比度暗色（`#1a1a1e` 背景）
- 所有颜色使用 CSS 变量，支持 `data-theme` 属性覆盖

#### 3.2 时间自动切换
- 07:00 ~ 22:00 → 浅色模式
- 22:00 ~ 07:00 → 深色模式
- `setInterval` 每分钟检查一次
- `localStorage` 记住用户手动选择

#### 3.3 悬浮切换按钮
- 右下角固定悬浮按钮
- 点击在三个模式间循环：自动 → 浅色 → 深色 → 自动
- 显示当前模式图标（🌓/☀️/🌙），分别对应自动/浅色/深色
- 鼠标悬停显示提示文字

#### 3.4 源码分析内容
- **类总览**：文件名、行数、作用
- **关键方法**：用代码块展示，每行关键代码旁添加中文注释（用 `<span class="cm">` 或 HTML 注释）
- **执行流程**：用表格或箭头图展示调用链
- **重点标记**：`<span class="tag">✦ ✦ ✦</span>` 标注核心方法
- **设计亮点**：单独章节列出关键设计模式
- **WSL 速查命令**：底部提供 grep/find 命令方便查阅

#### 3.5 输出
- 将生成的 HTML 写入 `D:\openclaw\<文件名>-analysis.html`
- 自动用浏览器打开

## 输出规范

### HTML 结构模板
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>类名 — AOSP 12 源码分析</title>
  <style>
    /* CSS 变量：浅色/深色主题 */
    /* data-theme 覆盖 + 时间自动切换 */
    /* 悬浮按钮样式 */
  </style>
</head>
<body>
  <!-- Header -->
  <!-- 内容区 (h2/h3 分章节) -->
  <!-- 代码块 (.code-block) -->
  <!-- 标注框 (.annotation / .annotation.star3) -->
  <!-- 表格 -->
  <!-- 浮按钮 -->
  <script>
    // 时间段判断 + setInterval 切换
    // 悬浮按钮点击切换
  </script>
</body>
</html>
```

### 代码块格式
```html
<div class="code-block">
  <div class="filename">文件名 — 方法名</div>
  <pre><span class="cm">// 中文注释</span>
<span class="kw">public void</span> <span class="fn">methodName</span>(...) {
    <span class="cm">// ★ 关键点注释</span>
}
</pre>
</div>
```

### 标注等级
| 等级 | CSS 类 | 用途 |
|------|--------|------|
| 普通 | `.annotation` | 一般说明 |
| 重要 | `.annotation.star3` + `<span class="tag">✦ ✦ ✦</span>` | 核心流程、关键设计 |

## 依赖
- WSL (访问 `/home/book/aosp12/` 下的源码)
- PowerShell (调用 `Start-Process` 打开浏览器)

### Step 4: 大文件落盘与验证（HTML 超过约 8KB 必须照做）
**禁止把整份 HTML 写进聊天回复正文**：输出长度会被截断，截断点之后的工具调用根本发不出去，现象是「用户看到卡住、什么都没执行」。改为分块 `write` 再拼接：
- `_build\p1_head.html`（head+样式）/ `p2_body.html`（body 结构）/ `p3_logic.js`（算法本体）/ `p4_render.js`（渲染+交互）分四次写，单块控制在 8KB 内。
- 拼接与检查放同一次 exec：`[IO.File]::ReadAllText` 逐块读、`-join "`r`n"`，用 `New-Object System.Text.UTF8Encoding($false)` 写回最终文件（无 BOM）。
- 抽 JS 语法检查：`p3_logic.js` 去掉 `<script>`、`p4_render.js` 去掉 `</script>`/`</body>`/`</html>` 后拼成临时 `.js` 跑 `node --check`；不剥标签必然报 `Unexpected token '<'`。
- 改动只重新拼接，不复用旧文件；`_build\` 保留供下次修改。

### Step 5: 算法类页面的正确性验证
- **先写独立参考实现**：把源码算法另外用 Python（或独立 JS 脚本）实现一遍，跑出权威输出（如最终树、事件序列），再与页面 JS 的逐步输出逐行比对。两边一致才算对，别只看页面「长得对」。
- **无头浏览器行为验证（交互页必做）**：在 HTML 末尾注入 `window.addEventListener('load', ...)` harness，里面 `document.getElementById('btnX').click()` 并跑断言，结果写进 `document.title`；用 `msedge --headless=new --disable-gpu --user-data-dir=<临时目录> --virtual-time-budget=4000 --dump-dom <file-url>` 执行，再正则取 `<title>` 看 `E2E_OK/FAIL`。
- file URL 用 `urllib.parse.quote(path, safe="/:")` 生成，不要手写 `%XX`（中文路径会变乱码导致加载失败）。
- 截图同法追加 `--screenshot=<png> --window-size=1400,2700 --hide-scrollbars`。`view_image` 只能读允许目录，`D:\` 下的截图读不了，直接留在原目录交给用户。
- 收尾删掉注入 harness 的临时 HTML。

### Step 6: 图示标签
缩写标签不要用 `charAt(0)`（`TASK` 和 `TOKENS` 会撞成同一个 `T`，用户完全分不清）；用两字符标签（如 `TK`/`IM`/`TO`），并确保生成的 CSS 类名与样式表里的选择器逐字一致（`tTOKEN` vs `tTOKENS` 这类拼写差会让整行样式静默失效）。
