# 3 节点精读 · Activity 加窗（AOSP 13）

> 只读三段，读完就能自己回答 round-01 的三问。行号全部在 `/home/book/aosp13` 现地核对。

---

## 节点 1：`ActivityThread.handleResumeActivity` —— 加窗三件套

```java
// ActivityThread.java:4835
if (r.window == null && !a.mFinished && willBeVisible) {
    r.window = r.activity.getWindow();          // :4836  拿到 PhoneWindow
    View decor = r.window.getDecorView();       // :4837  DecorView 这时才真正装着 R.layout.xxx
    decor.setVisibility(View.INVISIBLE);        // :4838  先隐身，等 WMS 算完尺寸再显示
    ViewManager wm = a.getWindowManager();      // :4839  →
    // :4842
    l.type = WindowManager.LayoutParams.TYPE_BASE_APPLICATION;
    ...
    wm.addView(decor, l);                       // :4859
}
```

三个条件缺一不可：

| 条件 | 挡的是什么 |
|---|---|
| `r.window == null` | 已经加过窗（重建复用 `mPreserveWindow`，走 `:4845` 只通知 `notifyChildRebuilt`） |
| `!a.mFinished` | Activity 在 `onResume` 里把自己 finish 了 |
| `willBeVisible` | `onResume` 里又启动了别的 Activity，且自己不会被看见（`r.hideForNow = true`，`:4874`） |

**白话**：Activity 自己不画窗口。它把 DecorView 交给 WindowManager，就像把画布交给裱框店——`type` 是“这是主窗口，不是对话框/悬浮窗”的标签。

---

## 节点 2：`applyTokens` + 三张表 —— token 不是 Activity 设的

```java
// WindowManagerImpl.java:146
public void addView(View view, ViewGroup.LayoutParams params) {
    applyTokens(params);                                  // :147
    mGlobal.addView(view, params, mContext.getDisplayNoVerify(), mParentWindow,
            mContext.getUserId());                        // :148
}

// WindowManagerImpl.java:158
private void applyTokens(ViewGroup.LayoutParams params) {
    ...
    if (mDefaultToken != null && mParentWindow == null && wparams.token == null) {
        wparams.token = mDefaultToken;                    // :165-167
    }
    wparams.mWindowContextToken = mWindowContextToken;    // :168
}
```

`mDefaultToken` 来自 WindowContext（Activity 的 WindowContext 绑 ActivityRecord.Token）。所以 WMS 拿到 `attrs.token` 就能 `token.asActivityRecord()`（`WindowManagerService.java:1610`）认出这是哪个 Activity。

```java
// WindowManagerGlobal.addView，:309；锁内
int index = findViewLocked(view, false);                 // :353
if (index >= 0) throw new IllegalStateException(...);    // :360
...
root = new ViewRootImpl(view.getContext(), display);     // :391（带 parent 时 :393）
mViews.add(view); mRoots.add(root); mParams.add(wparams); // :399-401
root.setView(view, wparams, panelParentView, userId);    // :405
```

**白话**：`View`、`ViewRootImpl`、`LayoutParams` 三条平行数组（`mViews/mRoots/mParams`）按下标一一对应。同一个 View 加第二次会直接抛异常——这就是“Activity 重复 addView 崩溃”的现场。

---

## 节点 3：`WMS.addWindow` 的判定顺序 —— 先便宜后昂贵

```java
public int addWindow(Session session, IWindow client, LayoutParams attrs, ...) {   // :1477
    int res = mPolicy.checkAddPermission(attrs.type, isRoundedCornerOverlay, ...); // :1486（锁外）
    if (res != ADD_OKAY) return res;                                              // :1488
    ...
    synchronized (mGlobalLock) {                                                  // :1497（持锁区开始）
        DisplayContent displayContent = getDisplayContentOrCreate(displayId, attrs.token); // :1501
        if (mWindowMap.containsKey(client.asBinder())) return ADD_DUPLICATE_ADD;  // :1518
        WindowToken token = displayContent.getWindowToken(attrs.token);           // :1570
        if (token == null) { ...new WindowToken.Builder(...)... }                 // :1581/:1593/:1602
        else if (rootType 是应用窗口) {
            activity = token.asActivityRecord();                                  // :1610
            if (activity == null) return ADD_NOT_APP_TOKEN;                       // :1614
            if (activity.getParent() == null) return ADD_APP_EXITING;             // :1618
        }
        final WindowState win = new WindowState(...);                             // :1683
        if (win.mDeathRecipient == null) return ADD_APP_EXITING;                  // :1686-1691
        win.attach();                                                             // :1789
        mWindowMap.put(client.asBinder(), win);                                   // :1790
        win.mToken.addWindow(win);                                                // :1802
        displayPolicy.addWindowLw(win, attrs);                                    // :1803
        res = ADD_OKAY;                                                           // :1775
    }
}
```

判定顺序的意义：权限（可能要跨进程查 AppOps）在锁外；进锁后先查 display、再查重复、再查 token、最后才 `new WindowState`。**越昂贵、越需要维护状态的动作越靠后**，前面的分支全是“直接 return 错误码”，不留半成品。

**白话**：`mWindowMap` 是 WMS 侧“我认识的所有窗口”的注册表，key 是 app 侧 `IWindow` 的 binder。`mWindowMap.put` 之前，这个窗口对系统来说不存在；之后，它才会被布局、合成、投递输入。

---

## 白话对照表

| 代码 | 白话 |
|---|---|
| `DecorView` | Activity 的整块画布（标题栏 + 内容区都挂在它下面） |
| `ViewRootImpl` | app 进程里这根“窗口的管子”，负责 measure/layout/draw 和跟 WMS 通讯 |
| `IWindowSession` / `Session` | app 与 WMS 之间的专属客服；`Session` 是 system_server 里的接线员 |
| `IWindow` / `mWindowMap` key | 窗口在 WMS 的身份证号（binder 引用） |
| `WindowToken` | 一组窗口的“户口”，决定它们属于哪个 Activity/哪个系统组件 |
| `WindowState` | WMS 侧的窗口对象：尺寸、可见性、层级、输入通道都记在它身上 |
| `ADD_*` | addWindow 的失败原因码，最终以 `RuntimeException` 的 cause 出现在 app 崩溃栈里 |

## 三个最容易读错的地方

1. **“addView 只是登记，真正加窗在 relayout”** —— 错。`setView` 里 `addToDisplayAsUser`（`:1281`）是**同步**的 binder 调用，`mWindowMap.put` 在 `setView` 返回前就发生了。`relayout`（`:8275`）只负责尺寸/insets/Surface，不负责“窗口存不存在”。
2. **“Activity 会给自己的窗口设 token”** —— 错。Activity 只设置 `type`；token 由 `WindowManagerImpl.applyTokens` 从 WindowContext 补上（`:165-168`），这也是 13 里 `mWindowContextToken` 存在的意义。
3. **“addWindow 失败会抛异常给 app”** —— 只返回 `ADD_*` 码；`ViewRootImpl` 在 catch 里包成 `RuntimeException("Adding window failed")`（`:1303`）。所以 `dumpsys window` 里看不到“加窗失败”，要看 logcat 里的 `WindowManager` 或崩溃栈。

---

## 补：WindowToken 到底"挂"在哪（Activity vs 系统窗口）

`ActivityRecord extends WindowToken`（`ActivityRecord.java:387`），构造时 `super(mWindowManager, new Token(), TYPE_APPLICATION, true, null, false)`（`:1974`）。所以 **Activity 自己的 WindowToken 就是 ActivityRecord**，它在启动阶段随 ActivityRecord 一起挂进 Task，不是 addWindow 时新建的。

`addWindow` 只是查表 + 挂窗口：`displayContent.getWindowToken(attrs.token)`（`WindowManagerService.java:1570`）→ `token.asActivityRecord()`（`:1610`，实现见 `ActivityRecord.java:2217`）→ `win.mToken.addWindow(win)`（`:1802`）。

`mTokenMap` 只是 DisplayContent 的查找表（`DisplayContent.java:1306/:1337`），真正的层级在 Task 里；`addWindowToken` 对 app token 特意不往 DisplayArea 塞：

```java
if (token.asActivityRecord() == null) {          // DisplayContent.java:1339
    // App tokens are added through the parent container managing them (e.g. Tasks).
    findAreaForToken(token).asTokens().addChild(token);
}
```

设备实测（emulator-5554，Task #73 有 2 个 Activity）：

```
$ adb shell dumpsys window tokens | grep -A12 "t73"
  ActivityRecord{de20979 .../.homepage.DeepLinkHomepageActivity} t73}:
    windows=[Window{28db859 ... DeepLinkHomepageActivity}]
    mVisibleRequested=false mVisible=false mClientVisible=false
    mAppStopped=true
  ActivityRecord{134ab6e .../.Settings$MyDeviceInfoActivity} t73}:
    windows=[Window{a40b17e ... Settings$MyDeviceInfoActivity}]
```

结论：**Task 里有 N 个 ActivityRecord 就有 N 个 WindowToken**，每个 token 下挂自己的 WindowState；Activity 只是 stop 时窗口仍留在 token 下（不可见），finish 后 ActivityRecord 被移除、token 才从 `mTokenMap` 摘掉。
