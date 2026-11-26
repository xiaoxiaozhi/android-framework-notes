# 自由窗口 · 学习索引（AOSP 13）

| 文件 | 内容 |
|---|---|
| `..\自由窗口学习轮次-AOSP13.html` | 单文件文章（深/浅色主题，等同本目录内容的阅读版） |
| `round-01.md` | 第一轮三块：骨架两段（A 状态线 + B 启动线）/ 决策点 5 条 / 3 个反问（`check_round.py` PASS） |
| `walkthrough-01.md` | 3 节点精读包（放行 / 算 bounds / 钳制）+ 骨架白话对照 + 名词表 + 3 个误读点 |
| `evidence-01.md` | 实测证据：设备能力来源、全屏 vs freeform 的完整命令与输出、锚点清单 |
| `D:\workspace\FramworkContent\LAB.md` | 学习卡四列（现象 / 判据命令 / 锚点 / 结论），见「学习卡：自由窗口」 |

## 一句话主线

`--windowingMode 5` → 设备能力（feature 或 `enable_freeform_support`）→ `canApplyFreeformWindowPolicy` 放行 → `isValidWindowingMode` 校验 → `getTaskBounds` 给初始 Rect → `Task.computeFreeformBounds` 钳制 → dump `mode=freeform` → WMShell `FreeformTaskListener` 装标题栏。

## 关键锚点

- 能力：`ActivityTaskManagerService.java:879`（赋值 `:935`）；运行时同步：`WindowManagerService.java:864` → `:966/:973`
- 桌面默认：`DisplayWindowSettings.java:134`
- 放行：`TaskLaunchParamsModifier.java:565`；校验：`TaskDisplayArea.java:1379`
- 初始 bounds：`TaskLaunchParamsModifier.java:728`；钳制：`Task.java:2128`
- dump：`Task.java:3798`；Shell 分发：`ShellTaskOrganizer.java:465/809`、`FreeformTaskListener.java:77`

## 状态

- 前 3 步（定模式 / 三块 / 出题）完成。
- 第 4 步回填未做：3 个反问还没有答案。
- 设备 `enable_freeform_support=1`（原 null），还原：`adb shell settings delete global enable_freeform_support`。
