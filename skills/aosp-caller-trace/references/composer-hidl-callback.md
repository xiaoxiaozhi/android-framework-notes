# 实例：composer 2.4 的 onVsync_2_4（AOSP12, sm7250）

本机树 `/home/book/aosp12` 实测。行号是当时的；树更新后先 `grep -n` 复核再用。

## 完整链路

| 跳 | 位置 | 作用 |
|---|---|---|
| 1 | `hardware/qcom/sm7250/display/composer/QtiComposerClient.cpp:162` | 厂商 HWC2 回调入口，`:265-266` 以 `HWC2_CALLBACK_VSYNC_2_4` 注册给 `hwc_session_` |
| 2 | 同文件 `:165` | `client->callback24_->onVsync_2_4(...)`，`callback24_` 是 `sp<composer_V2_4::IComposerCallback>`（`QtiComposerClient.h:358`，`setCallback` 在 `.cpp:1048` 赋值） |
| 3 | `out/soong/.intermediates/hardware/interfaces/graphics/composer/2.4/android.hardware.graphics.composer@2.4_genc++/gen/android/hardware/graphics/composer/2.4/ComposerCallbackAll.cpp:342` | `BpHwComposerCallback::onVsync_2_4` → `_hidl_onVsync_2_4`，oneway binder 发送 |
| 4 | 同生成文件 | `BnHwComposerCallback::_hidl_onVsync_2_4` 反序列化后虚调用 |
| 5 | `frameworks/native/services/surfaceflinger/DisplayHardware/HWComposer.cpp:107` | `ComposerCallbackBridge::onVsync_2_4` → `mCallback->onComposerHalVsync(display, timestamp, vsyncPeriodNanos)` |
| 6 | `frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp:1718` | `SurfaceFlinger::onComposerHalVsync`，override `HWC2::ComposerCallback`（`SurfaceFlinger.h:178` 继承，`:731` 声明）；跑在 SF 进程的 HwBinder 线程，持 `mStateLock` |
| 7 | 同文件 `:1724-1727` | `toPhysicalDisplayId` → `getPhysicalDisplayTokenLocked` → `getDisplayDeviceLocked` → `display->onVsync(timestamp)`，只更新 `mLastHwVsync` |
| 8 | 同文件 `:1730` | `getHwComposer().onVsync(...)`（`HWComposer.cpp:205-237`）校验 display、过滤与 `displayData.lastHwVsync` 相同的重复时间戳、翻转 ATRACE 0/1 标记；不检查 `vsyncEnabled`，返回 false 就丢弃 |
| 9 | 同文件 `:1734-1737` | 非内屏直接 return；外屏 vsync 只留下时间戳，不喂模型 |
| 10 | 同文件 `:1740` | `mScheduler->addResyncSample(timestamp, vsyncPeriod, &periodFlushed)` 只喂 VSyncReactor/VSyncPredictor 并决定硬件 vsync 开关；真正分发在 `EventThread::dispatchEvent` → `EventThreadConnection::postEvent` → BitTube |

## SF 侧语义：记录 vs 分发

- `DisplayDevice::onVsync`（`DisplayDevice.cpp:211-213`）只执行 `mLastHwVsync = timestamp`；字段是 `std::atomic<nsecs_t>`（`DisplayDevice.h:225`），没有计数或聚合。
- 唯一消费者是 `DisplayDevice::getRefreshTimestamp()`（`DisplayDevice.cpp:205-208`）：`now - ((now - mLastHwVsync) % vsyncPeriodNanos)`；HWC 不提供 present fence 时用它估算最近刷新边界（`BufferLayer.cpp:439`、`SurfaceFlinger.cpp:2377`）。
- `HWComposer::onVsync`（`HWComposer.cpp:205-237`）只做三件事：校验 display、过滤与 `displayData.lastHwVsync` 相同的重复时间戳、翻转 ATRACE 的 0/1 标记；没有 `vsyncEnabled` 检查，也不向 App 分发，不能当链路终点。
- 外层 `onComposerHalVsync` 继续调用 `addResyncSample` 才影响调度；但分发不在 `:1740`，而在 `EventThread::dispatchEvent`/`EventThreadConnection::postEvent`。回答时说清「这行只记录，:1740 只喂模型，分发在 EventThread」。

桥接对象的注册在 `HWComposer.cpp:162`：`mComposer->registerCallback(sp<ComposerCallbackBridge>::make(callback, mComposer->isVsyncPeriodSwitchSupported()))`。

## Scheduler::addResyncSample 语义

`Scheduler.cpp:548`：

```cpp
void Scheduler::addResyncSample(nsecs_t timestamp, std::optional<nsecs_t> hwcVsyncPeriod,
                                bool* periodFlushed) {
    bool needsHwVsync = false;
    *periodFlushed = false;
    {
        std::lock_guard<std::mutex> lock(mHWVsyncLock);
        if (mPrimaryHWVsyncEnabled) {
            needsHwVsync = mVsyncSchedule.controller->addHwVsyncTimestamp(timestamp, hwcVsyncPeriod,
                                                                          periodFlushed);
        }
    }
    if (needsHwVsync) enableHardwareVsync();
    else disableHardwareVsync(false);
}
```

- `mPrimaryHWVsyncEnabled == false` 时样本直接丢弃，不喂模型。
- `mVsyncSchedule.controller` 是 `VSyncReactor`：`addHwVsyncTimestamp` 确认/切换周期，把样本交给 `VSyncPredictor`（`mTracker`）。
- 返回值 `needsHwVsync` 决定继续开还是关硬件 vsync；`disableHardwareVsync(false)` 的 `false` 表示保留以后重开的资格。
- `periodFlushed` 只在刷新率周期切换完成时为 true，调用方据此 `modulateVsync(&VsyncModulator::onRefreshRateChangeCompleted)`。
- 锁 `mHWVsyncLock` 只包住喂样本，`enable/disableHardwareVsync()` 的 HAL 调用在锁外。
- 它不写 App 的 socket；真正的发送是 `EventThread::dispatchEvent()`（`EventThread.cpp:571`）→ `EventThreadConnection::postEvent()`（`:189`）→ `DisplayEventReceiver::sendEvents()` 写 BitTube。

## 版本分支

- 接口定义：`hardware/interfaces/graphics/composer/2.4/IComposerCallback.hal:34`，`oneway onVsync_2_4(Display, int64_t, VsyncPeriodNanos)`。名字是手写的，不是编译器改名。
- 2.1 的 `onVsync(display, timestamp)` 与 2.4 的 `onVsync_2_4(...)` 互斥：`mVsyncSwitchingSupported` 为真只收后者。
- 兜底日志在 `HWComposer.cpp:102` / `:112`：`Unexpected onVsync callback on composer >= 2.4` / `Unexpected onVsync_2_4 callback on composer <= 2.3`，出现即版本协商与回调不匹配。

## 为何源码里没有调用点

- `ComposerCallbackBridge` 在匿名 namespace，只被 `make` 一次，接口指针经 `registerCallback` 交给 HAL。
- 调用经 vtable + binder 反序列化发生，源码树里不存在 `bridge->onVsync_2_4(...)`。
- `Bp`/`Bn` 是构建生成物，在 `out/` 下，ASfP 默认不索引，因此 Find Usages 为空。

## 其他出现位置

- `hardware/interfaces/graphics/composer/2.4/utils/hal/include/composer-hal/2.4/ComposerClient.h:85`：通用 HAL 实现的 `mCallback->onVsync_2_4`。
- `hardware/interfaces/graphics/composer/2.4/utils/passthrough/include/composer-passthrough/2.4/HwcHal.h:354`：passthrough 模式。
- 测试/假实现：`frameworks/native/services/surfaceflinger/tests/fakehwc/FakeComposerClient.cpp`、`hardware/interfaces/graphics/composer/2.4/utils/vts/GraphicsComposerCallback.cpp`。
