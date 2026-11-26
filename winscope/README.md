# Winscope（AOSP 12 本地构建版）

从 `/home/book/aosp12/development/tools/winscope` 构建的静态产物，用于可视化 WMS / SurfaceFlinger 的 trace。

- 构建环境：WSL Ubuntu + Node v20.20.2（`~/opt/node`）+ JDK 11
- 构建命令：`NODE_OPTIONS=--openssl-legacy-provider npm run build`（webpack 4 需要 legacy provider）
- 前端产物：`index.html` + `js/`（约 13 MB）
- `winscope_proxy.py`：ADB Connect 代理，监听 `localhost:5544`，版本 0.8

## 启动

```powershell
powershell -ExecutionPolicy Bypass -File .\start-winscope.ps1
```

会做三件事：起静态服务（8123）、起 ADB 代理（5544）、用带 token 的 URL 打开浏览器。

## trace 抓取命令

```bash
# WMS 窗口状态
adb shell wm tracing start
adb shell wm tracing stop          # 文件: /data/misc/wmtrace/wm_trace.pb

# SurfaceFlinger 图层树
adb shell su root service call SurfaceFlinger 1025 i32 1
adb shell su root service call SurfaceFlinger 1025 i32 0   # 文件: /data/misc/wmtrace/layers_trace.pb

adb root && adb pull /data/misc/wmtrace
```

拿到的 `.pb` 直接在页面里 `ADD FILE` 加载，或拖进窗口。
