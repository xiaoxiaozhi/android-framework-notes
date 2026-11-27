# 「谁执行这一行」的追法

当用户贴出一行代码问「谁在执行 / 这行是谁调的」，需要定位外层函数、override、执行线程与真正下游时读它。

## 「谁执行这一行」的追法

1. 先在树里定位这行和最近的外层函数：`grep -rn "display->onVsync(timestamp)" frameworks/native/services/surfaceflinger`，再用 `awk 'NR<=<行号> && /Class::/ {n=NR; s=$0} END {print n": "s}' <文件>` 取外层函数，不要只看缩进猜。
2. 确认外层函数是谁的 override：在头文件里找类定义（如 `grep -n "class SurfaceFlinger" SurfaceFlinger.h` 看到 `private HWC2::ComposerCallback`），再在桥接类里找虚调用（`mCallback->onComposerHalVsync`）。源码里不会有 `surfaceflinger->onComposerHalVsync(...)`。
3. 判执行线程：HIDL/AIDL 回调跑在客户端进程的 binder 线程（`HwBinder:<pid>_n`），不是主线程；函数体里的 `Mutex::Autolock lock(mStateLock)` 就是并发边界。perfetto 里按 `ATRACE_CALL()` 的切片名确认。
4. 读被调函数体再定性：只写字段是「记录/状态更新」，要指出字段名和消费者；调 `EventThread`/`Scheduler`/`invalidate` 才是「分发/唤醒」。没有累计逻辑就不要写「统计」。同名 `onVsync` 逐层语义不同：`DisplayDevice::onVsync` 只写 `mLastHwVsync`，`HWComposer::onVsync` 只校验/去重，`Scheduler::addResyncSample` 只喂模型，`EventThread` 的 `dispatchEvent`/`postEvent` 才写 App 的 BitTube。
5. 继续读外层函数剩余部分，找到真正的下游（如 `mScheduler->addResyncSample` → VSyncReactor/VSyncPredictor，再到 EventThread 的 `dispatchEvent`/`postEvent`），回答里明确「这行不做什么，真正做这件事的是哪行」。
6. 用户指出文档注释措辞不准时：在该文档里搜同一措辞的所有出现（正文、其他代码块、其他小节都要查），逐处改成源码语义，再复查计数为 0；只改被指出的那一行不算完成。
