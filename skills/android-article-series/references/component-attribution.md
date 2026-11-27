# 归属题与「X 是什么」组件题：核实步骤

用于两类问答：用户问「某特性属于哪个模块 / 我要写文档但不知道归谁」，或「X 是什么、它负责什么」（WM Shell、某个 Shell 库、某个 manager）。两类都要先取证再答，不按进程印象作答。

## 一、归属题（特性属于哪个模块）

1. 先 `ls` 你猜的包再下结论。`packages/SystemUI/src/com/android/systemui/pip/` 不存在，PiP 在 `libs/WindowManager/Shell/src/com/android/wm/shell/pip/`。Shell 编进 SystemUI APK 但独立成库，按进程印象答「SystemUI 的功能」就错了。
2. 按数据流列归属表（App API / ATMS / WMCore / WM Shell / SurfaceFlinger），每层写进程与代表类，不用一句「属于 WMS」带过。
3. 归属分三层答：画面归 app 的 task（`windowingMode=pinned`）、尺寸动画手势归 Shell `PipController`、系统窗口只有菜单（AOSP12 `PipMenuController.java:99` `TYPE_APPLICATION_OVERLAY`、`:102` `PRIVATE_FLAG_TRUSTED_OVERLAY`；13 为 `:105`）。
4. 锚点与文章基线同树：`reparentChildSurfaceToTask` 只在 13 的 `ShellTaskOrganizer.java:711`，12 树零命中，不写进 12 系列；引用前先 `grep -n`。
5. 主归属按职责判：入口与状态机归 ATMS，容器/窗口模式/过渡归 WMCore，实际窗口动画与 bounds 归 Shell；文档主线挂 WMCore，ATMS 与 Shell 作为上下游章节。点明 Shell 不在 system_server，避免把 `PipTaskOrganizer` 一类当成 WMS 内部类。
6. 答篇目前先 `ls <系列目录>` 与 `index.html` 里的 `href="android-window-`：篇号会跳号（13、14 已发布，11/12 未发布），已有篇只给文件名、标签与阅读顺序，不另起号。计划号未落盘时不要抢号，给推荐位置与顺延方案让用户确认。
7. 交付三样：归属表、推荐篇号、可直接放进文章开头的定位段（含各层参与者与起点→终点）。

## 二、组件题（X 是什么、它负责什么）

以 WM Shell 为例，四步取证：

1. 查「编进谁」。`grep -n 'name: "WindowManager' libs/WindowManager/Shell/Android.bp` 得模块名 `WindowManager-Shell`（`Shell/Android.bp:104`），再 `grep -rn 'WindowManager-Shell' packages/SystemUI/Android.bp` 看它在谁的 `static_libs`（`:66`）。结论写成「编译进 SystemUI APK、跑在 systemui 进程，但是独立 library」。
2. 查入口与对端。入口 `WMShell extends SystemUI`（`packages/SystemUI/src/com/android/systemui/wmshell/WMShell.java:93`），启动走 `ShellInit.init()`（`ShellInit.java:25` 接口、`:29` 方法）；system_server 对端是 `TaskOrganizerController`（`:69`，注册入口 `registerTaskOrganizer` `:479`）与 `DisplayAreaOrganizerController`（`:42`），跨进程契约在 `core/java/android/window/ITaskOrganizer*.aidl`，Shell 拿到的核心是 `onTaskAppeared(RunningTaskInfo, SurfaceControl leash)`。
3. 类路径不要猜。猜的包 `ls` 不存在就 `find . -name '<Class>.java'`：12/13 树 `TaskOrganizer` 在 `core/java/android/window/TaskOrganizer.java:42`（不在 `android/wm/shell`），`ShellTaskOrganizer` 在 Shell 库 `ShellTaskOrganizer.java:65`（13 为 `:74`）。
4. 收尾给两个验证抓手：`adb shell logcat -s ShellTaskOrganizer ShellInitImpl`（TAG 已核）与断点 `ShellTaskOrganizer.onTaskAppeared`；用「WMS 决定能不能、Shell 决定怎么摆」收束，不把 Shell 写成窗口树的一层。

## 三、答案骨架

- 先给一句定义，再讲「为什么它不在 system_server」这类历史动因（改一次要重编整个 system_server、迭代慢）。
- 三层分工表：WMCore/WMS（system_server，状态权威）、WM Shell（SystemUI 进程，编排策略）、App（自己的窗口）。
- 说明 Shell 不是窗口树的一层，而是 WMS 的客户端：它「拥有」几棵 `Task`/`DisplayArea` 子树，数据结构仍在 system_server。
- AOSP 12 的 Shell 子包（实测）：`animation apppairs bubbles draganddrop hidedisplaycutout legacysplitscreen onehanded pip protolog sizecompatui splitscreen startingsurface tasksurfacehelper transition`；Recents 不在其中，它在 Launcher 进程。
