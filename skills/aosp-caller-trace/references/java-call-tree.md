# Java 生命周期链与调用树审阅

当需要画 Java 侧 ATMS → binder → ActivityThread 生命周期调用树、下断点，或审阅/合并别人给的调用树时读它。

## Java 侧生命周期链（ATMS → binder → ActivityThread）

1. 用户要「打印调用树 / 做笔记」时，只输出一个可直接复制的等宽块：每行 = `方法()` + `→ 产出形态` 或 `← 改了什么状态` + 右侧对齐 `文件:行号`；没有分支的纯链路也要写形态变化，只列方法名等于交了一张目录。分支用 `├─`/`└─` 缩进写出条件与去向（例：`├─ 进程不存在 → fork`），每个二选一都占独立分支行，不压进上一行尾巴——压成一行后读者看不出这是岔路；18 行只是默认值，不是上限：并列门禁（权限/防火墙/后台限制/abort）与二选一各占一行，需要时展开到 20–24 行，压缩只折细节行（建 ActivityRecord、挂栈），但追踪某个对象或参数时，每一次把它继续往下传的转发调用都单独占一行并带锚点，不折进细节——折掉 `executeRequest`→`startActivityUnchecked` 这类转发后，读者会把参数当成在下游才第一次出现，审计表也跟着错位；一行只放一个 `文件:行号`，同一行并两个锚点时 `audit_anchors.py` 会用行内最后一个 `Class#method` 去核前一个锚点、报「方法未出现在该行±6」，拆行即可避开，长行在 `.tree` 里只能横向滚动，拆行优先于加长；「进程在不在」这类判断常分散在多处（TaskFragment 预热/attached、Supervisor hasThread），在各处分别画，合成一处会把「有进程」那条线标成「无进程」。开机只跑一次的初始化（`retrieveSettings`、`systemReady` 写 flag）不要接进每次启动的链：先画 A 状态线（开机一次，或改设置时由 SettingsObserver 写回同一字段），再画 B 每次调用线（只读内存 flag），两段各自带箭头并注明各在什么时机跑；合成一条会把「开机时算好的状态」标成「本次启动重算」。锚点给准确行号并标明它是定义行、赋值行还是调用行（如 `ATMS.retrieveSettings()` 定义 `:879`、写 flag `:935`、唯一调用方 `AMS.systemReady()`），只给一个行号读者分不清判定点。核对别人画的调用树时逐条边找 caller 行再打标：调用点已核 ✅、只读写字段 ✔（写「状态读写」，不写成调用）、原图错误 ❌ 并补真实 caller、未核 ❓ 待补方法体；父子或并列摆放不构成调用，没有 caller 行就不能画成箭头。跨进程处插一行 `════ binder 跨进程 ════`，终点回调标 `★`；不混表格与解释段落。
2. 冷启动与热恢复分开画两张树：冷启动含 `LaunchActivityItem` → `handleLaunchActivity` → `performLaunchActivity` → `performCreate`/`performStart`；热恢复只走 `ResumeActivityItem` → `handleResumeActivity` → `performResume`，并注明 `onCreate`/`onStart` 不执行。
3. 树尾固定附三个断点：`ActivityTaskSupervisor.startSpecificActivity`（判冷/热）、`ActivityThread.handleLaunchActivity`（验目标任务）、`Activity.performResume`（看 reason）。
   用户说断点「离调用方法太近」时不要在同一栈上重跑，换发起侧下断：binder 线程栈（`ActivityClientController:onTransact` 一类）只截到尾巴，其中 `schedulePauseActivity(..., "auto-pip")` 是 PiP 流程收尾时补发的 pause，真正发起的那次在同一时刻的 system_server main 线程上，该栈里看不到；改为在入口 `TaskFragment.startPausing`（读 `reason`）与出口 `ClientLifecycleManager` 各下一个，`reason` 取值（`resumeTopActivity`/`pauseBackTasks`/`sleep`/`auto-pip`）直接区分走的哪条路。抓到 `auto-pip` 说明是 PiP 自动进入触发，先让 demo 去掉 `setAutoEnterEnabled(true)` 或不调 `enterPictureInPictureMode()`，再抓正常链路。栈里 `N hidden frame` 可先在调试器设置里取消隐藏库帧，或用 Drop Frame 往外跳，比重跑省一轮。
4. 逐边核对父方法体，锚点脚本通过不等于边成立：`audit_anchors.py` 只验「文件+行号+附近有该方法名」，跳过中间层或挂错父节点的树照样能全过。每条边用 `sed -n '<父方法定义行>,<下一个同级方法前一行>p'` 读出父方法体，`grep` 子调用名必须命中；取外层方法用 `awk 'NR<=<调用行> && /^    [a-zA-Z].*\(/ {n=NR;s=$0} END{print n": "s}' <文件>`，或 `awk 'NR>=A && NR<=B'` 读清候选父方法的起止，再决定层级。中间层不能跳：`RootWindowContainer.resumeFocusedTasksTopActivities` 经 `Task.resumeTopActivityUncheckedLocked` → `resumeTopActivityInnerLocked` 才到 `TaskFragment.resumeTopActivity`，少一层就藏掉「挑哪个 Task」；跨进程后按事务项并列（`LaunchActivityItem` → `handleLaunchActivity` → `performLaunchActivity`；`ResumeActivityItem` → `handleResumeActivity` → `performResumeActivity` → `setView`），串成父子边会指错方法。同名重载按调用处实参个数选行（`resumeFocusedTasksTopActivities` 3 参在 :2248、4 参在 :2254），抄错重载与挂错父节点同属一行错锚。行号与基线树绑定，改看 12/13/14 树必须重新 grep。
5. 只复用方法名与调用顺序，行号一律在当前基线树（默认 13）重新 grep：同一方法在 12/13 间整体位移，`Task.resumeTopActivityInnerLocked`、`ActivityTaskSupervisor.startSpecificActivity`、`ActivityThread.handleLaunchActivity` 三处都要重核；把旧基线的行号抄进回答等于给出错误锚点。历史答复或记忆里同一链用过旧基线时，回答开头写明当前基线，并在树后附「方法 | 旧行号 | 新行号」差异表、注明旧数字作废，避免用户继续引用旧锚点。

6. 同一功能有多个触发入口时先画入口分叉，再让每条线各自走到汇合点，不要挑一个入口当作全部：入口不同，经过的判定层就不同（`adb am start --windowingMode` 走 `ActivityStarter.execute` → `LaunchParamsController` → `TaskLaunchParamsModifier`；最近任务/快捷方式走 `startActivityFromRecents` → `anyTaskForId` + `reparent` → `setBounds`，完全不经过 `TaskLaunchParamsModifier`，窗口尺寸也由客户端算好传入），合成一条会把缺掉的那几层标成不存在。用户说骨架看不懂、起点选错了时，先确认这份骨架假设的是哪个入口，再按「入口分叉 → 各自链路 → 汇合（root task/Task/caption）」重排。标「汇合点」前对每个入口各走一遍，只被部分入口经过的方法是某条链的中转站而非汇合点：`am start -W` 从 `ATMS.startActivityAndWait` 直接调 `execute`，根本不进 `startActivityAsUser`；最近任务快路径连 `ActivityStarter.execute` 都不经过（`ActivityTaskSupervisor` 注明它不走 `executeRequest`），两者唯一的共同锚是 `TDA.getOrCreateRootTask`，在那里再标 mode/bounds 来源差异（谁传了 launchParams 决定从哪读）。

7. 断点下在 `obtain()` 这类小工厂方法上不中时，先查 ART 内联，不要先怀疑进程连错：`oatdump --oat-file=<odex> --instruction-set=x86_64 --class-filter=<类全名> --method-filter=<方法名>` 看 `compiler-filter`，`speed` 全量优化下短方法常在调用点被内联，原行没有可停代码。改在调用方大方法入口（如 `TaskFragment.startPausing`）下断点，停在构造调用行按 F7：跳进工厂方法说明未内联，可回填原断点；直接落到下一行说明已内联，改在构造后的字段赋值处看结果。

## 审阅别人给的调用树（对比 / 合并）

1. 逐行核锚点，不抽样：对每个 `文件:行号` 跑 `sed -n '<行号>p' <文件>` 看方法名是否对得上；错锚最常见的形态是抄了旧基线（`startActivity` 12:5700 → 13:5929），一行错锚就点在对比结论里。
2. 判分支行的层级：同一父节点下出现多个 `└─` 是把「顺序」写成了「并列选择」；正常链条是 判断 → 两分支 → 汇合 → 下一步，合并时用 `├─`/`└─` 加一行汇合重画。
3. 核「决策行」用的是不是做决策的方法：用 `grep -n "<方法>(" <文件>` 区分定义行与调用行，并分清决策方法与其后的关联动作（`computeTargetTask()` 决定新建，`setNewTask()` 只是把新 Task 关联给记录），用后者顶替前者等于把关键分支藏了。
4. 看树尾形态：必须落到可观察结果（首帧、`ClientTransaction`、回调）；停在服务端内部方法说明「完成」没定义，据此答不了白屏/没界面类问题。
5. 查两条排障锚点是否在树里：对外返回值被改写的拒绝分支（`START_ABORTED → START_SUCCESS`）与计时起点（`notifyActivityLaunching`）；缺这两条，树只能讲流程不能定位。
6. 结论分「净胜分 / 硬伤」两列，各带核对到的行号原文，不写「整体更好」；再给合并版，用 `python D:\openclaw\skills\framework-learning-loop\scripts\check_round.py <file>` 过门禁（骨架 ≤18 行、每行带箭头、至少一处分支）后交付。
