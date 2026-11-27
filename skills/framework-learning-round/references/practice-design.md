# 出题规则

## 四件套（缺一项就不出）

```
触发：一行可重复、无副作用的命令，或一次明确点击
判据：一条 dumpsys / logcat / 文件输出里的可判定字符串（grep 得到 = 过，得不到 = 不过）
锚点：一个能解释判据或能打断点的 文件:行号
产出：一句能写进笔记的结论（不是「理解了」）
```

## 分级（按反馈成本，不按难度）

| 级 | 改什么 | 单题耗时 | 例 |
|---|---|---|---|
| **L0** | 不编译：`dumpsys` / `logcat` / `am` / `settings` | ≤25 min | 两次快照对比、开关动画看现象、dumps 里定位字段 |
| **L1** | 只编 services：`m services` + push + reboot | 数小时 | 加 shell 子命令、改一个决策分支 |
| **L2** | 改 framework：只编模块（`m framework-minus-apex`） | 半天起 | 改复用策略、加计时打点 |

第一轮默认 L0。**禁止整树编译**（3 小时起的反馈会拖垮这一轮）。

## 选题优先级

1. 用户手上的真实现场（有现象、有设备）
2. 已有题库里没做过的题（见下）
3. 现编（仅当 1、2 都没有）

不要为了出题虚构现象；题目必须能在用户机器上跑出来。

## 已有题库（别重复造）

**ATMS 六题**

| 编号 | 题目 | 级 | 判据 |
|---|---|---|---|
| A1 | 还原一次启动的 Task 决策（换 flags 起三次） | L0 | `dumpsys activity activities` 里 taskId 是否新增 |
| A2 | 单实例 vs 多实例（`documentLaunchMode=always`） | L0 | `dumpsys activity activities \| grep -c "Task{"` = 3 |
| A5 | 删除三条路径对比（finish / force-stop / 回收） | L0 | 记录消失时机 + `onDestroy` 是否执行 |
| A4 | 让一次启动失败 | L1 | `am start -W` 输出错误且无新 Task |
| A3 | 加 `cmd activity task-move <taskId> <displayId>` | L1 | `dumpsys` 里 displayId 变化 |
| A6 | ATMS 侧启动耗时打点 | L1 | 打点差值 vs `am start -W` 的 TotalTime |

**AMS 三题**：M1 观测进程诞生五跳（L0）；M2 adj 三次快照（L0）；M3 有序 vs 无序广播延迟（L0）。

**故障注入六题**（`D:\workspace\FramworkContent\LAB.md`）：L1 焦点消失 / L2 触摸被吞 / L3 壁纸不出现 / L4 PiP 静默失败 / L5 无焦点 ANR / L6 旋转重建 —— 全部 L0。

## 出题禁忌

- 判据是「看看有没有」「观察一下」→ 重写。
- 一题要改三处才能验证 → 拆成三题。
- 需要用户装新工具或新设备 → 换题。
- 判据依赖不可复现的时序（如「快速点两下」）→ 换成命令可复现的。
