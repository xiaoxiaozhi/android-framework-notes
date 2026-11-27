# 系列版式标准（标题命名表 · 系列条 · 页脚 · 重排流程）

用途：写新篇、落盘临时稿、或用户要求「重新排版 / 标题和内容对齐 / 文章要有连续性」时照此执行。
目标是两条：**标题与内容对齐**、**全系列读起来是一条连续主线**。

## 一、权威命名表（所有位置逐字一致）

每篇的 `<title>`、`<h1>`、顶部系列条、页脚、index 卡片标题、上下篇链接文本，**必须用同一句标题**；
上下篇链接用括号里的「短名」即可（保持一行不被撑爆）。

| 篇 | 文件 | 标题（长名） | 短名 |
|---|---|---|---|
| 00 | 00-窗口为什么是一棵树.html | 窗口为什么是一棵树：DisplayArea 层级入门 | 窗口为什么是一棵树 |
| 01 | 01-窗口树全景.html | 窗口树全景：WindowContainer 家族、Z 序与 Token | 窗口树全景 |
| 02 | 02-窗口树的构建算法.html | 窗口树是怎样建起来的：DisplayAreaPolicyBuilder 构建算法 | 窗口树是怎样建起来的 |
| 03 | 03-窗口刷新与事务提交.html | 窗口刷新：布局、Z 序与事务提交 | 窗口刷新 |
| 04 | 04-像素怎样上屏.html | 像素怎样上屏：SurfaceControl、BLAST 与 SurfaceFlinger 合成 | 像素怎样上屏 |
| 05 | 05-输入分发与窗口命中.html | 输入事件的分发与窗口命中：InputDispatcher 全链路 | 输入事件的分发与窗口命中 |
| 06 | 06-窗口的诞生.html | 窗口的诞生：从 addView 到窗口上树 | 窗口的诞生 |
| 07 | 07-窗口的来路与归途.html | 窗口的来路与归途：Activity 启动链与窗口生命周期 | 窗口的来路与归途 |
| 08 | 08-窗口的尺寸与身体.html | 窗口的尺寸与身体：布局、Insets 与旋转 | 窗口的尺寸与身体 |
| 09 | 09-窗口动画与过渡.html | 窗口动画与过渡：AppTransition 与 leash 缰绳 | 窗口动画与过渡 |
| 10 | 10-显示子系统的节拍.html | 显示子系统的节拍：vsync 与 Choreographer | vsync 与 Choreographer |
| 13 | 13-画中画.html | 画中画 PiP：一次跨 ATMS / WMCore / WM Shell 的窗口模式迁移 | 画中画 |
| 14 | 14-图层是什么.html | Winscope 里的图层是什么：Layer、名字、id 与树→图层 | 图层是什么 |
| 🗺️ | WMS学习路线图.html | WMS 系统学习路线图 | 学习路线图 |

- 文件名统一为 `<篇号>-<中文短名>.html`，新篇按同一形式起名；`index.html` 保持英文名（浏览器与 live-server 的目录默认页），`WMS学习路线图.html` 与 `WMS学习路线图.md` 同名成对。
- `title` 形如 `<长名>（WMS 学习 0X）`；`h1` 形如 `<emoji> <长名>`（emoji：00/01 🌳、02 🏗️、03 🖥️、04 🎞️、05 👆、06 🪟、07 🔄、08 📐、09 🎬）。
- **非系列的框架级专题**（不占系列编号、不放进系列目录、不入本表编号列）：Binder 篇 = `D:\openclaw\Android framework\android-framework-binder.html`（长名「Binder 全链路：一次跨进程调用到底做了什么」，🔗）。它的系列条写「Android Framework 专题 · Binder 篇 ｜ … ｜ 🌳 窗口层级系列」，页脚链回系列 index 与两份路线图。
  - 渲染篇 = `D:\openclaw\Android framework\android-framework-render-pipeline.html`（长名「渲染是什么：从编舞者 Choreographer 到屏幕上的像素」；系列条写「Android Framework 专题 · 渲染篇」，页脚链回窗口系列 index 与 04）。
  - ATMS 篇 = `D:\openclaw\Android framework\android-framework-atms.html`（长名「ATMS 是什么：ActivityTaskManagerService 的职责、结构与四条入口」；系列条写「Android Framework 专题 · ATMS 篇」）。它横切 07 启动链与 12 多显示，所以不占系列编号；07 的系列条已加「配套深读」链过去。篇内只写 ATMS 自身的边界与结构，PiP、分屏的具体编排归 13 与 12 篇，不在这篇复述。
- **已发布篇号的阶段映射**：阶段 2 生命周期 = **06–07 篇**、阶段 3 = 08、阶段 4 = 09、阶段 4+ = **10（vsync 与 Choreographer）**、阶段 5 = **11（IME/壁纸，下一站）**、阶段 6 = **12（多屏多窗，按需）**。改篇号时 `.md` 与 `.html` 两版同步，含阶段卡片、章节序号（七/八/九）、周计划表。
- 冲突时以本表为准；改表要同步改全部位置（含 index 卡片与两份路线图）。
- 改文件名时按「旧名 → 新名」映射表整目录替换（Python 读 UTF-8、替换后写回），再跑一次 href 可达性检查，缺失必须为 0。

## 二、顶部系列条（每篇 h1/subtitle 之后一行）

```html
<p class="series">📚 Android 窗口层级专题 0X ｜ 基于 <code>android-12.0.0_r32</code> ｜ 上篇：<a href="上篇文件">← 0X-1 短名</a> ｜ 下篇：<a href="下篇文件">0X+1 短名 →</a></p>
```

- 00 篇没有上篇，写「起点篇（你从这开始）」；06 的下篇是 `<a href="WMS学习路线图.html">🗺️ 学习路线图 →</a>`。
- 依赖 `.series { color:var(--accent3); font-size:.85rem; margin-bottom:24px; }` 这条 CSS；老篇若缺就补进 `</style>` 前。

## 三、页脚块（每篇统一一块，替换时整块换）

```html
<div style="margin-top:50px; padding:20px 0; border-top:1px solid var(--border); text-align:center; color:var(--text2); font-size:.85rem;">
  <p>📚 Android 窗口层级专题 | <strong>0X — 长名</strong></p>
  <p>基于 AOSP 12（android-12.0.0_r32）· WSL 路径 <code>/home/book/aosp12/frameworks/</code> · 行号随文现地核实</p>
  <p style="margin-top:10px;">← 0X-1 短名 &nbsp;|&nbsp; <strong>0X 短名 ← 你在这</strong> &nbsp;|&nbsp; 0X+1 短名 →</p>
  <p style="margin-top:8px;"><a href="index.html">🏠 系列导航</a> &nbsp;|&nbsp; <a href="WMS学习路线图.html">🗺️ 学习路线图</a></p>
  <p style="margin-top:8px; color:var(--accent3);">📌 下篇预告：…</p>
</div>
```

- 旧的「后面一串 ← 03 ← 02 ← 01」式导航要改成「上篇 ｜ 你在这 ｜ 下篇」（用户要的是连续主线，不是索引堆叠）。

## 四、重排/统一流程

1. **先备份**：把要改的 html/index/路线图整体拷进 `_build\backup-<日期>\`（存在即跳过），再动原文件。
2. **改前先审计**：抽全部 `<title>` / `<h1>` / `<h2>` / 系列条 / 页脚，和上面命名表逐条比对，列出「不一致项」再动手（`_build\audit_layout.py` 是同类脚本，可按需改）。
3. **统一**：按命名表改 title/h1/系列条/页脚；`_build\relayout_series.py` 是已跑通的一次性脚本，直接改成目标文件清单复用即可。
4. **校验**（必做）：跑 `_build\verify_series.py`（脚本顶部 ROOT 硬编码；系列目录搬过后先按 SKILL.md 步骤 7 改成实探路径）—— ① `html.parser` 栈式标签闭合；② 全目录 `href` 可达性（缺失数为 0）；③ 逐篇打印 title/h1/系列条/页脚便于肉眼一致性检查；④ 06 篇专项检查（临时稿残词、TOC 与 h2 id 差集）。
5. **渲染抽检**：需要时用 Edge headless 对 ASCII 路径副本截图，`view_image` 核验首屏与页脚（做法见 SKILL.md 步骤 3.6 / 7）。

## 五、临时稿落盘为正式篇

`_draft\` 下的稿子按路线图**既有的计划篇号**入列，**不重排已发布篇号**（例：06 篇是路线图「阶段 2 生命周期」开篇，就占 06，07 顺延给「Activity/Task 启动链」）。

插入一个本来没排篇号的主题时，占下一个篇号并把**尚未发布**的计划篇号整体顺延一位；已发布篇号不动。系列内的新篇一律编号，不写「补篇」：用户会把无编号当成漏编号。顺延要同步命名表、两版路线图的阶段-篇号映射与阶段卡片、章节序号（如 IME 从「七」变「八」）、周计划表、index 学习路线那句话。

步骤：备份 → `shutil.copyfile` 成 `0X-<中文短名>.html` → 删掉临时稿提示块（`<div class="draft-note">` 整块 + 它那条 `.draft-note{}` CSS 规则与 `--draft-bg/--draft-border` 变量，块删了就是死代码）→ 改副标题去「临时稿」措辞 → title/h1/系列条/页脚统一（**按上面命名表生成，不要沿用草稿里那句「上承 X 篇…」的自造句**）→ 章节重编号 + TOC 文本与 `id`/`href` 同步 → 更新 index 卡片、上下篇、两份路线图篇号。

**落盘三处链接收尾（缺一即为断链）**：① 上一篇 footer 的「下篇预告」整句（含它的系列条右侧下篇链接）；② 新篇 footer 的 prev/next；③ `index.html` 卡片 + 底部「下一篇」说明 + 两份路线图。记着一并改 `index.html` 里描述路线图那句「（接续 00–0X 篇）」。

**落到系列目录之外（框架级专题）的额外一步**：Binder/渲染/ATMS 篇落在 `D:\openclaw\Android framework\`（系列目录的上层），落盘后必须改写它引用的相对路径——`WMS学习路线图.html` → `Android窗口层级/WMS学习路线图.html`、`index.html` → `Android窗口层级/index.html`、`../../Android-Framework学习路线图.html` → `../Android-Framework学习路线图.html`；改完跑一次全目录 `href` 可达性检查（缺失必须为 0）。

**批量落盘多篇时的顺序**：① 先一次性备份（`_build\backup-<日期>\`）；② 逐篇转换（去临时稿提示块，系列条/页脚/标题按命名表生成）；③ 再统一收尾跨篇链接（上一篇下篇预告、index 卡片与页脚、两份路线图阶段映射）；④ 最后跑 §4 的全目录校验（标签闭合 + href 可达 0 缺失 + 渲染抽检）。每步写成单独 `.py` 文件跑，便于某步失败后从断点重跑而不重复已完成动作。

**`_draft\` 里的旧稿不要删、也不要重复落盘**：它们留作用户改稿存档与回滚点。**判断「是否已落盘」只看系列目录（或框架层）里有没有对应正式篇目，不要看 `_draft\`**——稿子会一直躺在那里，据 `_draft\` 推断会得出「还没落盘」的错误结论。

## 六、坑（实测）

- **批量改锚点 id / 章节编号，绝不能用顺序 `replace`**：`p0→p1` 之后 `p1→p2` 会把刚改好的又改一遍，级联到最后一个 id（实测全塌成 `p7`）。正确做法是 `re.sub` + 计数器按文档序生成新编号（`_build\fix_ids.py` 是可复用的最小示例）。
- **编号与锚点要同一趟改**：只改 TOC 文本忘了 `id="pN"`/`href="#pN"`，点目录会跳错位。
- **删整节后必须重排编号并核对锚点**：删掉一节（如「关键代码」）后，后续 `<span class="num">`、顶部导航与页内目录的文案都要递补，`grep -n 'href="#s'` 逐条确认每个目标 `section id` 仍存在，死锚会让用户点到空白。
- **整块替换页脚**：在 `<script>` 之前取最后一个 `margin-top:50px`（老篇是 `36px`）锚点，再用 `<div>`/`</div>` 深度计数找块尾；不要用正则数 div 数量。
- **改结构的脚本一律写成 `.py` 文件跑**，不要在 pwsh 里用 `python -c` 单行（带括号/lambda/引号的会报 `“(”后应为表达式`）。
- 章节标题写的块数与实际块数要对齐（06 篇旧标题写「四块」实际五块，用户一眼看出——标题与内容对齐指的就是这类）。
