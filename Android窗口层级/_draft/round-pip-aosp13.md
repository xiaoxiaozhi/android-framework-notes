# 学习轮次：PiP（画中画）— AOSP 13

**模式：A（一页骨架 + 3 个问题，然后做题）** · 基线 AOSP 13（`android-13.0.0_r84`，`/home/book/aosp13`），全部锚点本轮现地 grep。

## ① 骨架

```
Activity#enterPictureInPictureMode(params) → ActivityClient.enterPictureInPictureMode(token) → Binder   Activity.java:2932/:2947
 └─ ActivityClientController ← token→ActivityRecord，clearCallingIdentity                                wm/ActivityClientController.java:823-825
    └─ ATMS.enterPictureInPictureMode(r, params, true) → 决策都在这里                                    wm/ActivityTaskManagerService.java:3536
       ├─ r.inPinnedWindowingMode() → 已在 PiP，直接 return true                                        :3539
       ├─ checkEnterPictureInPictureState() ← 返回 false 即整个入口 return false                        wm/ActivityRecord.java:3161
       │   ├─ RESUMED → 只挡 isCurrentAppLocked（不看 hasRootPinnedTask）                               ActivityRecord.java:3201
       │   └─ PAUSED/PAUSING → 还要 !hasRootPinnedTask（已有 PiP 就挡）                                  ActivityRecord.java:3208
       ├─ new Transition(TRANSIT_PIP) ← 只有「应用主动进」才自建；系统请求不建                          ATMS:3561
       └─ enterPipRunnable → RootWindowContainer.moveActivityToPinnedRootTask(r, null, ..., transition)  ATMS:3572
          └─ moveActivityToPinnedRootTask ← 搬 Task / 换 windowingMode                                   wm/RootWindowContainer.java:1964
             ├─ 已有 rootPinnedTask → collect 旧 PiP 再 removeRootTasksInWindowingModes(PINNED)          :1985-1991
             ├─ singleActivity → rootTask = task（原 Task 原地变 PiP）                                   :1999-2004
             └─ 否则 new Task.Builder(...) + r.reparent(rootTask) → 新 Task 只装 PiP 那个 Activity         :2009-2054
             └─ rootTask.setWindowingMode(WINDOWING_MODE_PINNED) → 状态真源就在这一行                     :2104
                r.mWaitForEnteringPinnedMode = true → 压住可见性提交                                      :2090 → ActivityRecord.java:5350
WM Shell（systemui 进程）：PipTransition.isEnteringPip ← windingMode==PINNED 且 type∈{PIP,OPEN,CHANGE}   pip/PipTransition.java:659-673
 └─ PipTaskOrganizer.onTaskAppeared(info,leash) → TASK_APPEARED → enterPipWithAlphaAnimation               pip/PipTaskOrganizer.java:651/:775
    └─ ENTRY_SCHEDULED(:792) → 动画结束 ENTERED_PIP(:864)；期间参数更新被 mDeferredTaskInfo 挡下(:918)
回程：Task.reparent → ATS.scheduleUpdatePictureInPictureModeIfNeeded(:2287) → REPORT_PIP_MODE_CHANGED_MSG(:2453)
 └─ ActivityRecord.updatePictureInPictureMode(:1482) → Activity.onPictureInPictureModeChanged(true, cfg)  Activity.java:8633
```

基线 AOSP 13，全部已核实（唯一没逐行读的是 `ActivityClientController.ensureValidPictureInPictureActivityParams` 方法体 :893）。12→13 行号漂移 → 必须换：`moveActivityToPinnedRootTask` 12 在 `RootWindowContainer.java:2105`、13 在 `:1964`；`PipTransition.startAnimation` 12 在 `:69`；**12 有 `TaskSupervisor.java`，13 已删，PiP 通知只剩 `ActivityTaskSupervisor.java:2287`**——你现有的《13-画中画.html》是 12 基线，引用时别直接套行号。

## ② 决策点

- **能不能进**：`ActivityRecord.checkEnterPictureInPictureState` 的 `mState` × `hasRootPinnedTask` × `supportsEnterPipOnTaskSwitch` 三维组合（`ActivityRecord.java:3197-3219`）。
- **原地改还是新建 Task**：`singleActivity = task.getNonFinishingActivityCount() == 1`（`RootWindowContainer.java:1999`）。
- **旧 PiP 的命运**：用 `removeRootTasksInWindowingModes(WINDOWING_MODE_PINNED)` 而不是 `Task#dismissPip`（`RootWindowContainer.java:1991`，注释写明：宁可旧 PiP 直接消失，也不要它同时在那一刻变全屏）。
- **动画归谁**：`Transition` 只在 `originallyFromClient` 时新建（`ActivityTaskManagerService.java:3553-3563`），系统 auto-enter 要搭已有 transition 的车。
- **Shell 何时接受参数更新**：`PipTaskOrganizer.onTaskInfoChanged` 只认 `ENTERED_PIP`/`EXITING_PIP`，其余状态推迟到动画结束（`PipTaskOrganizer.java:911-919`、`:257-259`）。

## ③ 我要你答的 3 个问题

1. `ATMS:3561` 只在 `originallyFromClient` 时 `new Transition(TRANSIT_PIP)`。那么用户按 Home 键由系统触发 auto-enter 时，Shell 那边凭什么还能认出"这是进 PiP"并做缩放动画？（提示：你只要找到 Shell 读的是什么信息就够了，不用解释 transition 生命周期。）
2. 多 Activity 的 Task 进 PiP 时为什么必须新建 Task 再 reparent（`:2005-2054`），而不是像单 Activity 那样把原 Task 直接改成 PINNED？如果偷懒不新建，用户会看到什么？
3. `r.mWaitForEnteringPinnedMode = true`（`:2090`）在 `ActivityRecord.java:5350` 挡住的是哪条路径？如果去掉这个标志，PiP 进入动画会出什么毛病？

---

## 骨架阅读法

- **一句话定位**：入口在 `Activity`，判据在 `ActivityRecord:3161`，真搬家在 `RootWindowContainer:1964`，动画在 Shell `PipTaskOrganizer:651`。
- **三个接力边界**：app→system_server（`ActivityClient` Binder :2947）；WMCore→Shell（不传 transition 对象，只靠 `TransitionInfo` 里 task 的 `windowingMode==PINNED`）；system_server→app（config change + `REPORT_PIP_MODE_CHANGED_MSG`）。
- **最小验证命令**：`adb shell dumpsys window | grep -iE "mState=|PipBounds"`（Shell 侧状态机）；没有设备就跑下面的 L0 判据题。
- **本链最贵的一行**：`RootWindowContainer.java:2104` `setWindowingMode(WINDOWING_MODE_PINNED)`——"进入 PiP"唯一的真源，上下游都只是它的因和果。
- **可追问的三个名字**：`mWaitForEnteringPinnedMode`、`PipTransitionState`、`PipBoundsAlgorithm`。

## L0 判据题（零编译，≤15 min，全部在源码树里跑）

**题 1｜门禁只挡 PAUSED，不挡 RESUMED**
- 触发：`cd /home/book/aosp13/frameworks/base/services/core/java/com/android/server/wm && grep -n "return isNotLockedOrOnKeyguard && !hasRootPinnedTask" ActivityRecord.java`
- 判据：输出恰好一行，行号 `3208`。
- 锚点：`ActivityRecord.java:3197-3219`。
- 产出：一句话写进笔记——"已有 PiP 时，PAUSED 的 App 进不去；RESUMED 的 App 不看 `hasRootPinnedTask`，所以第二个 App 抢 PiP 会顶掉旧 PiP（旧 Task 被 `removeRootTasksInWindowingModes` 干掉，:1991）。"

**题 2｜单 Activity 原地变，多 Activity 新建 Task**
- 触发：`cd /home/book/aosp13/frameworks/base/services/core/java/com/android/server/wm && grep -n "final boolean singleActivity" RootWindowContainer.java && sed -n '1999,2001p' RootWindowContainer.java`
- 判据：grep 命中 `1999`，sed 输出的三行里同时出现 `singleActivity` 与 `rootTask = task;`。
- 锚点：`RootWindowContainer.java:1999-2004`、`:2009-2054`。
- 产出："多 Activity 的 App 进 PiP → 新建 Task 只装顶层 Activity，原 Task 留在后面 → 这就是 PiP 一起来、底下的页面露出来的原因。"

**题 3｜进 PiP 期间改参数为什么没反应**
- 触发：`grep -n "Defer onTaskInfoChange" /home/book/aosp13/frameworks/base/libs/WindowManager/Shell/src/com/android/wm/shell/pip/PipTaskOrganizer.java`
- 判据：命中一行，行号 `914`；同文件 `:257-259` 能看到 `mDeferredTaskInfo` 在 `TRANSITION_DIRECTION_TO_PIP` 动画结束时被补发。
- 锚点：`PipTaskOrganizer.java:909-920`、`:257-259`。
- 产出："`setPictureInPictureParams` 在 ENTRY_SCHEDULED/ENTERING_PIP/ENTERED_PIP 之前会被 defer，不是丢了——排障时别急着怪 App。"

答完 ③ 的三问（每问 ≤5 句 + 锚点），我们再挑对不上的那条下钻，然后把结论落进 `D:\workspace\FramworkContent\LAB.md`。
