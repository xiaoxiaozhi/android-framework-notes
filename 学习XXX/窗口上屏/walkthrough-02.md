# WMS.relayoutWindow · 3 节点精读（AOSP 13）

> 只看三处：进入锁后先判什么、为什么先建 SurfaceControl 再 placement、out 参数怎么回给 app。
> 基线 `/home/book/aosp13`（`android-13.0.0_r84`）；行号为本轮现地 grep。

## 节点 1｜入口：锁、seq、`shouldRelayout`

```java
// WindowManagerService.java:2291
final long origId = Binder.clearCallingIdentity();
synchronized (mGlobalLock) {
    final WindowState win = windowForClientLocked(session, client, false);
    if (win == null) {
        return 0;                                                   // :2295
    }
    if (win.mRelayoutSeq < seq) {
        win.mRelayoutSeq = seq;                                     // :2298
    } else if (win.mRelayoutSeq > seq) {
        return 0;                                                   // :2300
    }
    // … 更新 requestedSize / LayoutParams / flags / mViewVisibility
    win.mRelayoutCalled = true;                                     // :2428
    win.mInRelayout = true;                                         // :2429

    final boolean shouldRelayout = viewVisibility == View.VISIBLE   // :2442
            && (win.mActivityRecord == null
                    || win.mAttrs.type == TYPE_APPLICATION_STARTING
                    || win.mActivityRecord.isClientVisible());
}
```

- **进入形态**：`Session.relayout` 从 binder 进来，`WMS.relayoutWindow` 先清 calling identity，再拿 `mGlobalLock`。
- **这里在决定**：`win` 是否还在、`seq` 是否过期、这次请求是否值得继续。`shouldRelayout` 只看“可见性 + Activity client 可见”，不是“参数变没变”。
- **出去形态**：早退时直接 `return 0`，app 拿到 0，不建 Surface；继续时 `mInRelayout=true`，窗口进入本次 relayout。
- **排障落点**：app 说“relayout 没反应”，先看 `mRelayoutSeq` 是否被旧 seq 挡掉，以及 `mViewVisibility`/`mActivityRecord.isClientVisible()` 是否让 `shouldRelayout=false`。

## 节点 2｜建 SurfaceControl 与强制 placement 的顺序

```java
// WindowManagerService.java:2477
// Create surfaceControl before surface placement otherwise layout will be skipped
// (because WS.isGoneForLayout() is true when there is no surface.
if (shouldRelayout && outSurfaceControl != null) {
    result = createSurfaceControl(outSurfaceControl, result, win, winAnimator);  // :2481
}

// WindowManagerService.java:2493
// We may be deferring layout passes at the moment, but since the client is interested
// in the new out values right now we need to force a layout.
mWindowPlacerLocked.performSurfacePlacement(true /* force */);        // :2495

if (shouldRelayout) {
    result = win.relayoutVisibleWindow(result);                       // :2500
}
```

- **进入形态**：`shouldRelayout` 为 true 且 `outSurfaceControl` 非空，才建/复用 SurfaceControl。
- **对象关系**：`WindowSurfaceController` 不是 `SurfaceControl` 的子类（`SurfaceControl` 是 `final`）；它只是 WMS 侧的包装器，字段 `mSurfaceControl` 持有 `SurfaceControl`。
- **这里在决定**：先有 Surface，`isGoneForLayout()` 才不会把窗口当成 gone；否则 `performSurfacePlacement` 会跳过这个窗口，frame 算不出来。
- **出去形态**：`performSurfacePlacement(true)` 在锁内强制跑一次 placement，把 frame 算到最新（insets 作输入）；`relayoutVisibleWindow` 处理首帧/可见性并更新 result。
- **关键顺序**：`createSurfaceControl`（`:2481`）必须在 `performSurfacePlacement`（`:2495`）之前；这不是风格问题，是布局是否执行的问题。
- **排障落点**：第一次 relayout 的 `outFrames` 为空/旧值，先看 `createSurfaceControl` 是否成功，再看 `performSurfacePlacement(true)` 是否真的跑了。

## 节点 3｜回填 out 参数并同步返回 app

```java
// WindowManagerService.java:2525
if (winAnimator.hasSurface()) {
    winAnimator.mSurfaceController.getSurfaceControl(outSurfaceControl);
} else {
    outSurfaceControl.release();                                      // :2533
}

// … focus / IME / wallpaper / orientation / configChanged

if (outFrames != null && outMergedConfiguration != null) {
    win.fillClientWindowFramesAndConfiguration(outFrames, outMergedConfiguration,
            false /* useLatestConfig */, shouldRelayout);             // :2590
}
if (outInsetsState != null) {
    outInsetsState.set(win.getCompatInsetsState(), true);             // :2598
}
if (outActiveControls != null) {
    getInsetsSourceControls(win, outActiveControls);                  // :2628
}
win.mInRelayout = false;                                              // :2607
return result;                                                        // :2633
```

- **进入形态**：Surface 已确保，placement 已算完；接下来把结果写进 binder 的 out 参数。
- **这里在决定**：SurfaceControl 是回传还是 release；outFrames/outConfiguration/outInsetsState/outActiveControls 分别填什么。
- **出去形态**：`WMS.relayoutWindow` 返回 `result` → `Session.relayout` 返回 `res`（`Session.java:260`）→ binder 回到 app；`ViewRootImpl.relayoutWindow` 返回 `relayoutResult`（`ViewRootImpl.java:8364`）→ `performTraversals` 继续 measure/layout/draw。
- **关键点**：这不是 WMS 回调 app，而是 app 的同步 binder 调用返回；`outFrames` 等对象在调用期间被 WMS 写入，返回时由 binder 带回。
- **排障落点**：app 拿到空 Surface，先看 `hasSurface` 分支；frame 旧，先看 `fillClientWindowFramesAndConfiguration` 是否在 placement 之后；insets 不对，看 `outInsetsState.set` 是否执行。
