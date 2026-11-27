# AOSP 12 源码速查（为系列文章核对过的位置）

本机 WSL 源码根：`/home/book/aosp12/`
WMS Java 包：`frameworks/base/services/core/java/com/android/server/wm/`

## 层级树的构建（02 篇已覆盖）

- `DisplayAreaPolicyBuilder.java`：Feature / PendingArea / HierarchyBuilder.build() 三层遍历、instantiateChildren。
- `DisplayAreaPolicy.java`：`DefaultProvider.configureTrustedHierarchyBuilder()`，Feature 逐个 addFeature。
- `RootDisplayArea.java`：`onHierarchyBuilt()` 缓存 `mAreaForLayer`（O(1) 查 layer 归属）。
- `DisplayContent.java`：构造时 `mDisplayAreaPolicyProvider.instantiate(...)`。

### 两趟遍历精确锚点（android-12.0.0_r32，已 grep 核实）

改交互模拟器或回答 build() 细节时直接照此，不必重新逐行 grep：

- `DisplayAreaPolicyBuilder.java`：maxWindowLayerCount=getMaxWindowLayer()+1 **:427**；虚拟 PendingArea root 与 `Arrays.fill(areaForLayer, root)` **:458-459**；Pass 1（逐 feature×layer，新建节点挂 `areaForLayer[layer]` 并回写槽位）**:462-490**；Pass 2（Tokens leaf，只 add 到槽位 children，**不回写槽位**）**:493-522**；`root.computeMaxLayer()` :524；`root.instantiateChildren(mRoot, ...)` **:527**；`mRoot.onHierarchyBuilt(...)` **:531**；递归实例化 **:839**（:840 排序、:843 createArea、:848 addChild(POSITION_TOP)、:849-850 feature 登记、:854 递归）；`createArea()`（mExisting=复用 TDA/IME、mSkipTokens 返回 null=TASK/IME 占位跳过）**:859-890**；`addTaskDisplayAreasToApplicationLayer()` :535。
- Feature.Builder：`all()` :649；`upTo()`（填 0..max-1 再 set 本层）:678；`build()` 强制最高层置 false（mExcludeRoundedCorner 默认 true）:703-708。
- `DisplayAreaPolicy.java` `configureTrustedHierarchyBuilder()`：WM **:121**（upTo(a11y mag overlay=32).except(32)，即 0-31，Dimmable）；HDC **:130**（all.except navbar×2/status/shade；默认显示才有）；OHBP **:138**（upTo(wallpaper)）；OH **:143**（all.except navbar×2）；FM **:149**（all.except layer32、IME×2、mag overlay、navbar×2）；IME **:156**（and(IME×2)）。addFeature 顺序即定义顺序。
- `WindowManagerPolicy.java`：getMaxWindowLayer() **:637 return 36**；layer 映射（默认接口方法）:wallpaper :531、IME :563/566、status :569、shade :573、navbar :587/590、mag overlay :600、accessibility overlay :610、a11y mag overlay :613、pointer :619。

### root 身份与 mChildren 存储（回答“root 谁挂的/树存哪”）

- **真实树 root 不是 builder 造的**：`HierarchyBuilder.mRoot` 是 final、构造传入（DisplayAreaPolicyBuilder.java:384、构造器 :390）。它就是 `DisplayContent`（DisplayContent.java:254 `extends RootDisplayArea`），另一子类是分屏用的 `DisplayAreaGroup`（DisplayAreaGroup.java:29）。DisplayContent 在屏幕加入 WMS 时先建好，随后 `DisplayAreaPolicy.java:104 new HierarchyBuilder(root)` 把它塞入；builder 只往它**下面** addChild，从不构造/挂载 root。
- Pass 1 :458 那个 `new PendingArea(null,0,null)` 是**一次性虚拟顶**，Pass 2 只 `instantiateChildren`（实例化它的 mChildren），它自身不落地、被丢弃，孩子直接挂真实 mRoot。
- `onHierarchyBuilt` 回调：接口 RootDisplayArea.java:133，:140 `mAreaForLayer = areaForLayer` 缓存 layer→leaf。
- **树不存在单一总列表**：`WindowContainer.mChildren` 是实例字段（WindowContainer.java:156），每个节点各持一份；`addChild(child,index)` :544（POSITION_TOP 在 :558 折算成 size 追加，POSITION_TOP 常量 :140）；带比较器版本 :514。树 = mChildren 套 mChildren；layer→leaf 数组与 featureAreas 是另外两张独立索引。

### root 直接孩子（Pass 1+2 结束后，已按 mMinLayer 排序）

回答“第 N 层挂在谁下面”时按此判定，parent 一律取该层**当时**的 `areaForLayer[layer]`：

1. `WM 0-31`（Pass 1 layer 0 时槽位还是 root）；
2. `HDC 32-35`（32 不在 HDC except 名单、WM 不覆盖，槽位仍指 root；HDC 其余分段都嵌在 WM 子树里）；
3. `Tokens 36`（Pass 2；rounded corner 层所有 feature 均被强制排除，槽位始终指 root）。

Pass 1 结束时 root 只有前 2 个 child，第 3 个 Tokens 是 Pass 2 才加。同理 WM 下直接挂 24-25 navbar 的 Tokens leaf（HDC/OH/FM 均 except）。模拟器终态统计：featureArea 25 · Tokens leaf 13 · TDA 1 · ImeContainer 1 · TASK 占位 1（L2，createArea 返回 null 跳过，由 DefaultTaskDisplayArea 承接）· 总 41。

## 窗口挂树（02 篇第五章）

第一个具体窗口的完整插树时序（已 grep 核实）：

- 入口 `WMS.addWindow()` **WMS.java:1457**：`:1662 new WindowState`（构造即按 type 算 mBaseLayer/mSubLayer，但此刻未挂树）→ `:1759 win.attach()`（仍无 Surface）→ `:1779 win.mToken.addWindow(win)`。
- **addWindow 内部精确锚点（2026-10-18 grep 核实，讲 token 解析/子窗归属时照此）**：子窗类型判定 **:1502-1515**——子窗的 `attrs.token` 装的是**父窗口 IWindow binder**，`:1503 windowForClientLocked` 在 mWindowMap 查父窗，null→:1507 `ADD_BAD_SUBWINDOW_TOKEN`，父窗自己也是子窗→:1509 同码拒绝；`hasParent` 定义 :1546；查牌三元 **:1549-1550** `displayContent.getWindowToken(hasParent ? parentWindow.mAttrs.token : attrs.token)`（子窗必须绕开自己的 attrs.token，取父窗当初上报的 ActivityRecord binder）；`rootType` :1553；token==null 四分支：特权检查失败 :1561-1562 `ADD_BAD_APP_TOKEN`、子窗复用 :1564-1565 `token = parentWindow.mToken`、WindowContext 新建牌 :1572-1580（`setFromClientToken(true)`）、系统窗口新建牌 :1581-1586（binder = `attrs.token != null ? attrs.token : client.asBinder()`）；系统窗误持 AR 牌则 :1652-1660 置空 attrs.token 后用 client.asBinder() 另造；应用窗口分支 :1592 起 `token.asActivityRecord()`，null→`ADD_NOT_APP_TOKEN`、`activity.getParent()==null`（已脱 Task）→`ADD_APP_EXITING`。
- **窗口类型区间常量（WindowManager.java，2026-10-18 核）**：FIRST_APPLICATION_WINDOW=1 **:1107** / LAST=99 **:1143**（实际仅 1/2/3，TYPE_APPLICATION_STARTING=3 :1131）；FIRST_SUB_WINDOW=1000 **:1151** / LAST=1999 **:1199**（实际仅 1000-1005 六个，ATTACHED_DIALOG=1003 :1176）；FIRST_SYSTEM_WINDOW=2000 **:1205** / LAST=2999 **:1524**；全文件仅 49 个 TYPE_ 常量，编号稀疏=区间策略判断+ABI 不回收+历史废弃号。系统窗具体值：TOAST 2005(:1255)、SYSTEM_OVERLAY 2006(:1265)、SYSTEM_ERROR 2010(:1296)、INPUT_METHOD 2011(:1304)、WALLPAPER 2013(:1318)、STATUS_BAR_PANEL 2014(:1326)、APPLICATION_OVERLAY 2038(:1495)。
- **WindowToken / ActivityRecord 字段锚点（2026-10-18 核）**：WindowToken.java——class :71、`final IBinder token` :75、`final int windowType` :78、removeAllWindowsIfPossible :226、Builder 构造器 :788（mToken=token）、build() :830；**WindowToken 全树仅两个子类**：ActivityRecord（ActivityRecord.java:365）与 WallpaperWindowToken（WallpaperWindowToken.java:44），IME/Toast 等用基类直接 new。DisplayContent mTokenMap 声明 :334、getWindowToken :1122-1123、注册 `mTokenMap.put(binder, token)` :1153。ActivityRecord.java——intent :445、packageName :434、mUserId :431、`WindowProcessController app` :492、getTask :1296、getState :4933、setState :4860、detachFromProcess（`app=null`）:3345-3349。客户端多 Activity 证据：ActivityThread.java `mActivities`（ArrayMap<IBinder, ActivityClientRecord>）:336、`mInitialApplication` :375。
- 非应用窗口 token 在 WindowToken 构造期挂树：`WindowToken.java:222 dc.addWindowToken(token,this)` → **`DisplayContent.addWindowToken()` DisplayContent.java:1134**，`:1163-1164 findAreaForToken(token).asTokens()` → `da.addChild(token)`。查叶子链路：`DisplayContent.findAreaForToken` :6108 → `RootDisplayArea.findAreaForTokenInLayer` :114 → type 经 policy 算 layer → `return mAreaForLayer[layer]` **:129**（建树时填的索引首次被消费；APPLICATION_LAYER 抛异常 :126-128）。
- 叶子登记：`WindowToken.addWindow()` **WindowToken.java:297**：子窗口 :301 直接 return（挂父 WindowState）；`:308` token 自身无 SurfaceControl 时 `createSurfaceControl(true)`；`:312 addChild(win, mWindowComparator)` 按 baseLayer 进 token 的 mChildren。
- 应用窗口：token 就是 ActivityRecord（extends WindowToken），由 ActivityStarter 挂在 Task→TaskDisplayArea 下（TDA 即建树 mExisting 复用的特殊节点），不走 addWindowToken。

## 客户端 addView 链与两个 token（2026-10-15 grep 核实，framework 侧）

讲“View 怎么变成一个窗口”“attrs.token 与 mWindowContextToken 有何区别”“Dialog 为何与 Activity 共用 token”时照此；这是 WMS.addWindow 的上游一环。

- `WindowManagerImpl.addView()` **:131** 先 `applyTokens(params)` **:132**，再调 `mGlobal.addView(view, params, mContext.getDisplayNoVerify(), mParentWindow, mContext.getUserId())`；`updateViewLayout()` **:138** 同样先 `applyTokens` **:139**。
- `applyTokens()` **:143**：只有「`mDefaultToken != null` && `mParentWindow == null` && `wparams.token == null`」三条同时成立才 `wparams.token = mDefaultToken` **:149-150**；随后**无条件** `wparams.mWindowContextToken = mWindowContextToken` **:152**。`mDefaultToken` 由 `setDefaultToken()` **:126** 赋值，全树唯一调用方是 `AccessibilityService.java:968/972/986/2181`。
- `mParentWindow` 只能经 `createLocalWindowManager(Window)` **:106**（→ :107 `new WindowManagerImpl(mContext, parentWindow, mWindowContextToken)`）或 `createPresentationWindowManager` **:110**（→ :111，复用 mParentWindow）设置；裸构造 `WindowManagerImpl(Context)` **:95** 与 `createWindowContextWindowManager(Context)` **:115** 都传 null。字段 `mWindowContextToken` **:93**，构造赋值 **:103**。
- **三个工厂方法（2026-10-16 grep 核实，回答“三个工厂什么时候用”）**：三者都只是私有构造器 **:99** `WindowManagerImpl(Context, Window, IBinder)` 的参数预设，差别在 `(Context, parentWindow, windowContextToken)` 三元组。① `createLocalWindowManager` :106（实例方法，只换 parentWindow）平台内**唯一**调用方 `Window.setWindowManager()` **Window.java:829** → 每个 Window 一诞生就配一个自己的 WM（Activity.attach **:7981/:7988**、Dialog **Dialog.java:210**）；② `createPresentationWindowManager` :110（只换 Context）**12 树内无平台调用方**——`grep -rn createPresentationWindowManager --include=*.java frameworks packages cts` 只命中自身 :110 与 layoutlib 同名 stub `frameworks/layoutlib/bridge/src/android/view/WindowManagerImpl.java:64`（S 起 Presentation 改走 `Presentation.createPresentationContext()` **Presentation.java:327-328** createDisplayContext+createWindowContext，即工厂③）；③ `createWindowContextWindowManager` :115（static，parentWindow=null，唯一带 `context.getWindowContextToken()` :116）调用方 `WindowContext.java:69`（构造器内）、`WindowProviderService.java:119`。类本身 `@hide` WindowManagerImpl.java:72/:74。
- `Window.setWindowManager()` 末行 **Window.java:829** `mWindowManager = ((WindowManagerImpl)wm).createLocalWindowManager(this)` → **每个 Window 的 getWindowManager() 返回的 WM，其 parentWindow 恒等于该 Window 自身**。这就是“parentWindow != null”**不等于**“这是个（子）窗口”的原因，回答 token 归属问题时先讲清这条。
- `WindowManagerGlobal.addView(view, params, display, parentWindow, userId)` **:321**：`:335 parentWindow.adjustLayoutParamsForSubWindow(wparams)`；`:336-345` 无宿主时按 Application 信息补 `FLAG_HARDWARE_ACCELERATED` **:343**；`:351-362` 惰性注册 SystemProperties 回调；`:365 findViewLocked` → `:367 mDyingViews` 命中则 `doDie()`、否则 `IllegalStateException`（同一 View 重复添加）；`:378-386` 子窗口按 `mRoots.get(i).mWindow.asBinder() == wparams.token` 反查 `panelParentView` **:384**；`:389 new ViewRootImpl`；`:393 mViews.add`（mViews / mRoots / mParams 三数组按下标对齐）；`:399 root.setView(...)`，抛异常则 `:403 removeViewLocked(index, true)` 回滚。
- `Window.adjustLayoutParamsForSubWindow(wp)` **Window.java:832**：被改的**永远是正在添加的新窗口**的 wp（不动宿主自己的 mWindowAttributes），按 `wp.type` 分三支——① 子窗口 1000–1999 **:834 起**：`:837 peekDecorView()` → `wp.token = decor.getWindowToken()`，标题按类型取 Panel / Media / Ovr / SubPanel / AtchDlg；② 系统窗口 2000–2999：**不给 app token**（就地注释：生命周期应独立，App 进 stopped 不该带走系统窗口），只设 `"Sys"+type` 标题；③ 其余（含 Activity/Dialog 的 TYPE_BASE_APPLICATION/TYPE_APPLICATION）**:878-886**：`:880 wp.token = mContainer == null ? mAppToken : mContainer.mAppToken`。末尾 **:888** 补 packageName。
- Activity 侧：`Activity.getSystemService(WINDOW_SERVICE)` 被覆写 **Activity.java:6872-6873** 直接返回 `mWindowManager`；`Activity.attach()` **:7981 `mWindow.setWindowManager(…, mToken, mComponent.flattenToString(), hwAccel)`**（mAppToken = ActivityRecord token）、**:7988 `mWindowManager = mWindow.getWindowManager()`**；resume 时 **ActivityThread.java:4827 `ViewManager wm = a.getWindowManager()`**、**:4830 `l.type = TYPE_BASE_APPLICATION`**、**:4847 `wm.addView(decor, l)`** → **Activity 自己的 decor 也走 parentWindow != null 分支，且 parentWindow 就是它自己的 PhoneWindow**，token 走支③ = ActivityRecord token。
- Dialog 侧：**Dialog.java:199 `mWindowManager = context.getSystemService(WINDOW_SERVICE)`**（Activity 覆写了该服务 → 拿到的是 **Activity 的 WM**）、**:210 `w.setWindowManager(mWindowManager, null, null)`**（appToken 传 null，Dialog 自身没有 token 来源）、**:345 `mWindowManager.addView(mDecor, l)`** → Dialog 的 **parentWindow = Activity 的 Window**，token 走支③ = Activity 的 mAppToken → **Dialog 与 Activity 共用同一个 ActivityRecord token**（Activity 销毁后 Dialog.show() 抛 BadTokenException 的根源）。
- WMS 消费 **WindowManagerService.java**：`:1557 attrs.mWindowContextToken`；`:1559 token == null` 分三支——`:1564-1566` 有父窗口则蹭 `parentWindow.mToken`；`:1567-1578` WindowContext listener 命中则用 `attrs.token ?: windowContextToken` 建 WindowToken 并带上 `getOptions` **:1571**；`:1580` 起裸 Context 用 `client.asBinder()` 造匿名 token。窗口建成后 `:1728-1739`：`type != getWindowType(contextToken)` 时 **:1735 `ADD_INVALID_TYPE`**，通过则 **:1739 `registerWindowContainerListener`**（Configuration 精准回调挂到该 token）。
- **attrs.token 的客户端赋值源头（2026-10-18 补核，回答"attrs.token 在哪被赋值"的完整链）**：牌在启动时由系统下发——`ActivityThread.performLaunchActivity` **:3586 `activity.attach(..., r.token, ...)`** → **Activity.java:7959 `mToken = token`** → **:7981 mWindow.setWindowManager(..., mToken, ...)** → **Window.java:823 `mAppToken = appToken`**；之后三条赋值链：①主窗口 Window.java:880 `wp.token = mContainer==null ? mAppToken : mContainer.mAppToken`；②子窗口 Window.java:834-840 `wp.token = decor.getWindowToken()`（取父窗口 ViewRootImpl 的 W/IWindow binder，**不是** ActivityRecord），View.getWindowToken() 在 **View.java:20641**；PopupWindow 更直接：**PopupWindow.java:1620 `p.token = token`**（createPopupLayoutParams，token 来自锚点 anchor.getWindowToken()）；③系统窗口保持 null（:866-869 注释明示生命周期独立），到 WMS 由 client.asBinder() 兜底造牌。
- `WindowManager.LayoutParams` Parcel 字段：**WindowManager.java:2982 mWindowContextToken**、`:3739 setWindowContextToken`、`:3758 getWindowContextToken`、`:3786 writeStrongBinder`、`:3858 readStrongBinder`、`:4027-4030 copyFrom`。
- 一句话区分：`attrs.token` = 窗口**归谁管**（WindowToken / ActivityRecord / 父窗口 binder，决定层级/权限/ANR 归属）；`mWindowContextToken` = **谁生的窗口**（WindowContext 预注册 options → 类型一致性校验 + Configuration 推送）。系统窗口没有可继承的 token 时由客户端自造：`StatusBarWindowController.attach()` **StatusBarWindowController.java:130 `mLp.token = new Binder()`**、**:137 `mWindowManager.addView(mStatusBarView, mLp)`**（该 WM 的 mWindowContextToken 为 null）——所以 SystemUI 建状态栏窗口不必从 AMS 拿 token。

## addWindow 后到首帧上屏（“第一个窗口怎么亮的”，已 grep 核实）

讲“逻辑节点 → 像素”顺序时按此，别在 addWindow 阶段就说有 Surface：

1. addWindow（:1457）只造逻辑节点进 WindowContainer 树，**无 Surface**。
2. 首次 `WMS.relayoutWindow()` :2210，FIRST_TIME 时 :2372 `createSurfaceControl(...)` → `WindowStateAnimator.createSurfaceLocked()` :304 → new WindowSurfaceController 向 SF 申请 Layer（BLAST 回传 SurfaceControl）；容器 Surface 懒创建、parent 取 WindowContainer 父节点，故 SF Layer 树与 WMS 树同构。:2386 `performSurfacePlacement(true)`。
3. App draw → BLASTBufferQueue queueBuffer，首帧入队但未 latch。
4. `WindowSurfacePlacer.performSurfacePlacementLoop()` :133 → mRoot.performSurfacePlacement（下详）→ 布局/可见性/show surface，Z 序走下方 assignChildLayers，事务 apply 跨进程到 SF。
5. SF commit latch 首帧 → VSYNC composite → present 上屏。

## 窗口 → 真实画布（04 篇已覆盖）

链路已核实：

- `WindowManagerService.relayoutWindow()`（约 2210 行）→ `createSurfaceControl(outSurfaceControl, result, win, winAnimator)`（约 2597 行）。
- `WindowStateAnimator.createSurfaceLocked(windowType)`（约 304 行）→ `new WindowSurfaceController(...)`。
- `WindowSurfaceController` 构造器：`win.makeSurface().setParent(win.getSurfaceControl()).setName(...).setBufferSize(...).setFormat(...).setFlags(HIDDEN...)...build()`；BLAST 时 `b.setBLASTLayer()`；`getSurfaceControl(out)` 里 `out.copyFrom(mSurfaceControl)`。
- Surface 父链来源：`WindowContainer.makeSurface()` → 父节点 `makeChildSurface(child)`；
  `DisplayContent.makeChildSurface()`（约 4733 行）用 `setContainerLayer()` + `setParent(mSurfaceControl)`。
- App 侧 `ViewRootImpl`：relayout 调用约 7786 行；`mSurfaceControl.isValid()` 后，非 BLAST 走 `mSurface.copyFrom(mSurfaceControl)`，BLAST 走 `getOrCreateBLASTSurface()`（约 1958 行）→ `new BLASTBufferQueue(tag, mSurfaceControl, w, h, format)` + `createSurface()`，`mSurface.transferFrom(...)`；随后 `mAttachInfo.mThreadedRenderer.setSurfaceControl(mSurfaceControl)`。
- 绘制：`mAttachInfo.mThreadedRenderer.draw(mView, mAttachInfo, this)`（约 4418 行）。

## 渲染篇初始化与帧驱动（2026-10-20 grep 核实）

讲“最开始怎么初始化/谁在推每一帧”时用；addView 细节见上节「客户端 addView 链」，Surface 创建见上节「窗口 → 真实画布」。

- App 启动到首帧：`ActivityThread.main` **:7793** → `attach` **:7513** → `handleBindApplication` **:6432** → `handleResumeActivity` **:4785**（:4847 `wm.addView(decor,l)`）→ `WindowManagerGlobal.addView` **:321** → `new ViewRootImpl` **:389** → `setView` **:399/993** → `enableHardwareAcceleration` **:1409** → `ThreadedRenderer.create` **:231** → `requestLayout` **:1770** → `scheduleTraversals` **:2097**（:2102 `postCallback(CALLBACK_TRAVERSAL)`）→ VSYNC → `doFrame` **:701** → `doTraversal` **:2117** → `performTraversals` **:2510**。
- Choreographer：`CALLBACK_INPUT` **:218**、`ANIMATION` **:225**、`INSETS_ANIMATION` **:241**、`TRAVERSAL` **:248**、`COMMIT` **:260**；`postCallback` **:430**；`scheduleFrameLocked` **:636**；`doFrame` **:701**；`FrameDisplayEventReceiver` **:966**；`onVsync` **:981**。
- 绘制接力：`performMeasure` **:3602** / `performLayout` **:3665** / `performDraw` **:4128** → `ThreadedRenderer.draw` **:4418/613** → `updateRootDisplayList` **:538** → `RenderNode.beginRecording` **:394** / `endRecording` **:426** → `syncAndDrawFrame` **:634**。
- 渲染执行链（2026-10-20 实测，补「谁真正画」）：`performTraversals` **:3306** `performDraw()` → `performDraw` **:4128** → `isHardwareEnabled` **:4381** → `mThreadedRenderer.draw` **:4418** → `ThreadedRenderer.draw` **:613** → `syncAndDrawFrame` **:634** → `HardwareRenderer.syncAndDrawFrame` **:455** → `nSyncAndDrawFrame` **:1308** → `RenderProxy.syncAndDrawFrame` **:136** → `DrawFrameTask.drawFrame` **:125** → `postAndWait` **:135** → `run` **:141** → `syncFrameState` **:150** → `unblockUiThread` **:169** → `context->draw` **:180** → `CanvasContext.draw` **:473** → `mRenderPipeline->draw` **:510** → `swapBuffers` **:532**。
- 开机侧：`SurfaceFlinger.onFirstRef` **:491** → `init` **:774**；`DisplayContent` 建 `"Root"` **:1061-1065**。

## 像素通道：BLASTBufferQueue（native）

- `frameworks/native/libs/gui/BLASTBufferQueue.cpp` 构造器（约 133 行）：
  `createBufferQueue(&mProducer, &mConsumer)` → `BLASTBufferItemConsumer(mConsumer, USAGE_HW_COMPOSER|USAGE_HW_TEXTURE, ...)` → setFrameAvailableListener(this)；
  对目标 layer 打 `eEnableBackpressure` 事务、带 applyToken。
- 即：BufferQueue 留在客户端进程，App 向 producer dequeue/queue buffer，BLAST 消费后通过带 SurfaceControl 的事务把 buffer 送到 SF。

## SurfaceFlinger 侧（04 篇已覆盖：合成与上屏）

- `frameworks/native/services/surfaceflinger/Client.cpp`：`createSurface(...)` → `mFlinger->createLayer(...)`（约 79 行）。
- `SurfaceFlinger.cpp` `createLayer()`（约 4289 行）：按 flags 分 `createBufferStateLayer` / `createEffectLayer` / `createContainerLayer`，再 `addClientLayer(...)`。
- 事务与合成：`commitTransaction()`（约 3232 行）；`postComposition()`（约 2235 行）。
- CompositionEngine：`Output::present()`（约 423 行）→ `prepareFrame()`（约 932 行）；HWC 路径经 Composer HAL `presentDisplay` 交驱动，复杂层回退 GPU（RenderEngine）客户端合成后再作为一层交 HWC。HWC 实现类在 `frameworks/native/services/surfaceflinger/DisplayHardware/HWComposer.cpp`（此前记“本机未命中”是错的，已 `ls`/grep 确认）。

### 显示子系统锚点（2026-10-21 grep 核实，AOSP 12 SP1A）

写 SurfaceFlinger / BufferQueue / 合成上屏系列时直接用；未列出的文件先 `ls` 再引用。

- `frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp`：`init()` **:774**、`initScheduler()` **:3151**、`onMessageRefresh()` **:2049**、`commitTransaction()` **:3232**、`initializeDisplays()` **:4533**。
- `frameworks/native/libs/gui/BufferQueueProducer.cpp`：`dequeueBuffer()` **:379**、`attachBuffer()` **:735**、`queueBuffer()` **:804**、`cancelBuffer()` **:1077**。
- `frameworks/native/libs/gui/BufferQueueConsumer.cpp`：`acquireBuffer()` **:78**、`releaseBuffer()` **:442**。
- `frameworks/native/libs/gui/BLASTBufferQueue.cpp`：`update()` **:193**、`transactionCallback()` **:256**、`processNextBufferLocked()` **:389**、`onFrameAvailable()` **:546**、`createBufferQueue()` **:797**。
- `frameworks/native/libs/gui/SurfaceComposerClient.cpp`：`Transaction::apply()` **:820**、`Transaction::setBuffer()` **:1263**。
- `frameworks/native/services/surfaceflinger/Layer.cpp`：`prepareCompositionState()` **:537**、`prepareClientComposition()` **:590**。
- `frameworks/native/services/surfaceflinger/CompositionEngine/src/Output.cpp`：`prepare()` **:415**、`present()` **:423**、`planComposition()` **:712**。
- `frameworks/native/services/surfaceflinger/CompositionEngine/src/OutputLayer.cpp`：`writeBufferStateToHWC()` **:554**。
- `frameworks/native/services/surfaceflinger/DisplayHardware/HWComposer.cpp`：`setClientTarget()` **:459**、`presentAndGetReleaseFences()` **:566**、`setActiveModeWithConstraints()` **:656**。
- `frameworks/native/services/surfaceflinger/Scheduler/EventThread.cpp`：`onVSyncEvent()` **:353**；`VSyncDispatchTimerQueue.cpp`：`schedule()` **:335**；`Scheduler.cpp`：`onDisplayRefreshed()` **:876**；`RefreshRateConfigs.cpp`：`getBestRefreshRate()` **:220**。
- `frameworks/native/libs/renderengine/skia/SkiaGLRenderEngine.cpp`：`drawLayers()` **:716**。`RenderEngine` 在 `frameworks/native/libs/renderengine/`，不在 `services/surfaceflinger/RenderEngine/`。
- `frameworks/base/services/core/java/com/android/server/display/`：`DisplayManagerService.java` 构造 **:430**、类 **:184**；`LogicalDisplayMapper.java` `updateLogicalDisplaysLocked()` **:369**；`DisplayDevice.java` 类 **:31**。
- `Scheduler/` 这棵树有 `VSyncDispatch.h` 与 `VSyncDispatchTimerQueue.cpp`（实现类是 TimerQueue），不要只按高版本 `VSyncDispatch.cpp` 找；写 VSYNC / 刷新率篇前先 `ls` 该目录。

### VSYNC / Choreographer 六站教学锚点（2026-10-23 grep 核实，AOSP 12 SP1A）

窗口系列读者按依赖顺序补显示子系统地基时用（① vsync 是什么 → ② 为什么两条 → ③ EventThread → ④ 按需 → ⑤ Choreographer → ⑥ WMS 接入），与 display-subsystem-outline.md 的 05 篇五跳数据流互补；用户已给出站点顺序时直接沿用、一次讲一站，别重排。

- **① 硬件中断只当采样源（不触发绘制）**：`SurfaceFlinger.cpp:1718 onComposerHalVsync`（HAL 回调线程；外屏在内部屏判定后直接 return、不喂模型）→ `Scheduler.cpp:548 addResyncSample` → `VSyncReactor.cpp:170 addHwVsyncTimestamp`（:142 periodConfirmed 连续样本间隔稳定才认周期）→ `VSyncPredictor.cpp:94 addVsyncTimestamp`（:91 slope、:240 nextAnticipatedVSyncTimeFrom 回答“未来第 N 拍几点”；模型学准后靠定时器醒，不等中断）。
- **① 闭环：HAL 级硬件 vsync 按需开关，与④分发层按需是两层，讲课时必须分开**：`Scheduler.cpp:487 enableHardwareVsync`（先 tracker->resetModel 再 setVsyncEnabled(true)）/ `:496 disableHardwareVsync`；开关实现链 = `SurfaceFlinger.cpp:1810 setVsyncEnabled` → `HWComposer.cpp:433` → `ComposerHal.cpp:573` → `HWC2.cpp:469` → Composer HAL 面板 TE。预测纠偏通道：`Scheduler.cpp:567 addPresentFence`（present 时间对不上就重新开硬件采样）。软件节拍定时器回调落在 `MessageQueue.cpp:105 vsyncCallback`（注释 `// Trace VSYNC-sf`），:119 initVsync 以名 "sf" 注册 dispatch。
- **② 双相位**：默认值在 `VsyncConfiguration.cpp` PhaseOffsets(Fps) 构造器（约 :86-98；sysprop `vsync_event_phase_offset_ns` / `vsync_sf_event_phase_offset_ns` 默认各 1000000ns；:97-98 high-fps late app=2000000/sf=1000000；:93-96 是 debug.sf.early* 覆盖项）；:148 sfOffsetToDuration、:152 appOffsetToDuration；early/late/earlyGpu 换档走 `VsyncModulator.cpp`。app/appSf 两个 EventThread 连接的创建在 `SurfaceFlinger.cpp:3179-3193`（workDuration=提前量）。`Scheduler.cpp:182 createVsyncSchedule`（tracker+dispatch+reactor 三件套）、:200 makePrimaryDispSyncSource、:296 createDisplayEventConnection；`DispSyncSource.cpp:139 setVSyncEnabled`（CallbackRepeater start/stop）；`VSyncDispatchTimerQueue.cpp:307 registerCallback`。
- **③ EventThread 与连接**（`Scheduler/EventThread.{h,cpp}`）：`EventThread.h:83 EventThreadConnection`（:95 requestNextVsync 声明、私有的 `gui::BitTube mChannel`）；cpp 构造器 :154（:161 `mChannel(gui::BitTube::DefaultSize)`）、:168 onFirstRef→registerDisplayEventConnection、:173 stealReceiveChannel（dup 出一对 fd 给客户端）、:192 postEvent→DisplayEventReceiver::sendEvents 写 BitTube（socketpair，不是 Binder）。sendEvents 调 `BitTube::sendObjects`（BitTube.cpp:148），把 count 个 `DisplayEventReceiver::Event` 当连续字节 count * objSize 交给 `BitTube::write`（:93）；write 最终执行 `::send(mSendFd, ..., MSG_DONTWAIT|MSG_NOSIGNAL)`（:96），socketpair 类型是 `AF_UNIX/SOCK_SEQPACKET`（:49），一次 send 即一条完整消息，接收端 `recvObjects` 按同型 Event 数组读，不走 Parcel；Event 定义在 DisplayEventReceiver.h:61（Header + union：VSync/Hotplug/ModeChange/FrameRateOverride）。**BitTube 头文件真实路径是 `frameworks/native/libs/gui/include/private/gui/BitTube.h`（实现 `libs/gui/BitTube.cpp`），不在 `libs/gui/BitTube.h`**。
- **④ 分发层按需 + 一次性请求状态机（“申请一次给一次”的实现）**：`EventThread.cpp:318 requestNextVsync`（None→Single）、:305 setVsyncRate（rate 0=None，N=每 N 拍一次）、:353 onVSyncEvent（入 mPendingEvents、++count）、:403 threadMain（:432 起只挑 vsyncRequest!=None 的连接；全无请求→:465 setVSyncEnabled(false)）、:519 起 shouldConsumeEvent（Single 命中先翻成 SingleSuppressCallback 返回 true，下一拍把 SingleSuppressCallback 翻回 None 返回 false = 一发即止）、:571 dispatchEvent（-EAGAIN 丢帧、EPIPE 摘连接）；:484-518 驱动停摆 1000ms / 灭屏 16ms 伪造合成 vsync。
- **④ 客户端 native 入口（方法名订正）**：native 层是 `DisplayEventReceiver.cpp:75 requestNextVsync()` 与 `:64 setVsyncRate()`，**没有 native `scheduleVsync`**（grep 此名必落空；scheduleVsync 只存在于 Java/JNI 层）；:40 构造时 `sf->createDisplayEventConnection(vsyncSource, ...)`，binder 端 `ISurfaceComposer.cpp:223/1380`。
- **⑤ Java/JNI/Choreographer**：`view/DisplayEventReceiver.java`：VSYNC_SOURCE_APP=0 **:49**、VSYNC_SOURCE_SURFACE_FLINGER=1 **:57**、nativeScheduleVsync :86、scheduleVsync :247、dispatchVsync :258；JNI `android_view_DisplayEventReceiver.cpp:208 nativeScheduleVsync`（:223 gMethods）。`Choreographer.java`：sThreadInstance :106（:113 建时 VSYNC_SOURCE_APP）、sSfThreadInstance :124（:132 VSYNC_SOURCE_SURFACE_FLINGER）、getInstance :295、getSfInstance :303、USE_VSYNC 受 `debug.choreographer.vsync` 控制；postCallback :430 → postCallbackDelayedInternal :462（:473 入队后 scheduleFrameLocked）、postFrameCallback :534（=CALLBACK_ANIMATION）；CALLBACK_INPUT/ANIMATION/INSETS_ANIMATION(:241)/TRAVERSAL(:248)/COMMIT(:260)；scheduleFrameLocked :636（非 Looper 线程投 MSG_DO_SCHEDULE_VSYNC 异步消息）、doScheduleVsync :860、scheduleVsyncLocked :880；FrameDisplayEventReceiver :966、onVsync :981（不直接干活，按帧时间戳 post 异步消息穿同步屏障）、run :1021→doFrame :701（:725 起 jitter≥帧间隔记 Skipped frames、:770-780 固定 input→animation→insets animation→traversal→commit 顺序）。
- **⑥ 接进窗口系统**：App 侧 `ViewRootImpl.java`：mChoreographer 字段 :467、构造 :812（useSfChoreographer 时取 getSfInstance）、scheduleTraversals :2097（:2100 postSyncBarrier 后 :2101 postCallback(CALLBACK_TRAVERSAL, mTraversalRunnable)）、doTraversal :2117。system_server 侧 `WindowAnimator.java`：:99-100 在 AnimationThread 上 runWithScissors 取 `Choreographer.getSfInstance()`（**WMS 动画跑在 vsync-sf 节拍，回答“动画在 vsync-sf 上跑”就指这里**）、:105 getVsyncId()、:128 animate 开头先 scheduleAnimation 做持续背压、:293 scheduleAnimation→:296 postFrameCallback、:302 cancelAnimation；线程在 `AnimationThread.java`（名 "android.anim"，THREAD_PRIORITY_DISPLAY），`WindowManagerService.java:766 mAnimationHandler = new Handler(AnimationThread.getHandler().getLooper())`、:1248 new WindowAnimator。
- **排障入口核实**：`dumpsys SurfaceFlinger --vsync` 的分发行在 `SurfaceFlinger.cpp:4661 {"--vsync"s, dumper(&SurfaceFlinger::dumpVSync)}`；引用任何 dumpsys 子命令前先在该分发表 grep 名字，不要凭印象写参数。

## 运行时遍历完整调用堆栈（“窗口变了 → 屏幕变了”，已 grep 核实）

回答“全景太笼统/要代码堆栈”时直接照此引用；行号为 android-12.0.0_r32 实测，跨三个进程、三种接力边界。

### 脏标记链（“窗口变化 → 标记脏”，已 grep 核实）

- `WMS.relayoutWindow()` WMS.java:2210 → `windowForClientLocked()` 找 `WindowState` → `win.setRequestedSize(w,h)` WindowState.java:2921：尺寸变了才 `mLayoutNeeded = true`（:2923）→ `win.setDisplayLayoutNeeded()` WMS.java:2328 → `DisplayContent.setLayoutNeeded()` DisplayContent.java:4056 置 `mLayoutNeeded = true`（:4058）→ `performSurfacePlacement(true)` WMS.java:2386 强制同步结算。
- `addWindow/removeWindow` 另置 `WMS.mWindowsChanged = true`：移除在 `postWindowRemoveCleanupLocked()` WMS.java:2060；`DisplayContent.layoutAndAssignWindowLayersIfNeeded()` DisplayContent.java:3575 同时置 `mWindowsChanged` 与 `setLayoutNeeded()`。`mWindowsChanged` 只给输入窗口列表/监听，布局脏看 `DisplayContent.mLayoutNeeded`。
- 异步路径：`WindowSurfacePlacer.requestTraversal()` WindowSurfacePlacer.java:213 → `mTraversalScheduled = true` :220；`mDeferDepth > 0` 时只 `mDeferredRequests++` :221-224，否则 `mAnimationHandler.post(mPerformSurfacePlacement)`。`performSurfacePlacement(true)` 绕过 defer 直接进 `performSurfacePlacementLoop()` :133。
- 强制结算内部的二次排程：`performSurfacePlacementLoop()` WindowSurfacePlacer.java:177 调 `RootWindowContainer.performSurfacePlacement()`，返回后 :179 `if (mService.mRoot.isLayoutNeeded())`，:183 `requestTraversal()`（`mLayoutRepeatCount < 6` 才排）。因此 `relayoutWindow` 的 trace 可间接出现 requestTraversal，不能答成直接调用。
- 两级脏标记：`WindowState.mLayoutNeeded` 是局部工单，`DisplayContent.mLayoutNeeded` 是遍历总开关；`performLayoutNoTrace()` DisplayContent.java:4417 开头 `if (!isLayoutNeeded()) return`，`mPerformLayout` :781 消费窗口级标记并置 false。

入口（二选一）：
- App relayout（同步）：`ViewRootImpl.performLayout` → Binder → `Session.relayout()` Session.java:235 → `WMS.relayoutWindow()` WMS.java:2210 →（首帧）`createSurfaceControl()` :2372 → `mWindowPlacerLocked.performSurfacePlacement(true)` :2386。
- 任意变化（异步）：改动标 layoutNeeded → `WindowSurfacePlacer.requestTraversal()` WindowSurfacePlacer.java:213 → `mAnimationHandler.post(mPerformSurfacePlacement)`【Handler 边界】。

WMS 侧（system_server / Animation 线程，持 mGlobalLock）：
- `Traverser.run()` WindowSurfacePlacer.java:53 → `performSurfacePlacement()` :114 → `(boolean)` :118 → `performSurfacePlacementLoop()` :133 → `RootWindowContainer.performSurfacePlacement()` RootWindowContainer.java:794 → `performSurfacePlacementNoTrace()` :805。
- :805 内：updateFocusedWindowLocked（若 mFocusMayChange）→ `openSurfaceTransaction()` → `applySurfaceChangesTransaction()` :1045 → 逐 DisplayContent：`DisplayContent.applySurfaceChangesTransaction()` DisplayContent.java:4268。
- :4268 do/while（≤6 次）：`performLayout(initial,false)` :4408 → `performLayoutNoTrace()` :4417 → 两遍 `forAllWindows`（`WindowContainer.forAllWindows(Consumer)` WindowContainer.java:1409 → 递归 :1391【DFS 边界】→ 回调 `mPerformLayout` DisplayContent.java:781 算 frame）；随后 `forAllWindows(mApplyPostLayoutPolicy)` :869 → DisplayPolicy.applyPostLayoutPolicyLw；pendingLayoutChanges!=0 则重入。
- 收敛后：`forAllWindows(mApplySurfaceChangesTransaction)` 回调 :873（遮挡/调光/commitFinishDrawingLocked）→ `prepareSurfaces()` :4872 → `WindowContainer.prepareSurfaces()` 递归 :2426 → mergeToGlobalTransaction。
- 回 :1045：`DisplayManagerInternal.performTraversal(...)` + `SurfaceControl.mergeToGlobalTransaction(...)`；回 :805：`closeSurfaceTransaction(...)` → Binder 到 SF【跨进程边界】。

Z 值写入（在上述事务中）：`DisplayContent.assignWindowLayers()` :3557 → `assignChildLayers(getSyncTransaction())` :3559 → `DisplayContent.assignChildLayers(t)` :4817（先 assignRelativeLayerForIme）→ `WindowContainer.assignChildLayers(t)` :2290（两遍：普通孩子 + needsZBoost）→ `assignLayer()` :2240 → `setLayer(t,layer)` :2266；叶子 `WindowState.assignLayer`（IME 目标走相对层级）。

SF 侧（独立进程，VSYNC，非同线程）：
- INVALIDATE：`SurfaceFlinger::onMessageReceived` SurfaceFlinger.cpp:1862 → `onMessageInvalidate` :1876 → `commitTransaction()` :3232（锁存几何/Z/可见性 + buffer）。
- REFRESH：`onMessageReceived(REFRESH)` :1862 → `onMessageRefresh()` :2049（按 Z 序收集可见 Layer）→ `CompositionEngine::present()` CompositionEngine.cpp:91（preComposition → output->prepare → `Output::present()` Output.cpp:423：update/plan/writeCompositionState → beginFrame → `prepareFrame()` :932 → finishFrame → postFramebuffer：HWC presentDisplay，或 GPU RenderEngine 先合成一块再交 HWC → 驱动 → 面板扫描）。
- 收尾：`postFrame()` + `postComposition()` SurfaceFlinger.cpp:2235（回收 buffer、通知可画下一帧）。

## SystemUI 启动链与状态栏建窗（2026-10-13 已 grep 核实，源码树 packages/SystemUI）

回答"SystemUIApplication#startServicesIfNeeded 怎么启动 StatusBar / 数组里怎么没有 StatusBar"时照此：

- 资源 `res/values/config.xml`：`config_systemUIServiceComponents` **:314**，第 5 个 item 就是 `com.android.systemui.statusbar.phone.StatusBar` **:319**（KeyguardViewMediator/Recents/VolumeUI 之后）。**易混点**:`config_systemUIServiceComponentsPerUser` **:348** 只有 NotificationChannels,本就不含 StatusBar——"数组里没 StatusBar"先确认看的是不是 perUser 数组,或厂商 overlay 是否删改。vendor 占位项引用 `@string/config_systemUIVendorServiceComponent`（:344，默认 VendorServices）。
- `SystemUIApplication.java`：`onCreate()` **:75**（:83-86 取 RootComponent/SysUIComponent/ComponentHelper）；无参 `startServicesIfNeeded()` **:161** 读数组后调私有重载；secondary 用户走 **:175**；私有 `startServicesIfNeeded(metricsPrefix, services)` **:178**。
- 循环体（:203-238）：**SystemUIApplication.java:209** `mComponentHelper.resolveSystemUI(clsName)` 先走 Dagger Map 拿实例；返回 null 才反射 `Class.forName(clsName).getConstructor(Context.class)` 兜底（:210-214）；随后 `mServices[i].start()`（约 :223）、boot 完成则 onBootCompleted、注册 DumpManager。
- `ContextComponentResolver.resolveSystemUI()` **ContextComponentResolver.java:91** → `resolve(className, mSystemUICreators)`（:93）：按 Class 查 `Map<Class<?>, Provider<SystemUI>>`，有 Provider 则 `provider.get()`（Dagger 注入构造），无则返回 null 走反射。
- Dagger 绑定：**SystemUIBinder.java:122-126** `@Binds @IntoMap @ClassKey(StatusBar.class) bindsStatusBar(StatusBar)`——字符串类名能在 Map 里命中 StatusBar 靠这条。
- `StatusBar.java`（:268 `extends SystemUI`）：`start()` **:918**；:968-972 `mBarService.registerStatusBar(mCommandQueue)` 跨进程注册到 system_server 的 StatusBarManagerService；**:975 `createAndAddWindows(result)`**。
- 建窗：`createAndAddWindows()` **StatusBar.java:2828** = `makeStatusBarView()` + `mNotificationShadeWindowController.attach()` + `mStatusBarWindowController.attach()`；视图膨胀在 `inflateStatusBarWindow()` **:1585**（SuperStatusBarViewFactory 取 NotificationShadeWindowView/StatusBarWindow，建 StatusBarComponent）。attach 之后最终由 `StatusBarWindowController.attach()` 加状态栏窗口（落进 DisplayArea 树的 StatusBar Feature 槽）——**已 grep 补核（2026-10-15）**：`StatusBarWindowController.attach()` **:117**，`:124 mLp` 定为 `TYPE_STATUS_BAR`，`:130 mLp.token = new Binder()`（自造 token，无 AMS 下发），`:137 mWindowManager.addView(mStatusBarView, mLp)`。
- **版本差异（已核）**：此 AOSP12 树**没有 SystemBars.java**（find 无结果），也没有 per-display SystemBar 字符串数组；不要凭高版本印象讲 SystemBars→StatusBar 包装链。

## 05–11 篇学习路线图锚点（2026-10-14/15 grep 核实；2026-10-18 篇号顺延）

> **篇号变更（2026-10-18）**：06 篇已由「窗口的诞生」（addView → addWindow → WindowState 上树）占用，原 06「Activity/Task 与窗口生命周期」整体顺延为 **07 篇**；后续阶段相应顺延（08 布局/Insets/旋转、09 动画、10 IME/壁纸、11 多屏多窗）。本节各小节标题的编号已按新篇号写，锚点行号本身未变。

规划文档：`<系列目录>\WMS学习路线图.md`（阶段 0 工具箱 → 05 输入 → 06 窗口的诞生 → 07 Activity/Task 生命周期 → 08 布局/Insets/旋转 → 09 动画 → 10 IME/壁纸 → 11 多屏多窗，含每阶段实战问题与实验）。用户要学习路线/章节规划时先读它，锚点直接照用本节。

### 版本/路径事实（防被高版本资料带偏）

- 本树**没有 TaskFragment.java**（12L/API32 才有）；任务容器 `Task`（Task.java:252 `extends WindowContainer<WindowContainer>`）。
- WMS/ATMS 同包同锁：全局锁在 **ATMS.java:362 `mGlobalLock`**（WindowManagerGlobalLock），:370 `mGlobalLockWithoutBoost` 是同一对象；WMS.java:683 `RootWindowContainer mRoot`。
- `PhoneWindowManager` 在 `frameworks/base/services/core/java/com/android/server/policy/`（**不是** wm/policy，该目录不存在）。
- `ImeContainer` 嵌套定义在 DisplayContent.java 内，无独立文件；wm/ 下只有 ImeInsetsSourceProvider.java。
- tracing 类是 **WindowTracing.java**（不是 WindowManagerTraceController）：:48 类、:98 startTrace、:191 isEnabled；shell 入口 WindowManagerShellCommand.java:85 `tracing`→:89 转 mWindowTracing。
- 冻结显示方法名不对称：**`startFreezingDisplay(...)` WMS.java:5702/5706/5711 三个重载（名字不带 Locked）** vs **`stopFreezingDisplayLocked()` WMS.java:5762**；DisplayContent.java:3008 只是 stop 调用点。旋转截屏对象 ScreenRotationAnimation 在 WMS.java 约 :5757 构造；配置冻结链入口 `DisplayContent.updateOrientation(Configuration, WindowContainer freezeDisplayWindow, boolean forceUpdate)` DisplayContent.java:1453。

### 05 输入事件与窗口命中（native 根：frameworks/native/services/inputflinger/）

- 建通道：WMS.addWindow 内 :1687-1690 `win.openInputChannel(outInputChannel)` → WindowState.java:**2689** openInputChannel，:2694 `mInputManager.createInputChannel(name)`；句柄 WindowState.java:607 mInputChannel / :615 mInputChannelToken。无输入窗口走 `Session.addToDisplayWithoutInputChannel` Session.java:209（正常 addToDisplay :189）。
- 窗口列表快照给 native：InputMonitor.java：:72 类、:338 `updateInputWindowsLw(boolean force)`、:360 updateInputWindowsImmediately、:270 populateInputWindowHandle（填 touchable region/token/focusable）、:490 updateInputWindows(inDrag)、:582 逐窗口 populate。IMS 在 `com/android/server/input/InputManagerService.java`（**不是 am/input**）：:149 类、:476 start；JNI：`services/core/jni/com_android_server_input_InputManagerService.cpp`（setInputWindows 桥在此）。
- InputDispatcher（dispatcher/InputDispatcher.cpp）：:559 起线程（名 "InputDispatcher"）、:572 dispatchOnce、:683 dispatchOnceInnerLocked、:1455 按键焦点路径、:1786 `findFocusedWindowTargetsLocked`、:1557/:1900 `findTouchedWindowTargetsLocked`（触摸命中/分裂/模态/遮挡）、:640 processAnrsLocked、:671 窗口 ANR、:5515 onAnrLocked(Connection)、:5550 onAnrLocked(InputApplicationHandle)、:5634 `notifyNoFocusedWindowAnr`、:5642 `notifyWindowUnresponsive`。
- 超时常量：InputDispatcher.cpp:102 DEFAULT_INPUT_DISPATCHING_TIMEOUT；基值 **5000ms 定义在 `frameworks/native/libs/input/android/os/IInputConstants.aidl:26`**（UNMULTIPLIED_DEFAULT_DISPATCHING_TIMEOUT_MILLIS = 5000），× HW_TIMEOUT_MULTIPLIER（Java 镜像 android/os/InputConstants.java:20-23）。
- 上游：reader/InputReader.cpp:73 "InputReader" 线程→:86 `loopOnce()`；同目录 EventHub.cpp（evdev）。
- Policy 拦截：PhoneWindowManager.java:3383 interceptKeyBeforeQueueing、:3964 interceptMotionBeforeQueueingNonInteractive。
- 焦点：DisplayContent.java:3362 findFocusedWindow、:3387 updateFocusedWindowLocked。
- App 侧：ViewRootImpl.java:8438 enqueueInputEvent、:8478/:8493 doProcessInputEvents、:8520 deliverInputEvent；接收端 android/view/InputEventReceiver.java:38。

### 06 窗口的诞生（addView → addWindow → WindowState 上树，2026-10-18 已写）

已落盘 `android-window-06-window-creation.html`；正文按「客户端 addView 四块（A–D2）→ Session → 服务端 addWindow 五块（E–I）→ BadTokenException 闭环 → 源码速查」组织，讲课时照它的块划分引用即可。

- **`WindowState` 构造函数九步（WindowState.java:1042-1162，2026-10-18 grep 核实，讲“new WindowState 都做了什么”照此）**：① :1046-1055 认身份（`super(service)`、mSession/mClient/mAppOp/mToken、`mActivityRecord = mToken.asActivityRecord()`、mOwnerUid/mShowUserId/mOwnerCanAddInternalSystemWindow）；② :1056-1061 `new WindowId(this)`、**`mAttrs.copyFrom(a)` 防御性拷贝**、mLastSurfaceInsets/mViewVisibility/mPolicy/mContext；③ :1062-1103 `c.asBinder().linkToDeath(deathRecipient,0)`，RemoteException 分支把字段置假值后 **return（半成品对象，调用方靠 `mDeathRecipient == null` 判 ADD_APP_EXITING）**；④ :1065-1081 `new InputWindowHandleWrapper(new InputWindowHandle(...))` + setOwnerPid/Uid/Name/PackageName/LayoutParamsType/TrustedOverlay；⑤ :1105-1131 定 Z 序（子窗抄父窗 `mBaseLayer`、自己取 `mSubLayer = getSubWindowLayerFromTypeLw`；否则自算 baseLayer、subLayer=0），:1131 `mIsFloatingLayer`；⑥ :1133-1137 mShowForAllUsers 补 FLAG_SHOW_WHEN_LOCKED；⑦ :1139-1148 `new WindowStateAnimator(this)` + mWinAnimator.mAlpha + requested/lastRequested 尺寸置 0 + compat scale；⑧ **:1150-1155 子窗 `parentWindow.addChild(this, sWindowSubLayerComparator)`（子窗上树点，注释：先初始化全部字段再挂）**；⑨ :1157-1161 登记 mWpcForDisplayAreaConfigChanges。职责边界：构造完不进任何表、不分配 Surface（mWindowMap.put / openInputChannel 在 WMS :1662 之后）。
- 上游链：`WindowManagerGlobal.addView` :321 → `ViewRootImpl.setView` :1090-1140（:1096 requestLayout 在 :1119 addToDisplayAsUser 之前）→ :1150 起错误码翻译成异常 → `Session.addToDisplayAsUser` :200 → `WMS.addWindow` :1457。

### 07 Activity/Task 启动链与窗口生命周期（原 06，编号 2026-10-18 顺延）

- 启动链：ATMS.java:1144 startActivity → ActivityStarter.java:611 execute → :665/:811 executeRequest → :1177/:1548 startActivityUnchecked → :1570 startActivityInner（launchMode/task 复用/回退栈）。
- **入口方法内部（grep 核实，讲 startActivityAsUser 时照此，不必重新逐行读）**：Binder 版 12 参 **ATMS.java:1169** 只补 `validateIncomingUser=true` 转调私有 13 参 **:1179**；私有版只有三步——`assertPackageMatchesCallingUid` **:1182**、`enforceNotIsolatedCaller` **:1183**、`checkTargetUser` **:1185**（→ ActivityStartController.java:243，`validateIncomingUser=false` 时只 `ensureNotSpecialUser` 跳过跨用户权限）——然后 `obtainStarter(intent,"startActivityAsUser")` **:1189** 连 12 个 setter，`:1197 .execute()`。**入口本身不持锁**，锁在 `ActivityStarter.execute()` 的 `synchronized (mService.mGlobalLock)` **ActivityStarter.java:619**。Starter 是池化对象：`ActivityStartController.obtainStarter` **:120** → `mFactory.obtain()` → ActivityStarter.java:**282** 从 `mStarterPool.acquire()`，回收 `reset(true)`。
- **锁与树的归属相反（写「两边入口」时必须点名，否则读者必追问）**：锁由 ATMS 建 `:362 new WindowManagerGlobalLock()`，WMS 在构造器取用 **WindowManagerService.java:1211 `mGlobalLock = atm.getGlobalLock()`**；两边 Binder 入口排在同一 monitor 上——WMS.addWindow **:1457**（锁 **:1477**）、relayoutWindow **:2210**（锁 **:2221**），`synchronized (mGlobalLock)` 出现次数 ATMS 174 / WMS 223。
- 身份：ActivityRecord.java:365 `extends WindowToken`（Activity 即 token）；WindowToken.java:71 `extends WindowContainer<WindowState>`；Task.java:252；RootWindowContainer.java:175；KeyguardController.java:65。
- Starting window：StartingSurfaceController.java:46 类、:60 createSplashScreenStartingSurface、:115 createTaskSnapshotSurface；12 优先 TaskOrganizerController.addStartingWindow（**入口 :550，per-organizer 转发 :125/:134**；旧记的「:71/:151」是错的）→ ShellStartingSurface，即 SystemUI Shell 接管。同目录 SnapshotStartingData/SplashScreenStartingData/StartingData。
- 绘制状态机：WindowState.java:2091 isDrawn、:2006 isReadyForDisplay、:322 mViewVisibility（:1059 赋值）、:1263 调 computeFrame（:1274 定义）；首绘翻转 commitFinishDrawingLocked 在 03 篇 mApplySurfaceChangesTransaction 回调链。
- 删除：WindowState.java:2418/:2423 removeIfPossible（条件/延迟）、:2362 removeImmediately。

### 08 布局 / Insets / 旋转 / 配置（2026-10-18 复核并补齐）

- 布局：DisplayContent.java:4417 performLayoutNoTrace（:4411 调用、开头 `if (!isLayoutNeeded()) return` 是 deferred 机制的前提）、:781 mPerformLayout 回调（逐窗判断 `isGoneForLayout()` → `w.mLayoutNeeded=false` → policy 布局）→ WindowState.java:1274 computeFrame。
- **policy 侧两个方法别混**：DisplayPolicy.java:181 类、**:1070 addWindowLw(WindowState, LayoutParams)** 是**窗口加入时**的登记（switch type 存 mNotificationShade 等），**:1561 layoutWindowLw(WindowState win, WindowState attached, DisplayFrames)** 才是**每轮布局**逐窗算 frame 的地方（开头 `if (win.getParentWindow() != null) return` 跳过子窗）；三个边界区间 systemDecorBounds/nonDecorBounds/stableBounds 在它内部组装。
- Insets：InsetsStateController.java:64（每屏一份）、:117 getInsetsForWindow、:234 getRawInsetsState、:264 getSourceProvider、:275 getImeSourceProvider、:289 **onPostLayout()（遍历 provider 调 `provider.onPostLayout()`，再比对 mLastState 与 mState，变了才 notifyInsetsChanged）**、:317 updateAboveInsetsState；InsetsSourceProvider.java:68、**:198 updateSourceFrame()**（用宿主窗口 frame 算 inset 区域；`mWin == null || mWin.mGivenInsetsPending` 时直接 return）、**:304 updateControlForTarget(InsetsControlTarget, boolean force)**、:390 setServerVisible、:439 isClientVisible；另 ImeInsetsSourceProvider.java:48、InsetsPolicy.java:62、InsetsControlTarget.java:27（接口）。
- frame 里的 insets 参与：WindowState.java:1262 computeFrameAndUpdateSourceFrame()（算完 frame 再 `updateSourceFrame(getLayoutingWindowFrames().mFrame)`）、:1274 computeFrame（开头 mWillReplaceWindow 冻结分支、`mHaveFrame = true`、按 `isFullscreenAndFillsArea`/`windowsAreFloating` 分流）、:1310 起用 `displayInfo.appRect`（全屏）或 Task bounds 当容身框，并算 `isImeTarget` 决定谁被 IME 顶起。**appRect 是「屏幕减系统装饰」的产物——App 那部分不是被裁掉，而是一开始就没分给它。**
- 旋转：DisplayRotation.java:84 类、:384/:393 入口、:415 updateRotationUnchecked（开头三种 defer：rotation 暂停 / 旋转动画未结束 / mDisplayFrozen）；冻结方法见上方「版本/路径事实」；DisplayContent.java:1357 是 startFreezingDisplay 的调用点之一。
- 配置：ActivityRecord.java:7142 resolveOverrideConfiguration、:7697 onConfigurationChanged、:7950/:7969 ensureActivityConfiguration。
- 模拟命令：WindowManagerShellCommand.java:75 size、:77 density、:106 user-rotation、:110 set-ignore-orientation-request、:122 reset。

### 09 动画与过渡（2026-10-18 复核并补齐）

- 转场状态机：AppTransition.java:158 类、:167 DEFAULT_APP_TRANSITION_DURATION=336ms、:350 isReady、:497 setAppTransitionState、**:990 loadAnimation(LayoutParams, transit, enter, uiMode, …)（transit → Animation 的入口）**、:1200 起 overridePendingAppTransition / :1316 overridePendingAppTransitionRemote（应用自定义动画的下发点）。
- **leash 缰绳（核心机制：往目标 Layer 与父 Layer 之间插一个可操控中间 Layer，动画只动 leash）**：SurfaceAnimator.java:49 类、:58 `SurfaceControl mLeash`、:134 startAnimation(Transaction, AnimationAdapter, hidden, type, OnAnimationFinishedCallback, SurfaceFreezer)（:163/:169 重载）、:150 走 createAnimationLeash、:153 onAnimationLeashCreated 回调、**:384 createAnimationLeash 定义（内部 `t.reparent(surface, leash)`）**、:223/:304 cancelAnimation、:335 reset(Transaction, destroyLeash)。
- leash 两侧接口在 **WindowContainer.java**：:2537 makeAnimationLeash()、:2542 getAnimationLeashParent()、:2837 onAnimationLeashCreated(Transaction, SurfaceControl)（内部 reassignLayer + resetSurfacePositionForAnimationLeash）。
- **帧驱动链（谁在推每一帧，之前缺的一环）**：WindowAnimator.java:128 `private void animate(long frameTimeNs, long vsyncId)`（开头就 scheduleAnimation 做背压）→ :293 **scheduleAnimation()** → :296 `mChoreographer.postFrameCallback(...)`（:300 cancelAnimation 解除，:310 isAnimationScheduled，:314 getChoreographer）。
- 动画真正执行：SurfaceAnimationRunner.java:48 类、**:134 startAnimation(AnimationSpec, SurfaceControl animationLeash, Transaction, …)**（在 leash 上跑 AnimationSpec，:267 RunningAnimation）。
- 窗口应用动画：WindowStateAnimator.java:99/:181 `WindowAnimator mAnimator`、**:701 applyAnimationLocked(int transit, boolean isEntrance)**（policy selectAnimation → AnimationUtils.loadAnimation；先判 `mWin.mToken.okToAnimate()`、同类型动画已在跑就直接复用）；WindowState.java:5226 startAnimation(Animation)、:5265 private startAnimation(Transaction, AnimationAdapter)、**:4971 onExitAnimationDone()**、:544 mAnimatingExit、:2055 isAnimatingLw。
- Shell 接管与远程动画：TaskOrganizerController.java:69 类、**:550 boolean addStartingWindow(Task, ActivityRecord, int launchTheme, TaskSnapshot)（入口；:125 是 per-organizer 转发、:134 调 mTaskOrganizer.addStartingWindow）——旧记的「:71/:151」是错的**；RemoteAnimationController.java:55 类、:107 goodToGo(int transit)；WindowContainerTransaction 为应用侧改层级事务 API。
- **版本事实**：12 上转场主力 = AppTransition + SurfaceAnimator(leash) + TaskOrganizer/RemoteAnimation；TransitionController / Shell Transitions 整套是 13/14 主线，12 上不是主线。
- 教学定位（2026-10-18 用户问「动画重要吗」时的答法）：动画是**窗口树的第三种改造方式**（① add 长节点 ② remove 摘节点 ③ 动画临时插 leash 中间节点，事后抽掉）——不懂 leash 会在 Winscope 里看到「凭空多出来的 Layer」。岗位权重：二线，但对手机厂商动效/车机多屏联动/稳定性（leash 泄漏→画面卡半透明、starting window 与 transition 不同步→闪两次）是刚需。

### 10 IME 与壁纸

- IMMS 实际路径 `com/android/server/inputmethod/InputMethodManagerService.java`：:3261 startInputOrWindowGainedFocus（→:3266 Internal 版，焦点变化重绑编辑器）、:3114 showCurrentInputLocked（:1096/:2312/:3083 调用点）。
- WMS 侧：ImeContainer（嵌 DisplayContent.java）、IME 相对 Z 序见 03 篇 assignRelativeLayerForIme、ImeInsetsSourceProvider（与 07 同线）。
- WallpaperController.java:60 类（壁纸目标选择、滚动 offset、固定 wallpaper layer）。

### 多屏多窗（11，按需核）

- windowingMode/TaskPositioner/freeform/pinned；12 上分屏由 Shell 经 TaskOrganizer 实现，WMS 只提供容器与策略钩子。具体行号未核，写篇前重新 grep。

### Binder 全链路（2026-10-18 grep 核实；教学/写篇均照此）

讲「一次跨进程调用经历了什么」时用；六层＝Java → JNI → Native → 驱动 → 对端 Native → 对端 Java。

- **Java 侧**（`frameworks/base/core/java/android/os/`）：`Binder.java:803 onTransact`、**:1057 transact（本地直通：直接调 onTransact，不走 IPC）**、`:1074 linkToDeath`（**本地实现是空方法**，只有 `BinderProxy` 才真向驱动登记——这是 06 篇 `mDeathRecipient == null` 判 ADD_APP_EXITING 的底层）、`:1080 unlinkToDeath`、`:1087 checkParcel`（**≥800KB 就告警**）、`:1136 execTransact`（JNI 回调进 Java 的落点）、`:1149 execTransactInternal`（★ `getCallingUid()` 从**线程 TLS** 读，值由 native 从驱动写入，调用方伪造不了）；`BinderProxy.java:48 类`、`:458 构造(持 nativeData)`、**:516 transact**（先 `Binder.checkParcel`）；`IBinder.java:93 FIRST_CALL_TRANSACTION`、`:102 PING_/ :107 DUMP_/ :119 INTERFACE_TRANSACTION`、`:307 interface DeathRecipient`（:308 binderDied）；`ServiceManager.java:110 getIServiceManager`（**handle 0 起点，鸡生蛋的特例**）、`:128 getService`、`:148 getServiceOrThrow`、`:165 addService`。
- **JNI**（`frameworks/base/core/jni/android_util_Binder.cpp`）：`:81 gBinderOffsets`（方法 ID 缓存表）、`:340 class JavaBBinder : public BBinder`（持 Java 对象全局引用）、**:407 `CallBooleanMethod(mObject, gBinderOffsets.mExecTransact, …)`（★ C++ 调回 Java 的全世界关键一行）**、`:1094 int_register_android_os_Binder`、`:1382 android_os_BinderProxy_transact`。
- **Native**（`frameworks/native/libs/binder/`）：`ProcessState.cpp:45 DEFAULT_MAX_BINDER_THREADS 15`、`:76 self()`、`:139 startThreadPool()`、**:148 becomeContextManager()**；`IPCThreadState.cpp:617 joinThreadPool`（`BC_ENTER_LOOPER`/`BC_REGISTER_LOOPER`；`result == TIMED_OUT && !isMain` 就退线程）、**:685 transact**（非 oneway 才等 `BR_REPLY`；oneway 仍要等 `BR_TRANSACTION_COMPLETE`，否则缓冲区被覆盖）、`:875 waitForResponse`、**:975 talkWithDriver（★ `ioctl(BINDER_WRITE_READ)` 就在这，跨进程发生在这一行之内）**、`:1125 executeCommand`（`BR_TRANSACTION`）、`:1118 the_context_object`。
- **必须讲对的四个点**：① **一次拷贝**——`copy_from_user` 后接收方走 `mmap` 映射直接读，省掉 `copy_to_user`（对比 Socket 两次）；代价是内核为每进程预留固定大小缓冲区（约 1MB），故有事务上限。② **UID 来源**——内核在传事务时写入，native 落到线程 TLS，Java 只读；这是 `checkCallingPermission` 系列可信的根基。③ **oneway**——不等 reply、不能有返回值/out 参数（AIDL 编译期拦），服务端异常**静默消失**（源码注释原话 "disappear into the ether"）。④ **AIDL 生成物**：`Stub`(Binder 子类，反序列化+分发) / `Proxy`(序列化+transact) / `asInterface` 里 `queryLocalInterface` 判断是**「本地不出门」的唯一开关**（同进程直接返本地对象，这也是单进程调试时「看不到跨进程开销」的原因）。
- 另：`Binder.checkParcel` / `TransactionTooLargeException` 的因果、Binder 线程池耗尽的环路死等模式，写到文章时按 06 篇同款的「现象→因果→怎么查」组织。

## Z 序、dump 字段与排障锚点（2026-10-18 grep 核实；实践项目 L1/L2/L4/L5/L6 用）

出题/讲课时直接照用，不必重新 grep：

- **Z 序两值（L1）**：`WindowManagerService.java:343 TYPE_LAYER_MULTIPLIER = 10000`、`:347 TYPE_LAYER_OFFSET = 1000`；`WindowManagerPolicy.java:466 getWindowLayerLw(WindowState)`、`:520 getWindowLayerFromTypeLw(int type, boolean canAddInternalSystemWindow, boolean roundedCornerOverlay)`（那张 `switch(type)` 就是层级字典；roundedCornerOverlay+可加内部系统窗 → `getMaxWindowLayer()`；应用窗口区间 → `APPLICATION_LAYER`；壁纸 → 1）。`WindowState.java:1104/1117` 两分支算 `mBaseLayer`；**`WindowContainer.java:2290 assignChildLayers(Transaction)` 两趟循环**（第一趟跳过 `needsZBoost()`，第二趟补号）→ `:2240 assignLayer()` → `:2266 setLayer()`；`WindowContainer.java:2310 assignChildLayers()`、`:2318 needsZBoost()`；叶子 `WindowState.java:5648 assignLayer(Transaction, int)`。（：2290 以后的行号同时见「运行时遍历完整调用堆栈」节，两处一致。）
- **dump 字段（L2）**：`WindowState.java:1262 computeFrameAndUpdateSourceFrame()`、`:1274 computeFrame()`（frame 的非零起点）；上树≠显示判据组合 `relayoutCalled=false` + `isDrawn=false`（`isDrawn` 定义 :2091、`isReadyForDisplay` :2006）。
- **窗口泄漏（L4）**：`WindowManagerGlobal.java:480` 就是 `"… has leaked window …"` 抛出点（客户端三本账清理时机见 06 篇块 C）。
- **trace（L5）**：`WindowTracing.java:98 startTrace(PrintWriter)`、`:116 stopTrace(PrintWriter)`、`:67 mBuffer` / `:94 new TraceBuffer(bufferCapacity)`；shell 入口见「版本/路径事实」。
- **输入命中（L6）**：`InputMonitor.java:270 populateInputWindowHandle(handle, w)`；`WindowState.java:3649 getTouchableRegion(Region outRegion)`、`:3713 subtractTouchExcludeRegionIfNeeded(Region)`（触摸排除区；:3689 是它对 getTouchableRegion 的调用点）。

## 已覆盖但不在缺口

- 遍历/布局/Z 序/事务提交：03 篇（WindowSurfacePlacer、forAllWindows、performLayout、assignChildLayers 两遍算法、open/closeSurfaceTransaction → mergeToGlobalTransaction）。
- 04 篇接续 03 结尾的预告，讲完 SurfaceControl / Surface / Layer 三者关系、BLASTBufferQueue 像素通道、SF 的 commit（约 3232 行）→ composite → present → postComposition。**05 已写**（`android-window-05-input-dispatch.html`，2026-10-15）：输入事件与窗口命中（InputDispatcher / focus / touchable region），锚点见上方「05 输入事件与窗口命中」节。**06 已写落盘**（`android-window-06-window-creation.html`，2026-10-18）：窗口的诞生（addView → binder → addWindow → WindowState 上树），锚点见上方「06」节。

**07/08/09 已于 2026-10-19 正式落盘**（用户下发落盘命令）：`android-window-07-activity-lifecycle.html`（原稿 `draft-2026-10-18-ams-launch.html`）、`android-window-08-layout-insets-rotation.html`、`android-window-09-window-animation.html`；**Binder 全链路作为独立专题**落在框架层 `D:\openclaw\Android framework\android-framework-binder.html`（原稿 `draft-2026-10-18-binder.html`，不占系列编号）。四篇均通过 html.parser 标签栈校验 + 全目录 href 可达性（0 缺失）+ Edge headless 渲染核验。`_draft\` 里的旧稿**保留未删**（存稿/回滚用），**不能当进度判据**——判断某篇是否已发布只看系列目录/框架层有没有正式篇目。

落盘后的阶段-篇号映射（两份路线图已同步）：阶段 2 生命周期 = **06–07 篇（均已完成）**、阶段 3 = 08（已完成）、阶段 4 = 09（已完成）、阶段 5 = 10（IME/壁纸，下一站）、阶段 6 = 11。

**系列外延产出（2026-10-18 建，别重造）**：上位路线图 `D:\openclaw\Android-Framework学习路线图.md` + `.html`（用户选定 B 赛道系统框架层；单模块问题仍用本系列的 `WMS学习路线图.md` / `android-window-roadmap.html`，两者是包含关系，改篇号时两版同步）；实践项目两份——`wms-practice-projects.html`（P0–P5，挖自马老师库）与 `wms-original-projects.html`（L1–L6，自造实验，用的锚点见上方新节），**index.html 已挂卡片**。规划类需求转 `android-framework-learning-plan` 技能。

**系列目录位置（2026-10-19 实探）**：在 `D:\openclaw\Android framework\Android窗口层级\`（当前 19 个文件：00–09 篇 + index + 两份实践清单 + 两份路线图 + 模拟器 html + png + `_sim_temp.py` + `层级树.md`，另有 `_build\`/`_draft\` 两个子目录）。**别把文件数写死**——目录会随新篇/新清单变化；本文档内未写目录前缀的相对路径均相对该目录；每次开工先搜定，别硬编码。

## Binder 分册锚点（B0–B2，2026-10-19 grep 核实）

写 Binder 篇或回答 Binder 问题时直接照用，不必重新 grep。三篇的定位：**B0 全链路**（用户态六层）、**B1 驱动边界**（一次拷贝与 1MB）、**B2 线程池与并发**。

**B0——Java 侧**（`frameworks/base/core/java/android/os/`）

- `Binder.java`：`:803 onTransact`、`:1057 transact()`（**本地直通**，直接调 onTransact）、`:1074 linkToDeath`（**空实现**，只有 BinderProxy 真登记）、`:1087 checkParcel`（**800KB 就开始警告**，非 1MB）、`:1136 execTransact`、`:1149 execTransactInternal`。
- `BinderProxy.java`：`:48 class`、`:458` 构造（只持 native 指针）、**`:491 queryLocalInterface` 返回 `null`——这是「跨进程 vs 本地直通」的唯一开关**、`:516 transact`（先 checkParcel）。
- `IBinder.java`：`:93 FIRST_CALL_TRANSACTION`、`:102/107/119 PING/DUMP/INTERFACE_TRANSACTION`、`:307 DeathRecipient`。
- `ServiceManager.java`：`:110 getIServiceManager`（`getContextObject()` 拿 handle 0）、`:128 getService`（带 sCache）、`:165 addService`。
- `Parcel.java`：**`:898 writeStrongBinder` / `:2534 readStrongBinder`**（「Binder 能否传 Binder 对象」的答案就在这两个）。

**B0——JNI / native**

- `frameworks/base/core/jni/android_util_Binder.cpp`：`:81 gBinderOffsets`（方法 ID 缓存表）、`:340 class JavaBBinder : public BBinder`、**`:407 CallBooleanMethod(mObject, mExecTransact, …)`（C++ 回调 Java 的落点）**、`:1094 int_register_android_os_Binder`、`:1382 android_os_BinderProxy_transact`。
- `frameworks/native/libs/binder/ProcessState.cpp`：`:45 DEFAULT_MAX_BINDER_THREADS=15`、`:76 self()`、`:139 startThreadPool()`、`:149 becomeContextManager()`（认领 handle 0）。
- `frameworks/native/libs/binder/IPCThreadState.cpp`：`:617 joinThreadPool`、`:685 transact`、`:875 waitForResponse`、`:975 talkWithDriver`、`:1125 executeCommand`。
- native 接口两半：`frameworks/native/include/binder/IInterface.h:70 BnInterface`（服务端）/ `:84 BpInterface`（客户端）；`Binder.h:30 class BBinder`——即 Java 的 Stub/Proxy 的 C++ 版本，AIDL→cpp 转换讲的就是这个。

**B0——其它交互形式**（证明「Binder 不止 AIDL 一种」）

- Messenger：`Messenger.java:35 mTarget`、`:45 ctor(Handler)`、`:68 getBinder()`、`:147 ctor(IBinder)`；`Handler.java:906 getIMessenger()`；**`IMessenger.aidl` 是 `oneway interface`（天生异步、无返回值）**。
- ContentProvider：`ContentProviderNative.java:46 extends Binder implements IContentProvider`；`ContentProvider.java:212 class Transport extends ContentProviderNative`。
- 广播：`IIntentReceiver.aidl` 是 `oneway interface`（系统→App 单向通知）。

**B1——驱动边界（用户态可见部分）**

- `ProcessState.cpp:44 BINDER_VM_SIZE = (1*1024*1024) - sysconf(_SC_PAGE_SIZE)*2`（**1MB 上限的真正来源**，减 2 页）、`:379 open_driver`（open + `:384 BINDER_VERSION` 严格相等 + `:396 BINDER_SET_MAX_THREADS`）、`:412-440` 构造与 **`:428 mmap(BINDER_VM_SIZE, PROT_READ, MAP_PRIVATE|MAP_NORESERVE, mDriverFD, 0)`**。
- `IPCThreadState.cpp:1082 writeTransactionData`（填 `binder_transaction_data`；**`sender_pid/sender_euid` 用户态填 0、真实值由驱动写**——这是「UID 不可伪造」的数据层证据）、`:975-1045 talkWithDriver` 里的 `ioctl(BINDER_WRITE_READ)`、`:1204 BR_TRANSACTION`、回执 `:899 BR_TRANSACTION_COMPLETE` / `:903 BR_DEAD_REPLY` / `:907 BR_FAILED_REPLY` / `:911 BR_FROZEN_REPLY`。
- `Parcel.cpp:2114 ipcSetDataReference`（**直接引用驱动缓冲区，接收侧不再拷贝**）。
- **uapi 合同头：`bionic/libc/kernel/uapi/linux/android/binder.h`**（这棵树里唯一能看到的内核接口定义）：`:26-31 BINDER_TYPE_*`、`:56-70 flat_binder_object / binder_fd_object`、**`:90-100 binder_write_read`（与驱动交互的唯一信封）**、`:102/104` 协议版本 7/8、`:120-124 BINDER_WRITE_READ / SET_MAX_THREADS / SET_CONTEXT_MGR`、`:130-136 TF_ONE_WAY/TF_STATUS_CODE/TF_ACCEPT_FDS`、**`:139-160 binder_transaction_data`（含 `data_size` / `offsets_size`）**、`:186-190 BR_*`、`:197 BR_SPAWN_LOOPER`、`:204-216 BC_*`。
- **`offsets` 的意义**：数据里混着普通字节与对象占位（binder/handle/fd），驱动不能扫描猜测，所以发送方另给一份「对象在数据中的偏移表」，驱动只按表翻译 → O(对象数) 且不误判。

**B2——线程池**

- `ProcessState.cpp:58 class PoolThread`（线程体只有一行 `joinThreadPool(mIsMain)`）、`:331 makeBinderThreadName`（**`Binder:<pid>_<seq>`**，排障入口）、`:339 spawnPooledThread`、`:348 setThreadPoolMaxThreadCount`（**启动后禁止调小，否则 LOG_ALWAYS_FATAL**）、`:364 enableOnewaySpamDetection`、`:416-423` 计数字段（`mExecutingThreadsCount` / `mMaxThreads` / `mWaitingForThreads` / `mStarvationStartTimeMs`）。
- `IPCThreadState.cpp:504 blockUntilThreadAvailable`（背压，打 `Waiting for thread to be free`）、`:519 getAndExecuteCommand`（**遍历前后对 `mExecutingThreadsCount` 自增自减**）、**`:536-551` 饥饿判定：`>= mMaxThreads` 开始计时，恢复时 >100ms 才打 `binder thread pool (N threads) starved for M ms`**、`:617 joinThreadPool`、`:621 BC_ENTER_LOOPER / BC_REGISTER_LOOPER`、**`:640 TIMED_OUT && !isMain → break`（池线程空闲退出、主线程不退）**、**`:1350 case BR_SPAWN_LOOPER → spawnPooledThread(false)`（扩容全部代码就这一行）**。

**内核边界（重要）**：`drivers/android/binder.c` **不在这棵 AOSP 树**（`kernel/` 只有 `configs/ prebuilts/ tests/`，实测 `find` 无结果）。所以「驱动何时发 `BR_SPAWN_LOOPER`」「`binder_alloc_new_buf` 怎么分配 1MB」这些**只能讲机制不能给行号**；要讲实现须另取内核源码（如 `android12-5.10`），并明确标注换树了。


