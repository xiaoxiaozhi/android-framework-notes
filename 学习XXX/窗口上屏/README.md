# 窗口上屏 · 学习材料（round 01 + round 02 草稿，AOSP 13）

> 主题：一次 vsync 之后，一个窗口怎样从“要更新”变成屏幕上的像素。
> 基线：`/home/book/aosp13`（`android-13.0.0_r84`）。本轮锁 13，不使用 12 的行号。

## 这条链的一句话

vsync 只负责放行 app 的 traversal；`performTraversals` 判断要不要 relayout；要，就同步 binder 进 WMS，WMS 在 `relayoutWindow` 内强制 `performSurfacePlacement(true)`，算好 frame/insets 并准备 Surface 再返回；app 拿到后 measure / layout / draw；画完 `finishDrawing` 回报 WMS，WMS 再 `requestTraversal` 排一次 placement，把 transaction 交给 SurfaceFlinger，在下一个 vsync 合成。

## 文件

- `round-01.md` —— 三块 + 骨架解说 + 阅读法（`check_round.py` PASS，`check_anchors.py` 0 error / 0 warning）
- `walkthrough-01.md` —— 3 个节点精读：守卫、强制 placement、交卷
- `evidence-01.md` —— 本轮真实命令与输出
- `round-02.md` —— `WMS.relayoutWindow` 深挖草稿：16 行骨架 + 决策点 + 3 问（未出 HTML）
- `walkthrough-02.md` —— `relayoutWindow` 3 节点精读：入口/顺序/回填
- `lab-01.md` —— 白屏 / frame 黑边 / 掉帧 / 动画旋转 四个练手场景（命令 + 判据）
- 文章：`D:\openclaw\Android framework\学习XXX\窗口上屏学习轮次-AOSP13.html`

## 三个最容易错的点

1. **vsync 不是 WMS 的开机键**：WMS 不订阅 vsync；app 的 `Choreographer` 收到 vsync 后才执行排队的 traversal。
2. **relayout 不是每帧都走**：守卫在 `ViewRootImpl.java:3069`；纯 invalidate 帧只 measure/layout/draw。
3. **relayout 不是只登记**：WMS 在 `WindowManagerService.java:2495` 强制跑一次 `performSurfacePlacement(true)`，否则回给 app 的 `outFrames` 不是新值。

## Round 02 草稿（未出 HTML）

主题：`WMS.relayoutWindow` 一次到底做了什么。先落 `round-02.md` 和 `walkthrough-02.md`，确认结构值得再构建 HTML。

三个先记住的锚点：

- `shouldRelayout`：`WindowManagerService.java:2442`，只看可见性 + Activity client 可见。
- 顺序：`createSurfaceControl`（`:2479/:2481`）必须在 `performSurfacePlacement(true)`（`:2495`）之前，否则 `isGoneForLayout()` 会让布局跳过。
- 回填：`fillClientWindowFramesAndConfiguration`（`:2590`）、`outInsetsState.set`（`:2598`）、`mInRelayout=false`（`:2607`）、`return result`（`:2633`）。

`round-02.md` 已过 `check_round.py`；`check_anchors.py` 51 锚点 0 error / 0 warning。

## 下一步

答 `round-01.md` 的 3 个问题；挑对不上的那条，用 `dumpsys gfxinfo` / perfetto 看一次真实帧；结论回填 `D:\workspace\FramworkContent\LAB.md`。
