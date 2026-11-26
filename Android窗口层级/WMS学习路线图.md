# WMS 系统学习路线图（接续 00–10 篇）

> 基线：本机 WSL `/home/book/aosp12/`，android-12.0.0_r32。
> 所有行号均已 grep 核实（2026-10-14），代码根包：
> `frameworks/base/services/core/java/com/android/server/wm/`（下文简称 `wm/`）。
> 已完成：00/01 概念、02 构建（DisplayAreaPolicyBuilder + addWindow 挂树）、03 遍历显示（performSurfacePlacement / performLayout / Z 序 / 事务）、04 Surface→BLAST→SF 合成、05 输入分发、06 窗口的诞生（addView → addWindow → WindowState 上树）、**07 窗口的来路与归途**（Activity 启动链与生命周期）、**08 窗口的尺寸与身体**（布局 / Insets / 旋转）、**09 窗口动画与过渡**（AppTransition 与 leash），以及专题补篇 **13 画中画 PiP**（跨 ATMS / WMCore / WM Shell 的窗口模式迁移）。

## 版本事实（先立住，防止被高版本资料带偏）

- AOSP12 树**没有 TaskFragment**（12L/API32 才引入），任务容器只有 `Task`（Task.java:252 `extends WindowContainer<WindowContainer>`）。
- WMS 与 ATMS 自 API30 起**同包同锁**：`wm/ActivityTaskManagerService.java`，全局锁 `mGlobalLock` 在 ATMS.java:362（不是 WMS 里）。
- `PhoneWindowManager` 在 `com.android.server.policy` 包（**不是** wm/policy，wm/policy 目录不存在）。
- SystemUI 侧**没有 SystemBars.java**（12 树已核实）。
- Shell Transitions（TransitionController 一整套）在 12 上不是主线，动画主力还是 AppTransition + TaskOrganizer + RemoteAnimation，别拿 13/14 的文章套。

---

## 阶段 0：工具箱（0.5 天，先武装再读代码）

| 工具 | 入口锚点 | 用途 |
|---|---|---|
| `adb shell dumpsys window` / `windows` / `displays` / `visible-window-views` | WMS dump 链 | 看窗口树、WindowState 全部字段（layer/frame/attr/focus） |
| `adb shell cmd window ...` | WindowManagerShellCommand.java:75 `size`、:85 `tracing`（:89 转 mWindowTracing）、:106 `user-rotation`、:110 `set-ignore-orientation-request`、:122 `reset` | 模拟分辨率/密度/旋转，复现配置类 bug |
| WindowTracing（Winscope） | WindowTracing.java:48 类、:98 `startTrace`、:191 `isEnabled`；`adb shell cmd window tracing start/stop` | 单步回放 WindowContainer 树随时间的变化，排查层级/动画问题第一神器 |
| `dumpsys input` | InputDispatcher 内部状态（focusedWindow、touchStates、ANR 队列、inboundQueue） | 输入类 bug 的第一现场 |
| `getevent -lt` / `sendevent` | EventHub 之下的 evdev | 判断问题在驱动前还是 framework |
| `dumpsys SurfaceFlinger` + SF tracing | 04 篇链路末端 | 验证 Layer 树与 WMS 树是否同构 |

**实验**：启动一个 App，先后抓 `dumpsys window windows`、开 window tracing 做一次旋转、Winscope 里回放。
**产出**：把 dump 字段对照 WindowState 源码逐个读懂（mBaseLayer/mSubLayer/frame/requestedWidth/relayoutCalled/hasSurface…）。

---

## 阶段 1：输入系统（对应 05 篇，预计 3–5 天）

> 一句话主线：**屏幕触摸 → evdev → InputReader 加工 → InputDispatcher 做命中测试 → 通过窗口的 InputChannel 发往 App → ViewRootImpl 入队派发**。焦点/ANR/触摸错位都在这条线上。

### 核心调用链（全部已核实）

1. 窗口侧"电话线"建立：`WMS.addWindow()`（WMS.java:1457）中 :1687-1690 `win.openInputChannel(outInputChannel)` →
   `WindowState.openInputChannel()`（WindowState.java:2689）:2694 `mInputManager.createInputChannel(name)`；
   句柄存于 WindowState.java:607 `mInputChannel` / :615 `mInputChannelToken`。
   （无输入能力的窗口走 `Session.addToDisplayWithoutInputChannel` Session.java:209。）
2. WMS 把"可接收输入的窗口列表"喂给 native：`InputMonitor`（InputMonitor.java:72）
   `updateInputWindowsLw()`（:338）→ 逐窗口 `populateInputWindowHandle()`（:270，填 touchable region / token / focusable 等）
   → :490 `updateInputWindows(inDrag)` → IMS → JNI `com_android_server_input_InputManagerService.cpp` → InputDispatcher。
3. native 分发线程：`InputDispatcher::dispatchOnce()`（InputDispatcher.cpp:572）→
   `dispatchOnceInnerLocked()`（:683）→ 按键走 `findFocusedWindowTargetsLocked()`（:1786），
   触摸走 `findTouchedWindowTargetsLocked()`（:1900，含触摸命中区域、分裂、模态、遮挡过滤）。
4. ANR：`processAnrsLocked()`（:640）→ 超时阈值 `DEFAULT_INPUT_DISPATCHING_TIMEOUT`（:102，
   基值 `UNMULTIPLIED_DEFAULT_DISPATCHING_TIMEOUT_MILLIS`=5000ms × 厂商 HwTimeoutMultiplier）
   → `onAnrLocked(Connection)`（:5515）/ `onAnrLocked(InputApplicationHandle)`（:5550）→ 回到 system_server 弹 ANR 框。
5. 上游设备读取：`reader/InputReader.cpp` 的 `loopOnce()` + `reader/EventHub.cpp`（evdev 原始事件）。
6. Policy 按键拦截（音量/电源/Home/唤醒）：`PhoneWindowManager.interceptKeyBeforeQueueing()`（PhoneWindowManager.java:3383）、
   `interceptMotionBeforeQueueingNonInteractive()`（:3964）。
7. 焦点：`DisplayContent.findFocusedWindow()`（:3362）、`updateFocusedWindowLocked()`（:3387）。
8. App 侧接收：`ViewRootImpl.enqueueInputEvent()`（ViewRootImpl.java:8438）→ `doProcessInputEvents()`（:8493）
   → `deliverInputEvent()`（:8520）；通道接收在 `InputEventReceiver`（InputEventReceiver.java:38，native 层 Looper 回调）。

### 实际会遇到的问题

- **Input dispatching timed out（ANR）**：区分"窗口无响应"（App 主线程卡）和"焦点窗口不存在/还没就绪"（awaitedFocusedApplication，常见于启动慢）——两者 onAnrLocked 重载不同，dumpsys input 里看 waitQueue。
- **触摸点到了错误的窗口**：touchable region 算错（SurfaceView/异形裁剪）、被一个不可见但有 InputChannel 的窗口拦截、FLAG_NOT_TOUCH_MODAL 行为、spy/policy flag。
- **点了没反应**：窗口 `NOT_FOCUSABLE` 导致按键没焦点、token 已 remove 但 channel 未注销、多显示器上焦点在另一块屏。
- 多点触控被"分裂"到两个窗口、模态对话框没拦住下层事件。
- IME 弹出后焦点和触摸宿主变化（和阶段 5 联动）。

### 动手实验

- 开发者选项"显示点按操作反馈" + `dumpsys input` 观察 focusedWindow 与 touchState。
- 放一个 `FLAG_NOT_FOCUSABLE | FLAG_NOT_TOUCH_MODAL` 的悬浮窗，验证区域内外事件路由。
- `adb shell input keyevent/tap` 注入，在 dispatchOnceInnerLocked 打断点（或加 log）跟一遍。

---

## 阶段 2：Activity/Task 与窗口生命周期（对应 06–07 篇，4–6 天）

> 已完成：**06 篇**（窗口的诞生）与 **07 篇**（窗口的来路与归途：Activity 启动链与窗口生命周期）均已完成，见 [06 窗口的诞生](06-窗口的诞生.html)、[07 窗口的来路与归途](07-窗口的来路与归途.html)。本阶段已收尾。

> 主线：**startActivity → ActivityStarter → ActivityRecord(=WindowToken) 挂进 Task → bindApplication/realStartActivity → ViewRootImpl 首次 relayout → 首绘 → 删除**。把 02 篇的"窗口怎么挂树"补全成"窗口从哪来、到哪去"。

### 核心调用链（已核实）

- `ActivityTaskManagerService.startActivity()`（ATMS.java:1144）→
  `ActivityStarter.execute()`（ActivityStarter.java:611）→ `executeRequest()`（:811）→
  `startActivityUnchecked()`（:1548）→ `startActivityInner()`（:1570 附近，含 launchMode/task 复用/回退栈决策）。
- 身份关系：`ActivityRecord extends WindowToken`（ActivityRecord.java:365）——Activity 在 WMS 树里就是一个 token；
  `WindowToken extends WindowContainer<WindowState>`（WindowToken.java:71）；
  非应用 token 经 `DisplayContent.addWindowToken()`（DisplayContent.java:1134）挂树（02 篇已学）。
- 容器：`Task`（Task.java:252）、`RootWindowContainer`（RootWindowContainer.java:175）、
  `KeyguardController`（KeyguardController.java:65，锁屏对可见性/转场有生杀权）。
- 启动窗口（splash/快照）：`StartingSurfaceController`（StartingSurfaceController.java:46）
  `createSplashScreenStartingSurface()`（:60）/ `createTaskSnapshotSurface()`（:115）；
  12 上优先走 `TaskOrganizerController.addStartingWindow()`（:71，ShellStartingSurface），即 SystemUI/Shell 接管。
- 绘制就绪状态机：`WindowState.isDrawn()`（:2091）、`isReadyForDisplay()`（:2006）、
  `mViewVisibility`（:322/:1059）、commitFinishDrawingLocked（首帧 buffer 到达后的"已绘制"翻转，03 篇 mApplySurfaceChangesTransaction 回调里出现过）。
- 删除：`WindowState.removeIfPossible()`（:2418，延迟/条件删除）与 `removeImmediately()`（:2362）；
  理解"Activity 已 onDestroy 但窗口还在等动画"的分离。
- 客户端入口：Session.addToDisplay（Session.java:189）。

### 实际会遇到的问题

- **启动黑屏/白屏**：starting window 没加上 vs 首帧太晚（isDrawn 迟迟不翻转）vs 背景 windowBackground 白色；排障点完全不同。
- **has leaked window**：Activity destroy 时 WindowManager.removeView 没配对（Dialog/Toast 持有 token）。
- starting window 残留、splash 图标不消失、冷启动快照（task snapshot）显示成旧画面。
- launchMode / taskAffinity / clearTop / 多实例行为与预期不符。
- 后台 Activity 启动被拦（Bal/ABL，Background Activity Launch）、锁屏上显示 Activity 的 showWhenLocked 机制。
- 配置变更期间窗口两次 add/remove 造成的闪烁。

### 动手实验

- `adb shell am start -W -n pkg/.Act` 看 WaitTime/TotalTime，配合 tracing 对齐 starting window→真实窗口接力点。
- 故意在 onCreate 弹 Dialog 后 finish，复现 leaked window 并读 WMS 日志。
- 跟一遍 recent 任务恢复：快照 surface 与真实 Activity 窗口的替换。

---

## 阶段 3：布局、Insets、旋转与配置（对应 08 篇，4–6 天）

> 已完成：**08 篇**（窗口的尺寸与身体）已落盘，见 [08 窗口的尺寸与身体](08-窗口的尺寸与身体.html)。

> 03 篇学了遍历"怎么跑"，这一阶段学每一遍里"算了什么"：窗口 frame 怎么定、系统栏怎么让位、旋转怎么不闪。

### 核心锚点（已核实）

- 布局：`DisplayContent.performLayoutNoTrace()`（DisplayContent.java:4417），逐窗口回调
  `mPerformLayout`（:781）→ `WindowState.computeFrame()`（WindowState.java:1274）；
  策略侧 `DisplayPolicy`（DisplayPolicy.java:181）`addWindowLw()`（:1070）与 performLayoutLw（系统装饰窗口的 frame 由 policy 先定，再约束应用窗口）。
- Insets 三件套：`InsetsStateController`（InsetsStateController.java:64，每屏一份，管所有 source）、
  `InsetsSourceProvider`（:68，一个 inset 源 = 状态栏/导航栏/IME 之一）、
  `ImeInsetsSourceProvider`、`InsetsPolicy`、`InsetsControlTarget`（谁能控制系统栏显隐）。
  对应客户端 API：WindowInsets / OnApplyWindowInsetsListener / setDecorFitsSystemWindows。
- 旋转：`DisplayRotation`（DisplayRotation.java:84）`updateRotationUnchecked()`（:415）；
  冻结显示 startFreezingDisplayLocked/stopFreezingDisplayLocked（DisplayContent.java:3008 可见 stop 调用点），
  冻结期间用截屏盖住直到新方向首帧就绪。
- 配置变更：`ActivityRecord.resolveOverrideConfiguration()`（:7142）、
  `onConfigurationChanged()`（:7697）、`ensureActivityConfiguration()`（:7950）；Task 也有 onConfigurationChanged 向下传播。
- 手动模拟：`cmd window user-rotation`（ShellCommand:106）、`set-ignore-orientation-request`（:110）。

### 实际会遇到的问题

- **键盘弹起布局被顶乱**：adjustResize/adjustPan 与 WindowInsetsAnimation 冲突；fitsSystemWindows 消费链断裂；IME inset 没收到（ImeInsetsSourceProvider 控制权没给目标窗口）。
- 沉浸式/手势导航：状态栏隐藏后导航栏留手势条、setSystemBarsBehavior 粘滞模式不生效。
- 旋转闪一下/截屏不更新（freeze 没解除）、传感器旋转与 Activity requestedOrientation 打架。
- 折叠屏/外屏：screenSize 变化走配置重建还是被 manifest configChanges 吃掉但代码没处理。
- DisplayCutout 安全区、圆角（rounded corner 层，02 篇最高 layer 36）避让。

### 动手实验

- `cmd window size 1080x1920 / density 240 / reset` 复现多分辨率。
- 强制旋转 + tracing，观察 freeze 截图 surface 与真实 surface 的交接。
- 写一个带 Insets 监听的 demo，弹出 IME，dump InsetsStateController 状态对照。

---

## 阶段 4：动画与过渡（对应 09 篇，3–5 天）

> 已完成：**09 篇**（窗口动画与过渡：AppTransition 与 leash 缰绳）已落盘，见 [09 窗口动画与过渡](09-窗口动画与过渡.html)。

### 核心锚点（已核实）

- `AppTransition`（AppTransition.java:158）：转场状态机，`isReady()`（:350），
  默认时长 `DEFAULT_APP_TRANSITION_DURATION = 336ms`（:167）；准备转场由 Task/ActivityRecord 触发。
- `SurfaceAnimator`（SurfaceAnimator.java:49）：`startAnimation()`（:134）核心机制是
  **leash（缰绳 surface）**——`createAnimationLeash()`（:384）在目标 Layer 上方插一个可操控的中间 Layer，
  动画只动 leash，原 Layer 保持不动；动画结束销毁 leash、提交最终位置。务必读透，04 篇的 Surface 树在这里被"动态插节点"。
- `TaskOrganizerController`（TaskOrganizerController.java:69）：SystemUI/Shell 接管 Task 层级与 starting window、
  分屏、手势动画；`WindowContainerTransaction` 是应用侧改层级的事务 API。
- RemoteAnimation：AMS 把转场动画 leash 交给应用进程（Launcher）自己绘制。

### 实际会遇到的问题

- 动画 leash 泄漏/残留（动画 cancel 时 finishCallback 没跑），画面卡在半透明/错位层。
- starting window 与 app transition 不同步导致"闪两次"。
- 手势返回动画过程中快速操作导致层级状态错乱。
- 自定义 overridePendingTransition / RemoteAnimation 不生效（被 TaskOrganizer 截胡、或窗口 isOnHomeDisplay 条件不满足）。

### 动手实验

- tracing 录一次 Activity 跳转，Winscope 里数 leash 的创建/销毁时刻。
- 开发者选项"窗口动画缩放 ×10"慢放对照代码分支。

---

## 阶段 4+：vsync 与 Choreographer（对应 10 篇，已落盘）

> 已落盘：**10 篇**（显示子系统的节拍：vsync 与 Choreographer），见 [10 vsync 与 Choreographer](10-显示子系统的节拍.html)。
> 这是显示子系统的地基：VSyncPredictor 模型（中断采样→软件预测→fence 纠偏）、app/sf 两条相位、EventThread 按连接分发、三层按需、Choreographer 的 doFrame、WMS 在 android.anim 上的接入。

---

## 阶段 5：IME 与壁纸专项（对应 11 篇，2–4 天）

> 这两个是 WMS 里唯二"反向跟踪目标窗口"的特殊系统，理解它们就理解了 policy 的灵活性上限。

### 核心锚点（已核实）

- IME 服务：`InputMethodManagerService.startInputOrWindowGainedFocus()`（IMMS.java:3261，焦点变化→重新绑定编辑器）、
  `showCurrentInputLocked()`（:3114）。
- WMS 侧：`ImeContainer`（ImeContainer 定义在 DisplayContent.java 内）、IME 目标窗口/相对 Z 序（03 篇 assignRelativeLayerForIme 见过）、
  `ImeInsetsSourceProvider`（阶段 3 同一条线）。
- 壁纸：`WallpaperController`（WallpaperController.java:60）：壁纸目标窗口选择、与窗口滚动联动（xOffset/yOffset）、
  壁纸窗口在 layer 表中的固定层（01 篇 wallpaper layer）。

### 实际会遇到的问题

- 输入法不弹出：焦点没真正切换（startInputOrWindowGainedFocus 没被调）、mCurToken 为 null、ImeContainer 不可见。
- IME 盖住输入框：insets 通知没下发或客户端没消费；多屏时 IME 跟错 display。
- 壁纸纯黑/不跟随桌面滑动：wallpaper target 没选对、壁纸进程死了没重连、FLAG_SHOW_WHEN_LOCKED 冲突。
- 第三方键盘/语音输入的切换竞态。

---

## 阶段 6：多显示与多窗口（对应 12 篇，按需，3–4 天）

- 多 Display：DisplayContent 列表管理、DisplayWindowSettings、display 0 vs 虚拟屏/外屏的焦点与 IME 归属。
- 多窗口：windowingMode（fullscreen/freeform/pinned）、TaskPositioner 拖动 resize、分屏在 12 上由 Shell（SystemUI）经 TaskOrganizer 实现——WMS 只提供容器与策略钩子。
- 实际问题：外屏黑屏/尺寸错误、freeform 窗口焦点、画中画生命周期、Activity 在多屏下的 recreate、投屏（VirtualDisplay）上的 Surface 与输入。

---

## 贯穿线：线程与锁模型（建议每个阶段都回看一次）

- 全局唯一锁 `WindowManagerGlobalLock`（ATMS.java:362，:370 mGlobalLockWithoutBoost 是同一把）。
- 三类线程：Binder 线程（拿锁执行 add/relayout 等）→ system_server 的 `mH` Handler（串行化收尾）→
  Animation 线程跑 performSurfacePlacement（03 篇 requestTraversal 的 Handler.post 边界）。
- 输入系统是**另一条无锁链路**：InputMonitor 只在持 WMS 锁时快照一份窗口列表交给 native，
  InputDispatcher 自己有锁——所以输入看到的窗口状态可能"略旧"，这是理解输入怪问题的关键。
- 实战红线：持 mGlobalLock 时做 Binder 跨进程调用（尤其回调 App）会引入卡顿/死锁，源码里大量用"清掉待办、出锁后回调"的模式。

---

## 推荐学习顺序与节奏

| 周 | 阶段 | 产出 |
|---|---|---|
| 第 0 周（半天） | 阶段 0 工具箱 | 能抓 tracing 并用 Winscope 回放 |
| 第 1–2 周 | 阶段 1 输入 | **05 篇 HTML** ✓ 已完成 |
| 第 3–4 周 | 阶段 2 生命周期（开篇） | 06 篇 ✓ 窗口的诞生 |
| 第 5–6 周 | 阶段 2 生命周期（续） | 07 篇 |
| 第 7 周 | 阶段 3 布局/Insets/旋转 | 08 篇 |
| 第 8 周 | 阶段 4 动画 | 09 篇（重点画 leash 图） |
| 第 8 周 + | 阶段 4+ vsync / Choreographer | 10 篇 |
| 第 9 周 | 阶段 5 IME/壁纸 | 11 篇 |
| 按需 | 阶段 6 多屏多窗 | 12 篇 |

> 插队补篇：**13 画中画 PiP**（已发布）——它是 09 篇 leash/Transition 与阶段 2 Task 生命周期的交叉产物，建议在读 12 篇多窗口之前读，`windowingMode` 的概念到这里才真正落地。

**每阶段固定套路**：先 dumpsys/Winscope 观察现象 → 按调用链读代码（行号锚点都在上面）→ 用 adb 复现一个真实问题 → 写成系列文章。
**阅读纪律**（沿用既有规则）：每个方法名先 grep 行号再下结论；native（inputflinger/SF）与 Java 两侧都核；不要凭高版本印象写 12 的代码。
