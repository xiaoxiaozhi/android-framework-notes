# 显示子系统系列路线（AOSP 12 SP1A）

用户要学 Android 显示子系统、问「能写几篇」，或要写 SurfaceFlinger / BLAST / HWC / VSYNC 系列时用本路线。源码根 `/home/book/aosp12`，锚点先查 [aosp12-source-map.md](aosp12-source-map.md) 的「显示子系统锚点」节，缺口再 `grep -n`。

## 规模与篇目

**12 篇：8 篇主线（缺一篇链路断）+ 4 篇扩展。** 主线能独立闭环，扩展按岗位方向选写。

| 阶段 | 编号 | 篇目 | 主要源码入口 |
|---|---|---|---|
| 基础闭环 | 00 | 显示子系统全景：一帧像素的完整旅程 | `BufferQueueProducer.cpp`、`BLASTBufferQueue.cpp`、`SurfaceFlinger.cpp`、`HWComposer.cpp` |
| | 01 | SurfaceFlinger 启动与架构 | `main_surfaceflinger.cpp`、`SurfaceFlinger::init():774` |
| | 02 | BufferQueue / BLASTBufferQueue：Buffer 的生产-消费协议 | `BufferQueueProducer.cpp`、`BLASTBufferQueue.cpp` |
| 核心机制 | 03 | SurfaceControl 与 Transaction：跨进程事务 | `SurfaceComposerClient.cpp:820/1263`、`BLASTBufferQueue.cpp:389` |
| | 04 | Layer 与合成准备：从 Layer 到 OutputLayer | `Layer.cpp`、`BufferLayer.cpp`、`CompositionEngine` |
| | 05 | VSYNC 与帧调度 | `Scheduler/` 下先 `ls`，已确认 `DispSyncSource.cpp`、`EventThread.cpp`、`LayerHistory.cpp` |
| 合成上屏 | 06 | 合成：RenderEngine/GPU 与 HWC 的分工 | `frameworks/native/libs/renderengine/`、`SkiaGLRenderEngine.cpp:716`、`HWComposer::setClientTarget():459` |
| | 07 | 上屏：presentDisplay、fence 与刷新率 | `HWComposer::presentAndGetReleaseFences():566`、`DisplayMode` |
| 实战与专题 | 08 | 多屏与虚拟屏 | `DisplayManagerService.java:184`、`LogicalDisplayMapper.java`、`DisplayDevice.java` |
| | 09 | 实战排障：jank/黑屏/闪屏/冻屏 | `dumpsys SurfaceFlinger`、Perfetto/systrace |
| | 10 | 进阶：VRR/ARR、HDR/广色域 | `RefreshRateConfigs`、色彩管理接口 |
| | 11 | 进阶：RenderEngine 特效与 GPU 合成性能 | `frameworks/native/libs/renderengine/`、`SkiaGLRenderEngine.cpp:716`、blur/shadow 路径 |

## 切分与写作顺序

- **一跳一篇**：每篇必须能用 `文件:行号` 说明「进入时是什么形态、出去变成什么」，按主题名词凑数会写出无法闭环的篇。
- 先写 **00 → 01 → 02**：00 建地图，01 讲清 sf 进程怎么起来，02 讲 Buffer 协议；03–07 依赖这三篇的对象与术语。
- 00 只做全景，不重复 `android-framework-render-pipeline.html` 的 App 侧绘制细节；窗口篇 `android-window-04-surface-render.html` 是 WMS 视角，本系列从 native SF/HWC 视角往下钻。
- 05 不要凭高版本印象写 `VSyncDispatch`：先 `ls frameworks/native/services/surfaceflinger/Scheduler`，以当前树文件名和 `grep` 结果为准。

## 已核实锚点（按篇，AOSP 12 SP1A）

- 00 全景：`BufferQueueProducer.cpp:804`、`BLASTBufferQueue.cpp:546`、`SurfaceFlinger.cpp:2049`、`HWComposer.cpp:566`。
- 01 启动：`main_surfaceflinger.cpp:95`、`SurfaceFlinger.cpp:774`、`SurfaceFlinger.cpp:3151`。
- 02 BufferQueue：`BufferQueueProducer.cpp:379/804`、`BufferQueueConsumer.cpp:78/442`、`BLASTBufferQueue.cpp:797`。
- 03 Transaction：`SurfaceComposerClient.cpp:820/1263`、`BLASTBufferQueue.cpp:389`。
- 04 Layer：`Layer.cpp:537`、`Output.cpp:415/712`。
- 05 VSYNC（五跳全链，均已 grep 核实；只写 EventThread 中段会缺源头与 App 侧，按五跳组织）：
  - 跳1 硬件中断只采样不转发：`SurfaceFlinger.cpp:1718`（onComposerHalVsync，仅内屏做节拍源，调 addResyncSample）、`Scheduler.cpp:548`（addResyncSample 喂 VSyncTracker）、`Scheduler.cpp:83`（createVSyncDispatch 建 VSyncDispatchTimerQueue，timerSlack 500us、vsyncMoveThreshold 3ms）
  - 跳2 一个定时器变出双相位：`VSyncDispatchTimerQueue.cpp:268`（timerCallback 一次到期遍历全部注册者、锁外回调、rearmTimer）、`SurfaceFlinger.cpp:3179-3193`（createConnection "app"/"appSf"，workDuration=提前量：App=appWorkDuration、SF=整个 vsyncPeriod）、`MessageQueue.cpp:105`（SF 主线程以 "sf" 名直接注册 dispatch，不经 EventThread）
  - 跳3 App 挂号：`ViewRootImpl.java:2097`（scheduleTraversals 先 postSyncBarrier 再 postCallback TRAVERSAL）、`Choreographer.java:636`（scheduleFrameLocked，非 Looper 线程投 MSG_DO_SCHEDULE_VSYNC 异步消息）、`:880`（scheduleVsyncLocked）、`android_view_DisplayEventReceiver.cpp:208`（nativeScheduleVsync）
  - 跳4 按需闸门：`EventThread.cpp:184`（EventThreadConnection::requestNextVsync 一次性 Single）、`:353`（onVSyncEvent 入 mPendingEvents）、`:432-471`（threadMain 挑连接、无请求即 setVSyncEnabled(false) 省电、驱动停摆伪造合成 vsync）、`:571`（dispatchEvent 写 BitTube，-EAGAIN 丢帧，非 Binder）
  - 跳5 doFrame 闭环：`android_view_DisplayEventReceiver.cpp:101`（dispatchVsync 经 JNI）、`Choreographer.java:981`（onVsync 不直接干活，按帧时间戳投递异步消息穿屏障）、`:701`（doFrame）、`:722-782`（jitter≥帧间隔记 Skipped frames、frameTime 回拨最近边界只跑一次不补偿堆积、input→animation→insets animation→traversal→commit 固定顺序）
- 06 合成：`Output.cpp:423`、`HWComposer.cpp:459`、`SkiaGLRenderEngine.cpp:716`。
- 07 上屏：`HWComposer.cpp:566/656`、`RefreshRateConfigs.cpp:220`。
- 08 多屏：`DisplayManagerService.java:430`、`LogicalDisplayMapper.java:369`、`DisplayDevice.java:31`。
- 09 排障：`SurfaceFlinger.cpp:2049`、`HWComposer.cpp:566`；其余以 dumpsys/trace 为主。
- 10 VRR/HDR：`RefreshRateConfigs.cpp:220`、`HWComposer.cpp:656`、`OutputLayer.cpp:554`。
- 11 RenderEngine：`Layer.cpp:590`、`SkiaGLRenderEngine.cpp:716`。

`RenderEngine` 实现位于 `frameworks/native/libs/renderengine/`（`skia/SkiaGLRenderEngine.cpp`），不在 `services/surfaceflinger/RenderEngine/`。

## 输出位置

- 临时稿：`D:\openclaw\Android framework\Android显示子系统\_draft\`。
- 正式篇：同系列目录；编号与文件名在阶段二与用户确认后再定。
- 新系列没有旧篇目时，按 `android-window-*` 现有篇目的 `<head>` CSS、主题脚本和类名自建；先读最近一篇再落盘。

## 校验

- 每个 `Class.method():line` 先用 `grep -n` 核实，成稿后跑批量锚点审计，汇报通过数/总数。
- HTML 用 `HTMLParser` 栈式校验；Edge headless 先直接传中文 `file://` 路径，只有报 `ERR_FILE_NOT_FOUND` 时才复制到 ASCII 路径，确认暖色纸张背景与调用树无溢出。
- 用户说「都落盘 / 全部出稿」时，按 SKILL.md 步骤 4.5 用 `scripts/extract_series_style.py` + `scripts/build_series_drafts.py` 一次生成全部 `_draft\draft-YYYY-MM-DD-<slug>.html`；文件名不带编号，阶段一不碰 index 与正式目录。生成后在 `_draft\README.md` 写顺序/主题/源码入口表。
