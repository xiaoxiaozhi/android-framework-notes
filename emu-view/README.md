# 模拟器屏幕镜像（emu-view）

因为 Gateway 跑在 Windows **session 0**（无桌面），WSLg 里启动的模拟器窗口不会显示在用户桌面上。
这个页面通过 `adb exec-out screencap` 取帧，在浏览器里看和操作模拟器。

## 启动

```powershell
python "D:\openclaw\Android framework\emu-view\emu_view_server.py"
```

端口 `8124`（可用环境变量 `EMU_VIEW_PORT` 改）。

## 端点

| 路径 | 作用 |
|---|---|
| `/` | 自动刷新页面（1.2 s/帧），点图即点按，顶部有 返回/Home/最近 按钮 |
| `/shot.png` | 最新一帧 PNG（缓存 0.6 s） |
| `/tap?x=..&y=..` | `adb shell input tap` |
| `/key?k=back|home|recent|power` | 按键 |
| `/type?t=...` | 输入文字 |
| `/devices` | `adb devices` 输出 |

## 依赖

- WSL 发行版 `Ubuntu` 里有可用的 `adb`，且模拟器在跑（`emulator-5554`）
- Windows 侧 adb 不必可用；本服务全部走 `wsl -d Ubuntu -- bash -lc "adb …"`

## 更省事的替代

真要一个**可交互的原生窗口**，直接在自己的桌面终端跑 scrcpy（已安装）：

```powershell
scrcpy --select-usb=0   # 或直接 scrcpy，会自动挑唯一的设备
```

scrcpy 从 session 1 启动，窗口就会出现在你的显示器上，且延迟低于本页面轮询。
