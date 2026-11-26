# 窗口上屏 · 证据（2026-11-22）

> 基线 `/home/book/aosp13`。以下命令与输出均为本轮真实执行，未做改写。

## 1. L0 触发命令

```bash
cd /home/book/aosp13/frameworks/base && \
grep -n "mFirst || windowShouldResize" core/java/android/view/ViewRootImpl.java && \
grep -n "performSurfacePlacement(true /\* force \*/)" services/core/java/com/android/server/wm/WindowManagerService.java && \
grep -n "reportDrawFinished" core/java/android/view/ViewRootImpl.java
```

输出：

```text
3069:        if (mFirst || windowShouldResize || viewVisibilityChanged || params != null
2495:            mWindowPlacerLocked.performSurfacePlacement(true /* force */);
3726:                reportDrawFinished(seqId);
4379:    private void reportDrawFinished(int seqId) {
4381:            Log.d(mTag, "reportDrawFinished " + Debug.getCallers(5));
```

## 2. 守卫与强制布局的源码片段

```bash
sed -n '3069,3071p' frameworks/base/core/java/android/view/ViewRootImpl.java
```

```text
if (mFirst || windowShouldResize || viewVisibilityChanged || params != null
                || mForceNextWindowRelayout) {
            if (Trace.isTagEnabled(Trace.TRACE_TAG_VIEW)) {
```

```bash
sed -n '2493,2496p' frameworks/base/services/core/java/com/android/server/wm/WindowManagerService.java
```

```text
            // We may be deferring layout passes at the moment, but since the client is interested
            // in the new out values right now we need to force a layout.
            mWindowPlacerLocked.performSurfacePlacement(true /* force */);
```

## 3. `finishDrawing` 的 seqId

```bash
sed -n '4379,4386p' frameworks/base/core/java/android/view/ViewRootImpl.java
```

```text
    private void reportDrawFinished(int seqId) {
        if (DEBUG_BLAST) {
            Log.d(mTag, "reportDrawFinished " + Debug.getCallers(5));
        }

        try {
            mWindowSession.finishDrawing(mWindow, mSurfaceChangedTransaction, seqId);
        } catch (RemoteException e) {
```

## 4. 形状与锚点校验

```bash
python D:\openclaw\skills\framework-learning-round\scripts\check_round.py \
  "D:\openclaw\Android framework\学习XXX\窗口上屏\round-01.md"
```

```text
PASS：三块齐全 + 解说 6 行 + 阅读法 5 行；骨架 16 行（含分支）、决策点 5 条、问题 3 条
```

```bash
python D:\openclaw\skills\framework-learning-round\scripts\check_anchors.py \
  "D:\openclaw\Android framework\学习XXX\窗口上屏\round-01.md" --root /home/book/aosp13
```

```text
锚点 38 个，文件 4 个，基线 /home/book/aosp13
PASS: 无 error（0 warning）
```

## 5. 文章验证

```bash
python D:\openclaw\skills\framework-learning-round\scripts\verify_html.py \
  "D:\openclaw\Android framework\学习XXX\窗口上屏学习轮次-AOSP13.html" \
  --sections 7 --shot "D:\openclaw\Android framework\学习XXX\窗口上屏\verify.png"
```

```text
SHOT: D:\openclaw\Android framework\学习XXX\窗口上屏\verify.png 313408 bytes
PASS: ready / theme cycle / sections=7 / no residue
```
