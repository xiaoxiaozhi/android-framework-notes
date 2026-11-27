---
name: "html-headless-verify"
description: "验证生成的单文件 HTML/交互页：Edge headless 跑断言、截图分区、480px 移动端检查。用于交付动态 HTML 前后。"
---

# 单文件 HTML 的无头验证

交付动态 HTML（源码分析页、交互模拟器、系列文章）前，用 Edge headless 证明脚本能跑、布局不炸；只截图不跑断言不算验证。

## 步骤

1. 生成 file URL：把 Windows 路径的反斜杠换成 `/`，再 `urllib.parse.quote(path, safe='/:')`，拼成 `file:///...`。中文或空格路径不手写 `%XX`。
2. 复制一份临时页注入断言，改完即删，不污染交付文件。harness 在 `load` 后点击按钮或调用页面暴露的对象，把结果写进 `document.title`：
   ```html
   <script>window.addEventListener('load',function(){
     var R=[]; function ok(c,m){if(!c)R.push('FAIL:'+m);}
     // 调用 window.__lab.runAllSync() 或点击 #play，然后轮询到终态
     ok(true,'smoke'); document.title = R.length ? 'E2E_FAIL '+R.join(' | ') : 'E2E_OK';
   });</script>
   ```
   有定时器时用 `setInterval` 轮询终态（如 `#statArray` 达到预期层数）再写 title，不要立刻断言。`--dump-dom` 里中文是乱码，只断言 ASCII 标记。
3. 取 DOM 用 `Start-Process` 重定向到文件；不要用管道或变量接收 `msedge --dump-dom`，Edge 进程分离时实测得到空串。参数拼成一条带引号的字符串，不要传数组：数组里的路径含空格时会被拆成多个位置参数，Edge 报 `Multiple targets are not supported in headless mode`、退出码 13、输出 0 字节。
   ```powershell
   $edge = (Get-Command msedge -ErrorAction SilentlyContinue).Source
   if (-not $edge) { $edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' }
   $argstr = '--headless=new --disable-gpu --user-data-dir="D:\openclaw\tmp\edge-e2e" --virtual-time-budget=12000 --dump-dom "' + $url + '"'
   $p = Start-Process -FilePath $edge -ArgumentList $argstr -RedirectStandardOutput D:\openclaw\tmp\dom.html -Wait -PassThru
   'EXIT=' + $p.ExitCode
   ```
   再读 `dom.html`，正则取 `<title>`，要求 `E2E_OK`；`EXIT` 非 0 或文件为空说明参数没送到，先修命令行再判断页面。
4. 截图看最终视觉态：沿用第 3 步的 `Start-Process` + 单字符串 + `--user-data-dir` 启动方式，只把 `--dump-dom` 换成 `--screenshot="<绝对路径>.png" --window-size=1400,3600 --hide-scrollbars`，页面用自动播放版本。不要用 `& $edge` 直接调用：默认配置被占用时它退出而不写 PNG，只看“无报错”会误判成功。`EXIT=0` 且 `Test-Path` 为真、PNG 字节数非零再看图。窗口高度只覆盖首屏，长页要分段截或先隔离区块。
5. 隔离某个区块时不要靠 `scrollIntoView`（截图仍从文档顶部开始），注入样式隐藏其它兄弟节点：
   ```css
   body>.wrap>*{display:none!important} body>.wrap>#lab,body>.wrap>.lab{display:block!important}
   ```
   单独截该区块，再分别看浅色与深色。深色版不能只在临时页改 `<html data-theme>`：页面自带主题脚本会在 load 时按 localStorage 或当前时间重设（auto 模式 07:00–22:00 恒为 light），截出来仍是浅色。临时页里删掉整段 `<script>` 再设 `data-theme="dark"`，并核验 PNG 里背景确实变深（浅色 `#faf8f5` 对深色 `#1a1a1e`）。
6. 加一轮窄屏截图：`--window-size=520,1700`，不要用 480。Edge 的 Windows 无头窗口有最小宽度，设 430/480 时 CSS 视口仍是 ~492px，PNG 只是被裁窄，按它判断会漏掉溢出。用注入脚本把 `innerWidth` 与 `document.documentElement.scrollWidth` 写进 `document.title`，要求 `scrollWidth <= innerWidth`。溢出修法：表格外面包 `overflow-x:auto` 的容器；终端 `pre` 在 `@media (max-width:720px)` 改 `white-space:pre-wrap;overflow-wrap:anywhere`；树/表格列用 `minmax(0,1fr)`，行与列容器加 `min-width:0`，否则长名字把卡片撑出横向滚动。
7. 汇报写“E2E_OK + 断言数量/关键值”，并给出源码锚点或页内路径；清理 `e2e_*.html`、`shot_*.html` 与临时截图。

## 判据

- `document.title` 为 `E2E_OK`，且断言覆盖至少：元素数量、关键状态值、一次真实点击后的终态。
- 浅色、深色、520px 三张截图均无横向溢出（`scrollWidth <= innerWidth`），长名字显示省略号。
