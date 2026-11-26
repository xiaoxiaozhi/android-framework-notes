# 一帧上屏：vsync → relayout → draw → finishDrawing · round 01（AOSP 13）

## ① 骨架

```
Vsync → Choreographer.FrameDisplayEventReceiver.onVsync() → post → doFrame() → CALLBACK_TRAVERSAL   Choreographer.java:1172/:742/:832
 └─ ViewRootImpl.doTraversal() ← 清 mTraversalScheduled、拆 sync barrier          ViewRootImpl.java:2362
   └─ performTraversals() ← 一帧总入口                                             ViewRootImpl.java:2806
     ├─ 纯 invalidate 帧 → 不跨进程，继续 measure/layout/draw                     ViewRootImpl.java:3069/:3423/:3459/:3687
     └─ 首帧/尺寸/可见性/参数/强制 → relayoutWindow()                             ViewRootImpl.java:3069/:3106
       └─ mWindowSession.relayout() → binder 跨进程 → Session.relayout() → app 线程阻塞  ViewRootImpl.java:8275
         └─ WMS.relayoutWindow() ← 锁内处理这次请求                              WindowManagerService.java:2278
             ├─ shouldRelayout 时 createSurfaceControl() → 确保 SurfaceControl 存在  WindowManagerService.java:2481/:2717
             ├─ performSurfacePlacement(true) ← 强制量窗口、摆位置                  WindowManagerService.java:2495
             └─ fillClientWindowFrames…() → 回填 outFrames/Configuration（insets 另 set）  WindowManagerService.java:2590/:2597
               ↩ relayout 返回 app → 按需 performMeasure() → performLayout() → createSyncIfNeeded() → performDraw()  ViewRootImpl.java:3423/:3459/:3658/:3687
                 └─ SurfaceSyncer 同步完成 → 合并 transaction → reportDrawFinished(seqId)  ViewRootImpl.java:3726/:4379
                   └─ mWindowSession.finishDrawing() → 告诉 WMS 这帧画完           ViewRootImpl.java:4385
                     └─ WMS.finishDrawingWindow() → win.finishDrawing() 收尾       WindowManagerService.java:2760/:2772
                       └─ requestTraversal() → animationHandler 异步排 placement   WindowManagerService.java:2778 / WindowSurfacePlacer.java:225
                         └─ performSurfacePlacement() → applySurfaceChangesTransaction → SF（下个 vsync）  WindowSurfacePlacer.java:177 / DisplayContent.java:4823
```

基线 AOSP 13（`android-13.0.0_r84`，`/home/book/aosp13`）；骨架 16 行全部现地 grep 核实。本轮锁 13，不使用 12 的行号。未核实：软件绘制路径下 `reportDrawFinished` 是否走同一 `seqId` 对账（本轮只核硬件路径）。

## 骨架解说（这段在讲什么）

- ① **vsync 只是放行**：`Choreographer` 在 `doFrame` 里执行已排队的 `CALLBACK_TRAVERSAL`，它不决定窗口多大，只决定“这一帧什么时候开始”。
- ② **先判要不要 relayout**：`performTraversals` 用 `mFirst || windowShouldResize || viewVisibilityChanged || params != null || mForceNextWindowRelayout` 分流；纯 invalidate 不跨进程。
- ③ **relayout 是同步 binder**：app 线程在 `mWindowSession.relayout` 阻塞，system_server 的 WMS 接手这次请求。
- ④ **WMS 在 relayout 内强制 placement**：先 `createSurfaceControl` 确保 SurfaceControl 存在（已有 controller 就复用），再 `performSurfacePlacement(true)` 算 frame（insets 作输入），`fillClientWindowFrames` 把结果回填到 out 参数，然后 relayout 同步返回 app。
- ⑤ **app 拿到 frame+Surface 才画**：measure → layout → draw；像素由 RenderThread（或软件绘制）产生。
- ⑥ **画完要交卷**：`reportDrawFinished(seqId)` → `finishDrawing` 回到 WMS；WMS 再 `requestTraversal`，把 transaction 交给 SF，在下一个 vsync 合成。

## ② 决策点

- **这帧要不要跨进程**：守卫 `mFirst || windowShouldResize || viewVisibilityChanged || params != null || mForceNextWindowRelayout`（`ViewRootImpl.java:3069`）——不满足就只 measure/layout/draw。
- **relayout 内要不要立刻算几何**：`performSurfacePlacement(true /* force */)`（`WindowManagerService.java:2495`）——客户端马上要 out 值，不能等异步 placement。
- **画布是新建还是复用**：`createSurfaceControl(...)`（`WindowManagerService.java:2481` → `:2717`）——`mSurfaceController == null` 才新建，否则直接复用；尺寸变化不在这个分支重建。
- **什么时候算“画完”**：`reportDrawFinished(seqId)`（`ViewRootImpl.java:4379`）——要等 RenderThread 的 frame complete 回调合并 transaction。
- **WMS 什么时候交给 SF**：`finishDrawingWindow` 里 `requestTraversal()`（`WindowManagerService.java:2778`）——不是立刻 commit，而是排一次 placement。

## ③ 我要你答的 3 个问题

1. **白屏**：Activity 的窗口已经在 `dumpsys window windows` 里、`Frames:` 也有尺寸，但内容一直白。用 `adb shell dumpsys window windows | grep -E "Window\{|mHasSurface|mDrawState|Frames:"` 抓一次，怎么用 `mHasSurface` 和 `mDrawState` 区分「WMS 没建/没给 SurfaceControl」「app 没画完」「画完没交卷」三种情况？分别该看哪一行？
2. **滑动掉帧**：列表滚动掉帧，但 perfetto / atrace 里几乎没有 `relayoutWindow` 切片。这正常吗？如果拿 `relayoutWindow` 次数当滑动流畅度指标，会漏掉哪一类帧？给出 `atrace` 过滤命令和对应守卫。
3. **旋转/分屏黑边**：旋转或分屏后窗口比例不对、出现黑边。`dumpsys window windows` 里看哪两个字段能区分「WMS 的 frame 没更新」和「app 还没往新 Surface 画完」？给出判断顺序和下一步该抓的 trace。

## 骨架阅读法

- **一句话定位**：把 vsync 变成屏幕上的一帧；终点是 WMS 拿到 `finishDrawing` 并把 transaction 交给 SF。
- **三个接力边界**：同线程 `ViewRootImpl.java:2806` → `:3106`；跨进程 `ViewRootImpl.java:8275` → `WindowManagerService.java:2278`；持锁区 `WindowManagerService.java:2278`–`:2590`。
- **最小验证命令**：`cd /home/book/aosp13 && grep -n "performSurfacePlacement(true /\* force \*/)" frameworks/base/services/core/java/com/android/server/wm/WindowManagerService.java`，应得 2495。
- **最贵的一行**：`WindowManagerService.java:2495`——relayout 里强制 placement，frame/insets/Surface 都在这之后才定。
- **可追问的名字**：`relayoutWindow`（什么时候必须走）、`performSurfacePlacement`（谁触发、为什么 force）、`reportDrawFinished`（seqId 怎么对账）。

## 配套 L0 题（≤15 分钟）

- **触发**：`cd /home/book/aosp13/frameworks/base && grep -n "mFirst || windowShouldResize" core/java/android/view/ViewRootImpl.java && grep -n "performSurfacePlacement(true /\* force \*/)" services/core/java/com/android/server/wm/WindowManagerService.java && grep -n "reportDrawFinished" core/java/android/view/ViewRootImpl.java`
- **判据**：分别命中 3069、2495、3726/4379；`sed -n '3069,3071p'` 能看到 `|| mForceNextWindowRelayout`。
- **锚点**：`ViewRootImpl.java:3069`、`WindowManagerService.java:2495`、`ViewRootImpl.java:3726`。
- **产出**：一句「relayout 只在几何/可见性/参数变化时走；WMS 在 relayout 内强制 placement；finishDrawing 由 draw 后的 SurfaceSyncer 完成回调触发」。
