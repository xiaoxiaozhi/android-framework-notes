# WMS.relayoutWindow：一次 relayout 到底做了什么 · round 02（AOSP 13）

## ① 骨架

```
Session.relayout() → WMS.relayoutWindow()                                  WindowManagerService.java:2278
 └─ 入口：clearCallingIdentity + synchronized(mGlobalLock) → 进入锁内       WindowManagerService.java:2291/:2292
   ├─ 找 win；win == null → return 0                                        WindowManagerService.java:2293/:2294
   ├─ 校验 mRelayoutSeq；旧 seq → return 0                                  WindowManagerService.java:2297/:2299
   ├─ cancelAndRedraw 且 sync 未完成 → result |= CANCEL_AND_REDRAW          WindowManagerService.java:2303/:2306
   ├─ setRequestedSize / LayoutParams / flags / mViewVisibility → 写入 win  WindowManagerService.java:2313/:2431
   ├─ shouldRelayout ← 可见 && (无 Activity 或 starting 或 client visible)  WindowManagerService.java:2442
   ├─ !shouldRelayout && hasSurface → 走退出动画 / SURFACE_CHANGED          WindowManagerService.java:2455/:2460
   ├─ shouldRelayout && outSurfaceControl → createSurfaceControl            WindowManagerService.java:2479/:2481
   ├─ performSurfacePlacement(true) ← 先建 Surface 再强制 placement          WindowManagerService.java:2495
   ├─ shouldRelayout → relayoutVisibleWindow(result)                        WindowManagerService.java:2497/:2500
   ├─ hasSurface → getSurfaceControl(out)；否则 release                     WindowManagerService.java:2525/:2533
   ├─ focus / IME / wallpaper / orientation / configChanged → 更新状态      WindowManagerService.java:2543/:2573
   ├─ fillClientWindowFramesAndConfiguration(...) → 回填 outFrames/Config   WindowManagerService.java:2590
   ├─ outInsetsState.set(...) / outActiveControls / outSyncIdBundle → 回填   WindowManagerService.java:2598/:2628
   └─ mInRelayout=false → return result                                     WindowManagerService.java:2607/:2633
```

基线 AOSP 13（`android-13.0.0_r84`，`/home/book/aosp13`）；骨架 16 行全部现地 grep 核实。本轮锁 13，不使用 12 的行号。未核实：软绘路径下 `relayoutVisibleWindow` 的首帧行为是否与硬绘完全一致（本轮只核硬绘）。

## 骨架解说（这段在讲什么）

- ① **relayout 不是“重画”**：它同步算 frame（insets 作输入）、确保 SurfaceControl，再把 out 值带回 app；真正画像素是 app 后续的 measure/layout/draw。
- ② **入口先做两件事**：`Binder.clearCallingIdentity()` + `synchronized (mGlobalLock)`；`win == null` 或旧 `seq` 直接 `return 0`。
- ③ **`shouldRelayout` 只看可见性**：`viewVisibility == VISIBLE` 且 Activity client 可见（starting window 例外）；不可见但已有 Surface 时，走退出动画并置 `SURFACE_CHANGED`。
- ④ **顺序不能乱**：`createSurfaceControl` 必须在 `performSurfacePlacement(true)` 之前，否则 `isGoneForLayout()` 会让布局跳过，frame 算不出来。
- ⑤ **`relayoutVisibleWindow` 管首帧/可见性**：它决定 `FIRST_TIME` 等 result；之后 `getSurfaceControl` 把句柄回传，没有 Surface 就 `release` out。
- ⑥ **收尾是回填 out 参数**：`fillClientWindowFramesAndConfiguration`、`outInsetsState`、`outActiveControls`、`outSyncIdBundle`，最后 `mInRelayout=false` + `return result`。

## ② 决策点

- **这次要不要 relayout**：`shouldRelayout`（`WindowManagerService.java:2442`）——不可见窗口不重新布局，但不等于马上销毁 Surface。
- **先建 Surface 还是先 placement**：`createSurfaceControl`（`WindowManagerService.java:2479/:2481`）必须在 `performSurfacePlacement(true)`（`WindowManagerService.java:2495`）之前；否则没有 Surface，`isGoneForLayout()` 会让布局跳过。
- **不可见但还有 Surface**：`!shouldRelayout && winAnimator.hasSurface()`（`WindowManagerService.java:2455`）——走退出动画/`SURFACE_CHANGED`，不是立刻 release。
- **什么时候回传 SurfaceControl**：`hasSurface` 时 `getSurfaceControl`（`WindowManagerService.java:2525`），否则 `outSurfaceControl.release()`（`WindowManagerService.java:2533`）。
- **这次 relayout 什么时候算完成**：out 参数填完、`mInRelayout=false`（`WindowManagerService.java:2607`）、`return result`（`WindowManagerService.java:2633`）；app 在 `ViewRootImpl.relayoutWindow` 返回后继续。

## ③ 我要你答的 3 个问题

1. **白屏**：`dumpsys window windows` 里窗口有 `Frames:`，但内容一直白。用 `mHasSurface`、`mDrawState`、`mViewVisibility`、`mRelayoutSeq` 四个字段，怎么区分「`shouldRelayout` 没进」「WMS 没建/没给 SurfaceControl」「app 没画完」「画完没交卷」？分别下一步抓哪条 trace？
2. **旋转/分屏黑边**：旋转后 `outFrames` 已经是新尺寸，但画面还是旧比例。说明 `fillClientWindowFramesAndConfiguration` 和 `SurfaceControl`/buffer 之间哪一步没跟上？`RELAYOUT_RES_SURFACE_CHANGED` 在这里起什么作用？
3. **滑动掉帧**：列表滚动时 `relayoutWindow` 切片很少，这正常吗？如果 `shouldRelayout` 为 false，`performSurfacePlacement(true)` 还会不会跑？用 `atrace` 应该过滤哪几个 tag 才能看到“placement 有、relayout 没有”的帧？

## 骨架阅读法

- **一句话定位**：`relayoutWindow` 是 WMS 锁内的一次同步事务：校验请求 → 更新窗口状态 → 建/复用 SurfaceControl → 强制 placement 算 frame → 回填 out 参数 → 返回 app。
- **三个接力边界**：binder 入口 `WindowManagerService.java:2291/:2292`；布局分支 `WindowManagerService.java:2442`；out 参数回填 `WindowManagerService.java:2590/:2598/:2633`。
- **最小验证命令**：`cd /home/book/aosp13 && grep -n "shouldRelayout\|performSurfacePlacement(true /\* force \*/)" frameworks/base/services/core/java/com/android/server/wm/WindowManagerService.java`，应命中 2442、2479、2495、2497。
- **最贵的一行**：`WindowManagerService.java:2495`——relayout 内强制 placement；frame/insets 都在这之后才定，滑动时别把它当成“免费”。
- **可追问的名字**：`shouldRelayout`（为什么不可见还要保留 Surface）、`relayoutVisibleWindow`（首帧和可见性）、`getSurfaceControl`（句柄什么时候为空）。

## 配套 L0 题（≤15 分钟）

- **触发**：`cd /home/book/aosp13/frameworks/base && grep -n "shouldRelayout\|createSurfaceControl(outSurfaceControl\|performSurfacePlacement(true /\* force \*/)" services/core/java/com/android/server/wm/WindowManagerService.java`
- **判据**：分别命中 2442、2481、2495；`sed -n '2477,2482p'` 能看到“先 create 再 placement”的注释。
- **锚点**：`WindowManagerService.java:2442`、`WindowManagerService.java:2481`、`WindowManagerService.java:2495`。
- **产出**：一句「relayout 先判 `shouldRelayout`，可见才建/复用 SurfaceControl，再强制 placement 算 frame；不可见但还有 Surface 时走退出动画，不直接销毁」。
