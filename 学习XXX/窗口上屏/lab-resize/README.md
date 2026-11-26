# 黑边/比例练手 01（AOSP 13 / emulator-5554）

> 目标：不只“看代码”，而是亲手制造四种黑边，学会用 `Frames:` / `mHasSurface` / `mDrawState` / SurfaceFlinger 区分原因。
> 代码在 `D:\workspace\FramworkContent\app\src\main\java\com\example\framworkcontent\lab`。
> 设备：`emulator-5554`，AOSP 13（API 33）。

## 先装/起

```powershell
cd D:\workspace\FramworkContent
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
.\gradlew.bat :app:assembleDebug
adb install -r app\build\outputs\apk\debug\app-debug.apk
```

四个入口：

```powershell
# 练手页：A/B/C/D 四种黑边
adb shell am start -n com.example.framworkcontent/.lab.ResizePlaygroundActivity

# 固定竖屏 + 不可 resize：系统 letterbox
adb shell am start -n com.example.framworkcontent/.lab.FixedPortraitActivity
```

## 场景 A｜固定 16:9：预期 letterbox

```powershell
adb shell am start -n com.example.framworkcontent/.lab.ResizePlaygroundActivity
# 点 A. 固定 16:9
```

页面中间是 900x506 的内容区，外面是 Activity 背景。  
这是“内容自己固定比例”，不是 WMS frame 错，也不是 buffer 没跟上。

看：

```powershell
adb shell "dumpsys window windows | grep -A 30 'Window{.*ResizePlayground' | grep -E 'Frames:|mHasSurface|mDrawState'"
```

预期：

- `Frames: frame=[0,0][1440,2960]`：窗口占满；
- `mHasSurface=true`、`mDrawState=HAS_DRAWN`；
- 黑边来自内容容器只有 900x506。

结论：**预期 letterbox，不是 bug。**

## 场景 B｜SurfaceView 固定 900x506：buffer 尺寸不匹配

```powershell
# 点 B. SurfaceView 固定 900x506
```

SurfaceView 的 view 和 buffer 都固定 900x506；窗口更大时，四周黑边。  
这模拟“frame 新了、Surface buffer 没跟上”。

看：

```powershell
adb shell "dumpsys window windows | grep -A 30 'Window{.*ResizePlayground' | grep -E 'Frames:|mHasSurface|mDrawState'"
adb shell "dumpsys SurfaceFlinger --list | grep -i ResizePlayground"
adb shell "dumpsys SurfaceFlinger | grep -A 30 -i ResizePlayground"
```

预期：

- `Frames:` 是窗口大小；
- `mHasSurface=true`、`mDrawState=HAS_DRAWN`；
- SurfaceFlinger 里 SurfaceView 的 buffer 是 900x506；
- 黑边 = view 大小和 buffer 大小不一致。

结论：**不是 WMS frame 没算，是 SurfaceView/buffer 固定了尺寸。**

## 场景 C｜延迟 3 秒重绘：过渡黑边

```powershell
# 点 C. 延迟 3 秒重绘，然后立刻旋转
adb shell wm user-rotation lock 1
```

配置已经变了，但代码故意 3 秒后才 `requestLayout`。  
期间 `Frames:` 可能是新尺寸，但内容还是旧布局。

看：

```powershell
adb shell "dumpsys window windows | grep -A 30 'Window{.*ResizePlayground' | grep -E 'Frames:|mHasSurface|mDrawState'"
```

预期：

- `Frames:` 已经变成横屏；
- `mDrawState` 可能是 `DRAW_PENDING` 或 `HAS_DRAWN`；
- 3 秒内画面比例不对/黑边，3 秒后恢复。

结论：**过渡态，不是永久布局错误；查 app 是否延迟/漏了重绘。**

## 场景 D｜固定竖屏 + 不可 resize：系统 letterbox

```powershell
adb shell wm user-rotation lock 0
adb shell am start -n com.example.framworkcontent/.lab.FixedPortraitActivity
adb shell wm user-rotation lock 1
```

这个 Activity 在 manifest 里写了：

```xml
android:screenOrientation="portrait"
android:resizeableActivity="false"
```

横屏时系统保留竖屏比例，两侧是系统 letterbox。

看：

```powershell
adb shell "dumpsys window windows | grep -A 30 'Window{.*FixedPortrait' | grep -E 'Frames:|mHasSurface|mDrawState'"
adb shell "dumpsys activity activities | grep -A 5 FixedPortrait"
```

预期：

- `Frames:` 是一个竖屏比例的矩形，不是全屏；
- `mHasSurface=true`、`mDrawState=HAS_DRAWN`；
- `dumpsys activity` 里能看到 task bounds / letterbox 配置。

结论：**系统按 Activity 声明加的 letterbox，不是 WMS 算错。**

## 判断顺序（黑边通用）

```text
1. Frames: 是旧尺寸？
   → WMS frame 没更新：查 performSurfacePlacement / waitingForConfig / layout

2. Frames: 新，mDrawState=DRAW_PENDING？
   → app 还没交新帧：查 app draw / gfxinfo

3. Frames: 新，mDrawState=COMMIT_DRAW_PENDING / READY_TO_SHOW？
   → app 交卷了，WMS 还没 commit/show

4. Frames: 新，mDrawState=HAS_DRAWN，但黑边还在？
   → buffer/crop/transform 不匹配，或本来就是 letterbox
   → 查 SurfaceFlinger layer、Activity 的 screenOrientation/resizeableActivity
```

## 抓 trace

```powershell
adb shell atrace --async_start -b 32768 gfx view wm sched freq
adb shell wm user-rotation lock 1
adb exec-out atrace --async_stop > "D:\openclaw\Android framework\学习XXX\窗口上屏\lab-resize\rotate.trace"
```

Perfetto 搜：

- `relayoutWindow`
- `performSurfacePlacement`
- `applySurfaceChangesTransaction`
- `DrawFrame`
- `queueBuffer`
- `composite`

## 收尾

```powershell
adb shell wm set-ignore-orientation-request false
adb shell wm user-rotation free
adb shell settings put system accelerometer_rotation 1
```
