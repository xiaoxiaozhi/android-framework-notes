# Activity 加窗（DecorView → WMS.addWindow）· 学习索引（AOSP 13）

| 文件 | 内容 |
|---|---|
| `..\Activity加窗学习轮次-AOSP13.html` | 单文件文章（深/浅色主题自动切换，阅读版） |
| `round-01.md` | 第一轮：骨架 18 行 / **骨架解说（白话）** / 决策点 5 条 / 3 个反问（`check_round.py` PASS） |
| `walkthrough-01.md` | 3 节点精读（加窗三件套 / token 与三张表 / WMS 判定顺序）+ 白话对照 + 名词表 + 3 个误读点 |
| `evidence-01.md` | 实测证据：命令与输出、锚点清单、可选设备验证 |
| `D:\workspace\FramworkContent\LAB.md` | 学习卡四列，见「学习卡：Activity 加窗」 |

## 一句话主线

`handleResumeActivity` 里 `wm.addView(decor, l)` → `WindowManagerImpl.applyTokens` 补 token → `WindowManagerGlobal.addView` 建 `ViewRootImpl` 并 `setView` → `mWindowSession.addToDisplayAsUser` **同步** binder → `Session` 透传 → `WMS.addWindow` 做权限/token/重复检查，`new WindowState` 后 `mWindowMap.put` 落库 → 之后 `performTraversals → relayout` 才拿 Surface。

## 关键锚点（AOSP 13，全部现地 grep）

- 加窗入口：`ActivityThread.java:4835`（条件）、`:4838`（INVISIBLE）、`:4842`（TYPE_BASE_APPLICATION）、`:4859`（addView）
- token：`WindowManagerImpl.java:146`（addView）、`:165-168`（applyTokens 补 `token` / `mWindowContextToken`）
- 三张表 + ViewRoot：`WindowManagerGlobal.java:309`（addView）、`:391-401`、`:405`（setView）
- 同步加窗：`ViewRootImpl.java:1160`（setView）、`:1249`（mAdded）、`:1255`（requestLayout）、`:1281`（addToDisplayAsUser）
- 透传：`Session.java:209/:214`
- 落库：`WindowManagerService.java:1477`（addWindow）、`:1486`（checkAddPermission，实体在 `PhoneWindowManager.java:2595`）、`:1518`（重复）、`:1570`（getWindowToken）、`:1683`（new WindowState）、`:1789-1790`（attach + mWindowMap.put）、`:1802-1803`（token.addWindow / displayPolicy.addWindowLw）
- 异步后续：`ViewRootImpl.java:2806`（performTraversals）、`:8275`（relayout）

## 状态

- 步骤 1–3 完成：模式 A（一页骨架 + 3 问 + 判据题），骨架已过形状校验，L0 题已出。
- 步骤 4 回填未做：3 个反问还没有答案。
- 与 PiP/自由窗口不同：这条链 **12→13 没有增删方法**，只有行号漂移（见文章末节）。
