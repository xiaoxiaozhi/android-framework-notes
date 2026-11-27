---
name: "aosp-caller-trace"
description: "AOSP 调用链追踪：HIDL/AIDL 回调（onVsync_2_4 等）与 Java 侧 Activity 生命周期/启动链；输出带 文件:行号、进程边界、断点的调用树。"
---

# AOSP 方法「谁调用我」追踪

## 触发场景

- 用户问「这个方法怎么找不到被谁调用 / 谁调它 / 调用链是什么」，方法名带 `::`，或在 ASfP 里 Ctrl+Click 只跳到定义、Find Usages 为空。
- 方法名形如 `onVsync_2_4`、`processCaptureResult_3_4`：先怀疑是 HIDL/AIDL 版本化回调，不要当普通 C++ 方法找调用点。
- 栈/日志里出现匿名 namespace 的桥接类（`ComposerCallbackBridge`、`*CallbackBridge`、`*Adapter`）。
- 用户贴一行代码问「谁在执行 / 这行是谁调的」，要求说明执行线程、上下游和这行做了什么。

## 判断它是不是「没有源码调用点」的那类方法

读定义处，命中任一条就按本技能走，不要在源码树里死磕 grep：

- 返回 `Return<void>`/`Return<...>`、参数是 `hal::` 类型、函数带 `override` → HIDL 接口实现，调用方在 binder 对端进程。
- 类在匿名 namespace，且只在一处 `registerCallback(sp<X>::make(...))` 被创建 → 接口指针已交给对端，本进程内没有直接调用。
- 方法名后缀 `_主版本_次版本` → 版本化回调，名字就写在 `.hal` 里（不是编译器改名），旧版本走不带后缀的同名方法。

## 步骤

1. 解析源码根与版本，不硬编码：`wsl -e bash -c 'ls -d /home/book/aosp*'`；默认基线 `/home/book/aosp13`（`TP1A` = Android 13），`aosp12` 仅作差异对照，版本读 `build/make/core/version_defaults.mk`。
2. 用一条命令同时拿「定义 + 接口 + 全树调用者」，先看到全景再细读：
   ```bash
   wsl -e bash -c 'cd /home/book/aosp13; grep -n "METHOD" <定义文件>; grep -rn "METHOD" hardware/interfaces/ | head; grep -rln "METHOD" frameworks hardware vendor | head -30'
   ```
   只读 `frameworks hardware vendor`，不要扫 `out/`（几百万文件会挂住）。
3. 判读结果：`frameworks/` 下通常只有「实现」，`hardware/`（尤其 `hardware/qcom/<platform>/`）才是真正发起调用的 HAL 侧。按链路逐跳补行号：
   - HAL 注册回调的入口（`RegisterCallback(HWC2_CALLBACK_*, ...)` 之类）；
   - HAL 侧 `sp<IComposerCallback> callback24_->METHOD(...)`；
   - 生成代理：`out/soong/.intermediates/<module>/..._genc++/gen/.../<Iface>All.cpp` 里 `BpHw*::METHOD` → `_hidl_METHOD`（`oneway` 异步）；
   - 生成桩：`BnHw*::_hidl_METHOD` 反序列化后虚调用 → 落到桥接类的 `override`。
4. 找生成代码直接 `ls` 已知 intermediates 目录，不要 `find out`：
   ```bash
   wsl -e bash -c 'ls /home/book/aosp13/out/soong/.intermediates/hardware/interfaces/graphics/composer/2.4/android.hardware.graphics.composer@2.4_genc++/gen/android/hardware/graphics/composer/2.4/'
   ```
   文件名是 `ComposerCallbackAll.cpp` 这种 `<Iface>All.cpp`；用 `grep -n -A14 "BpHw...::METHOD"` 取代理体。
5. 回答按固定顺序，先结论后链路：
   1) 一句话：不是普通方法，调用方在 HAL 进程，源码里只有实现；
   2) 调用链，每跳 `文件:行号`，标出跨进程/异步边界，并注明该跳是记录、过滤、喂模型还是分发；
   3) 为什么 IDE 搜不到（匿名 namespace + 虚调用 + 生成代码不在源码树/未被索引）；
   4) 版本分支与兜底日志（哪个版本走哪个方法，日志出现说明什么）；
   5) 怎么运行验证：perfetto/systrace 抓 binder transaction，`adb shell ps -A | grep -i composer` 确认发送进程。
6. 本机已核实的 composer/VSYNC 实例见 [references/composer-hidl-callback.md](references/composer-hidl-callback.md)，同主题直接引用行号，不再重 grep。
7. 用户要求把结论写回 HTML 或给某行补注释时：在 `D:\openclaw\Android framework\Android窗口层级\*.html` 用 `Select-String -Path <file> -Pattern '<代码片段>' -Encoding utf8` 定位代码块，在代码行前或行尾插入 `<span class="cm">// ...</span>`，注释写「做什么 + 不做什么 + 下游是谁」；同步改同段正文；最后用 `Select-String` 复查旧措辞（如「统计」）为 0。行尾已有返回值注释（如「false = 本次样本作废」）不算解释调用本身，仍要补「这行做了什么」。

## 坑

- 核锚点、读方法体从 Windows 直读源码树，不经 WSL 回传输出：`Select-String -Path '\\wsl.localhost\Ubuntu\home\book\aosp13\frameworks\base\...\X.java' -Pattern 'METHOD' | % { "$($_.LineNumber): $($_.Line.Trim())" }` 一次拿到行号加原文；按区间读方法体用 `(Get-Content $p)[3535..3604] | % -Begin {$i=3536} -Process { "$i`: $_"; $i++ }`。输出一长就被压缩截断，所以一次只问一个文件、一个方法。要读一段带行号的源码，在 WSL 侧用 `nl -ba <file> | sed -n 'A,Bp'`；要确认构造函数调了哪个超类、传了哪些参数，别按文档猜形参名（形参常带前导下划线，如 `_service`，猜名会 grep 不到），直接 `grep -n 'super(' <file>` 取命中行再按区间打印。PowerShell 里不写 `| head`（不是 cmdlet，直接报错），截断用 `Select-Object -First N`。
- 从 Windows 调 WSL 时，整条 bash 命令用单引号包给 `wsl -e bash -c '...'`；写成双引号且命令里含 `2>/dev/null` 会被 pwsh 当重定向，报 `Out-File: ... D:\dev\null`。
- 不要在 `out/` 上跑全树 `find`，按 module 的已知路径 `ls`；`find out -path '*2.4*'` 几分钟不返回。
- 不要断言 HIDL 会自动把方法名改成 `_2_4`：`onVsync_2_4` 是 `.hal` 里手写的名字（`IComposerCallback.hal:34` 为 `oneway`）。
- 不要把 `hwc2_callback_data_t`/C 函数指针层与 HIDL 接口层混成一步；厂商树里两层都出现（`QtiComposerClient::onVsync_2_4` 既是 HWC2 回调，又调 `callback24_->onVsync_2_4`）。

## Look up the case

- 用户贴出一行代码问「谁在执行 / 这行是谁调的」，要判外层 override、执行线程与真正下游；或用户指出文档注释措辞不准，要在该文档搜同一措辞的所有出现逐处改并复查计数为 0 → [references/line-execution-trace.md](references/line-execution-trace.md)
- 用户要「打印调用树 / 做笔记」要按格式画（含 HIDL/composer 树），要画或核对 Java 侧 ATMS → binder → ActivityThread 生命周期调用树，要下断点、断点「离调用方法太近」或下在 `obtain()` 这类小工厂方法上不中，或审阅、合并别人给的调用树 → [references/java-call-tree.md](references/java-call-tree.md)
- 追踪本机已核实的 composer/VSYNC HIDL 回调实例，直接引用现成行号 → [references/composer-hidl-callback.md](references/composer-hidl-callback.md)
