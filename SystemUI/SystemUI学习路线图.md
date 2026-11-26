# SystemUI 系统学习路线图（AOSP 12 · android-12.0.0_r32）

> 基线：本机 WSL `/home/book/aosp12`，`PLATFORM_VERSION_LAST_STABLE := 12`（`build/make/core/version_defaults.mk:91`）。
> SystemUI 源码根：`frameworks/base/packages/SystemUI/`，下文简称 `sysui/`；全部行号 2026-11-06 grep 核实。
> 定位：**与 WMS 路线图平级的模块**，不是它的子集。WMS 决定「窗口放哪、多大、谁在上面」，SystemUI 决定「这些系统窗口里画什么、怎么交互」。
> 学完 WMS 再学 SystemUI 最省力：窗口树、Insets、输入分发、转场这些地基可以直接复用。
>
> 相关导航：[Framework 总纲](../Android-Framework学习路线图.md) · [WMS 学习路线图（建议前置）](../Android窗口层级/WMS学习路线图.md)

---

## 一、先看全：8 个阶段约 180 小时

| 阶段 | 主题 | 学时 | 日历（12h/周） | 学完能做到 |
|---|---|---|---|---|
| 0 | 地图、启动链、组件模型、调试工具 | 6 h | 0.5 周 | 说清 SystemUI 进程怎么起来、有哪些组件、窗口怎么加上去 |
| 1 | 状态栏与图标系统 | 20 h | 2 周 | 改图标、改颜色、加系统图标不崩 |
| 2 | 通知管线（post → 展示） | 30 h | 2.5 周 | 定位通知不显示/重复/不折叠/不弹 heads-up |
| 3 | Shade 下拉面板与 QS | 24 h | 2 周 | 改面板布局、加 QS tile、排「拉不下来/收不回去」 |
| 4 | Keyguard 锁屏与解锁 | 20 h | 2 周 | 跟完一次解锁全链路，处理锁屏显示/黑屏类问题 |
| 5 | 导航栏、手势与 Recents | 20 h | 2 周 | 三键/手势切换、返回失效、Recents 拉起排查 |
| 6 | 系统级 UI 服务（音量/关机/截图/圆角） | 14 h | 1 周 | 这些「小窗口」的特性和坑都能改 |
| 7 | 与 WMS / WMShell 的交界 | 24 h | 2 周 | 用窗口视角解释 SystemUI 的冻屏、黑屏、转场问题 |
| 8 | 定制（RRO/主题/车机）、稳定性、项目与面试 | 22 h | 2 周 | 能独立接一个 SystemUI 定制需求 |

**总计约 180 h**：每天 2 h、每周 6 天 ≈ **3.5 个月**；有 WMS 基础可压到 3 个月；只有 App 经验、没碰过 AOSP 则 5–6 个月。

三档「胜任」的定义：

- **能改**（约 100 h / 2 个月）：给你需求能改出来，不引入明显回归。
- **能修**（约 180 h / 3.5 个月）：给现象能用 dumpsys + 日志 + 断点定位到具体类，这是面试和入职的门槛。
- **能扛**（再 6–12 个月实战）：复杂交互（锁屏×转场×多用户×车机）与稳定性问题（ANR/冻屏/内存）能兜底。

---

## 二、版本事实（先立住，别被 13/14 的文章带偏）

1. **12 树没有 `SystemBars.java`**，也没有 `CentralSurfaces`。状态栏就是 `StatusBar`，而且它是**启动组件**之一（`sysui/res/values/config.xml:319`），不是被谁 new 出来的。网上讲 `SystemBars`/`CentralSurfaces` 的基本是 Android 13+。
2. **通知管线是新的**：`NotifPipeline`（`sysui/statusbar/notification/collection/NotifPipeline.java:75`）+ `NotifCollection`（同目录 `NotifCollection.java:128`）。本树里**没有 `NotificationEntryManager`**，老文章那条链在 12 已经被拆掉，别照着找。
3. **WMShell 跑在 SystemUI 进程里**：`WMShell` 本身就是一个 SystemUI 组件（`sysui/wmshell/WMShell.java:93`），Shell 的 `Transitions`/`ShellTransitions` 代码在同进程加载。所以 SystemUI 崩了，分屏/PIP/转场一起没。
4. **两个方向的 binder 别搞反**：
   - `IStatusBarService`（`StatusBarManagerService`，`services/core/java/com/android/server/statusbar/StatusBarManagerService.java:95`）：**SystemUI 调 system_server**，比如展开面板、设置 disable 标志。
   - `IStatusBar`（SystemUI 的 `CommandQueue` 实现，`sysui/statusbar/CommandQueue.java:81`）：**system_server 调 SystemUI**，比如 `disable`、`appTransitionStarting`、`onSystemBarAttributesChanged`。
5. **Shell Transitions 在 12 已有代码但不是默认主线**：`Transitions.java` / `ShellTransitions.java` 都在，本树转场仍以 WMS 的 `AppTransition` + leash 为主（与 WMS 路线图一致）。排障先看 AppTransition，再确认有没有走 Shell。

---

## 三、阶段 0：地图、启动链与工具箱（6 h）

### 启动链（已核实）

```
SystemServer.startSystemUi()            SystemServer.java:2931（定义 :3024）
  → startServiceAsUser(SystemUIService)
    → SystemUIService.onCreate()        SystemUIService.java:66
      → SystemUIApplication.startServicesIfNeeded()   :70
        → 读 config_systemUIServiceComponents（config.xml:314，23+ 项）
        → 反射实例化 mServices[i]        SystemUIApplication.java:214
        → 逐个 start() / onBootCompleted()
```

要点：

- `SystemUIApplication`（:49）不是「一个 UI」，是**组件容器**；每个组件继承 `SystemUI`，有 `start()`、`onBootCompleted()`、`onConfigurationChanged()`。
- `config_systemUIServiceComponentsPerUser`（config.xml:348）只有 `NotificationChannels` 一项：**换用户时只重启这一部分**，其余组件跟进程走。
- `SystemUIFactory`（`sysui/SystemUIFactory.java:42`）+ Dagger：读 `config_systemUIFactoryComponent` 决定实现类。定制 ROM 常在这里换工厂，而不是改 `StatusBar`。
- SystemUI 能加 `TYPE_STATUS_BAR` / `TYPE_NOTIFICATION_SHADE` 这类窗口，是因为它持有 `INTERNAL_SYSTEM_WINDOW` 权限；普通 App 加会被 WMS 直接拒。

### 工具箱

| 工具 | 用法 | 用途 |
|---|---|---|
| `cmd statusbar` | `adb shell cmd statusbar help`（`StatusBarShellCommand.java:34`） | 展开/收起面板、改 disable 标志、模拟系统栏状态 |
| SystemUI dump | `adb shell dumpsys activity service com.android.systemui/.SystemUIService` | `SystemUIService.dump`（:112）把 dump 分发给各 `Dumpable` 组件 |
| `dumpsys window` | 看 `NotificationShade`、`StatusBar`、`NavigationBar` 的 frame/visibility | 判断是「没画」还是「画错位置」 |
| `dumpsys notification --noredact` | 通知记录、ranking、channel | 通知类问题第一现场 |
| `cmd overlay list` | RRO 列表与启用状态 | 定制/主题问题 |
| Winscope | 抓 transition + window trace | 转场、冻屏、层级异常 |
| 杀进程 | `adb shell killall com.android.systemui`（userdebug） | 验证「重启后是否自愈」，区分状态残留 vs 逻辑错误 |

### 常见坑

- 把 SystemUI 当成「一个 Activity/一个 View」：它是常驻系统进程 + 多组件，很多「界面不刷新」是组件没收到回调，不是 View 画错。
- 在 `StatusBar` 里找不到功能就放弃：大量逻辑已经下沉到 `NotificationPanelViewController`、`ShadeControllerImpl`、`CentralSurfaces`（13+）等，`StatusBar` 更像装配工。
- 改了 `config.xml` 不生效：SystemUI 的资源有 overlay，先 `cmd overlay list` 看有没有 RRO 覆盖。

### 验收

能脱稿画出「SystemServer → SystemUIService → 组件 → 各窗口」的启动图，并说出 `StatusBar`、`WMShell`、`KeyguardViewMediator` 三个组件各自的职责边界。

---

## 四、阶段 1：状态栏与图标系统（20 h）

### 主线

```
系统状态源（电池/网络/时钟/信号）
  → BatteryControllerImpl(:55) / NetworkController / Clock
  → StatusBarIconControllerImpl(:59)  setIcon / setIconVisibility
  → StatusBar 的 icon 区域（left/right slot）
```

- `StatusBar`（`statusbar/phone/StatusBar.java:268`）是装配工：把窗口、面板、锁屏、图标、回调接在一起，本体近 5000 行，**不要试图从头读到尾**，按功能跳读。
- 图标槽位：`StatusBarIconControllerImpl` 继承 `StatusBarIconList`，按 slot 管理；`setIcon(slot, icon)` / `removeIcon(slot)` 是入口。
- 深浅色：system_server 通过 `DisplayPolicy.java:2561 statusBar.onSystemBarAttributesChanged(...)` 把 `appearance` 推给 SystemUI，`CommandQueue` 再分发给监听者，最终切 dark icon。**状态栏变白/图标看不清，先查这条链，不要先改颜色。**
- `StatusBarManager`（`core/java/android/app/StatusBarManager.java:48`）是给 App 的公开 API（`disable()` :239、`expandNotificationsPanel()` :317），最终都落到 `StatusBarManagerService`（:657 / :881）。

### 常见坑

- 图标重复/不消失：slot 名冲突，或 `removeIcon` 没配对。
- 深色页面图标不变白：`appearance` 没传到，或 `light bar` 被某个全屏窗口的 flag 覆盖。
- 状态栏高度改了但内容没动：高度在 WMS 的 `DisplayPolicy`/`Insets` 侧生效，SystemUI 只负责画；两边要一起改。

### 实验与验收

- 用 `cmd statusbar` 切换 disable 标志，观察图标区变化。
- 动态加一个自定义 system icon，再移除，确认无残留。
- 验收：能解释「为什么状态栏图标是黑的/白的」，并指出链路上任意一环出错会看到什么现象。

---

## 五、阶段 2：通知管线（30 h，SystemUI 最值钱的一块）

### 主线（12 的新管线）

```
App postNotification
  → NotificationManagerService（system_server）
  → NotificationListener(:47) 收到 onNotificationPosted
  → NotifPipeline(:75) 收集
  → NotifCollection(:128) 去重/更新/取消
  → NotifCoordinators(:41)（RankingCoordinator:43 / HeadsUpCoordinator:59 / Media…）
  → HeadsUpManager(:51) 决定弹不弹
  → NotificationRowBinderImpl(:51) 绑定 View
  → Shade / StatusBar 展示
```

关键点：

- **`NotifPipeline` 是编排者，`NotifCollection` 是数据源**。所有「通知为什么没出现」的问题，先确认它有没有进 `NotifCollection`。
- **分组/折叠**由 `NotifCollection` 的 group 逻辑与各 coordinator 共同决定（12 树里没有 `GroupCoordinator.java`，别照老文章找）；**弹不弹 heads-up** 由 `HeadsUpManager` + `HeadsUpCoordinator(:59)` 决策；**排序**在 `RankingCoordinator(:43)`。
- 12 的 heads-up 实现是 `HeadsUpManagerPhone`（`statusbar/phone/`），抽象基类在 `statusbar/policy/HeadsUpManager.java:51`。
- 通知的 View 绑定是异步的（`NotificationRowBinderImpl`），所以「数据到了但界面晚一拍」是正常的，不要当 bug。

### 常见坑

- 通知不显示：channel 被关、importance 太低、被 ranking 压到折叠组、或 App 被禁止通知。
- 通知重复：同一 key 更新没走 `NotifCollection` 的 update 路径，或两条不同 key。
- heads-up 不弹：屏幕熄灭/免打扰/前台服务/全屏窗口抑制，逐项排除，别只盯 `HeadsUpManager`。
- 通知点击没反应：`PendingIntent` 失效或包被冻结，先在 `dumpsys notification` 里看记录。

### 实验与验收

- 用不同 importance 的 channel 各发一条，记录「是否 heads-up / 是否折叠 / 排序位置」。
- 抓一次 `dumpsys notification --noredact`，把一条通知从 posted 到展示的字段变化讲清楚。
- 验收：给定「通知不显示」，能在 10 分钟内用三层（NMS / NotifCollection / Shade）缩小范围。

---

## 六、阶段 3：Shade 下拉面板与 QS（24 h）

### 主线

- 面板本体：`NotificationPanelViewController`（`statusbar/phone/NotificationPanelViewController.java:181`）负责手势、展开高度、折叠、与锁屏的联动。
- 面板状态机：`ShadeControllerImpl`（`statusbar/phone/ShadeControllerImpl.java:41`）负责「现在该不该展开/收起」，以及和 Keyguard、转场的协调。
- 承载窗口：`NotificationShadeWindowControllerImpl`（:77）创建 `TYPE_NOTIFICATION_SHADE` 窗口（:211），`mWindowManager.addView(mNotificationShadeView, mLp)`（:232）。**这是 SystemUI 与 WMS 最直接的接触点之一。**
- 背景遮罩：`ScrimController`（`statusbar/phone/ScrimController.java:75`）管 scrim 的透明度与前后层。
- QS：`QSTileHost`（`qs/QSTileHost.java:78`）管 tile 的创建/排序/监听；`QuickQSPanelController`（`qs/QuickQSPanelController.java:42`）管快捷面板那 6 个。

### 常见坑

- 面板拉不下来：锁屏状态、`disable` 标志、或 `NotificationPanelViewController` 的手势被上层窗口吃掉。
- 拉下来收不回去：`ShadeControllerImpl` 的状态与 Keyguard/转场不同步，常见于解锁瞬间。
- 加 QS tile 后不显示：tile 没在 `QSTileHost` 注册，或 `defaultTileList` 没加。
- 面板背景透明/黑块：`ScrimController` 的 alpha 被动画打断。

### 实验与验收

- 加一个自定义 QS tile（带长按跳转），重启后仍在。
- 用 `cmd statusbar expand-notifications` / `collapse` 驱动面板，观察 `ShadeControllerImpl` 的状态变化。
- 验收：能画出「手指下拉 → 面板展开 → 松手吸附/回弹」的状态机，并指出每个状态由谁维护。

---

## 七、阶段 4：Keyguard 锁屏与解锁（20 h）

### 主线

```
灭屏/亮屏 → KeyguardViewMediator(:173) 决定 show/hide
  → KeyguardUpdateMonitor(:141) 收集凭据/生物识别/ SIM 状态
  → KeyguardBouncer(:57) 弹出密码/PIN 界面
  → 解锁成功 → hide → 通知 Shade/StatusBar/转场
```

- `KeyguardViewMediator` 是总调度，`KeyguardUpdateMonitor` 是状态源，`KeyguardBouncer` 是「要输密码时的那层」。
- 与 WMS 的关系：锁屏是一个特殊窗口 + 一组可见性规则；`showWhenLocked` 的 Activity 能盖在锁屏上，但转场仍受 Keyguard 控制。
- 与 Shade 的关系：锁屏上下拉是「锁屏面板」，解锁后才是「通知面板」，两者共用 `NotificationPanelViewController` 的不同配置。

### 常见坑

- 解锁后黑屏：Keyguard 已 hide 但下面的窗口还没 drawn，属于转场时序问题，不是锁屏 bug。
- 锁屏上通知不显示：通知的 `visibility` / `isSensitive` 被隐藏，属正常策略。
- 指纹解锁后仍停在锁屏：`KeyguardUpdateMonitor` 的生物识别回调没触发 `KeyguardViewMediator` 的 dismiss。
- 多用户/工作资料下锁屏异常：`config_systemUIServiceComponentsPerUser` 只重启 `NotificationChannels`，其他组件状态要自己处理。

### 实验与验收

- 用 `adb shell input keyevent 26/82` 走一遍灭屏→亮屏→解锁，配合 logcat 打出每个阶段的时间戳。
- 做一个 `showWhenLocked` 的 Activity，观察它与锁屏、通知面板的层级关系。
- 验收：能解释「解锁后黑屏」和「锁屏不显示通知」是两条完全不同的链路。

---

## 八、阶段 5：导航栏、手势与 Recents（20 h）

### 主线

- 导航栏：`NavigationBarController`（`navigationbar/NavigationBarController.java:85`）按 display 创建/销毁 `NavigationBarView`（:101），支持三键/两键/手势三种模式。
- 手势返回：`EdgeBackGestureHandler`（`navigationbar/gestural/EdgeBackGestureHandler.java:94`）在 SystemUI 侧识别边缘滑动；WMS 侧的 `SystemGesturesPointerEventListener`（`services/core/java/com/android/server/wm/SystemGesturesPointerEventListener.java:40`）负责把系统手势事件送过来。**边缘返回失效，两边都要查。**
- Recents：`Recents`（`recents/Recents.java:33`）只是壳，真正实现由 Launcher/QuickStep 提供（`RecentsImplementation`）；跨进程入口是 `OverviewProxyService`（`recents/OverviewProxyService.java:122`）。
- 与 WMS 的边界：导航栏高度决定 Insets；手势区域属于 WMS 的 system gesture exclusion；Recents 动画走 Shell。

### 常见坑

- 隐藏导航栏后手势失效：只改了可见性，没同步 gesture inset / exclusion 区域。
- 三键切换手势后返回键位置错：`NavigationBarView` 没重建，或 overlay 配置没生效。
- Recents 拉不起来：Launcher 进程死了 / `OverviewProxyService` 没连上，不是 SystemUI 本身。
- 手势与 App 的 edge-to-edge 冲突：App 没处理 `systemGestures` inset。

### 实验与验收

- 用 `cmd overlay` 切换手势/三键导航，观察 `NavigationBarView` 重建。
- 复现一次「隐藏导航栏导致手势返回失效」，定位是 inset 还是 exclusion 区域。
- 验收：能说清一次边缘返回从触摸到 App `onBackPressed` 的完整链路，以及 SystemUI 在哪一环。

---

## 九、阶段 6：系统级 UI 服务（14 h）

这些组件单个不大，但线上问题不少，按需读：

| 组件 | 锚点 | 要点 |
|---|---|---|
| 音量 | `VolumeUI(:35)` → `VolumeDialogImpl(:136)` | 音量键拦截在 `PhoneWindowManager`，面板在 SystemUI |
| 关机/重启 | `GlobalActionsComponent(:39)` | 长按电源键的菜单；与 Keyguard 的交互 |
| 截图 | `TakeScreenshotService(:60)` | system_server 起服务，`takeScreenshotFullscreen/Partial` |
| 圆角/刘海 | `ScreenDecorations(:107)` | 用 overlay 窗口画圆角/挖孔，多屏要分别处理 |
| 放大镜 | `WindowMagnification` | 无障碍放大，窗口层级特殊 |
| 勿扰/AOD | `DozeService(:36)` | DreamService 体系，和灭屏时序强相关 |
| Toast/存储/电源 | `ToastUI` / `StorageNotification` / `PowerUI` | 都是 SystemUI 组件，按 config 启动 |

### 验收

任选两个，能说出「它加了什么类型的窗口、什么时候显示、和 WMS 的哪条规则交互」。

---

## 十、阶段 7：与 WMS / WMShell 的交界（24 h，决定你能不能排疑难）

这一阶段是把 WMS 知识变现的地方。四条交界线：

1. **窗口类型与权限**：`TYPE_STATUS_BAR`、`TYPE_NOTIFICATION_SHADE`、`TYPE_NAVIGATION_BAR` 由 SystemUI 添加；层级、焦点、触摸区域仍由 WMS 的 `DisplayPolicy`/`InputMonitor` 决定。
2. **Insets 与 SystemBarAttributes**：SystemUI 画多高，WMS 就留多少 inset；`DisplayPolicy.java:2561` 把 appearance 推下来。**状态栏遮挡 App 内容、全屏手势冲突，都在这条线上。**
3. **转场**：`WMShell`（`sysui/wmshell/WMShell.java:93`）在 SystemUI 进程里加载 `Transitions`/`ShellTransitions`；SystemUI 的窗口要参与转场，否则会出现「动画跳变/闪黑」。
4. **冻屏/黑屏**：SystemUI 的窗口没 draw，WMS 等 `isDrawn`，输入/转场就卡住。之前那个「隐藏 TaskBar 导致冻屏」的案例就是典型：**表面是 SystemUI 少画一帧，根因在窗口的绘制回调链**。

### 排障顺序（建议固化成习惯）

```
现象（黑屏/冻屏/闪）
  → dumpsys window：窗口在不在、visible 吗、frame 对吗、mDrawState 是什么
  → dumpsys input：焦点窗口是谁、有没有 waitQueue
  → logcat --pid=$(pidof com.android.systemui)：异常/ANR/掉帧
  → Winscope：转场与层级随时间的变化
  → 最后才怀疑业务逻辑
```

### 验收

拿一个真实的 SystemUI 冻屏/黑屏 case，写出「现象 → 三层 dump → 根因 → 修复/规避」的完整记录。

### 工具

[Window Dump × 壁纸黑闪分析器](wallpaper-blackflash-analyzer.html)：粘贴 `dumpsys window windows` 与 logcat，自动对齐壁纸窗口状态、转场时间窗和 Surface 重建事件。

---

## 十一、阶段 8：定制、稳定性与面试（22 h）

### 定制三板斧

- **RRO/Overlay**：改资源不改代码，`cmd overlay list` 验证；车机/ODM 最常用。
- **SystemUIFactory / Dagger**：换实现类，适合深度定制；先看 `config_systemUIFactoryComponent`。
- **直接改组件**：只有前两条走不通时才做，改完必须回归锁屏、通知、转场三条主线。

### 稳定性

- SystemUI ANR：主线程被通知绑定/数据库/锁竞争阻塞；看 `dumpsys activity processes` + traces。
- 内存：通知过多、图标缓存、壁纸；`GarbageMonitor` 是内置的泄漏监控组件。
- 进程重启：`SysuiRestartReceiver` / `killall` 后能否自愈，是判断「状态残留」最快的实验。

### 面试高频 12 题

1. SystemUI 进程怎么启动？组件模型是什么？
2. `StatusBar` 和 `SystemUIApplication` 是什么关系？
3. 一条通知从 post 到展示经过哪些类？12 和 11 有什么区别？
4. heads-up 什么时候弹？被什么抑制？
5. 状态栏图标怎么加？深色图标怎么切？
6. QS tile 的生命周期？怎么加一个？
7. 锁屏解锁流程？Keyguard 和 WMS 怎么配合？
8. 手势返回怎么实现？SystemUI 和 WMS 各做什么？
9. SystemUI 的窗口类型有哪些？为什么普通 App 加不了？
10. 下拉面板卡住/收不回去怎么排？
11. SystemUI ANR/冻屏怎么定位？
12. 怎么用 RRO 定制 SystemUI？

---

## 十二、四个实战项目（必须交付东西）

> 判断标准：有 patch / 工具有报告，能复现、能验证。跑两条 dumpsys 不算项目。

### P1 通知全链路时间戳工具（3–5 天）

- 做什么：监听 `NotifPipeline`/`NotifCollection`/`RowBinder` 的关键节点，输出一条通知从 post 到可见各阶段耗时。
- 交付物：一个可重复运行的脚本或 debug 版 patch + 一份 10 条通知的耗时表。
- 验收：能解释「为什么这条通知比别人慢 100 ms」。

### P2 QS Tile + 状态栏图标定制（3–5 天）

- 做什么：加一个自定义 tile（带长按动作）+ 一个动态 system icon。
- 交付物：patch + 截图 + 回归记录（重启、多用户、深浅色切换）。
- 验收：三种场景都不崩、不残留。

### P3 锁屏解锁时序与故障注入（5–7 天）

- 做什么：抓一次完整解锁的时序图；人为注入 3 个故障（bouncer 不消失、指纹回调丢失、解锁后黑屏）。
- 交付物：时序图 + 3 份「现象→根因→修复」记录。
- 验收：每个故障都能在 15 分钟内定位到类。

### P4 SystemUI × WMS 冻屏复现（5–7 天）

- 做什么：复现「隐藏 TaskBar 导致冻屏」类问题，从 SystemUI 侧确认谁没 draw，再从 WMS 侧确认在等什么。
- 交付物：完整 case 报告 + 两种修法对比。
- 验收：能讲清「为什么少画一帧会冻住整个输入/转场」。

---

## 十三、节奏表（12 h/周）

| 周 | 内容 | 产出 |
|---|---|---|
| 1 | 阶段 0 + 阶段 1 前半 | 启动链笔记 + 图标实验 |
| 2 | 阶段 1 后半 | 状态栏 appearance 链路图 |
| 3–4 | 阶段 2 | 通知管线图 + P1 开工 |
| 5 | 阶段 2 收尾 + P1 | P1 交付 |
| 6–7 | 阶段 3 | P2 交付 |
| 8–9 | 阶段 4 | P3 交付 |
| 10–11 | 阶段 5 | 手势/Recents 链路笔记 |
| 12 | 阶段 6 | 两个小系统笔记 |
| 13–14 | 阶段 7 | P4 交付 |
| 15 | 阶段 8 + 面试 | 12 题自测 + 项目复盘 |

---

## 十四、源码速查

```bash
# 进程与组件
adb shell dumpsys activity service com.android.systemui/.SystemUIService
adb shell ps -A | grep systemui

# 窗口
adb shell dumpsys window | grep -E "StatusBar|NotificationShade|NavigationBar"
adb shell dumpsys window windows

# 通知
adb shell dumpsys notification --noredact

# 系统栏控制
adb shell cmd statusbar help
adb shell cmd statusbar expand-notifications
adb shell cmd statusbar collapse

# 定制
adb shell cmd overlay list
adb shell cmd overlay enable <package>

# 重启验证
adb shell killall com.android.systemui
```

**关键路径速记**

```
sysui/SystemUIApplication.java            组件容器
sysui/SystemUIService.java                入口 Service
sysui/statusbar/phone/StatusBar.java      装配工
sysui/statusbar/CommandQueue.java         system_server → SystemUI 的回调入口
sysui/statusbar/phone/NotificationShadeWindowControllerImpl.java  Shade 窗口
sysui/statusbar/phone/NotificationPanelViewController.java        面板手势/展开
sysui/statusbar/notification/collection/NotifPipeline.java        通知编排
sysui/statusbar/notification/collection/NotifCollection.java      通知数据
sysui/keyguard/KeyguardViewMediator.java  锁屏总调度（注意是 keyguard/ 包）
sysui/wmshell/WMShell.java                Shell 接入点
```

> 注：`KeyguardViewMediator`、`KeyguardUpdateMonitor` 在 `com/android/keyguard/` 包（不是 `com/android/systemui/`），AOSP 12 里这两个包并存，`find` 时别漏。
