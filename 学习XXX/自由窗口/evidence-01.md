# 自由窗口 round 01 · 实测证据（AOSP 13 / emulator-5554）

日期：2026-11-19
基线：`/home/book/aosp13`，`repo info` → `refs/tags/android-13.0.0_r84`；设备 `ro.build.version.sdk=33`。

## 1. 设备能力来源

```bash
adb shell settings get global enable_freeform_support
# null（默认关闭；AndroidManifest feature 也没有 freeform）

adb shell settings put global enable_freeform_support 1
```

代码依据：`ActivityTaskManagerService.java:879`（开机 `retrieveSettings`，feature 或该设置，赋值在 `:935`）、`WindowManagerService.java:864` → `:966/:973`（运行时改设置，由 WMS 观察者重算并写回 ATMS 的 flag）。

## 2. 同一 app：全屏 vs 自由窗口

```bash
adb shell am force-stop com.android.settings
adb shell am start -n com.android.settings/.Settings
adb shell dumpsys activity activities | grep -m1 "A=1000:com.android.settings"
# * Task{54979ad #69 type=standard A=1000:com.android.settings.root U=0 visible=true visibleRequested=true mode=fullscreen translucent=false sz=1}

adb shell am force-stop com.android.settings
adb shell am start --windowingMode 5 -n com.android.settings/.Settings
adb shell dumpsys activity activities | grep -m1 "mode=freeform"
# * Task{11929c7 #70 type=standard A=1000:com.android.settings.root U=0 visible=true visibleRequested=true mode=freeform translucent=false sz=1}
adb shell dumpsys activity activities | grep -A1 "mode=freeform"
#   mBounds=Rect(338, 718 - 1103, 2158)
```

显示尺寸 `adb shell dumpsys window displays | grep init=` → `init=1440x2960 560dpi`，所以自由窗口 bounds 不是全屏。

## 3. 锚点

- `TaskLaunchParamsModifier.java:565`：`canApplyFreeformWindowPolicy()`，设备不支持时 5 不放行。
- `TaskDisplayArea.java:1379`：`isValidWindowingMode()`，最终把非法模式退回。
- `TaskLaunchParamsModifier.java:728`：`getTaskBounds()`，初始 Rect 的来源。
- `Task.java:2128`：`computeFreeformBounds()`，拖出屏后的钳制（本轮未跑 resize，仅代码核实）。
- `Task.java:3798`：`Task.toString()` 输出 `mode=`，即 `dumpsys` 里那行的来源。
- `ShellTaskOrganizer.java:465/809` → `FreeformTaskListener.java:77` → `FreeformTaskTransitionObserver.java:70`：WMShell 侧装饰与转场。

## 4. 设备状态

`enable_freeform_support` 置为 1 后未还原。需要还原：

```bash
adb shell settings delete global enable_freeform_support
```
