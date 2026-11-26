# 窗口上屏 · 练手卡 01（AOSP 13 / emulator-5554）

> 目标：不追完整调用链，只练「症状 → 先看哪个黑盒 → 用哪个字段/命令判定」。
> 设备：`emulator-5554`，AOSP 13（API 33）。命令在 Windows PowerShell 下执行。
> 示例包名：`com.example.framworkcontent`（当前 demo）；也可换成 `com.android.settings`。
> 注意：改旋转/动画后，最后按「收尾」恢复，别把模拟器留在横屏。

## 练手 1｜白屏：看 `mHasSurface` / `mDrawState`

### 操作

```powershell
$pkg = "com.example.framworkcontent"
$act = "com.example.framworkcontent.WindowDemoActivity"

adb shell am force-stop $pkg
adb shell am start -n "$pkg/$act"

1..30 | ForEach-Object {
  adb shell "dumpsys window windows | grep -A 30 'Window{.*$pkg' | grep -E 'mHasSurface|mDrawState|Frames:'"
  Start-Sleep -Milliseconds 100
}
```

### 先看什么

- `mHasSurface=false` + `mDrawState=NO_SURFACE`：WMS 侧没有可用 SurfaceControl（app 也就没有有效的 window Surface）。
- `mHasSurface=true` + `mDrawState=DRAW_PENDING`：WMS 已建 layer，app 还没画完。
- `mDrawState=COMMIT_DRAW_PENDING / READY_TO_SHOW`：app 已画完/已提交，WMS 还没真正上屏。
- `mDrawState=HAS_DRAWN`：WMS 认为已经显示过。
- `Frames: ... frame=[l,t][r,b]`：WMS 当前 frame；A13 的 dump 不是 `mFrame=`，是 `Frames:` 行。

### 判定模板

- `mHasSurface=false` 且窗口已可见 → 先查 `relayoutWindow` / `shouldRelayout` / SurfaceControl 创建。
- `mHasSurface=true` 但 `mDrawState` 长期 `DRAW_PENDING` → 先查 app 的 `dumpsys gfxinfo $pkg`，不要读 `DisplayPolicy`。
- `mDrawState=HAS_DRAWN` 但内容白 → 不是“没建 Surface”，更像 app 画了空白/错误 buffer，转去看 app 内容。

## 练手 2｜frame 不对/黑边：看 `outFrames` 与 `SurfaceControl`

### 操作

```powershell
$pkg = "com.android.settings"
# 用 Settings 做旋转，避免 demo Activity 固定竖屏导致 frame 不变

adb shell am start -n com.android.settings/.Settings
adb shell wm user-rotation lock 0
Start-Sleep -Seconds 1

# 竖屏 frame
adb shell "dumpsys window windows | grep -A 30 'Window{.*$pkg' | grep -E 'Frames:|mHasSurface|mDrawState'"

adb shell wm user-rotation lock 1
Start-Sleep -Seconds 2

# 横屏 frame
adb shell "dumpsys window windows | grep -A 30 'Window{.*$pkg' | grep -E 'Frames:|mHasSurface|mDrawState'"

# Surface 层是否还在、名字是否变化
adb shell "dumpsys SurfaceFlinger --list | grep -i -E 'Settings|Leash'"
```

### 先看什么

- `Frames: ... frame=[0,0][2960,1440]`：WMS 已经按横屏算 frame。
- `mHasSurface=true` / `mDrawState=HAS_DRAWN`：Surface 还在。
- `dumpsys SurfaceFlinger --list` 里能看到 app 层；动画期间可能多出 `Leash#...`。

### 判定模板

- frame 已经是新尺寸，但画面比例旧/黑边 → `outFrames` 更新了，buffer/SurfaceControl 没跟上；查 `RELAYOUT_RES_SURFACE_CHANGED`、`mSurface.copyFrom`、app 是否重画。
- frame 还是旧尺寸 → WMS 布局没跑或没算到；查 `performSurfacePlacement` / `waitingForConfig`，不要先读 `performDraw`。
- 只在动画/旋转瞬间有黑边 → 先看 leash 和动画，不要把它当成静态布局错误。

## 练手 3｜掉帧：看 trace 切片，不逐行读 `forAllWindows`

### 操作

```powershell
# 开始抓 trace
adb shell atrace --async_start -b 32768 gfx view wm sched freq
Start-Sleep -Milliseconds 500

# 制造滚动（Settings 或当前列表页都行）
adb shell input swipe 700 2000 700 500 300
adb shell input swipe 700 500 700 2000 300
adb shell input swipe 700 2000 700 500 300

# 停止并取回（adb exec-out 保留二进制）
adb exec-out atrace --async_stop > "D:\openclaw\Android framework\学习XXX\窗口上屏\scroll.trace"
```

用 Perfetto UI（`https://ui.perfetto.dev`）打开 `scroll.trace`，搜索这些 slice：

- `relayoutWindow`
- `performTraversals`
- `draw`
- `performSurfacePlacement`
- `Choreographer#doFrame`

### 先看什么

- 纯滚动帧：应该有 `Choreographer#doFrame` / `performTraversals` / `draw`，但 `relayoutWindow` 很少或没有。
- 如果每帧都有 `relayoutWindow`：先查 `mForceNextWindowRelayout`、`params`、`windowShouldResize`，不要先读 `forAllWindows`。
- `performSurfacePlacement` 是 WMS 的全局 pass；它出现不等于 app 每帧都 relayout。

### 判定模板

- 滚动掉帧但 `relayoutWindow` 很少 → 正常；瓶颈更可能在 draw/RenderThread/SF。
- `relayoutWindow` 每帧都有 → 有东西在改几何/参数；先看守卫五条件。
- `performSurfacePlacement` 很长 → 看 WMS 侧窗口数量/布局重复，而不是逐行读 `forAllWindows`。

## 练手 4｜动画/旋转：才展开 `SurfaceAnimator` / leash

### 操作

```powershell
adb shell settings put global window_animation_scale 1
adb shell settings put global transition_animation_scale 1
adb shell settings put global animator_duration_scale 1

adb shell wm user-rotation lock 0
Start-Sleep -Milliseconds 300
adb shell wm user-rotation lock 1

1..15 | ForEach-Object {
  adb shell "dumpsys SurfaceFlinger --list | grep -i -E 'Leash|Settings'"
  Start-Sleep -Milliseconds 100
}
```

### 先看什么

- 动画期间 SurfaceFlinger 里可能出现 `Leash#...`，它是 `SurfaceAnimator` 临时插在 app 层上面的父层。
- 动画结束后 leash 应该消失，app 自己的 layer 还在。
- 如果完全没有 leash：先确认动画 scale 不是 0、旋转真的触发了 transition。

### 判定模板

- 有 leash、动画结束后消失 → 正常；位置/矩阵在 leash 上，不在窗口自己的 Surface 上。
- leash 残留 → 查动画是否被取消/`SurfaceAnimator` 收尾。
- 旋转黑边但无 leash → 回到练手 2，先看 frame/SurfaceControl，不要先怀疑动画。

## 收尾

```powershell
adb shell wm user-rotation free
adb shell settings put system accelerometer_rotation 1
adb shell settings put global window_animation_scale 1
adb shell settings put global transition_animation_scale 1
adb shell settings put global animator_duration_scale 1
```

## 记录表

| 场景 | 先看 | 你看到的值 | 结论 |
|---|---|---|---|
| 白屏 | `mHasSurface` / `mDrawState` |  |  |
| frame/黑边 | `Frames:` / `SurfaceFlinger --list` |  |  |
| 掉帧 | `relayoutWindow` / `performSurfacePlacement` trace |  |  |
| 动画/旋转 | `Leash` 层 |  |  |
