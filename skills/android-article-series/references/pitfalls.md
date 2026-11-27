# 实测坑（窗口层级系列 / 长篇源码文章）

- **从 WSL 取源码片段时，长输出会被压缩/省略**（页面显示 `... N lines omitted ...`），不能把截断结果当引用底本：先把精确行段导出到本地文件，`wsl -e bash -lc 'sed -n "a,bp" <file> > /mnt/d/openclaw/tmp/<name>.txt'`，再用 `read D:\openclaw\tmp\<name>.txt` 读原文；`read` 直接读 `\\wsl.localhost\...` 会报 `file identity changed or could not be verified`。代码块行号以导出原文为准。
- **改稿前先备份**：整批要动的 html/index/路线图拷进 `_build\backup-<日期>\`（存在即跳过），再动原文件；重排/落盘都属于不可逆的批量编辑。
- **整节套 `<div class="card">` 会在分段落盘时重复闭合**：每节只在开篇引言和表格上用 card，代码块固定写 `<div class="code-block"><div class="filename">…</div><pre>…</pre></div>`；分段写完先跑一次逐行 open/close 深度图，确认收尾深度为 0 再合并，合并后再跑 `check_html.py`；报「无匹配闭合 </div>」时用同一张深度图定位到具体行再改，不要按总数补标签。
- **批量改锚点 id 或章节编号，绝不能用顺序 `replace`**（`p0→p1` 后再 `p1→p2` 会级联，实测全塌成 `p7`）：用 `re.sub` + 计数器按文档序生成新编号，且 TOC 文本与 `id`/`href` 同一趟改（详见 series-layout.md 第六节）。
- `wsl -e bash -c "..."` 只对单条简单命令可靠：命令里含 bash 变量（`$f`）、`;` 串联或 `awk '{...}'` 时，wsl.exe 会重新切分命令行、PowerShell 又先展开 `$var`，表现为变量变空、`;` 被当成路径参数（实测 `ls: cannot access ';'`）。这类脚本一律写到 `D:\openclaw\tmp\<name>.sh`，再用 `wsl -e bash /mnt/d/openclaw/tmp/<name>.sh` 运行；这条路径形式实测稳定。
- exec 工具的超时参数是 `timeoutSeconds`，写 `timeout` 会直接被拒。
- 其他 WSL/PowerShell 联调坑（`bash -lc` 输出丢失、`$_` 被外层解析、中文注释编码）见 MEMORY.md "WSL + PowerShell 联调时的坑"，复杂逻辑落到 .sh/.ps1 文件再跑；**本目录的 HTML 结构改写/校对一律写成 .py 文件执行**，不要在 pwsh 里用 `python -c` 单行（带括号/lambda/引号的会报错，测过。）
- **输出被 `length` 截断，看起来像"任务停止/终端不响应"**：模型在 openclaw.json 未声明 `maxTokens` 时，OpenClaw 默认输出上限只有 **8192 token**，整篇 HTML 一次写完必被 `finish_reason=length` 硬截断、回合结束但文件没落盘（04 篇曾连续三次因此中断，非会话崩溃）。ark-code-latest 已按火山 Coding Plan 官方上限声明 `contextWindow:256000 / maxTokens:32000`；再遇莫名中断先查该模型的 maxTokens 是否缺失，再按步骤 4 分段落盘，写完用 ls/读取核对字节数与 `</html>` 收尾。
- **断言「每帧都走这条链」前先读调用点的守卫条件**：`grep -n "<callee>(" <file>` 只证明调用边存在，不证明每次都会执行——命中行要落在父方法行段内，再读包住它的 `if (...)`（如 `mFirst || windowShouldResize || viewVisibilityChanged || params != null || mForceNextWindowRelayout`），才能把 trace 里「vsync 后没有 relayoutWindow」归因为条件不满足而非丢帧；`dumpsys window` 的 `mRelayoutCalled=true` 也只说明调用过，不代表每帧都调。回答前先看守卫，再下结论。
