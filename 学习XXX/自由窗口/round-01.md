# 自由窗口 round 01（AOSP 13）

## ① 骨架

> 两段要分开读：`retrieveSettings()` 只在开机 `systemReady` 跑一次；`am start` 不会调用它，只读内存里的 `mSupportsFreeformWindowManagement`。

**A. 开机一次 / 改设置时（状态线）**

```
AMS.systemReady()  → 触发一次 retrieveSettings，之后 launch 不再走这里        ActivityManagerService.java:8161
 └ AMS.retrieveSettings()  → 把 resolver 转交给 ATMS                          ActivityManagerService.java:8043
   └ ATMS.retrieveSettings(resolver)  ← feature || enable_freeform_support     ActivityTaskManagerService.java:879
     └ mSupportsFreeformWindowManagement  → 有 true（:935）/ 无 false（:942）   ActivityTaskManagerService.java:935
WMS SettingsObserver.onChange()  ← freeform URI 变了才进来                     WindowManagerService.java:864
 └ updateFreeformWindowManagement()  → 重算并写回 ATMS flag                    WindowManagerService.java:966/:973
   └ RootWindowContainer.onSettingsRetrieved()  → 重配显示与默认 TDA           RootWindowContainer.java:976
DisplayWindowSettings.getWindowingModeLocked()  ← 能力关则 fullscreen（:128）    DisplayWindowSettings.java:124
 └ 默认给不给 freeform  → 只有 mIsPc || forceDesktopMode 才给                  DisplayWindowSettings.java:135
```

**B. 每次 am start（启动线，只读 flag）**

```
adb shell am start --windowingMode 5 -n com.android.settings/.Settings  → 5 写进 options     ActivityManagerShellCommand.java:563
 └ startActivityAndWait / AsUserWithFeature()  → options.toBundle() 走 Binder（:600/:605）    ActivityManagerShellCommand.java:600
   └ ATMS.startActivityAsUser()  ← obtainStarter:1280 → setActivityOptions:1290 → execute:1292  ActivityTaskManagerService.java:1238
     └ execute → executeRequest → startActivityUnchecked → startActivityInner
         :647 → :703 → :1227 → :1398（checkedOptions :1024，mOptions :2234）                ActivityStarter.java:647–1543
       └ computeLaunchParams()  → calculate(PHASE_BOUNDS)（:1582 → :1753）                 ActivityStarter.java:1751
         └ LaunchParamsController.calculate()  → 遍历 modifier，onCalculate(:100)          LaunchParamsController.java:84
           └ TaskLaunchParamsModifier :149  ← launchMode = options.getLaunchWindowingMode()  TaskLaunchParamsModifier.java:149
             └ canApplyFreeformWindowPolicy()  ← 能力 flag(:567) + 显式 5 → true             TaskLaunchParamsModifier.java:565
               └ TDA.getOrCreateRootTask()  → ActivityStarter:1621 → Root:2849 → validate:957 → new Task:988  TaskDisplayArea.java:942
                 └ getTaskBounds() → computeFreeformBounds()  → 初值:289/:728，钳制 Task:2066/:2128  TaskLaunchParamsModifier.java:728
```

> 输出旁路（异步，不是调用子节点）：`Task.toString :3798` 给出 `mode=freeform`；`ShellTaskOrganizer :809 → FreeformTaskListener :77` 装 caption。

基线 AOSP 13（`android-13.0.0_r84`，`/home/book/aosp13`，`repo info` 已核）；模拟器 API 33 上 `settings put global enable_freeform_support 1` + `am start --windowingMode 5` 实测通过，`mode=freeform`、`bounds=[338,718][1108,2158]` 已抓到；未核实：desktop/PC 显示模式下的默认 freeform TDA（`mIsPc` 分支只做了代码核实，未跑设备）。

## ② 决策点

- 这台设备到底支不支持 freeform：`feature` 与开发者开关二选一；开机时 ATMS 算一次（`:935`），运行时改设置由 WMS 观察者写回 flag（`:864` → `:973`）。
- 是“整个桌面都是自由窗口”还是“手机上偶尔飘一个窗”：默认 TDA 是否 freeform 取决 `mIsPc || forceDesktopMode()`（`DisplayWindowSettings.java:134`）。
- 这次启动到底 freeform 还是被最大化：`canApplyFreeformWindowPolicy()` 放行 + unresizable 分支（`TaskLaunchParamsModifier.java:565`、`:286`）。
- 初始 Rect 谁定、拖出屏幕会不会丢：`getTaskBounds()` 给初始值，`computeFreeformBounds()` 做钳制（`TaskLaunchParamsModifier.java:728`、`Task.java:2128`）。
- caption 和 maximize 动画归谁：ShellTaskOrganizer 按 mode 分发，三个 Freeform Shell 组件接装饰与转场（`ShellTaskOrganizer.java:809`）。

## ③ 3 个诊断题（现象 → 定位）

1. `am start --windowingMode 5` 后 `dumpsys` 仍是 `mode=fullscreen`，logcat 无异常。列出 3 个可能断点（能力 flag / 任务复用 / 应用时校验），每个给一条区分命令或字段。
2. `settings put global enable_freeform_support 1` 后立刻 `am start` 仍落回全屏，隔 0.3s 再试成功。指出哪一步是异步的，并设计一个不改代码的验证。
3. `am task resize` 把 freeform 推到屏幕外，bounds 被改回来。判断是 `getTaskBounds` 还是 `computeFreeformBounds`，给出改前 / 改后 `bounds` 与依据行。
