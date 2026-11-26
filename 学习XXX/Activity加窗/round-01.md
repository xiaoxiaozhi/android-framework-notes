# Activity 加窗到 WMS.addWindow · round 01（AOSP 13）

## ① 骨架

> 主线只有一个方向：`ActivityThread` 把 DecorView 交给 `WindowManager`，一路同线程走到 `ViewRootImpl`，再 binder 进 `system_server`。**加窗是同步发生的**，不是第一次 relayout 时才加。

```
ActivityThread.performResumeActivity() → 返回 true 才继续加窗                          ActivityThread.java:4725
 └ handleResumeActivity()  ← r.window==null && !a.mFinished && willBeVisible            ActivityThread.java:4835
   └ decor = r.window.getDecorView() → 先 setVisibility(INVISIBLE)                       ActivityThread.java:4837-4838
     └ ViewManager wm = a.getWindowManager()；l.type = TYPE_BASE_APPLICATION ← 定成主窗口 ActivityThread.java:4839/:4842
       └ wm.addView(decor, l) → 同线程直调，离开 app 前的最后一跳                          ActivityThread.java:4859
         └ WindowManagerImpl.addView() ← applyTokens 只补 mDefaultToken / mWindowContextToken  WindowManagerImpl.java:146/:165
           └ WindowManagerGlobal.addView() → new ViewRootImpl + 三张表登记                 WindowManagerGlobal.java:309/:391-401
             └ root.setView(view, wparams, panelParentView, userId) → 交给 ViewRootImpl    WindowManagerGlobal.java:405
               └ ViewRootImpl.setView() ← mAdded=true(:1249)；requestLayout() 先排队(:1255) ViewRootImpl.java:1160
                 └ mWindowSession.addToDisplayAsUser() → 第一次 binder 跨进程              ViewRootImpl.java:1281
                   └ Session.addToDisplayAsUser() → 原样透传，不做策略                    Session.java:209/:214
                     └ WMS.addWindow() ← checkAddPermission 不过就直接 return 错误码       WindowManagerService.java:1477/:1486
                       ├─ mWindowMap 已有同一 client → ADD_DUPLICATE_ADD                   WindowManagerService.java:1518
                       ├─ getWindowToken(attrs.token)==null → 走“能不能建 token”判断          WindowManagerService.java:1570/:1581
                       └─ 应用类型命中 → asActivityRecord()，null 即 ADD_NOT_APP_TOKEN        WindowManagerService.java:1610/:1614
                         └ new WindowState() → win.attach() → mWindowMap.put() ← 真源        WindowManagerService.java:1683/:1789-1790
                           └ win.mToken.addWindow() → 挂进 token，再 displayPolicy.addWindowLw WindowManagerService.java:1802-1803
异步后续：ViewRootImpl.performTraversals() → mWindowSession.relayout() 才拿到 Surface     ViewRootImpl.java:2806/:8275
```

基线 AOSP 13（`android-13.0.0_r84`，`/home/book/aosp13`，`repo info` 已核）；骨架 18 行全部现地 grep 核实。未核实：`TYPE_APPLICATION_STARTING` 启动窗口与本次 addView 的先后（走 `ActivityRecord.attachStartingWindow`，本轮不展开）。

## 骨架解说（这段在讲什么）

Activity 在 `onResume` 里把 DecorView 交给 WindowManager，最终变成 system_server 里一个被 WMS 认识的窗口。分五段看：

- ① **app 主线程**：`ActivityThread` 拿到 PhoneWindow 和 DecorView，把类型固定成 `TYPE_BASE_APPLICATION`，然后调用 `wm.addView`。
- ② **仍在本进程**：`Window`（PhoneWindow）先把 Activity token 写进 `LayoutParams`（`Window.adjustLayoutParamsForSubWindow`），`WindowManagerImpl.applyTokens` 只补 `mDefaultToken` 和 `mWindowContextToken`——Activity 路径这两个都是空；随后 `WindowManagerGlobal` 建 `ViewRootImpl` 并登记三张平行表。
- ③ **跨进程**：`ViewRootImpl.setView` 把 `mAdded` 置 true、先排一次 traversal，再同步调用 `mWindowSession.addToDisplayAsUser`，binder 进 `Session`，`Session` 原样转给 WMS。
- ④ **system_server**：`WMS.addWindow` 先在锁外查权限，进锁后查 display、查重复、按 token 找归属（Activity 的 token 就是 ActivityRecord），再 `new WindowState` 并 `mWindowMap.put` 落库。
- ⑤ **落库之后**：下一次 `performTraversals` 调 `relayout`，WMS 算尺寸 / insets 并返回 Surface，窗口才真正有内容。

一句话：前四步决定「窗口存不存在」，最后一步决定「窗口长什么样」。

## ② 决策点

- **这是不是“主窗口”**：`l.type = TYPE_BASE_APPLICATION`（`ActivityThread.java:4842`）——同一棵 DecorView，类型决定后面走应用 token 分支还是系统窗口分支。
- **token 谁填的**：Activity 的 token 来自 `Window.mAppToken`：`WindowManagerGlobal.addView` 先调 `parentWindow.adjustLayoutParamsForSubWindow`（`WindowManagerGlobal.java:322`），后者写 `wp.token = mAppToken`（`Window.java:916`）。`applyTokens` 的 `mDefaultToken`（`WindowManagerImpl.java:165-167`）只服务**没有父窗口**的客户端，例如 AccessibilityService 的 overlay（`AccessibilityService.java:2555`）。
- **权限门禁在哪一层**：`mPolicy.checkAddPermission` 在 `synchronized (mGlobalLock)` 之前跑（`WindowManagerService.java:1486` → `PhoneWindowManager.java:2595`），顺序错了会拿着锁做权限检查。
- **同一个 client 能不能加两次**：app 侧 `findViewLocked` 直接抛 `IllegalStateException`（`WindowManagerGlobal.java:353-360`），WMS 侧还有一道 `mWindowMap.containsKey` → `ADD_DUPLICATE_ADD`（`WindowManagerService.java:1518`）。
- **失败为什么是 int 而不是异常**：`addWindow` 全程 return `ADD_*` 错误码（`WindowManagerService.java:1477`），要等 `setView` catch 住再包成 `RuntimeException("Adding window failed")`（`ViewRootImpl.java:1303`）。

## ③ 我要你答的 3 个问题

1. `r.window == null`（`ActivityThread.java:4835`）挡的是哪种情况？`mPreserveWindow` 为 true 时走 `:4845` 那条分支，为什么这时不能再 `addView` 一次？
2. `requestLayout()` 在 `addToDisplayAsUser()` **之前**（`ViewRootImpl.java:1255` vs `:1281`）。如果反过来（先加窗再 requestLayout），第一次 traversal 会拿不到什么？
3. `dumpsys window windows` 里哪个字段能和 `mWindowMap.put(client.asBinder(), win)`（`WindowManagerService.java:1790`）的 key 对上？给出字段名和一条 grep 命令。

## 骨架阅读法

- **一句话定位**：把 Activity 的 DecorView 注册成 WMS 认识的窗口；终点是 `mWindowMap` 里多一个 `WindowState`。
- **三个接力边界**：同线程直调 `ActivityThread.java:4859` → `ViewRootImpl.java:1160`；跨进程 `ViewRootImpl.java:1281` → `Session.java:209`；持锁区 `WindowManagerService.java:1497`–`:1803`。
- **最小验证命令**：`cd /home/book/aosp13 && grep -n "wm.addView(decor, l)" frameworks/base/core/java/android/app/ActivityThread.java && grep -n "mWindowMap.put(client.asBinder(), win)" frameworks/base/services/core/java/com/android/server/wm/WindowManagerService.java`，应得 4859 与 1790。
- **最贵的一行**：`WindowManagerService.java:1790` 的 `mWindowMap.put(...)`——在此之前系统里没有这个窗口，之后才有布局、合成、输入。
- **可追问的名字**：`mDefaultToken`（户口谁给的）、`ADD_DUPLICATE_ADD`（什么情况撞车）、`mRelayoutSeq`（第一次 relayout 怎么和 addWindow 对上）。
