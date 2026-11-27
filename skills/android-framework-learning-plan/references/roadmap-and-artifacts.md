# Framework 路线图：已产出文件、内容骨架与刷新方式

用途：规划/更新 Android Framework 学习路线时照此，避免重新推导结构、重新抓一轮样本、或造出与既有文档冲突的第二份规划。

## 一、已产出文件（先看它们，别重造）

> **路径前提**：系列目录 2026-10-18 已从 `D:\openclaw\Android窗口层级` 移到 `D:\openclaw\Android framework\Android窗口层级\`（下表已按新位置写；再动前先按 `android-window-06*.html` 搜定实际目录）。

| 文件 | 内容 | 说明 |
|---|---|---|
| `D:\openclaw\Android-Framework学习路线图.md` | 权威正文（Markdown） | 2026-10-18 建，同日按用户选定 **B 赛道** 改过一版 |
| `D:\openclaw\Android-Framework学习路线图.html` | 同内容 HTML（系列同款版式） | 顶部/页脚与系列文章互链；页脚指 md 版、系列 index、WMS 路线图 |
| `<系列目录>\wms-practice-projects.html` | 实践清单①：挖自马老师库的实战作业（P0–P5） | index 有卡片 |
| `<系列目录>\wms-original-projects.html` | 实践清单②：自造项目（L1–L6） | index 有卡片 |
| `<系列目录>\WMS学习路线图.md` / `android-window-roadmap.html` | WMS 单模块六阶段路线 | 本图的**下位**（阶段 3 的 WMS 部分展开） |

## 二、正文骨架（章节顺序即目录顺序）

1. 〇 赛道分诊：三赛道对照表 + **B 赛道加减法**（砍什么/补什么两个清单）+ B 的三个「能」（能改/能查/能讲）+ B 的三个「不」。
2. 一 岗位分布：按需求量排序，每条附招聘原文摘录当证据（见下「样本纪律」）。
3. 二 必修清单：必备表（AOSP 编译刷机、Binder、Handler/Looper、init→Zygote→SystemServer、AMS/WMS/PMS、SurfaceFlinger、Input、调试工具链、SELinux）+ 加分表（HAL(HIDL/AIDL)、C++/JNI、稳定性专精、性能专精、车机 CarService/VehicleHAL/CAN、图形进阶、端侧 AI）。
4. 三 六阶段路线（地基 → AOSP 上手与调试体系 → 进程与 IPC → 三大主服务 → 图形与输入 → 稳定性与性能 → 方向专项）。
5. 四 按岗位反查要学什么（表：目标岗 × 必修阶段 × 加分项 × 样本要求）。
6. 五 时间节奏（总计约 6 个月到「能面试」）+ 三条纪律。
7. 六 你的起点与下一步（**按用户已有进度裁剪**，不从头排）。
8. 七 B 岗面试必答清单（10 题，附参考锚点）。
9. 附 常用命令速查（编译/窗口/输入/包权限/图形/性能内存/崩溃）。

文件当前位置速览（2026-10-18 实探）：路线图两份在 `D:\openclaw` 根目录；系列文章与两份实践清单在 `D:\openclaw\Android framework\Android窗口层级\`（用户会自己搬目录，报到用户面前时给实探到的绝对路径）。

## 三、岗位分布要点（2026-10-18 抓取的样本结论，重抓时以当日为准）

需求量从大到小：

1. **车载 / 智能座舱 Android FW + HAL** —— 当前最大增量池。样本原文：光庭信息「负责智能座舱 Android 系统 Framework 层、HAL 层核心模块的定制开发…依托 Binder、HIDL/AIDL 通信机制，打通系统层、硬件驱动层交互链路」；智联上海样本里「车载项目 + Framework」反复出现。
2. **系统稳定性 / 性能优化** —— 每家大厂常备。样本原文：联想性能优化岗「深入理解 Android 系统架构，熟悉 AMS、WMS、Binder」；联想 Framework Engineer 职责第 2 条即「ANR、Crash、内存泄漏、卡顿、冻屏 等疑难问题」。
3. **Framework 多媒体** —— 联想「Framework 多媒体工程师」：「深入理解 AudioFlinger / AudioPolicyManager 等核心流程」。
4. **短距通信 FW**（WiFi/BT/GPS/NFC）—— 联想独立成岗。
5. **手机厂商框架定制**（SystemUI / 多窗口 / 折叠屏 / 动效）。
6. **系统应用 / ROM 定制**（Settings、Launcher、OTA、权限中心）。

一句话结论（可直接引用）：想快进圈 → 车载 FW/HAL；想走深 → 稳定性 + 性能优化；想炫技 → 图形/多媒体。三者共用 `Binder + AMS + WMS + SystemServer` 地基。

### 样本纪律

- 抓取命令：`web_search`，query 如「Android Framework 系统开发 岗位需求 招聘方向」「Android 系统开发 学习路线 framework 层」。
- 产出里**必须写明**「样本观察，不是全量统计，具体数量别当精确数字」，并标注抓取日期与来源（联想/光庭/智联/Indeed 等）。
- JD 引文只摘与技能栈相关的要点，不整段搬运。

## 四、B 赛道加减法（用户选 B 时的时间分配依据）

**砍掉 / 降级**：App 业务栈（Jetpack 全家桶、MVVM、跨端 Flutter/RN、Gradle 工程化）→ 只留「能读懂 App 怎么写」的上游视角；App 侧性能优化（列表复用、图片库、App 启动优化）→ 知道概念即可；三方库源码（OkHttp/Glide）→ 无投入价值；内核/驱动开发 → 除非日后转 C。

**补上 / 升级**：AOSP 编译→裁剪→定制→刷机（从「会」变「日常」）；Binder 深水区（驱动、线程池、oneway、死亡通知、ServiceManager）；SystemServer 启动顺序与服务注册；AMS/WMS/PMS 源码级；SystemUI；系统应用 + 系统签名（platform 签名 / sharedUserId / 特权权限）；SELinux 与权限模型；系统裁剪与定制（config 默认值、RRO overlay）；OTA/升级/多用户；Watchdog 与稳定性机制；稳定性与性能工具链（Perfetto/ANR/native crash/内存）；（车机向）HAL(HIDL/AIDL)、CarService、VehicleHAL。

## 五、用户进度耦合（别忘的映射）

- 用户已把 **WMS 走到 09 篇**（00–09 均已正式落盘，含 07 Activity 启动链与生命周期、08 布局/Insets/旋转、09 动画与 leash），且有框架级 **Binder 独立专题** `D:\openclaw\Android framework\android-framework-binder.html`；故路线图「六 你的起点」写成：① 补 Binder（WMS 全链路底层，当前知识断口——虽已有专题篇，但知识点本身仍需掌握）→ ② 接 AMS（顺着 `ActivityRecord extends WindowToken`，已升到 07 篇）→ ③ 补 PMS → ④ 图形/输入回炉（补 RenderThread 与 Perfetto）→ ⑤ 稳定性与性能 → ⑥ 按目标岗选专项。**开工前先实探系列目录实际篇目**（只信正式目录，不信 `_draft\`：落盘后旧稿仍留在那里）。
- 阶段-篇号联动（2026-10-19 落盘后）：路线图「阶段 2 生命周期 = 06–07 篇」（均已落盘）、阶段 3 → 08（已落盘）、4 → 09（已落盘）、5 → 10、6 → 11。改篇号时 `.md` 与 `android-window-roadmap.html` **两版同步**。
- 每阶段「验收标准」写成可检查项（例：阶段 2 = 自写 AIDL 服务跨进程调用成功、能说清 Binder 拷贝次数；阶段 5 = 能独立从 bugreport 定位一个 ANR 根因）。

## 六、HTML 版式要求（与系列文章一致）

- 内联 CSS + `:root` / `[data-theme="dark"]` 双主题变量；右下角浮动主题钮三态（auto/light/dark，按键名存 localStorage，**换一个键名**避免与系列文章互相干扰）。
- 组件：`.toc` 目录（锚点 == `<h2 id>` 集合）、`.card`（可加左色边变体）、`table`、`.annotation`（含 `.star3` 强调版）、`.point`/`.hint`、`.step`（圆形序号）、`.pitfall`、`.think`、`.analogy`、`.deliver`、`.code-block`（带文件名条）、`.tree`（ASCII 图）。
- 容器 `max-width:1020px`，移动端 media query；不依赖任何外部 JS/CSS（可直接双击打开）。
- 分段落盘：先 write 出 head + 骨架（含 `<!--MORE-->` 占位），再 edit 逐章替换占位符与收尾；最后补 `</div>` 收容器。
- 校验：`html.parser` 栈式标签闭合 + TOC 与 `id` 差集为空 + 内部 `href` 可达性 0 缺失 + Edge headless 对 ASCII 副本截图抽检。
