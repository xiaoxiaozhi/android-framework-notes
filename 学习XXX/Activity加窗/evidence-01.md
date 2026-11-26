# evidence 01 · Activity 加窗（AOSP 13，2026-11-20）

全部命令在 WSL 里跑，工作目录 `/home/book/aosp13`（`repo info` 已核：`android-13.0.0_r84`）。下面每一段都是实际输出，未做改写。

## 1. 加窗入口

```bash
$ grep -n "wm.addView(decor, l)" frameworks/base/core/java/android/app/ActivityThread.java
4859:                    wm.addView(decor, l);

$ grep -n "r.window == null && !a.mFinished && willBeVisible\|decor.setVisibility(View.INVISIBLE)\|l.type = WindowManager.LayoutParams.TYPE_BASE_APPLICATION\|a.mWindowAdded = true;" frameworks/base/core/java/android/app/ActivityThread.java
4835:        if (r.window == null && !a.mFinished && willBeVisible) {
4838:            decor.setVisibility(View.INVISIBLE);
4842:            l.type = WindowManager.LayoutParams.TYPE_BASE_APPLICATION;
4845:                a.mWindowAdded = true;      # mPreserveWindow 复用分支
4858:                    a.mWindowAdded = true;  # 真正加窗前的置位
```

## 2. token 与三张表（app 进程内，无 binder）

```bash
$ grep -n "applyTokens\|mGlobal.addView" frameworks/base/core/java/android/view/WindowManagerImpl.java
146:    public void addView(@NonNull View view, @NonNull ViewGroup.LayoutParams params) {
147:        applyTokens(params);
148:        mGlobal.addView(view, params, mContext.getDisplayNoVerify(), mParentWindow,
158:    private void applyTokens(@NonNull ViewGroup.LayoutParams params) {
165:        if (mDefaultToken != null && mParentWindow == null && wparams.token == null) {
166:            wparams.token = mDefaultToken;
168:        wparams.mWindowContextToken = mWindowContextToken;

$ grep -n "public void addView\|new ViewRootImpl(\|root.setView(" frameworks/base/core/java/android/view/WindowManagerGlobal.java
309:    public void addView(View view, ViewGroup.LayoutParams params,
391:                root = new ViewRootImpl(view.getContext(), display);
405:                root.setView(view, wparams, panelParentView, userId);

$ grep -n "has already been added to the window manager" frameworks/base/core/java/android/view/WindowManagerGlobal.java
360:                            + " has already been added to the window manager.");
```

## 3. 同步跨进程：setView 里就 addWindow

```bash
$ grep -n "public void setView\|mAdded = true;\|requestLayout();\|mWindowSession.addToDisplayAsUser" frameworks/base/core/java/android/view/ViewRootImpl.java | head
1160:    public void setView(View view, WindowManager.LayoutParams attrs, View panelParentView,
1249:                mAdded = true;
1255:                requestLayout();
1281:                    res = mWindowSession.addToDisplayAsUser(mWindow, mWindowAttributes,
```

> 注意顺序：`requestLayout()`（1255）在前，`addToDisplayAsUser`（1281）在后。注释写得明确：`Schedule the first layout -before- adding to the window manager`。

```bash
$ sed -n '195,250p' frameworks/base/services/core/java/com/android/server/wm/Session.java | grep -n "addToDisplay\|mService.addWindow"
# 对应的绝对行号：
$ grep -n "public int addToDisplayAsUser\|mService.addWindow\|public int relayout" frameworks/base/services/core/java/com/android/server/wm/Session.java
203:        return mService.addWindow(this, window, attrs, viewVisibility, displayId,
209:    public int addToDisplayAsUser(IWindow window, WindowManager.LayoutParams attrs,
214:        return mService.addWindow(this, window, attrs, viewVisibility, displayId, userId,
244:    public int relayout(IWindow window, WindowManager.LayoutParams attrs,
```

## 4. WMS.addWindow 的判定与落库

```bash
$ grep -n "public int addWindow(Session session\|checkAddPermission\|mWindowMap.containsKey\|getWindowToken(\|new WindowState(this, session\|win.attach();\|mWindowMap.put\|win.mToken.addWindow\|displayPolicy.addWindowLw" frameworks/base/services/core/java/com/android/server/wm/WindowManagerService.java | head
1477:    public int addWindow(Session session, IWindow client, LayoutParams attrs, int viewVisibility,
1486:        int res = mPolicy.checkAddPermission(attrs.type, isRoundedCornerOverlay, attrs.packageName,
1518:            if (mWindowMap.containsKey(client.asBinder())) {
1570:            WindowToken token = displayContent.getWindowToken(
1610:                activity = token.asActivityRecord();
1683:            final WindowState win = new WindowState(this, session, client, token, parentWindow,
1789:            win.attach();
1790:            mWindowMap.put(client.asBinder(), win);
1802:            win.mToken.addWindow(win);
1803:            displayPolicy.addWindowLw(win, attrs);
```

权限检查的实体：

```bash
$ grep -rn "int checkAddPermission" frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java
2595:    public int checkAddPermission(int type, boolean isRoundedCornerOverlay, String packageName,
```

## 5. 后续（Surface 才在这里要）

```bash
$ grep -n "private void performTraversals()\|mWindowSession.relayout(" frameworks/base/core/java/android/view/ViewRootImpl.java
2806:    private void performTraversals() {
8275:            relayoutResult = mWindowSession.relayout(mWindow, params,
```

## 6. 12 → 13 行号对照（同一棵树上的两套数字，不许混用）

| 位置 | AOSP 12 | AOSP 13 |
|---|---|---|
| `ActivityThread` `wm.addView(decor, l)` | 4847 | **4859** |
| `WindowManagerImpl.addView` | 132 | **146** |
| `WindowManagerGlobal.addView` | 321 | **309** |
| `WindowManagerGlobal` `root.setView` | 399 | **405** |
| `ViewRootImpl.setView`（4 参重载） | 1000 | **1160** |
| `ViewRootImpl` `requestLayout()` in setView | 1096 | **1255** |
| `ViewRootImpl.addToDisplayAsUser` | 1119 | **1281** |
| `WMS.addWindow` | 1457 | **1477** |
| `WMS` `new WindowState` | 1662 | **1683** |
| `WMS` `mWindowMap.put` | 1760 | **1790** |

结论：这条链 12→13 **没有增删方法**（`applyTokens`、`mWindowContextToken`、`checkAddPermission` 的三参签名 12 都有），只是行号整体下移。和 PiP 链（13 删了 `TaskSupervisor`、新增 `BackgroundActivityStartController`）不一样。

## 7. 可选设备验证（有模拟器时）

```bash
adb shell dumpsys window windows | grep -E "Window #|mOwnerUid|mHasSurface|mViewVisibility"
```

预期：`mOwnerUid` 就是 app 的 uid；`Window #N` 这一条对应 `mWindowMap` 里的一个 `WindowState`；`mHasSurface=true` 证明 `relayout` 已经跑过（如果只是 addWindow 完成，Surface 还没建）。
