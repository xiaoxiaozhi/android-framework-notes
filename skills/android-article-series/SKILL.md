---
name: "android-article-series"
description: "审计/补篇/重排 Android 窗口层级与框架级 HTML 系列（含渲染、显示子系统、Binder、交互模拟器），按 AOSP13 核实锚点并做 HTML/截图校验，也覆盖同源码树教学问答。单篇在会话讲完后用户说「落盘」=直接写正式篇到目标目录并更新 index/上下篇，不走 _draft；只有明确要草稿或批量『都出稿』才暂存 _draft。"
---

# Android 窗口层级系列文章：审计与补充

## 触发场景

- **用户要学 Android 显示子系统、问显示系列能写几篇，或要写 SurfaceFlinger/BLAST/HWC/VSYNC 系列**：按 [references/display-subsystem-outline.md](references/display-subsystem-outline.md) 的 12 篇路线评估与写作；与窗口系列分开编号，默认放 `D:\openclaw\Android framework\Android显示子系统`。
- 用户要求检索系列目录里的文章、判断齐不齐、补缺或写续篇。
- **系列目录位置会变，先实探再动手**：现为 `D:\openclaw\Android framework\Android窗口层级\`（篇目已是中文文件名）；每次先 `ls` 该目录，不硬编码文件名，搬动走 `windows-folder-move-locked-server`。框架级独立篇放上层 `D:\openclaw\Android framework\`、卡片挂该层 index.html；用户问「X 是什么 / 我要学习，也给我整个文章」且 X 是 system_server 服务时，按 references/framework-service-article.md 新建，先查目标文件是否已存在。
- 该系列持续更新，篇号、文件名与是否已发布只以 [references/series-layout.md](references/series-layout.md) 第一节为准（00–09 已落盘；`_draft\` 里的旧稿是存稿，不能当作「还没落盘」的判据）。另有 **Binder 独立专题**（框架层，不占系列编号）按 B0–B5 分册：B0 全链路已落盘 `..\android-framework-binder.html`，B1/B2 在 `_draft\` 待审，B3–B5 待写；内核 `drivers/android/binder.c` 不在这棵树，Binder 篇只写用户态 + `bionic/libc/kernel/uapi/linux/android/binder.h`（锚点见 source-map「Binder 分册锚点」节）。路线图阶段 2 = 06–07、3 = 08、4 = 09（均完成）、5 = 10（下一站）；`android-window-roadmap.html` 与 `WMS学习路线图.md` 两版必须同步且都被 index 链接；index 与各篇 footer 有下篇预告。
  - **框架级渲染篇（2026-10-20 落盘）**：`..\android-framework-render-pipeline.html`（Choreographer→上屏；骨架见 references/render-pipeline-outline.md）。
  - **`_draft\` 不可用作进度判据**：落盘后旧稿仍留在 `_draft\`（存稿/回滚用，不删），据它推断会得出「还没落盘」的错误结论；判断某篇是否已发布只看系列目录里有没有正式篇目。
- **用户在已有系列里点一个子主题（如「学习 vsync 和 Choreographer」）**：默认续下一个篇号写进系列，不要自造「补篇」——无编号会被当成漏编号并要求返工。路线图已把下一个篇号许给别的主题时，占用该号并把后续**尚未发布**的篇号各顺延一位；已发布篇号一律不动。只有用户明确要求不编号、或该主题本就在系列之外（Binder / 渲染等框架级专题）时才用描述性 slug。占用篇号后按步骤 5 同步五处：新篇 footer、上一篇 footer 与系列条、index 卡片与学习路线、「下一篇」说明、两份路线图的阶段-篇号映射与阶段卡片。
- **用户要求「重新排版 / 标题和内容对齐 / 文章要有连续性」**：这是对本系列的常驻要求（2026-10-18 提出），按 [references/series-layout.md](references/series-layout.md) 执行——命名表统一 title/h1/系列条/页脚，先备份再改，最后跑校验脚本。新写任何一篇时同样遵守该命名表。
- **用户把话题扩到整个 Android Framework**（学习规划 / 岗位方向 / 要实践项目，「你没给我出项目」「你自己也出实践项目」）：改用 `android-framework-learning-plan` 技能，**不要在本技能里铺开**。本系列已有的姊妹产出（2026-10-18，别再重造）：上位路线图 `D:\openclaw\Android-Framework学习路线图.md` + `.html`；实践清单 `wms-practice-projects.html`（P0–P5，挖自马老师库）与 `wms-original-projects.html`（L1–L6，自造实验），两者都在本目录且 index 已挂卡片。
- **用户要框架级“渲染/上屏”专题**（Choreographer、ViewRootImpl、ThreadedRenderer、SurfaceFlinger），或说现有渲染篇“没头没尾”：按 [references/render-pipeline-outline.md](references/render-pipeline-outline.md) 的固定骨架写，放 `D:\openclaw\Android framework\`（与 Binder 篇并列，不占系列编号）；四块缺一不可：初始化、驱动机制（不能停在 Choreographer，必须写到 `performDraw → ThreadedRenderer → RenderThread`）、方法逐个表、稳态闭环；并独立成篇：开头 0.0 名词表，不把窗口系列 03/04 当必读（详见 outline）。
- 用户要求修改/扩展同目录交互模拟器 `displayarea-builder-algorithm.html`（步进演示 build() 两趟遍历）。
- 用户就这块源码提问教学（build()/instantiateChildren、root 谁挂的、树存在哪、第一个窗口怎么挂树到首帧上屏、SystemUI 启动链 SystemUIApplication→Dagger→StatusBar.start 及状态栏窗口怎么挂上树、客户端加窗链 WindowManagerGlobal.addView / WindowManagerImpl.applyTokens / Window.setWindowManager（含 attrs.token 与 mWindowContextToken 的区别，锚点见 source-map「客户端 addView 链与两个 token」节），以及 05 输入 / 06 窗口的诞生 / 07 Activity 启动链 / 08 布局 Insets 旋转 / 09 动画 / 10 IME 壁纸等后续主题）：同样先查 source-map 已核实锚点直接用，缺口才补 grep；行号被质疑时先在基线 tag 下核对真实行，确认是 tag 或偏移差异，锚点落在语句行而非注释行；写类关系前 `grep -n "class X" <file>` 看 extends 还是字段持有，`final` 类不可继承；再按"具体类+行号+真实例子"作答（窗口 token 归属与 addWindow 三分支直接用 [references/wms-window-token.md](references/wms-window-token.md)）；用户贴自己的层级图或理解求核对时，逐条边对照类的 extends 与父容器的 addChild（如 `TaskFragment.addChild(ActivityRecord)`），逐边标对错后给修正版 ASCII 树，并点明 token 只是查表键（`ActivityRecord.Token→ActivityRecord`、`Task.mRemoteToken→Task`）而非容器节点；不为教学问答另起炉灶。
   - 骨架或正文里的命令行示例一次给成可直接粘贴执行的完整形式（`adb shell am start --windowingMode 5 -n <pkg>/.<Activity>`，脚本里加 `-W`；只写半截选项会被要求“补全命令”），改完同步该轮 HTML 骨架与同目录 round-XX.md 两处。用户说「学 X / 讲讲 X 的流程」时，先输出**方法名表**（每行：方法名 + 一句话职责 + `文件:行号`，8–18 行），再让他挑一个名字深挖；只给概念叙述会让他无法追问，因为问不出自己没见过的名字。问「某方法找不到被谁调用 / 要完整调用链」时改用 `aosp-caller-trace`，按 HAL 定义→厂商调用→out 生成 Bp/Bn→客户端桥接排查，不要在本技能里只 grep 源码树。SystemUI 源码在 `frameworks/base/packages/SystemUI/`（与 WMS 同树，source-map 末节有已核实锚点）；05–11 各篇锚点见 source-map「05–11 篇学习路线图锚点」节。
- 用户要 WMS/窗口系统的**学习路线图/下一步学什么**：权威规划已落盘 `<系列目录>\WMS学习路线图.md`（六阶段：工具箱→输入→窗口的诞生→Activity/Task 生命周期→布局/Insets/旋转→动画→IME/壁纸→按需多屏，每阶段含已核实锚点、实战问题、实验），同名 HTML 版 `android-window-roadmap.html`（系列同款样式，含卡片墙/TOC，index 有导航卡片）。直接引用或按用户进度裁剪，不要重新排顺序；**路线图改动时 .md 与 .html 两版都要同步**；新增锚点补回 source-map 对应小节。注意其中版本事实（12 树无 TaskFragment、mGlobalLock 在 ATMS、PhoneWindowManager 在 server.policy 包、startFreezingDisplay/stopFreezingDisplayLocked 命名不对称等），讲高版本差异前先核对。

## 步骤

0. 用户问「能写几篇 / 先给篇数」时，只做规模评估，不写 HTML：
   - 先定位源码根与版本：`wsl -e bash -lc 'ls -d ~/aosp*'`（`/home/book/aosp13` 是基线，`aosp12` 仅作差异对照），版本读 `build/make/core/version_defaults.mk` 的 `DEFAULT_PLATFORM_VERSION`（`TP1A` = Android 13，`SP1A` = 12）。
   - 抽旧篇章节判重叠：`Select-String -Path "<既有系列>\*.html" -Pattern "<h2[^>]*>"`，把已被覆盖的链路（如“一帧的一生”）标出来；新系列只写旧篇没下沉到的层。
   - 沿数据流切分，**一跳 = 一篇**：每篇要能独立用 `文件:行号` 验证一段“进入什么形态、出去什么形态”；按主题名词凑数会写出无法闭环的篇。
   - 回答第一句给总数，并拆成“必写主线（少一篇链路断）+ 可选扩展”，再按 3–4 个阶段列编号/标题/源码入口；结尾只问从哪篇开始，默认第 0 篇。
   - 显示子系统直接照 [references/display-subsystem-outline.md](references/display-subsystem-outline.md) 的 12 篇路线回答（8 主线 + 4 扩展），不要重新发明篇目。
   - 这一步不落 `_draft`、不写正文。
1. 盘点覆盖范围，不要逐篇通读：
   - 先定位系列目录（见触发场景第二条），`ls <系列目录>` 看文件清单。
   - 改已有篇前按文件名在工作区实搜确认真实路径（`Get-ChildItem -Recurse -Filter "*关键词*"`），用户会把篇目移进子目录或改名，别沿用上一轮的绝对路径；篇目落在子目录时把 footer 与站内链接改成 `../` 前缀、index 卡片 href 指向新相对路径，改完跑 `check_html.py` 确认站内链接 0 错误。
   - 一条命令抽出全部标题与章节骨架：
     `Select-String -Path "<系列目录>\*.html" -Pattern "<title>|<h2[^>]*>"`
   - **用户问「X 讲过没有 / 系列齐不齐」时做术语覆盖审计**（比通读快得多，2026-10-18 实测有效）：对每篇 HTML 统计该主题的关键类名/术语出现次数，**统计前必须先按 `</style>` 截断去掉 CSS 段**——否则 `transition:background .3s` 会把 Transition 计数灌水、`WindowStateAnimator` 会把 Animation 计数灌高，得出假的「已覆盖」；再读路线图看该主题是否已排篇号，两个结论合起来答复。
   - 只读与用户问题直接相关的章节，以及 `index.html` 的系列规划。
2. 定缺口：把用户的问题逐一对到已有章节。文章自己写的"留作下一篇 / 下篇预告"是最可靠的缺口信号；把缺口和计划中的篇章对齐后再决定新篇编号。
   - **用户嫌某篇太长/内容埋得深、要单独一篇聚焦子主题**：不要继续往原篇里加；拆成独立分册（单一主题、独立 TOC、独立标题），原篇保留为全集，两边互加“配套阅读”链接。位置按用户指定；框架级分册放 `..\`，相对链接按 series-layout 第五节改。
3. 写之前先核对源码，类名、方法名、行号必须真实存在（用户明确要求"具体类+行号"风格）：
   - 基线 AOSP13（`/home/book/aosp13`）；已核实的关键定位见 [references/aosp12-source-map.md](references/aosp12-source-map.md)，行号在 13 树复核后再引用。
   - 每个事实用 `grep -n` / `sed -n` 核实，不凭记忆写；native 与 Java 两侧都要核（如同一概念在 framework 与 surfaceflinger 的对应类）。
   - 讲解大方法内部十几条语句要标行号时，不要一句一条 grep：把方法行段导出后，用一条 `awk 'NR>=A && NR<=B && (/pat1/ || /pat2/ || ...) {print NR": "$0}' <file>`（写成 .sh 运行）一次打印全部锚点，代码块行号直接取自这份输出；再拿关键几行回读一次确认无错位。
   - 画调用树前逐条验证父子边：`grep -n "<callee>(" <file>`，命中行必须落在父方法的行段内才连那条边；不能按「这层看着该调它」连线。压缩层级时中间层不能省（`executeRequest → startActivityUnchecked → startActivityInner`），漏层会让读者按树去父方法里 grep 一个不存在的调用。
   - 只做校验与委托的「壳方法」（`startActivityAsUser`、`ActivityStarter.execute`）先给压缩骨架再讲：代码块按「锁外准备 / 锁内执行 / finally 收尾」分段标行号，省略处写 `// …`；正文只写每段持不持锁、真正的活委托给谁（`executeRequest` → `startActivityInner` → `realStartActivityLocked`），末尾列 2–4 条易漏点（`clearCallingIdentity` 必须配对、`getExternalResult` 会改写返回码、池化对象在 finally 里 `reset` 回收），不逐行复述方法体。
   - **教学问答中现 grep 出的新锚点（含"用户按依赖顺序补一层"式多站带学），当轮就补进 source-map 对应小节，即使本篇不落盘 HTML**，下次同主题直接复用、不重新 grep；同时顺手订正旧锚点的方法名/路径错误（例：native 层只有 `DisplayEventReceiver::requestNextVsync()`，无 `scheduleVsync`；BitTube 头在 `libs/gui/include/private/gui/`）。
  - **成稿后用 `audit_anchors.py` 做全量锚点审计**（`--root /home/book/aosp13`，要求 n/n 全过；判卷规则、跨版本行号迁移步骤与 `cm` 自注/缩写块/裸行号的补查清单见 [references/anchor-migration.md](references/anchor-migration.md)）。
   - 写「某字段/回调负责 X」前先 `grep -rn "<getter>" frameworks/base --include=*.java --include=*.kt` 找消费者，零命中就写成预留管道并指出真正生效的那条路（如 PiP 回调走 windowingMode 配置变化），不要给 WCT 字段安一个不存在的消费者。
  - source-map 已含本节高频锚点，直接照用：build 两趟遍历、root 身份与 mChildren 存储、addWindow 插树时序、addWindow→relayout→首帧上屏、运行时遍历堆栈。讲 root 时分清**虚拟 PendingArea root（:458，不落地）与真实 mRoot/DisplayContent（构造传入，非 builder 挂载）**；讲挂树时强调 addWindow 只造逻辑节点、relayout 才造 Surface。
3.5 回答“怎么从 X 走到 Y / 全景太笼统 / 执行 X 之后发生了什么”这类问题时，给**带 文件:行号 的完整编号调用堆栈**，不要只列几个方法名当“全景”（用户明确反馈过方法名清单看不出代码全貌）：
   - 问“执行 X 之后 / 讲重点”时先一句结论（如“API 返回只是受理，状态未生效”），再按生效时间列 3–6 个重点，每条一句机制 + 一个 `文件:行号` 锚点；不重列入口校验和整条调用链，结尾给验证判据（`dumpsys` 字段、回调名、logcat tag），不以返回值为结论。
   - 每一级都先 `grep -n` 核实方法名与行号；堆栈里必须标出三种“接力边界”，否则读者顺着读会断：**同线程直接调用**、**Handler.post 到 Animation 线程异步执行**（如 requestTraversal→Traverser.run）、**跨进程序列化/等 VSYNC**（closeSurfaceTransaction→SF，及 SF 的 INVALIDATE→REFRESH）。
   - 逐窗口的活都藏在 `forAllWindows` 的 DFS 递归里，写堆栈要展开到回调体（mPerformLayout / mApplySurfaceChangesTransaction），不能停在 forAllWindows。
   - 已核实的“窗口变了→屏幕变了”完整堆栈定位见 [references/aosp12-source-map.md](references/aosp12-source-map.md) 的“运行时遍历完整调用堆栈”节，直接照用、不必重新逐行 grep。
   - 用户指着既有篇里某条箭头问“X 到 Y 中间发生了什么”时，先按 `<h2>` 抽出该图所在章节并去标签读原文，再 grep 源码把图里合并掉的分支拆开；回答开头先点明“图是压缩路径”，再给每个入口的真实分支。窗口刷新图要区分：`relayoutWindow` 标脏后直接 `performSurfacePlacement(true)` 强制同步结算，不直接调用 `requestTraversal()`；`addWindow/removeWindow/动画` 才走 `requestTraversal()` 投递动画线程。强制结算内部若 `RootWindowContainer.isLayoutNeeded()` 仍为 true，`WindowSurfacePlacer.performSurfacePlacementLoop()` 会调用 `requestTraversal()` 再排一轮（最多 6 轮），所以 trace 里可能看到 `relayoutWindow → performSurfacePlacement → requestTraversal` 的间接栈，不要答成直接调用。`mWindowsChanged` 只服务输入/监听，布局脏是 `mLayoutNeeded`（锚点见 source-map「脏标记链」）。
3.6 交互模拟器（现名 `DisplayArea构建算法演示.html`）的改与答：
   - 被问「第 N 步 / 最后一步树长什么样」时，把演示的常量、步骤表与 applyStep/Pass 逻辑抽成 `D:\openclaw\tmp\*.mjs`（去掉 DOM）用 node 重跑，树打印到文件再 read；不要凭截图或记忆描述某一帧。输出用 ASCII 分支符 `|--` / `\--`，`├─`/`└─` 经 exec→文件→read 会按 GBK 解成乱码。先打印节点计数（featureArea/Tokens/TDA/占位）与演示统计对账，再给树。
   - 演示头部标注的基线版本与用户基线不同时（如 AOSP12 r32），先用 13 树核对同类常量（`DisplayAreaPolicyBuilder.typeOfLayer()` 的 `LEAF_TYPE_*`、feature 列表、`APPLICATION_LAYER`）再答，并说明差异；单 TDA、无 DisplayAreaGroup 时 12/13 树形一致。
   - 改模拟逻辑时必须与源码逐行等价（用户会逐条揪语义偏差，锚点见 source-map「两趟遍历精确锚点」）：
   - 初始全部槽位指向**同一个 root 对象**（等价 `Arrays.fill`），不能每槽建独立对象，否则 Pass 1 分段全散。
   - Pass 1 新建 PendingArea 的 parent 取**当前** `areaForLayer[layer]`，随后槽位回写为新节点。
   - **Pass 2 不回写槽位**：只往槽位节点的 children 挂 Tokens leaf（源码 :494-522 无 `areaForLayer[layer] = leaf`）；末尾槽位仍是 Pass 1 终态的 feature 节点，例外是无任何 feature 覆盖的最高层（rounded corner，layer 36）直接挂 root。
   - 「同一 PendingArea」分段用**对象引用身份**判定，不用 layer 范围字符串。相邻分段间无空列时（border-collapse 会让两框粘成一个）在格上加 3px 深色割线。
   - 渲染验证用 Edge headless 截图；本机实测可直接传中文 `file://` 路径，只有报 `ERR_FILE_NOT_FOUND` 时才复制到 ASCII 路径。截图文件大小可粗判是否真渲染。**副本用 Python `shutil.copyfile` 生成**——PowerShell `-File` 读中文路径按 ANSI 解析会乱码（实测报“找不到路径 …绐楀彛灞傜骇”），Python 路径处理可靠；视觉核验时把 PNG 先拷进工作区再 `view_image`（`%TEMP%` 不在允许目录会被拒）。Python 生成并注入 `<script>` 时闭合标签写 `'<'+'/script>'` 拼接——`"</script>"` 写成 `"<\/script>"` 在 Python 字符串里是字面反斜杠，浏览器不认闭合、注入静默失效。视觉核验可派视觉模型子代理读图。
3.7 源码讲解的排版（用户硬要求，2026-10-14 连续两轮纠正）：逐行/逐块讲代码时，讲解文字写成**代码块内部对应那一行的行内注释**，不要把逐行讲解写成代码块下面的段落；每个代码块**下方只放总结性文字**。用户原话：“代码旁边写注释，不要写在代码段落下面，总结性的文字写在代码段落下面”。该要求与模型无关（用户换模型后要求“重新回答”，格式仍需一致），违反会被整篇打回重答。行内注释里带 `文件:行号`（如 `// WindowManagerGlobal.java:389`）方便用户对源码；长代码分多块时每块独立：代码（行内注释）+ 下方小结。树块或代码块下方的小结围绕「这段代码在做什么」和「为什么这样设计」这两个中心写，但不要把这两个中心写成标签、加粗引导或小标题（不出现「这段在干什么：」「设计意图：」），用连贯段落自然带出；章节名只写功能或方法名，不写这两个词。
3.8 概念/数量关系类问答（"为什么一个 X 有多个 Y""X 是不是 Y 的一部分""一个 app 不是只有一个 token 吗"）按此顺序讲，2026-10-18 用户对"一个进程为什么有多个 AR"连问三轮才通，跳步会被听成自相矛盾：
   - **先定位对象住在哪个进程，再讲数量关系**：第一句就用已核实字段点明 Activity 对象在 app 进程、ActivityRecord/WindowToken 在 system_server（AR 的 `app` 字段只是引用，进程死了 `detachFromProcess()` 置 null、AR 留在 Task）。
   - **先拆维度再给数字**：进程维度 = Session（一进程一个），窗口归属维度 = WindowToken（按 IBinder，挂 DisplayContent.mTokenMap，一进程名下可多张）；"一个 Activity 严格一个 AR，多个 AR 是因为多个页面同时存活（跳转不 finish、只 onStop）"。纠正错误前提时点明错在哪个维度，不要只堆反例。
   - **一句最小因果句 + 一个类比收尾**：浏览器多标签页（进程=浏览器、Activity=标签页、AR=系统侧标签记录）、房子/房间/房本已验证有效；先甩一行源码证据（如 ActivityThread.mActivities 是 Map 而 mInitialApplication 单例）再讲道理。
3.9 短答与“动态演示”请求：用户说“简短些 / 少于 500 字 / 尽量少字数”时，先给一句结论，再 3–4 条要点（类+方法+行号随行），结尾一句设计含义；不贴长代码、不套四要素模板、不追问落盘。用户要“HTML 动态演示”讲机制时，写单文件步骤演示到 `D:\openclaw\demos\<topic>.html`：STEPS 数组 + setStep() 状态机，chips 步进 + 上一步/下一步 + ← → 键；左侧设备/图层预览，右侧层级树与参与方指示灯；写完用 `Start-Process <file>` 打开（browser 工具只接受 http(s)），并告知绝对路径。
3.10 用户问「某特性属于哪个模块」「X 是什么 / 它负责什么」（WM Shell、某个 Shell 库、某个 manager），或「我要写文档但不知道归谁」时，先取证再答，不按进程印象作答；完整步骤与已核实锚点见 [references/component-attribution.md](references/component-attribution.md)。三条硬约束：
   - 包路径先 `ls` / `find . -name '<Class>.java'` 验证（`TaskOrganizer` 在 `core/java/android/window/`，不在 `android/wm/shell`；PiP 在 `libs/WindowManager/Shell/.../pip/`，不在 SystemUI），按进程印象答「SystemUI 的功能」就错。
   - 锚点与文章基线同树：只写 `/home/book/aosp13` 里存在的符号，引用前先 `grep -n`；12 树特有的写法不写进 13 系列。
   - 答篇目前先 `ls <系列目录>` 与 `index.html` 里的 `href="android-window-`：篇号会跳号（13/14 已发布，11/12 未发布），已有篇只给文件名、标签与阅读顺序，不另起号。
   - 交付：归属表（逐层写进程与代表类）+ 推荐篇号 + 可直接放文章开头的定位段。
   - 解释类名与术语时保留英文原名、中文只补一句职责；`-er` 结尾的 `Handler`/`Executor` 一律译“处理器/执行者”，"句柄"只留给 native 资源标识（`SurfaceControl`、`IBinder` handle、fd），因为把 `ClientTransactionHandler` 这类能力接口译成句柄会让读者以为它指向某个对象（12 树 `ClientTransactionHandler.java:39` 的类注释就是“定义能对客户端执行哪些操作”）。

4. 写新篇（标题、系列条、页脚一律按 [references/series-layout.md](references/series-layout.md) 的命名表与模板，别各篇自行造句）：
   - **落盘口令路由（用户硬要求）**：文章已在会话里输出、用户说「落盘/出稿/生成 HTML」时，**直接把正式篇写入目标目录**——当场续编号，一次做完步骤 5 的 footer/index/路线图两版更新，**不再先生成 `_draft`、不再等第二道「正式落盘」命令**；写完跑步骤 7 校验并开浏览器。`_draft` 只在两种情况下使用：用户明确说「先出草稿/先写了我自己改」，或步骤 4.5 的批量「都出稿」场景。
   - 写作模板与组件规范用系列目录下的 `层级树.md`（概念先行、类比框/步骤框/思考框、九节结构等）。
   - 框架级渲染/上屏专题用 [references/render-pipeline-outline.md](references/render-pipeline-outline.md) 的骨架；初始化、驱动、方法表、稳态闭环四块缺一不可；且自包含：0.0 名词表、前篇只作延伸阅读。
   - 样式直接沿用 02/03 篇：内联 CSS、CSS 变量双主题、右下角主题切换按钮、toc、card/code-block/annotation/step-box，不依赖任何外部 JS/CSS。
   - 概念篇不贴超过 3 行代码；源码篇才放带行号定位的代码块。
   - 长文分段落盘，不要在一条回复里贴整篇 HTML：先用 write 写 head + 骨架，再用 edit 分章节追加（每段控制在约 1 万 token 内）。整篇一次输出会撞模型输出上限被截断（见坑），分段落盘则任何中断都不丢已写内容。
   - **默认串行自己写、每完成一段就落盘**（分段落盘本身能抗中断）：长篇源码文章（几十 KB、需逐处 grep）产出周期 > 2 分钟、界面看不到文件变化，用户见没动静就会中断，而**父会话 abort 会级联杀掉全部子代理**（日志 `mutationKind=subagent-kill`，实测就这样丢了 3 篇草稿，`_draft` 里不留任何产出）——串行是唯一能真正保住产出的做法。
   - 仅在用户明确表示「不着急、可以等」时才用子代理并行（每篇一个，可 `context:"isolated"`；**长会话里 `context:"fork"` 会失败**，父上下文 270K > 100K 上限实测自动退化为 isolated），且先跟用户说清「要等几分钟，中途别点停止」。**格式铁律与锚点清单必须写进子代理任务**，否则会被整篇打回：显式带上步骤 3.7 的「行内注释 + 代码块下方只放总结」要求、单块 ≤40 行、省略分支占位写法、**不放上/下篇链接与下篇预告、不碰 index.html 与正式目录**、只写 `_draft` 绝对路径、要核实的锚点清单（从 source-map 抄）；并要求它自己跑 HTMLParser 校验 + ASCII 副本截图。
4.5 用户说「都落盘 / 全部出稿 / 都写了以后改」时，按批量阶段一出稿，不要逐篇追问：
   - 建 `<系列目录>\_build\bodies` 与 `_draft`；从最近一篇正式篇提取样式：`py -3.12 scripts/extract_series_style.py --source <最近的正式篇> --build-dir <系列>\_build --storage-key <该系列键>`。它生成 `base.html`（占位 `{{TITLE}}`/`{{CSS}}`/`{{CONTENT}}`/`{{THEME}}`）、`css.txt`、`theme.txt`，并补上符号字体回退。
   - 每篇正文写成 `_build\bodies_NN_MM.py` 的 `ARTICLES` 列表（`order/slug/title/subtitle/series/toc/body`）；代码块用 `html.escape` 包装，避免 `<`/`>` 破坏 HTML。
   - 一次构建：`py -3.12 scripts/build_series_drafts.py --build-dir <系列>\_build --out-dir <系列>\_draft`。文件名固定 `draft-YYYY-MM-DD-<slug>.html`，不带系列编号；阶段一不碰 index、不写正式目录。
   - 构建脚本的 f-string 表达式含 `\n` 等反斜杠时用 `py -3.12` 运行；3.11 会报 `f-string expression part cannot include a backslash`，或把代码块先赋给变量再插入。
   - 生成后统一跑：HTMLParser 标签栈、TOC `href` 与 `id` 对齐、`.filename` 的 `path:line` 存在性审计（WSL 循环 `[ -f ]` + `wc -l`），并对 00、中段合成篇、排障篇做 Edge headless 截图；全部通过再汇报通过数/总数。
   - 在 `_draft\README.md` 写顺序/主题/源码入口表，方便用户分批修改；阶段二仍以用户改过的临时稿为唯一准稿。
   - 汇报时给 `_draft` 的绝对目录并让用户从该目录打开；聊天里只列 basename 会被 Control UI 当会话文件链接解析，构建脚本经 exec 生成的 HTML 不在会话「已更改」索引里，点开常报 `session file not found`。要给可点路径就写完整路径，或直接开目录，不要让用户以为文件没生成。

5. 收尾三处链接，缺一不可（文本用命名表里的短名，逐字一致）：
   - 新篇 footer 的 prev/next（页脚整块模板见 series-layout.md 第三节）；
   - 上一篇 footer 的"下篇预告"；
   - `index.html` 的篇章卡片、学习路线与底部"下一篇"说明。
   - 若新篇占用/顺延了路线图里的计划篇号，`WMS学习路线图.md` 与 `android-window-roadmap.html` **两版的阶段-篇号映射一起改**（例：07+ 整体顺延）。
   - 相邻篇的「下篇」链接要同时改显示文字与 `href`：只换文字会留下指向旧文件名的 href，`check_html.py` 报「站内链接目标不存在」。
   - 改完对成品、`index.html`、相邻篇三个文件各跑一次 `check_html.py`，确认新增卡片与上下篇链接、页内锚点全部命中；再用 `Select-String -Path <系列目录>\*.html,<系列目录>\*.md -Pattern '<旧文件名>'` 确认旧名 0 命中。
6. 完成判据：新文件无外部依赖可直接打开；index 导航能点到新篇；文中引用的每个源码符号都经过 grep 核实。
7. 标签闭合用 Python 栈式解析器核验，不要数正则：
   - 用 `html.parser.HTMLParser` 跟踪 start/end 标签栈（忽略 void 标签 meta/br/img/hr/link/input），报错位和未闭合标签。
   - **坑（实测）**：用 `<regex> 数 `<div>` vs `</div>` 会因多行/自闭合/属性换行得到假的不平衡（曾报 52 开 / 28 闭，实际完全闭合）。以 HTMLParser 栈结果为准，别据正则计数去“补标签”。
   - **交互式工具页（粘贴 dump/logcat → 解析 → 结论）要连解析逻辑一起验**，只截图证明不了结论对不对：页面里留 `if (location.hash === '#selftest')` 分支，载入内置示例后把结论写进 `document.title`（如 `SELFTEST|high|4`），再跑 `msedge --headless=new --disable-gpu --dump-dom "file:///D:/openclaw/tmp/x.html#selftest"` 并 `Select-String '<title>'` 断言；`--dump-dom` 里的中文是乱码，只断言 ASCII 片段，文案与版式靠截图核验。页面必须带「载入示例」按钮，让用户不开真实日志也能验证工具本身。
     - **时间相关性不要做全量交叉配对**：每条结论绑定被配对事件的下标（如转场事件的 `event.i`），同一目标事件只出一条结论、只留最近一条证据；否则 setWallpaper×transition 的双重循环会产出两条一模一样的结论，SELFTEST 条数虚高。示例数据必须能触发至少一条 `high`，条数为 0 说明字段名或判定规则没命中，先修再交付。
     - 单页双输入（dump + logcat）时两侧各自独立降级：缺 dump 只跳过窗口侧结论、缺 logcat 只跳过时序结论，并在结论区写“已跳过”，不要整页报错。
   - 渲染验证用 Edge headless 截图：路径含空格（系列目录在 `Android framework\` 下）时 `-Uri` 会被拆成多参数，报 `Multiple targets are not supported in headless mode` 且 `-Path` 绑空——先把成品复制到无空格路径（如 `D:\openclaw\tmp\shotpage.html`，页面自包含）再截图；中文但无空格的路径可直接传。headless 不可用时以解析器做合法性校验，并在汇报里说明未做真实浏览器渲染。
   - **长文整页截图必须分段看**：长文章的全页 PNG 常超 1 万像素高，整图丢进 view_image 会被缩到无法辨认代码块是否溢出。用 PIL 按高度切成 2500–3000px 高的横带（`Image.open(p).crop((0,y0,w,y1))`，宽度取图宽），至少看首/中/尾三带，逐带检查：暖色纸张非白底、代码块无横向溢出、树块缩进完整、表格不裁切、无占位或乱码；检查清单写进给视觉模型的 prompt。临时截图放 `D:\openclaw\tmp\`（允许目录），看完即删。
   - **可复用校验脚本已落盘 `_build\verify_series.py`**：一次跑完标签栈闭合 + 全目录 href 可达性 + 逐篇 title/h1/系列条/页脚一致性。批量重排或改多篇时直接跑它，不必每次重写；一次性脚本写完即删，**只把可复用的留在 `_build\`，不要留在文章目录**。
   - **脚本顶部 `ROOT` 是硬编码的**：系列目录搬动后直接跑会 `FileNotFoundError`（2026-10-19 实测旧路径 `D:\openclaw\Android窗口层级` 已失效）；跑前先按实探路径改 `ROOT`，或改成按脚本自身位置推导。

## 坑（实测）

完整清单见 [references/pitfalls.md](references/pitfalls.md)：WSL 长输出被截断（先导出行段再读）、改稿前备份、card 重复闭合、批量改 id 用 re.sub、`wsl -e bash -c` 引号坑、`timeoutSeconds` 拼写、maxTokens 默认 8192 导致整篇被截断。

## 用户硬要求（2026-10-20 渲染篇修订后固化）

写/改本系列（尤其框架级渲染篇）时，以下优先级高于默认模板：

1. **源码先核实再下笔**：任何 `Class.method():line` 先在 AOSP 13 树 `grep -n` 确认（12 树只作差异对照）；禁止凭“应该有这个 API”写方法名。反例：`SurfaceFlinger::create()` 不存在，实际是 `main_surfaceflinger.cpp:130` → `createSurfaceFlinger()`（`SurfaceFlingerFactory.cpp:26`）→ `onFirstRef():491` → `init():774`。成稿后按 source-map 锚点逐条 `grep -n` 复核，汇报“通过数/总数”（一次性脚本跑完即删，不留在文章目录）。
2. **调用顺序用属性风格树**：有调用链的地方写成 `├─/└─` 缩进树，节点后右对齐 `[文件:行号]`，每行节点后都写 `//` 注释说明这一层做什么（不能只给关键分支写）；不要用“A → B → C”长句或 step-box 堆叠。缩进树只在同一行内对齐时可靠；画「两条线汇进一个节点」（如 WMS 与 ATMS 两个字段指向同一个 RootWindowContainer）或任何跨行竖线对齐时改用 CSS 结构：所有者卡片 + 合并说明 + `border-left` 主干配 `::before` 横齿的节点链，中文全角与差一列会让 `┐ ┘ │` 错位、重排空格修不好；改完截图核验明暗两主题。用户要求只保留调用树时，删除代码块，只留树；树块用柔和墨色（深色主题约 `#2f3540`，浅色主题暖纸色），不要纯黑，配圆角、内边距和细边框。章节按功能或入口函数拆分，一章一个功能；每章先给调用树，再用连贯段落写这一层做什么、为什么这样设计。
3. **美术风格**：禁止纯白背景。默认暖色纸张（米/驼色渐变 + 细纸纹）、柔和墨色目录与调用树（深色主题约 `#2f3540`，浅色主题暖纸色，不要纯黑）、赤陶色强调、衬线标题、暖米色表格；新篇必须用 Edge headless 对 ASCII 副本截图，确认不是白底、树块无溢出。具体组件、摘要卡与树-only 改造步骤见 [references/article-visual-polish.md](references/article-visual-polish.md)。
4. **有头有尾**：从“初始化”讲起（系统/进程/对象谁创建），中段写“每个方法做什么、谁调它、下一步是谁”，结尾落到“稳态闭环”（点击/动画/重绘如何驱动下一帧）；不要只从中段 `draw()` 开始。**渲染/上屏篇的中段必须写到实际执行者**：`performTraversals → performDraw → ThreadedRenderer.draw → syncAndDrawFrame → DrawFrameTask → RenderThread → CanvasContext.draw → queueBuffer`；只停在 Choreographer/performTraversals 视为“没讲驱动”（2026-10-20 验收反馈）。
5. **独立成篇**：用户说“不要受前面的影响/从这篇文章开始讲”时，不假设读者读过前篇；开头用 0.0 名词表定义 View/WindowState/Surface/SurfaceControl/Layer/Buffer/Transaction/VSYNC/Choreographer/WMS/SF/BLAST，删除“见 0X 篇”前置依赖，前篇只放延伸阅读。
6. **方法与注释**：长文必须有“方法逐个看”表（方法/类/谁调它/作用/下一步）；代码块和调用树都要有行内注释，写 why（为什么在这里/为什么这个顺序），总结只放块下方。
7. **追问写回文章**：用户针对已有文章追问某个机制时，把答案补进对应章节并重建、校验、告知路径，不要只在聊天里回答；用户说“你写进去啊”就是本条的显式触发。用户指出某句注释或措辞不准时，先按源码核实该函数体与消费者，再在该文档搜同一措辞的所有出现（正文、其他代码块、其他小节）逐处改成源码语义，复查计数为 0；用户要求删掉某主题（“把 X 的内容去掉/删了这节”）时：先按关键词变体全量扫描（中文名、缩写、全类名、flag 名，如 PiP / 画中画 / PictureInPicture / pinned），把命中位置列表化再动手，因为同一主题常散落在系列条、表格示例、独立小节、坑表、页脚导航五处；整节删除用「起始标题字符串 → 结束注解字符串」切片（Python find/index），不用行号；其余位置的引用改写成同义替代而不是留空；改完把 ≤3 个连续空行归一、跑标签平衡与残留计数（应全为 0）、再截首屏确认该节后面紧跟的标题未落空。
8. **反引号清零**：HTML 正文与表格用 `<code>`，不要留 Markdown 反引号；成稿后统计 `<pre>` 外反引号必须为 0，否则页面会显示字面反引号。
9. **行号范围与代码块内容对齐**：`.filename` 写 `File:start-end` 时，块内必须覆盖该范围的关键代码；裁剪用 `// … 省略` 标出，不能用 4 行范围包 7 行代码。成稿抽查每个代码块首尾行。
10. **开篇先讲清定位**：第一块代码或第一节之前，用**一段连贯的话**交代背景，覆盖四个方向——这是什么（所属子系统/层、解决什么问题）、有什么用/用在哪（开发、ROM 定制、线上排障）、设计思想（1-2 个关键取舍，附一句反向设计会怎样）、机制骨架（3-6 个真实参与者 + 起点→终点主流程）。这四个方向是这段话的写作内容，不是四个小标题、不是四条 bullet，不要出现「这是什么：」「设计思想：」「机制骨架：」这类标签。独立成篇时放在 0.0 名词表之前；骨架里的类名、线程名同样先 grep 核实。
11. **篇幅随复杂度伸缩**：单方法、单标志位、纯 getter 这类简单问题用 3-8 句加必要的 3-5 行代码答完，不套四要素、方法表、思考题、下一步或落盘追问；只有跨模块、状态机、整站主题才走长文骨架。删掉任一模板项答案仍完整，就删掉该项。
12. **正文按数据流或事件流推进**：先判定链路类型（数据流：buffer、transaction、输入事件逐跳加工；事件流：生命周期、状态机、焦点变化），按“起点→每跳形态或状态变化→终点”排序，代码块编号即流经顺序（如 `块A｜第1跳`）。分叉与回环显式画出，不按文件或类顺序罗列；每块开头交代进入时的形态，结尾交代出去后的形态。
13. **自测题只出判据题**：每题写成「症状 → 可执行命令 → 判据表 → 一句归因」，答案必须能靠 `logcat` / `dumpsys` / `am` 的真实输出判定；不要出「哪个调用点是优化」「realStart 从哪个入口进来」这类背机制题，它们只验记忆、现场用不上，会被用户当成扣概念。
