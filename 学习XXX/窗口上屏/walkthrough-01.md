# 窗口上屏 · 3 节点精读（AOSP 13）

> 只看三处：要不要 relayout、WMS 怎么在 relayout 里定 frame/Surface、画完怎么交卷。
> 基线 `/home/book/aosp13`；行号为本轮现地 grep。

## 节点 1｜`performTraversals` 的守卫：这帧要不要跨进程

```java
// ViewRootImpl.java:3069
if (mFirst || windowShouldResize || viewVisibilityChanged || params != null
        || mForceNextWindowRelayout) {
    // … 省略：窗口动画、insets 同步、Surface 替换等分支
    relayoutResult = relayoutWindow(params, viewVisibility, insetsPending);  // :3106
}
```

- **进入形态**：`doTraversal()`（`:2362`）在 vsync 放行后调用 `performTraversals()`（`:2806`）；此时 `mTraversalScheduled` 已清、sync barrier 已拆。
- **这里在决定**：窗口几何/可见性/参数有没有变。变了才走 `relayoutWindow`；纯 invalidate（比如按钮变色）不跨进程，直接去 `performDraw()`（`:3687`）。
- **出去形态**：`relayoutResult` 带回 `RELAYOUT_RES_*` 标志；`mSurface` 可能被替换，`cancelDraw` 可能置位。
- **排障落点**：trace 里某帧没有 `relayoutWindow` 切片，不一定是丢帧；先看 `:3069` 的五个条件。

## 节点 2｜`WMS.relayoutWindow`：同步量窗口、摆位置、发画布

```java
// WindowManagerService.java:2493
// We may be deferring layout passes at the moment, but since the client is interested
// in the new out values right now we need to force a layout.
mWindowPlacerLocked.performSurfacePlacement(true /* force */);   // :2495

// … 省略：可见性/动画/输入窗口更新

if (outFrames != null && outMergedConfiguration != null) {
    win.fillClientWindowFramesAndConfiguration(outFrames, outMergedConfiguration,
            false /* useLatestConfig */, shouldRelayout);         // :2590
}
```

- **进入形态**：`ViewRootImpl.java:8275` 的 `mWindowSession.relayout(...)` 同步 binder 进来；WMS 在锁内找到 `WindowState`，更新 `LayoutParams`。
- **这里在决定**：`createSurfaceControl`（`:2481` → `:2717`）确保 SurfaceControl 存在（有就复用，没有才新建）；`performSurfacePlacement(true)` 立即算 frame/insets；`fillClientWindowFrames...` 把 `mWindowFrames.mCompatFrame`、`mDisplayFrame` 填进 `outFrames`。
- **出去形态**：`outFrames`、`outInsetsState`、`outSurfaceControl` 回到 app；app 线程从阻塞中醒来。
- **关键顺序**：`performSurfacePlacement(true)` 必须在 `fillClientWindowFrames` 之前，否则客户端拿到的是上一次布局的 frame。
- **排障落点**：第一次 relayout 拿到的 frame 不对、Surface 为空，先看 `createSurfaceControl` 和 `performSurfacePlacement(true)` 是否都执行了。

## 节点 3｜`finishDrawing`：画完交卷，WMS 再排 placement

```java
// ViewRootImpl.java:4379
private void reportDrawFinished(int seqId) {
    // … 省略：DEBUG_BLAST 日志
    try {
        mWindowSession.finishDrawing(mWindow, mSurfaceChangedTransaction, seqId);  // :4385
    } catch (RemoteException e) {
        mSurfaceChangedTransaction.apply();
    }
}
```

```java
// WindowManagerService.java:2772
if (win != null && win.finishDrawing(postDrawTransaction, seqId)) {
    win.setDisplayLayoutNeeded();
    mWindowPlacerLocked.requestTraversal();                       // :2778
}
```

- **进入形态**：`performDraw()`（`:4470`）把 DisplayList 交给 RenderThread；硬件路径在 frame complete 回调里合并 `mSurfaceChangedTransaction`，再 `reportDrawFinished(seqId)`（调用点 `:3726`）。
- **这里在决定**：这一帧的 buffer/几何 transaction 是否已经完整；`seqId` 用来和 WMS 侧的 draw 序号对账。
- **出去形态**：`finishDrawing` binder 到 WMS；`finishDrawingWindow`（`:2760`）调用 `win.finishDrawing`，成功则 `requestTraversal()`。
- **WMS 的下一跳**：`WindowSurfacePlacer.requestTraversal()`（`:213`）把 `mPerformSurfacePlacement` post 到 `mAnimationHandler`；`performSurfacePlacement()`（`:114`）最终生成 transaction 给 SF，在下一个 vsync 合成。
- **排障落点**：`finishDrawing` 出现在 `performDraw` 切片之后是正常的；如果它一直不出现，先查 RenderThread 是否卡住或 `seqId` 是否对不上。
