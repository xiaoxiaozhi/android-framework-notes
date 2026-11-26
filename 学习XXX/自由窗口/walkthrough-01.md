# 自由窗口：3 节点精读包（20 分钟，AOSP 13）

> 结论先说：**不用**跟着这两段骨架逐行走。这两段是“查问题时往哪看”的地图，不是阅读清单；其中 A 段（开机/改设置）不是 `am start` 的调用链。
> 真正要走的只有 3 个决策点；其余行只要记住名字，等出现症状再 grep。

走法（每个节点固定三步）：

1. `grep -n` 定位 → `sed -n 'A,Bp'` 只看 30 行窗口，不整文件读；
2. 读之前先猜：这段会怎么分支？猜错的地方才是你今天学到的；
3. 用一条命令验证你的猜测，输出贴进笔记。

---

## 节点 1（5 min）：谁允许 freeform —— `TaskLaunchParamsModifier.java:565`

看什么：`canApplyFreeformWindowPolicy()` 只有两个条件，设备开关 + 显式模式。
要猜的：把 `enable_freeform_support` 关掉后，`--windowingMode 5` 会失败还是静默变全屏？
验证：`adb shell dumpsys activity activities | grep -m1 "A=1000:com.android.settings"`

```java
                && ((displayArea.getWindowingMode() == WINDOWING_MODE_FULLSCREEN
                && launchMode == WINDOWING_MODE_UNDEFINED)
                || launchMode == WINDOWING_MODE_FULLSCREEN);
    }

    private boolean canApplyFreeformWindowPolicy(@NonNull TaskDisplayArea suggestedDisplayArea,
            int launchMode) {
        return mSupervisor.mService.mSupportsFreeformWindowManagement
                && ((suggestedDisplayArea.inFreeformWindowingMode()
                && launchMode == WINDOWING_MODE_UNDEFINED)
                || launchMode == WINDOWING_MODE_FREEFORM);
    }

    private boolean canApplyPipWindowPolicy(int launchMode) {
        return mSupervisor.mService.mSupportsPictureInPicture
                && launchMode == WINDOWING_MODE_PINNED;
    }
```

同一文件往下 20 行，就是这条放行规则的落地分支（`:282` 起）：非 resizeable 的 app 只有在“显示区本身就是 freeform”时才允许 size-compat，否则直接清 bounds 变全屏。

```java
        if (suggestedDisplayArea.inFreeformWindowingMode()) {
            if (launchMode == WINDOWING_MODE_PINNED) {
                if (DEBUG) appendLog("picture-in-picture");
            } else if (!root.isResizeable()) {
                if (shouldLaunchUnresizableAppInFreeform(root, suggestedDisplayArea, options)) {
                    launchMode = WINDOWING_MODE_FREEFORM;
                    if (outParams.mBounds.isEmpty()) {
                        getTaskBounds(root, suggestedDisplayArea, layout, launchMode,
                                hasInitialBounds, outParams.mBounds);
                        hasInitialBoundsForSuggestedDisplayAreaInFreeformMode = true;
                    }
                    if (DEBUG) appendLog("unresizable-freeform");
                } else {
                    launchMode = WINDOWING_MODE_FULLSCREEN;
                    outParams.mBounds.setEmpty();
                    if (DEBUG) appendLog("unresizable-forced-maximize");
```

---

## 节点 2（7 min）：初始 Rect 谁算 —— `TaskLaunchParamsModifier.java:728`

看什么：默认尺寸 → 方向不匹配就转置 → 不匹配就居中 → 再避让已有窗口。
要猜的：同一个 app 连续起两次，bounds 会完全一样，还是会错开？
验证：连起两次后 `dumpsys activity activities | grep -A1 "mode=freeform"`，比较两个 Rect。

```java
    private void getTaskBounds(@NonNull ActivityRecord root, @NonNull TaskDisplayArea displayArea,
            @NonNull ActivityInfo.WindowLayout layout, int resolvedMode, boolean hasInitialBounds,
            @NonNull Rect inOutBounds) {
        if (resolvedMode != WINDOWING_MODE_FREEFORM
                && resolvedMode != WINDOWING_MODE_FULLSCREEN) {
            // This function should be used only for freeform bounds adjustment. Freeform bounds
            // needs to be set to fullscreen tasks too as restore bounds.
            if (DEBUG) {
                appendLog("skip-bounds-" + WindowConfiguration.windowingModeToString(resolvedMode));
            }
            return;
        }

        final int orientation = resolveOrientation(root, displayArea, inOutBounds);
        if (orientation != SCREEN_ORIENTATION_PORTRAIT
                && orientation != SCREEN_ORIENTATION_LANDSCAPE) {
            throw new IllegalStateException(
                    "Orientation must be one of portrait or landscape, but it's "
                    + ActivityInfo.screenOrientationToString(orientation));
        }

        // First we get the default size we want.
        displayArea.getStableRect(mTmpStableBounds);
        final Size defaultSize = LaunchParamsUtil.getDefaultFreeformSize(root, displayArea,
                layout, orientation, mTmpStableBounds);
        mTmpBounds.set(0, 0, defaultSize.getWidth(), defaultSize.getHeight());
        if (hasInitialBounds || sizeMatches(inOutBounds, mTmpBounds)) {
            // We're here because either input parameters specified initial bounds, or the suggested
            // bounds have the same size of the default freeform size. We should use the suggested
            // bounds if possible -- so if app can handle the orientation we just use it, and if not
            // we transpose the suggested bounds in-place.
            if (orientation == orientationFromBounds(inOutBounds)) {
                if (DEBUG) appendLog("freeform-size-orientation-match=" + inOutBounds);
            } else {
                // Meh, orientation doesn't match. Let's rotate inOutBounds in-place.
                LaunchParamsUtil.centerBounds(displayArea, inOutBounds.height(),
                        inOutBounds.width(), inOutBounds);
                if (DEBUG) appendLog("freeform-orientation-mismatch=" + inOutBounds);
            }
        } else {
            // We are here either because there is no suggested bounds, or the suggested bounds is
            // a cascade from source activity. We should use the default freeform size and center it
            // to the center of suggested bounds (or the displayArea if no suggested bounds). The
            // default size might be too big to center to source activity bounds in displayArea, so
            // we may need to move it back to the displayArea.
            adjustBoundsToFitInDisplayArea(displayArea, layout, mTmpBounds);
            inOutBounds.setEmpty();
            LaunchParamsUtil.centerBounds(displayArea, mTmpBounds.width(), mTmpBounds.height(),
                    inOutBounds);
            if (DEBUG) appendLog("freeform-size-mismatch=" + inOutBounds);
        }

        // Lastly we adjust bounds to avoid conflicts with other tasks as much as possible.
        adjustBoundsToAvoidConflictInDisplayArea(displayArea, inOutBounds);
    }

    private int convertOrientationToScreenOrientation(int orientation) {
        switch (orientation) {
            case Configuration.ORIENTATION_LANDSCAPE:
```

---

## 节点 3（5 min）：为什么拖不丢 —— `Task.java:2128`

看什么：先和 stable 区求交（避开状态栏），再保证至少 `MINIMUM_VISIBLE_*` 那一条边可见。
要猜的：把窗口拖到左上角外，是整窗被拉回，还是只保留一条边？
验证：`adb shell am task resize <taskId> -500 -500 300 300`，再 dump 看 Rect。

```java
    private void computeFreeformBounds(@NonNull Rect outBounds,
            @NonNull Configuration newParentConfig) {
        // by policy, make sure the window remains within parent somewhere
        final float density =
                ((float) newParentConfig.densityDpi) / DisplayMetrics.DENSITY_DEFAULT;
        final Rect parentBounds =
                new Rect(newParentConfig.windowConfiguration.getBounds());
        final DisplayContent display = getDisplayContent();
        if (display != null) {
            // If a freeform window moves below system bar, there is no way to move it again
            // by touch. Because its caption is covered by system bar. So we exclude them
            // from root task bounds. and then caption will be shown inside stable area.
            final Rect stableBounds = new Rect();
            display.getStableRect(stableBounds);
            parentBounds.intersect(stableBounds);
        }

        fitWithinBounds(outBounds, parentBounds,
                (int) (density * WindowState.MINIMUM_VISIBLE_WIDTH_IN_DP),
                (int) (density * WindowState.MINIMUM_VISIBLE_HEIGHT_IN_DP));

        // Prevent to overlap caption with stable insets.
        final int offsetTop = parentBounds.top - outBounds.top;
        if (offsetTop > 0) {
            outBounds.offset(0, offsetTop);
        }
    }
```

---

## 剩下 12 行怎么处理

不用读，记住“症状 → 名字”即可：

- 设置改了没生效 → `WindowManagerService.updateFreeformWindowManagement`（`:966`）、`RootWindowContainer.onSettingsRetrieved`（`:521`）
- 桌面模式才有全屏 freeform → `DisplayWindowSettings.getWindowingModeLocked`（`:134`）
- dump 里 `mode=` 从哪来 → `Task.toString`（`:3798`）
- caption / maximize 动画 / 关闭动画 → `FreeformTaskListener`（`:77`）、`FreeformTaskTransitionObserver`（`:70`）、`FreeformTaskTransitionHandler`（`:69`）
- 跨进程那一步 → `ShellTaskOrganizer.onTaskAppeared`（`:465`）按 mode 分发（`:809`）

出现上面任一症状，再回来只读那一处 30 行窗口。没有症状就不读——读了也记不住。

---

## 骨架白话对照（看不懂时先读这个）

**记号**

- `→`：这行产出什么、往哪流；`←`：这行的结果被谁决定，或它改了什么状态。
- 缩进 = 调用/归属层级；`├─` / `└─` = 同一处的两个分支，不是先后顺序。
- 行号 = 打开文件跳过去的位置。骨架不是执行顺序表，是“谁归谁管”的结构表。

**八句话版本**

1. 你敲 `--windowingMode 5`，这个 5 被塞进 `ActivityOptions`，跟着这次启动走。
2. 开机时 system_server 读一次 feature 和 `enable_freeform_support`，算出内存里的能力 flag；`am start` 不会重跑这一步，只读结果。
3. 运行时改设置，由 WMS 的 SettingsObserver 重算并写回 ATMS 的 flag，再让 RootWindowContainer 重配显示（不用重启）。
4. 显示模式是另一件事：只有 PC/desktop 才把默认显示区设成 freeform；手机仍是全屏显示区。
5. 真正放行在 launch 解析：设备有能力 + 这次显式要 freeform，两个都满足才保留 5。
6. 显示区再校验一次“这个 task 支不支持 freeform”；不支持就退回全屏。
7. 如果 app 不可缩放、且显示区本身就是 freeform：方向不合就用 size-compat 起 freeform，否则强制全屏并清 bounds。
8. bounds 在 launch 阶段就算好：默认尺寸 → 方向转置 → 居中 → 避开已有窗口；WMS 只负责执行，Task 还会记住它以便下次还原。

**五个名词**

- TDA（TaskDisplayArea）：一块显示区，“这一屏里的任务默认什么窗口模式”由它定。
- bounds vs frame：bounds 是任务被要求的大小/位置（launch 阶段给），frame 是 WMS 最终摆出来的，通常等于 bounds。
- stable 区：扣掉状态栏/导航栏后可安全放窗口的区域；`computeFreeformBounds` 拿它做交集。
- listener：WMShell 里按窗口模式注册的回调；freeform 的 listener 负责标题栏等装饰。
- caption/decoration：自由窗口的标题栏和边框，不在 app 里画，归 WMShell。

**三个最容易误读的点**

- `:565` 放行 ≠ app 一定能 freeform：`:286` 还有一次针对“不可缩放 app”的策略分支。
- “手机也能自由窗口” ≠ “手机桌面是 freeform”：前者靠显式 5，后者要 `mIsPc || forceDesktopMode()`。
- bounds 不是 WMS 布局算的；WMS 只执行，钳制在 `Task.computeFreeformBounds`。
