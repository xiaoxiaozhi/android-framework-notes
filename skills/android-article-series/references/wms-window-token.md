# 窗口树的 token 归属与挂载时序（AOSP13 实核）

用于回答「这个窗口挂哪个 token / 为什么有的窗口进 `if (token == null)` / 树建好后叶子是什么 / task 什么时候挂上去」。

## 树骨架

`RootWindowContainer → DisplayContent → DisplayArea（TaskDisplayArea / Tokens）→ Task → TaskFragment → ActivityRecord → WindowState`。

- `Task extends TaskFragment`（Task.java:222），ActivityRecord 的父可能是 TaskFragment（嵌入/PiP），不假定父一定是 Task。
- `ActivityRecord extends WindowToken`（ActivityRecord.java:387），`WindowToken extends WindowContainer<WindowState>`（WindowToken.java:64）。

## 叶子与 token

- 叶子是 `WindowState`；token 是它的父节点 `mToken`（WindowState.java:311），`mActivityRecord = mToken.asActivityRecord()`（:1123）。
- Activity 窗口：`mToken` 就是 ActivityRecord 对象，`asActivityRecord()` 返回 this（ActivityRecord.java:2217），`mActivityRecord != null`。
- 非 Activity 窗口：普通 `WindowToken`，构造末尾 `dc.addWindowToken(token, this)`（WindowToken.java:212），由 `DisplayContent.addWindowToken` 映射 binder 并挂到 `findAreaForToken(token).asTokens()`（DisplayContent.java:1318-1349）；app token 不走这里，由 Task 管理。
- 子窗口（`FIRST_SUB_WINDOW..LAST_SUB_WINDOW`）：不挂 token，构造时 `parentWindow.addChild(this, ...)`（WindowState.java:1219-1223），`WindowToken.addWindow` 对子窗口直接 return（WindowToken.java:282-288）。真正的叶子是「没有子窗口的最上层 WindowState」。
- 区分两个 token：`LayoutParams.token` 是客户端交给 WMS 的 IBinder（app 为 ActivityRecord 的 app token）；`WindowState.mToken` 是服务端父节点对象。

## 挂载时序（三个不同时刻）

1. Task 进树：`Task.Builder.build()` 末尾 `mParent.addChild(task, ...)`（Task.java:6629-6666），创建入口 ActivityTaskManagerService.java:2793、TaskDisplayArea.java:925/988。发生在 startActivity 决策阶段，早于 ActivityRecord attach。
2. ActivityRecord 进树：`ActivityStarter.addOrReparentStartingActivity`（ActivityStarter.java:2721-2752）在 `getTaskFragment()==null` 时 `newParent.addChild(mStartActivity, POSITION_TOP)`（:2749），已有 parent 则 `reparent`；调用点 2699、1629。
3. WindowState 进树：app 侧 `Session.addWindow` → `WMS.addWindow`（WindowManagerService.java:1477）解析 `attrs.token` 命中 ActivityRecord → `new WindowState`（:1683）→ `win.mToken.addWindow(win)`（:1802）→ `WindowToken.addWindow` 里 `addChild(win, mWindowComparator)`（WindowToken.java:300）。

推论：Task 与 ActivityRecord 在 app 调 addWindow 之前就在树上；ActivityRecord 的 `mChildren` 为空是正常中间态，不是漏挂。Task 本身没有窗口树 token，只有 `mTaskId`；`WindowContainerToken` 是 TaskOrganizer 那套标识。

## addWindow 的三个新建 token 分支

1. 有父窗口 → 复用 `parentWindow.mAttrs.token`：PopupWindow、依附型子窗口，随父移动/裁剪/销毁。
2. `windowContextListenerController.hasListener(...)` → 客户端 token、`fromClientToken=true`：`createWindowContext()` 窗口（SystemUI 状态栏/导航栏、浮层），归属随 WindowContext 结束。
3. 兜底 → `attrs.token ?: client.asBinder()`：Application/Service 上下文窗口，一 session 一颗；普通应用须过 `unprivilegedAppCanCreateTokenWith`，否则 `ADD_BAD_APP_TOKEN`。

## 核实命令

```bash
cd ~/aosp13/frameworks/base/services/core/java/com/android/server/wm
grep -n 'extends WindowToken' ActivityRecord.java
grep -n 'class Task extends' Task.java
grep -n 'mToken\|mActivityRecord' WindowState.java | head
grep -n 'addOrReparentStartingActivity' ActivityStarter.java
```

读片段时一次只取 ≤12 行（`awk 'NR>=a && NR<=b' file`），一段一行命令；把多个 `sed` 范围合在一条命令里输出会被压缩截掉中段，恰好藏住要引用的那一行。引用前确认该行出现在本次输出里；仍被压缩就把该段重读到单独一条命令。

## 讲法

先给树骨架与三步挂载顺序，再答「叶子 token 是哪个」；用户问 task 何时挂时按 1→2→3 说清哪一步在 app 建窗之前。用户要短答时压到 350 字以内，只留结论与锚点。