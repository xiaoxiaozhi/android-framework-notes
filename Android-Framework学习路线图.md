# Android Framework 学习路线图（2026 版）· B 赛道专版

> **已选定 B：系统框架层（真正的 Framework）**。本文已按 B 裁剪：A 向技能整块降级，时间集中投到 Binder / 系统服务 / 稳定性。

> 面向：已有基础、想转/深入 Android 系统框架层的开发者。
> 写于 2026-10-18。**HTML 版（同款系列样式，带深/浅色主题）**：[`Android-Framework学习路线图.html`](Android-Framework学习路线图.html)
> 岗位分布结论来自当日实际抓取的招聘样本（联想 Framework 工程师 / Framework 多媒体 / 性能优化岗、光庭信息车载 Android FW/HAL、智联与 Indeed 的 Framework 岗位列表），属于样本观察，不是全量统计。
> 学习阶段里的源码路径以 AOSP 12 为准，你本机就在 `/home/book/aosp12`。

---

## 〇、你已选定 B：系统框架层（真正的 Framework）

目标锁定 **B**。下面保留三赛道对照，是为了说清「为什么不是 A/C」；从第二章起全部内容按 B 裁剪。

| 赛道 | 干什么 | 岗位量 | 门槛 | 天花板 | 对你 |
|---|---|---|---|---|---|
| A. 应用层（App/客户端） | 写业务 App、SDK、跨端 | ★★★★★ 最多 | 低 | 中 | ❌ 不选（护城河浅） |
| **B. 系统框架层** | 改 `frameworks/base`、系统服务、SystemUI、稳定性 | ★★★ 中等 | 高 | **高** | ✅ **目标** |
| C. 内核 / BSP / HAL | 内核、驱动、HAL 适配、板级移植 | ★★★ 中等偏硬件 | 最高 | 高 | ⚠️ 只把 HAL 当 B 的接口用 |

### B 赛道的加减法（这张表决定你时间花在哪）

| | 内容 | 为什么 |
|---|---|---|
| **砍掉 / 降级** | App 业务栈：Jetpack 全家桶、MVVM、跨端 Flutter/RN、Gradle 工程化 | B 岗不看；只留「能读懂 App 怎么写」的上游视角 |
| | App 侧性能优化（列表复用、图片库、App 启动优化） | 知道概念即可，深挖是 A 的 KPI |
| | 三方库源码（OkHttp / Glide 之类） | 对 B 无投入价值 |
| | 内核 / 驱动开发 | B 不主动深入；除非你日后转 C |
| **补上 / 升级** | **AOSP 编译 → 裁剪 → 定制 → 刷机** | 从「会」变「日常」——B 岗第一天就要用 |
| | **Binder 深水区** | 驱动、线程池、oneway、死亡通知、ServiceManager |
| | **SystemServer 启动顺序与服务注册机制** | 所有系统服务的户口本 |
| | **AMS / WMS / PMS 源码级** | B 岗笔试面试主战场 |
| | **SystemUI** | B 岗「能立刻上手改东西」的最低门槛项目 |
| | **系统应用 + 系统签名**（platform 签名 / sharedUserId / 特权权限） | 改系统必碰 |
| | **SELinux 与权限模型** | 改系统必踩的坑 |
| | **系统裁剪与定制**（config 默认配置、RRO overlay） | 厂商岗日常 |
| | **OTA / 升级 / 多用户** | 厂商岗常见 |
| | **Watchdog 与稳定性机制** | 稳定性岗核心 |
| | **稳定性与性能工具链**（Perfetto / ANR / native crash / 内存） | 你的核心竞争力来源 |
| | （车机向）HAL（HIDL/AIDL）、CarService、VehicleHAL | 车机 B 岗硬要求 |

### B 的三个「能」（验收标准，达不到就不算入门）

1. **能改**——改一处系统行为（状态栏 / 导航栏 / 默认策略），编译刷机看到效果。
2. **能查**——给你一个 ANR 或系统 bug，能独立定位到根因（不是猜）。
3. **能讲**——三大服务全链路时序图讲得出来，每步带**类名 + 文件 + 行号**。

### B 的三个「不」

1. **不做 API 调用工程师**——那是 A；会调 API 不等于懂系统。
2. **不背结论**——所有说法都要能追到源码行号。
3. **不跳过 Binder**——它是 B 赛道的第一道分水岭，跳过的人永远在表层打转。

> 📌 B 岗面试必答清单见第七章。

---

## 一、实际开发中哪一部分岗位最多

按 2026-10 抓到的招聘样本，需求量从大到小：

### 1️⃣ 车载 / 智能座舱 Android FW + HAL —— 当前最大增量池
证据：光庭信息「Android FW/HAL」明确写「智能座舱 Framework 层、HAL 层核心模块定制开发」「Binder、HIDL/AIDL 打通系统层与驱动层」；智联上海样本里「车载项目 + Framework」「车载项目 Java/C++」反复出现。

要求画像：
- 熟悉 AOSP 编译、裁剪、定制流程
- 精通 Framework 系统层 **或** HAL（HIDL/AIDL）硬件适配
- 至少擅长车载任一模块：**车控 CarService/VehicleHAL、车载音频、相机、网络、车载诊断、系统策略定制**
- 独立处理量产稳定性问题

> 这是**目前最容易进、也最缺人**的方向。缺点是项目节奏紧、偏交付。

### 2️⃣ 系统稳定性 / 性能优化 —— 每家大厂都有，永远缺
证据：联想「Android 性能优化工程师（武汉）」要求「熟悉 AMS、WMS、Binder」；联想 Framework Engineer 岗位职责第 2 条直接是「ANR、Crash、内存泄漏、卡顿、冻屏等疑难问题」。

要求画像：
- 精通 Systrace / Perfetto / bugreport / gdb
- 会看 ANR trace、native crash、内存 dump、冻屏日志
- 懂开机优化、内存优化、长待机功耗

> 这是**最能体现"资深"的方向**，也是 Framework 岗面试的核心考察区。

### 3️⃣ Framework 多媒体（音视频 / 图形）
证据：联想「Framework 多媒体工程师」要求 AudioFlinger / AudioPolicyManager 核心流程、音视频编解码协议、图形模块。

### 4️⃣ 短距通信（WiFi / BT / GPS / NFC）FW
证据：联想「Framework 短距通信工程师」。

### 5️⃣ 手机厂商框架定制（SystemUI / 多窗口 / 折叠屏 / 动效）
需要：WindowManager / SystemUI / Shell Transitions / 多屏多窗。**你正在学的 WMS 正好落在这里。**

### 6️⃣ 系统应用 / ROM 定制（Settings、Launcher、OTA、FOTA、权限中心）

### 结论一句话
> **想快进圈 → 车载 FW/HAL；想走深 → 稳定性+性能优化；想炫技 → 图形/多媒体。**
> 三者都以 **Binder + AMS + WMS + SystemServer** 为公共地基，所以地基不会白学。

---

## 二、哪些最重要：必备 vs 加分

### 🔴 必备（面试必问、日常必用、不学就干不了活）

| # | 知识点 | 一句话为什么 | 源码位置（AOSP 12） |
|---|---|---|---|
| 1 | **AOSP 编译与刷机** | 不会编译刷机 = 不会调试系统 | `build/`、`device/`、`lunch`/`m` |
| 2 | **Binder** | 所有跨进程的根，AMS/WMS/PMS 全靠它 | `frameworks/native/libs/binder/`、`frameworks/base/core/java/android/os/Binder.java` |
| 3 | **Handler / Looper / MessageQueue** | 所有异步与主线程的根，ANR 的源头 | `frameworks/base/core/java/android/os/Looper.java` |
| 4 | **启动流程 init → Zygote → SystemServer** | 一切系统服务诞生的地方 | `system/core/init/`、`ZygoteInit.java`、`SystemServer.java` |
| 5 | **AMS（ActivityTaskManagerService）** | 四大组件 + 任务栈 + 生命周期 | `services/core/java/com/android/server/wm/ActivityTaskManagerService.java` |
| 6 | **WMS** | 窗口、层级、显示、输入的前提 | `services/core/java/com/android/server/wm/WindowManagerService.java` |
| 7 | **PMS（PackageManagerService）** | 安装、权限、包解析 | `services/core/java/com/android/server/pm/PackageManagerService.java` |
| 8 | **SurfaceFlinger + 图形栈** | 像素怎么上屏，卡顿/掉帧必查 | `frameworks/native/services/surfaceflinger/` |
| 9 | **Input 分发** | 触摸/按键到窗口的全链路 | `frameworks/native/services/inputflinger/` |
| 10 | **调试工具链** | logcat / dumpsys / Systrace / Perfetto / bugreport / gdb | — |
| 11 | **SELinux 与权限模型** | 改系统必碰的拦路虎 | `system/sepolicy/` |

### 🟡 加分（决定你值多少钱、能不能拿高薪）

- **HAL 层**：HIDL / AIDL、HAL 接口定义与适配（车机岗硬要求）
- **C++ / Native / JNI**：`frameworks/native`、`frameworks/av` 全是 C++
- **稳定性专精**：ANR/Crash/内存/冻屏/开机优化
- **性能专精**：Perfetto 抓帧、GPU/CPU 调度、功耗
- **车机特有**：CarService、VehicleHAL、CAN 总线、多屏互动
- **图形进阶**：RenderEngine、HWC、BLAST、Choreographer
- **AI 端侧**：TFLite / MNN / NCNN（2026 年不少 JD 已列加分项）

---

## 三、学习路线图（六阶段）

> 原则：**问题驱动 + 必须动手**。每阶段都要「改一处代码 → 编译 → 刷机 → 观察现象」。
> 光看不练的 framework 学习 = 白学，因为所有知识都长在「运行时行为」上。

### 阶段 0：地基（1–2 周）

| 内容 | 到什么程度 |
|---|---|
| Linux 基础 | 进程/线程/内存/文件系统/信号/`ps`/`top`/`strace`/`readelf` |
| Java 进阶 | 反射、注解、并发、AIDL 语法 |
| C++ 基础 | 指针、引用、类、STL 够读 `frameworks/native` |
| 构建工具 | Make/Soong/Blueprint、Ninja 概念 |
| Git + repo | AOSP 是多仓，`repo` 必须会 |

**产出**：能写 shell/python 脚本自动化；能看懂 `Android.bp`。

### 阶段 1：AOSP 上手与调试体系（2–3 周）

- 拉源码（你已有：`/home/book/aosp12`）
- 学会 `lunch` / `m` / `mmm` / `adb sync` / 单模块编译
- **刷机**：`fastboot flashall` 或 `adb push` 单文件替换
- 调试四件套：
  - `adb shell dumpsys activity|window|input|package|SurfaceFlinger`
  - `adb shell cmd window` / `cmd activity`
  - Perfetto / Systrace 抓 trace
  - `adb bugreportz`

**验收**：独立把 SystemUI 的一个字符串/颜色改掉，编译、刷机、看到效果。

### 阶段 2：进程与 IPC —— 系统的骨架（3–4 周）★ 最容易被跳过、但最关键

1. **init 与 init.rc** —— 系统第一个进程
2. **Zygote** —— 所有 Java 进程的母体（fork + COW）
3. **SystemServer** —— 系统服务的诞生地（`startBootstrapServices` / `startCoreServices` / `startOtherServices`）
4. **Binder（重点中的重点）**
   - Java 侧：`Binder` / `BinderProxy` / `AIDL` / `ServiceManager`
   - Native 侧：`IPCThreadState` / `ProcessState` / `binder.c`
   - 一句话能讲清：一次跨进程调用，数据从 Java 到驱动再回来，一共拷贝几次？
5. **Handler / Looper / MessageQueue / IdleHandler / Barrier**
   - 同步屏障与 VSYNC 的关系（后面图形栈会用到）
6. **AIDL / HIDL 写法**

**验收**：自己写一个 AIDL 服务，从另一个进程调用；能用 `dumpsys` 看服务注册表。

### 阶段 3：三大主服务 —— 系统的器官（4–6 周）

| 服务 | 学什么 | 你现在的进度 |
|---|---|---|
| **WMS** | 窗口树、DisplayArea、层级/Z 序、遍历刷新、Surface 创建、事务提交 | ✅ **你已深入**（00–06 篇） |
| **AMS** | startActivity 全链路、ActivityRecord/Task、生命周期、launchMode、进程管理、回退栈 | ⬜ 下一个重点 |
| **PMS** | APK 解析、签名校验、权限、安装流程、包扫描 | ⬜ 之后 |

**学习顺序建议**：`WMS → AMS → PMS`。
你已经把 WMS 走通了，而 WMS 的上游正是 AMS（`ActivityRecord extends WindowToken` —— 你 06 篇已经摸到了），**顺着这条线接 AMS 是最省力的路径**。

**验收**：能画出一张「startActivity → ActivityRecord 挂进 Task → 首帧上屏 → 删除」的完整时序图，每步都带类名+行号。

### 阶段 4：图形与输入 —— 让人"看得见、摸得着"（3–4 周）

- **图形栈**：`Choreographer` → VSYNC → `ViewRootImpl.performTraversals` → `relayoutWindow` → `SurfaceControl` → `BLASTBufferQueue` → `SurfaceFlinger` → `HWC`
  （你 03/04 篇已经覆盖了后半段）
- **渲染线程模型**：UI 线程 / RenderThread / Binder 线程池
- **输入**：`InputReader` → `InputDispatcher` → `InputChannel` → `ViewRootImpl`（你 05 篇已覆盖）
- **动画与过渡**：`AppTransition` / `TaskOrganizer` / `RemoteAnimation`（12 上还不是 Shell Transitions 主线）

**验收**：用 Perfetto 抓一次「点击 → 界面刷新」，能在 trace 里指出每一帧的耗时构成。

### 阶段 5：稳定性与性能 —— 从"会读代码"到"能解决问题"（持续）

| 主题 | 关键工具 | 典型问题 |
|---|---|---|
| ANR | ANR trace、`dumpsys input`、主线程堆栈 | 主线程阻塞 / 无焦点窗口 / Binder 阻塞 |
| Crash | tombstone、`debuggerd`、native crash | SIGSEGV / abort / abort message |
| 内存 | `dumpsys meminfo`、heapprof、LeakCanary、native 泄漏 | 系统服务泄漏、fd 泄漏 |
| 卡顿/掉帧 | Perfetto、Systrace、`dumpsys gfxinfo` | 掉帧、jank、RenderThread 阻塞 |
| 开机 | `bootchart`、`logcat --pid`、event log | 服务启动慢、SELinux 拒绝 |
| 功耗 | `batterystats`、Wakelock、Wakeup 统计 | 长待机异常唤醒 |
| 冻屏 | WMS 日志、SF 日志、Watchdog | 死锁、Watchdog 触发 |

**验收**：能独立从 bugreport 里定位一个 ANR 的根因。

### 阶段 6：方向专项（按目标岗选，4 周起）

- **走车载**：HAL（HIDL/AIDL）→ 写一个 HAL → CarService / VehicleHAL / CAN / 多屏
- **走手机厂商**：SystemUI 定制 → 多窗口/分屏/折叠屏 → 动效与过渡
- **走多媒体**：AudioFlinger / AudioPolicyManager / MediaCodec / 图形管线
- **走通信**：WiFi framework / Bluetooth / RIL
- **走内核**：Binder 驱动 → 调度 → 内存管理 → 驱动开发

---

## 四、按岗位反查要学什么

| 目标岗位 | 必修阶段 | 加分项 | 样本要求（2026-10 实抓） |
|---|---|---|---|
| 车载 Android FW/HAL | 0–3 | HAL、CarService、CAN | 「精通 Framework 系统层或 HAL（HIDL/AIDL）」 |
| 系统稳定性/性能优化 | 0–5 | Perfetto 深挖、内核基础 | 「熟悉 AMS、WMS、Binder」「ANR/Crash/内存/卡顿/冻屏」 |
| Framework 多媒体 | 0–4 | AudioFlinger、编解码 | 「AudioFlinger/AudioPolicyManager 核心流程」 |
| 短距通信 FW | 0–3 | WiFi/BT 协议栈 | 「WiFi/BT/GPS/NFC 模块」 |
| 手机厂商框架定制 | 0–4 | SystemUI、多窗口 | 「SystemUI/多窗口/动效」 |
| 系统应用/ROM | 0–2 | Settings/Launcher/OTA | 「AOSP 裁剪、定制」 |

---

## 五、时间与节奏建议

| 阶段 | 时长 | 每天投入 | 里程碑 |
|---|---|---|---|
| 0 地基 | 1–2 周 | 1–2h | 能写脚本、能读 Android.bp |
| 1 AOSP 上手 | 2–3 周 | 2h | 独立编译刷机 |
| 2 进程与 IPC | 3–4 周 | 2h | AIDL 服务 + Binder 讲得清 |
| 3 三大主服务 | 4–6 周 | 2–3h | 三大服务时序图 |
| 4 图形与输入 | 3–4 周 | 2h | Perfetto 能定位掉帧 |
| 5 稳定性性能 | 持续 | 2h | 独立解 ANR |
| 6 方向专项 | 4 周+ | 2h | 一个真实项目/PR |

**总计约 6 个月**能到「能面试 Framework 岗」的水平；到「能独当一面」通常需要 1–2 个真实项目周期。

### 三条纪律

1. **不要只读书/只读源码**：每学一块，必须有一次「改→编→刷→看」的闭环。
2. **一切结论落到「类名 + 文件 + 行号」**：含糊的"大概在 AMS 里"不算学会。
3. **建自己的问题库**：把遇到的每个 ANR/Crash/黑屏都写下来（现象 → 因果 → 怎么查），这就是你未来的面试题库和工作手册。

---

## 六、你现在的起点与下一步（个人建议）

**你已经在阶段 3 的 WMS 部分走了很深**（窗口层级 00–06 篇、AOSP12 源码树、ASfP、WSL 环境都齐了），这是很多人半年都到不了的位置。

**按 B 赛道**，这个起点非常关键：B 的三根支柱是 **Binder（地基）+ 系统服务（主体）+ 稳定性（价值）**，而你已经拿下「系统服务」里最大的一块 WMS。所以要补的是**两侧**，不是从头重学。

所以你的路线**不需要从头走**，建议这样接：

```
已完成：阶段 1（编译/环境✅ 部分） + 阶段 3 的 WMS ✅
     ↓
① 补 Binder        （阶段 2 的核心，你一直在用它但没系统学过）
     ↓
② 接 AMS           （阶段 3 续，顺着 ActivityRecord = WindowToken 这条线走最顺）
     ↓
③ 补 PMS           （阶段 3 收尾）
     ↓
④ 图形/输入回炉     （阶段 4，你 03/04/05 篇已覆盖大半，补齐 RenderThread 与 Perfetto）
     ↓
⑤ 稳定性与性能      （阶段 5，这是你最该花时间的地方 → 直接对应岗位最多的方向之一）
     ↓
⑥ 按目标岗选专项     （车机 HAL / 手机厂商定制 / 多媒体）
```

**下一步最该做的三件事**

1. **补 Binder**：它是你已学的 WMS 全链路的底层（`addToDisplayAsUser` 就是一次 Binder 调用）。你现在的知识在 Binder 处有个"断口"。
2. **接 AMS**：把 06 篇结尾的悬念（ActivityRecord 从哪来、到哪去）接着写下去 —— 这正好是路线图里的 **07 篇**。
3. **建"实战坑"档案**：你已经在文章里写「🐛 实战」和思考题了，把这个习惯扩展成一份独立的《Android 系统问题库》（现象/因果/排查命令），面试和干活都靠它。

---

## 七、B 岗面试必答清单（B 赛道专用）

这 10 题是 B 岗技术面的主战场。每题的答案都要求能落到类名 / 行号，含糊过关会被追问到底。

| # | 问题 | 考什么 | 参考锚点（AOSP 12） |
|---|---|---|---|
| 1 | 一次 `startActivity` 从 App 到新 Activity 首帧的完整链路 | 跨 ATMS → WMS → App 的全局观 | `ATMS.startActivity` → `ActivityStarter.execute` → `ActivityRecord` → `ViewRootImpl.setView` |
| 2 | Binder 一次调用数据拷贝几次？为什么？oneway / 死亡通知 | IPC 底层 | `libs/binder/`、`IPCThreadState`、`Binder.java` |
| 3 | Handler 的同步屏障（Barrier）是什么？和 VSYNC 什么关系 | 异步与渲染 | `MessageQueue.postSyncBarrier`、`Choreographer` |
| 4 | ANR 有哪几种？怎么从 bugreport 定位 | 稳定性核心 | `InputDispatcher` 超时、`ActivityManagerService` ANR 路径 |
| 5 | 系统启动：init → Zygote → SystemServer 各做了什么？服务怎么注册 | 启动链路 | `init.rc`、`ZygoteInit`、`SystemServer.startOtherServices` |
| 6 | WMS 窗口树结构、Z 序怎么定、relayout 与 Surface 创建 | 窗口系统 | 你 00–06 篇已覆盖 |
| 7 | Activity 生命周期与 Task / launchMode 的关系 | 组件模型 | `ActivityRecord`、`Task`、`startActivityUnchecked` |
| 8 | 权限模型：安装时 / 运行时 / 特权权限 / SELinux | 安全与权限 | `pms/`、`system/sepolicy/` |
| 9 | 卡顿怎么分析？一帧的耗时构成 | 性能 | Perfetto / Systrace + `Choreographer` |
| 10 | 一个系统 bug 的完整定位过程（现象→假设→工具→根因→修复） | 综合实战 | 无固定答案，看方法 |

**面试加分行为**：被问到不确定的，主动说「我下去查一下源码，目前推断是 XXX，验证点是 YYY」——B 岗面试官最反感的是编。

---

## 附：常用命令速查

```bash
# 环境
lunch aosp_x86_64-userdebug && m -j$(nproc)
adb sync system / adb reboot

# 观察窗口与 Activity
adb shell dumpsys window windows
adb shell dumpsys activity activities
adb shell dumpsys activity displays
adb shell cmd window tracing start / stop

# 输入
adb shell dumpsys input
adb shell getevent -lt

# 包与权限
adb shell dumpsys package <pkg>
adb shell appops get <pkg> <OP>

# 图形
adb shell dumpsys SurfaceFlinger
adb shell dumpsys gfxinfo <pkg>

# 性能
perfetto（web 端加载 trace）
adb shell dumpsys meminfo <pkg>
adb shell dumpsys batterystats

# 崩溃
adb shell dumpsys dropbox --print
adb bugreportz
```

---

*本文与你的《WMS 学习路线图》是包含关系：WMS 路线图 = 本文「阶段 3 的 WMS 部分」的展开。*
