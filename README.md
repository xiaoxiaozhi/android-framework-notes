# Android Framework 学习笔记

AOSP 13 基线（部分篇目对照 12）的 Framework 深水区笔记：**窗口层级 / WMS、Binder、AMS·ATMS、SystemUI、渲染管线**。

所有结论都落到 **「类名 + 文件 + 行号」**，可直接在源码里 grep 验证；配 `dumpsys` / winscope / 真机实验的观测方法。

> 本地看书建议起一个静态服务：`python _serve.py 8090`，然后打开 <http://localhost:8090>。直接双击 HTML 也能看，但页面内的相对链接和 fetch 在 `file://` 下可能受限。

---

## 从哪里开始

| 入口 | 内容 |
|---|---|
| `index.html` | 门户页，所有专题的卡片导航 |
| `Android-Framework学习路线图.html` / `.md` | 上位路线图：学什么、按什么顺序学 |
| `Android窗口层级/WMS学习路线图.html` | WMS 专项路线图 |
| `SystemUI/systemui-roadmap.html` | SystemUI 专项路线图 |

## 窗口层级专题（`Android窗口层级/`，00–14）

一棵树把窗口从「谁在上」讲到「像素怎么上屏」：

- `00-窗口为什么是一棵树` — layer 号与树结构
- `01-窗口树全景` — DisplayArea / TaskDisplayArea / WindowToken / WindowState 的层级全貌
- `02-窗口树的构建算法` — `DisplayAreaPolicy` 与 Feature 实例化
- `03-窗口刷新与事务提交` — relayout 到 SurfaceControl 事务
- `04-像素怎样上屏` — SurfaceFlinger 合成链路
- `05-输入分发与窗口命中` — InputDispatcher 的命中判定
- `06-窗口的诞生` — `addView` → `addToDisplayAsUser` → `mWindowMap`
- `07-窗口的来路与归途` — 增删窗口的完整生命周期
- `08-窗口的尺寸与身体` — frame / bounds / insets 归属与重算
- `09-窗口动画与过渡` — 动画与转场
- `10-显示子系统的节拍` — VSYNC 与显示时序
- `13-画中画` — PiP 的加窗路径
- `14-图层是什么` — Layer / LayerMetadata

配套：

- `WMS实践项目清单.html` — P0–P5 动手项目（修别人的 bug）
- `WMS原创实践项目.html` — L1–L6 自造项目（把机制自己实现一遍再验证）
- `DisplayArea构建算法演示.html` — 树构建过程的可视化

## 独立专题

- `android-framework-binder.html` — Binder：驱动、协议、线程池
- `android-framework-atms.html` / `android-framework-ams.html` — ATMS 与 AMS
- `android-framework-render-pipeline.html` — 从 View 树到屏幕
- `wallpaper-setbitmap-framework.html` — 壁纸 setBitmap 链路（黑闪问题分析）
- `SystemUI/` — SystemUI 路线图 + 壁纸黑闪分析器

## 动手实验（`学习XXX/`）

以「一轮一个机制」的方式做的带学记录，每轮含 `README` / `round` / `walkthrough` / `evidence` 四件套 + 一篇成稿 HTML：

- `Activity启动流程.html`
- `Activity加窗学习轮次-AOSP13.html`（`学习XXX/Activity加窗/`）
- `窗口上屏学习轮次-AOSP13.html`（`学习XXX/窗口上屏/`，含 `lab-resize` 实测截图）
- `自由窗口学习轮次-AOSP13.html`（`学习XXX/自由窗口/`）
- `PiP学习轮次-AOSP13.html`

## 工具

- `_serve.py` — 本地静态服务（Python 标准库，启动时同步上位路线图副本，禁用缓存）
- `winscope/` — 预编译的 winscope 前端，直接开 `winscope/index.html` 读 trace
- `winscope13/pull-trace.ps1` / `start-winscope.ps1` — 设备抓 trace + 起服务
- `emu-view/` — 模拟器视图小工具

## 约定

- 行号默认按 **AOSP 13**；少数篇目标注 12，两套行号不可混用。
- 每篇都尽量给「一条可执行的验证命令」，而不是只给结论。
- `_build*`、`.bak`、日志不入库（见 `.gitignore`），由脚本重新生成。
