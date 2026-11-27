---
name: "android-framework-learning-plan"
description: "规划 Android Framework 学习路线(用户:'我要学 framework 不知道学习步骤 / 哪一部分岗位最多 / 哪些最重要 / 帮我规划',或回'我的目的是 A/B/C')与设计配套实践项目(用户:'你没给我出实践项目 / 你自己也出实践项目')。先定位系列目录(位置会被用户调整,2026-10-18 已移到 D:\\openclaw\\Android framework\\Android窗口层级),分诊三赛道(A 应用层 / B 系统框架层 / C 内核 HAL),选定后按 references/roadmap-and-artifacts.md 裁剪并产出 D:\\openclaw\\Android-Framework学习路线图.md + 系列同款 HTML;项目必须是可验收交付物、且不止挖现成资料(马老师库)还要自己出原创'用实现验证理解'型,设计模型与两份清单见 references/practice-projects.md。单模块文章/源码问答走 android-article-series,不在本技能。"
---

# Android Framework 学习路线规划与实践项目设计

## 触发场景

- 用户说「我要学 Android framework，不知道学习步骤 / 实际开发里哪部分岗位最多 / 哪些最重要 / 学习路线图是什么，帮我规划」。
- 用户回「我的目的是 A / B / C」或「我想走系统层 / 车机 / 内核」——这是选道信号，按下面分诊。
- 用户问「学完能干什么岗 / 要不要学某块 / 我这水平该下一步学什么」。
- 用户纠正「你没给我出实践项目」「要有练习项目」「你自己也出实践项目」——见步骤 5（常驻要求）。
- **不属于本技能**：单个模块（WMS 等）的文章写作、源码逐行讲解 → `android-article-series`；查/下载马老师知识库 → `wechat-mp-article-kb`。

## 步骤

1. **先定位系列目录**（位置会被用户调整）：2026-10-18 会话期间从 `D:\openclaw\Android窗口层级` 移到了 `D:\openclaw\Android framework\Android窗口层级\`。动手前先搜定（`Get-ChildItem D:\openclaw -Recurse -Filter "android-window-06*.html" -Depth 4`），下文写「系列目录」处均指实探结果，不要硬编码旧路径。
2. **定赛道**（决定性分叉，先问或从上下文取）：A 应用层 / B 系统框架层 / C 内核-BSP-HAL。三者岗位量、门槛、天花板差得很远，混着讲会让路线失焦。
   - 按「实现层 vs 消费层」判定用户已有经历，别按关键词匹配：App 通过 JNI 调用别人做好的 .so 属 **A 应用层**（native 边界、ABI、tombstone 调试），不算 B/C 的 HAL、中间件、系统集成或驱动经历；只有自己设计实现 .so/HAL 接口、写系统服务与 IPC、或做寄存器-总线 bring-up 才算 B/C。判错会把路线难度和岗位预期一起抬高一档，用户会当场纠正。
   - 用户选 **B** 时按 [references/roadmap-and-artifacts.md](references/roadmap-and-artifacts.md) 的「B 赛道加减法」裁剪：A 向技能（Jetpack 全家桶、MVVM、跨端、三方库源码、App 侧性能）整块降级，时间转到 AOSP 编译定制、Binder、SystemServer、AMS/WMS/PMS、SystemUI、系统签名/SELinux、系统裁剪(RRO)、OTA、Watchdog/稳定性、Perfetto/ANR/native crash。
3. **岗位分布与「哪些最重要」**：当场用 `web_search` 抓招聘样本（中文 query，如「Android Framework 系统开发 岗位需求 招聘方向」），把命中的 JD 原文要点当证据。**必须注明这是样本观察、不是全量统计**，别报精确数字。
4. **排阶段路线**：用 reference 里的六阶段骨架（地基 → AOSP 上手与调试体系 → 进程与 IPC → 三大主服务 → 图形与输入 → 稳定性与性能 → 方向专项），**先按用户已有进度裁剪，不要从头排**（用户常已深入某模块，例：WMS 已通 → 接 Binder → AMS → PMS）。每阶段给验收标准。
   - **单模块路线图**（例：用户说「SystemUI 我不熟，讲一下并出学习路线图」）：先 `ls -d` 定位模块源码（SystemUI 在 `frameworks/base/packages/SystemUI`，不是 `packages/SystemUI`），再读模块的组件注册表当职责地图（SystemUI 为 `res/values/config.xml` 的 `config_systemUIServiceComponents`，逐项即真实组件）；每站绑一个真实类名 + 本次 grep 的行号，站点顺序按「启动骨架 → 窗口层 → 核心数据流 → 交互面板 → 状态机 → 定制/稳定性」，每站给验收标准与 1 个修 bug 型或自造型项目。
   - 引用类名和行号前先确认这棵树的重构代际：SP1A 的 SystemUI 仍是 `statusbar/phone/StatusBar.java` 集中式、没有 `CentralSurfaces`，网上 13/14 文章的结构对不上，以本地树为准并点明差异。
   - 单模块路线图先在对话里给全文，末尾问是否落盘；只有用户说「落盘」才写 HTML，不要默认生成 `D:\openclaw\Android-Framework学习路线图.md`（那是全框架大图）。
   - **目标驱动模式（用户说「前置知识太多 / 有个功能想自己做但不知从哪学」）**：先判定他列的前置是否同层——grep 它们的共同父类或枚举取值（PiP、分屏、自由窗口、最近任务都是 `windowingMode` 的并列取值），同层就直接说「这不是前置，是兄弟」，不要按课程线性排；再把目标功能拆成 3–5 跳、每跳给 `文件:行号`（例：找 task → 找目标 DisplayArea → reparent → 配置变更下发），只列真正挡路的知识块，每块给「一句话够用版 + 一条可判定判据」（dumpsys 字段或 logcat 行）；最后给「第一天可跑的最小实验」，含造环境命令（如 `settings put global overlay_display_devices`）与判据命令，让现象先于理论出现；课程资料当字典按卡点查，明确不要求线性看完。
5. **产出两份文档**：`D:\openclaw\Android-Framework学习路线图.md` 与同名 `.html`，两版内容一致。
   - HTML 沿用窗口层级系列同款版式：内联 CSS + CSS 变量双主题、右下角浮动主题钮（localStorage，键名换一个避免与系列文章互相干扰）、TOC、card/table/annotation/step/deliver/analogy/think 组件、不依赖任何外部 JS/CSS、移动端 media query。
   - **放在 `D:\openclaw` 根目录**，不要塞进系列目录（那是自包含站点；本图是它上层的大图，用相对路径互相跳转即可）。
6. **必须给实践项目**（2026-10-18 用户连续两次纠正的常驻要求：只给命令/实验不算）。
   - 两类都要给：**修 bug 型**（挖现成案例）+ **自造型**（自己设计，`预测 → 实现 → 实测 → 记录偏差`）。
   - **用户问「某子系统能出什么实践题」时按编译成本分级出题**：先给零编译题（只改 app/manifest 或只敲 `dumpsys`/`am` 命令），再给只编 `m services` 的题，最后才是要改 framework 的题；每题四要素为改哪个变量、可 grep 的判据命令、根因 `文件:行号`、能写进简历的产出，并注明编译成本（`m services` 几分钟 vs 整树数小时），否则用户被一堆要重编的题压住而不动手。
   - **每题先过「动作测试」**：问一句「答完这题，用户下次排障的动作会变吗」，不会变的是锚点考古题（背 `mWindowMap` 的 key 是哪个 binder、某两行谁先谁后），改写成「现象 → 判断依据 → 命令 → 预期输出」四段式；出题前 `grep -n` 复核题干每个前提（token 由谁设、哪行赋值），题面引用的代码必须包含决定答案的那几行，删掉关键行就是让用户答没给出的代码。
   - 每个项目必须写清「交付物」与「怎么算做完」；每份清单落一个 HTML（同款版式）并挂到系列目录的 `index.html` 卡片。
   - 设计模型、两份已产出清单、挖马老师库作业的方法见 [references/practice-projects.md](references/practice-projects.md)。
7. **校验**（写完必做，按 `android-article-series` 的 `_build\verify_series.py` 同款写一次性脚本）：`html.parser` 栈式标签闭合 + TOC 锚点集合与 `id` 差集为空 + 内部 `href` 可达性（缺失 0）+ Edge headless 对 **ASCII 路径副本**截图抽检首屏；一次性脚本跑完即删。

## 决策规则

- **用户问的是学习方法本身**（「先粗过一遍还是直接做题」「不想跟视频了」「学了记不住」「陷入死循环」）：不要只讲方法论，按 `D:\openclaw\skills\framework-learning-loop\SKILL.md` 立刻走一轮——一页三块（骨架 ≤18 行带行号 / 决策点 3–5 / 3 个反问）+ 一道 L0 判据题，`python scripts/check_round.py <round.md>` 退出码 0 才能发；方法讨论只在用户追问「为什么这样学」时展开。
- **实验 ≠ 项目**：实验是 10 分钟看现象、无产出；项目要几天、有可交付物（patch/工具/报告/功能）。学习支持类产出没有项目 = 没交付。说话时别把「跑条 dumpsys」当项目交付给用户。
- **用户说没有真实 bug、看 dumpsys/logcat 抓不住重点**：不要改造读书目或继续加观测清单，改出一份故障注入清单——每个实验只改一个变量（注入：改一行让它坏；回退：去掉已有功能的一个 flag；对比：同一操作改前改后各抓一次 diff），每张卡写全五要素（改哪个变量 / 期望现象 / 可 grep 的判据字符串 / 不符合预期时看哪一段 / 根因 `文件:行号`），落成用户 demo 工程的 `LAB.md` 并在其 README 挂链接，把「读日志」变成「查一条判据」。
- **既有资料够用就直接引用，不重写**：`<系列目录>\WMS学习路线图.md`（+ `android-window-roadmap.html`）是 WMS 单模块路线，本图是它的上位；两者是包含关系（WMS 路线 = 本图「阶段 3 的 WMS 部分」的展开），别造第二份冲突的规划。
- **阶段-篇号耦合**：路线图里「阶段 N 对应 0X 篇」的映射与系列篇号联动，改篇号要 **.md 与 .html 两版一起改**（细节见 `android-article-series` 的 series-layout.md 第五节）。
- **岗位结论要带证据与日期**：招聘样本会过期，重新抓时以当日结果为准，旧结论标注日期即可，不要凭记忆断言「今年最缺 X」。
- **不承诺课程/付费内容**：只规划与出题；马老师那类课程链接不主动引导购买。

## 坑（实测）

- **别把路线图塞进系列目录**：系列目录（现 `D:\openclaw\Android framework\Android窗口层级\`）是自包含站点（有自己的 index/校验脚本），上位路线图放 `D:\openclaw` 根目录，两处用相对路径互链；构建互链前先按上文实探路径确认相对层数（系列目录一旦再被移动，相对路径要跟着改——搬动流程见 `windows-folder-move-locked-server`，直接 Move-Item 会因 live-server 占用而失败）。
- **HTML 中文路径截图会失败**：file:// 中文路径 ERR_FILE_NOT_FOUND，先用 Python `shutil.copyfile` 造 ASCII 副本再 Edge headless 截图；PNG 要拷进允许目录再 `view_image`。
- **结构改写的脚本一律写成 `.py` 文件跑**，别在 pwsh 里用 `python -c` 单行（带括号/引号会报解析错）。
- **产出落到哪个子目录要说清**：新增清单/路线图只在目录里躺着、或落在 `_draft\` 这类子目录里，用户会说「我没看到具体文件」「Binder 去哪了」——加 index 卡片，并给**含末级子目录的完整路径**（如 `…\Android窗口层级\_draft\x.html`）与可直接打开的方式（双击路径/预览 URL），别只给父目录；路径本身按实探结果给，目录被移动后旧绝对路径会误导用户。
- 长 HTML 分段落盘（write 骨架 → edit 追加），一次输出会撞模型输出上限被截断（同 `android-article-series` 记录的现象）。
