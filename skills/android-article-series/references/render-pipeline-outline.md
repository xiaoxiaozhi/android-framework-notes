# 框架级渲染/上屏专题文章骨架

用途：用户要一篇「渲染是什么 / Choreographer / 一帧怎么上屏」的框架级专题，或反馈现有渲染篇「没头没尾」。放在 `D:\openclaw\Android framework\`（系列目录上层），与 Binder 篇并列，不占系列编号。

**行号统一查同目录的 `aosp12-source-map.md` 的「渲染篇初始化与帧驱动」节；本文件只列顺序、验收点与版式，避免两处维护行号。**

## 用户验收点（2026-10-20）

- 必须从「最开始怎么初始化」讲起，不能从 `draw()` 开始。
- 必须讲「这套逻辑怎么驱动」，而且不能停在 Choreographer：`invalidate` / `requestLayout` → `scheduleTraversals` → `Choreographer` → VSYNC → `doTraversal` / `performTraversals` → **`performDraw` → `ThreadedRenderer.draw` → `syncAndDrawFrame` → `DrawFrameTask` → RenderThread → `CanvasContext.draw` → `queueBuffer`**；再写 SurfaceFlinger 自己的 VSYNC → `composite`。只讲到 Choreographer/performTraversals 视为没讲驱动。
- 讲 VSYNC 必须分清「物理源头 / 软件派发 / App 消费」：`Display Controller` 产生脉冲，HWC/`ComposerCallbackBridge` 上报，`SurfaceFlinger::onComposerHalVsync` → `HWComposer::onVsync` → `Scheduler`/`EventThread` 分发，App 的 `DisplayEventReceiver` → `Choreographer#onVsync` 消费；写明 `scheduleVsync()` 是订阅下一拍，不是产生 VSYNC。
- 必须逐个方法说明「谁调它 / 作用 / 下一步」，不能只列类名。
- 必须收尾到稳态：点击之后下一帧怎么来，形成闭环。
- **必须独立成篇、不依赖前篇**（2026-10-20 用户二次纠正）：开头放 0.0 名词表（View/WindowState/Surface/SurfaceControl/Layer/Buffer/Transaction/VSYNC/Choreographer/WMS/SurfaceFlinger/BLAST）；正文不写“前面几节”“见 03/04 篇”这类前置句；系列条/页脚标“独立成篇”，前篇只放“延伸阅读”，不是必读。用户原话：“不要受前面的影响，就从这篇文章开始讲。”

四块正文缺一不可；自包含是版式要求，不是可选加分项——缺了用户会判为「没头没尾」。

## 固定骨架

0.0 **先定名词（自包含）**：View / View 树、Window / WindowState、Surface、SurfaceControl、Layer、Buffer / GraphicBuffer、Transaction、VSYNC、Choreographer、WMS、SurfaceFlinger、BLAST。
0. **从开机到第一帧：初始化全景**
   - SurfaceFlinger：`onFirstRef()` → `init()`
   - `DisplayContent` 建 `"Root"` 容器图层
   - App 启动：`ActivityThread.main()` → `attach()` → `handleBindApplication()` → `handleResumeActivity()` → `WindowManagerGlobal.addView()` → `new ViewRootImpl()` → `setView()`
   - `setView`：`enableHardwareAcceleration()` → `ThreadedRenderer.create()`；`requestLayout()` → `scheduleTraversals()` → `Choreographer.postCallback()`
   - 第一帧：VSYNC → `Choreographer.doFrame()` → `doTraversal()` → `performTraversals()`
1. **渲染是什么**：View 树 / 窗口树 / Layer 树；录制 → 绘制 → 合成 → 上屏
2. **编舞者 Choreographer**：回调顺序 `INPUT → ANIMATION → INSETS_ANIMATION → TRAVERSAL → COMMIT`；`postCallback`、`scheduleFrameLocked`、`doFrame`、`onVsync`
3. **驱动机制（必须写到实际执行者）**：`invalidate` / `requestLayout` → `scheduleTraversals` → VSYNC → `doTraversal` → `performTraversals` → `performDraw` → `ThreadedRenderer.draw` → `syncAndDrawFrame` → `DrawFrameTask` → RenderThread → `CanvasContext.draw` → `swapBuffers/queueBuffer`；再写 SurfaceFlinger 自己的 VSYNC → `composite`。明确三句话：**Choreographer 只调度、不画像素；RenderThread 才是绘制执行者；SurfaceFlinger 是合成上屏者。** 两套循环靠 BLAST 事务对齐。
4. **角色表**：类 / 进程 / 职责 / 入口
5. **方法逐个看**：三张表（初始化与调度、布局与绘制、窗口与合成），每行写「谁调它 / 作用 / 下一步」
6. **App 侧**：`performTraversals` → `performMeasure` / `performLayout` / `performDraw` → `ThreadedRenderer.draw` → `updateRootDisplayList` → `RenderNode.beginRecording` / `endRecording` → `syncAndDrawFrame`
7. **Buffer 过河**：`BLASTBufferQueue.onFrameAvailable` → SF `commitTransaction`
8. **层级树渲染**：每个 `WindowState` → `BufferStateLayer`；WMS `relayoutWindow` → `createSurfaceControl` → `WindowStateAnimator.createSurfaceLocked` → `WindowSurfaceController` → SF `createLayer`
9. **合成上屏**：commit / composite / present（HWC 与 GPU 回退）
10. **完整时序**：VSYNC → Choreographer → traversal → draw → BLAST → SF → 面板扫描
11. **稳态**：点击 → `invalidate` / `requestLayout` → 下一帧；掉帧因果
12. **速查 + 自测**：类/方法速查表 + 5 题

## 完成判据

- 四块齐全：初始化 / 驱动 / 方法表 / 稳态闭环。
- **驱动链不能断在 Choreographer**：全文必须能指出 `performDraw` 之后谁执行绘制；至少出现 `ThreadedRenderer.draw`、`syncAndDrawFrame`、`DrawFrameTask`/`RenderThread`、`CanvasContext.draw`、`queueBuffer`。只写到 `performTraversals` 会被判“渲染是什么驱动的还没讲”（2026-10-20 验收反馈）。
- 自包含：有 0.0 名词表；全文搜索 `前面几节|见.*篇|配套：` 无命中（“延伸阅读”除外）；首节从初始化讲起，不假设读者读过窗口系列。
- 方法表每行有 caller + role + next；不是只列类名的「角色表」。
- 锚点全部来自 `references/aosp12-source-map.md` 或本轮 grep；不编行号。
- `html.parser` 0 错误；TOC 与 `<h2 id>` 全对齐；站内 href 0 缺失；Edge headless 截图验证。
- 文末给「三句话收尾」：节拍器 / 点火 / 合成。

## 版式

- 复用 04 篇的 `<style>` 与主题切换脚本；无外部依赖。
- 标题、系列条、页脚沿用 `references/series-layout.md` 的通用模板；框架级专题按“独立成篇”写：系列条/页脚标“独立成篇”，前篇链接只作“延伸阅读”，不排上下篇；站内链接用 `Android窗口层级/...` 相对路径。
- 框架级篇目在系列目录上层；8080 的根是系列目录，预览它要么 `file://`，要么另起一个以父目录为根的静态服务（如 8081），不要把父目录文件塞进系列根。
- 每节一个 `card`；初始化/驱动用 `step-box`；关键结论用 `annotation star3`；方法表用普通 `table`。
