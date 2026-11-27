# 跨 AOSP 版本迁移文章行号

基线：`/home/book/aosp13`（`DEFAULT_PLATFORM_VERSION=TP1A`）。`/home/book/aosp12` 只作版本差异对照，不作为引用依据。

## 迁移步骤

1. 从 HTML 抽出全部引用：`File.java:NNN`、代码块行首 `NNN:`、裸 `:NNN`（字段表、速查表、问答）。
2. 每条 `File.java:NNN`：读旧树该行文本，在新树同名文件里逐行比 `re.sub(r"\s+", "", line)`，唯一命中即新行号；输出「文件:旧→新」表，不按方法相对偏移推算。
3. 多义行按所在方法人工定：`addWindow`/`relayoutWindow` 取方法体内第一个 `synchronized (mGlobalLock)`，`execute()` 取方法体内第一个锁，`if (displayChanged)` 取方法体内的那个而不是内层嵌套的。
4. 补查三类漏网，正则只认 `行号:` 前缀，它们会被跳过：
   - `<span class="cm">// :NNN</span>` 文档自注行号；
   - `方法名() { ... }` 缩写块；
   - 未带文件名的裸 `:NNN`，按同行符号名在 13 树 grep 后逐项映射。
5. 版本串同步：title / subtitle / series / footer 里的 `AOSP 12`、`android-12.0.0_rXX`、`/home/book/aosp12`。
6. 备份旧版到 `<篇目目录>\.backup\<name>.aosp12.html`，再覆盖正式文件。
7. 校验：新 HTML 每条 `File.java:NNN` 回 13 树读该行文本，确认是同一方法或语句；代码块行号前缀逐条比对；Edge headless 截图明暗两主题。

## audit_anchors.py 规则

- 跑法：`python3 /mnt/d/openclaw/skills/android-framework-tutor/scripts/audit_anchors.py --html '<html>' --root /home/book/aosp13/frameworks/base`，要求 n/n 全过；根收窄到 frameworks/base 可避开 `packages/SystemUI`、`packages/SettingsLib` 里的同名类，索引也从 1–2 分钟降到十几秒。
- 锚点一律写父目录前缀：`wm/ActivityStarter.java:1567`、`am/ActivityManagerService.java:2827`、`app/ActivityThread.java:3753`、`view/ViewRootImpl.java:1153`。不写前缀就按 basename 取第一个候选（`ActivityStarter.java` 在 SystemUI/SettingsLib 各有一份 115 行副本），结果是「行号越界」或静默核到错文件还判 OK。
- 它在锚点前 80 字符里取最后一个 `Class#method(` 或 `Class.method(`，要求方法名出现在 `文件:行±6` 内；树行一行只放一个 `文件:行号`，`setView() → WMS#relayoutWindow()` 后面挂一个锚点会被只校验最后一个；代码块末尾的 `notify_all()`、`unlockAnimationClock()` 同理，给锚点前写不含方法调用的引导语即可，不要删锚点或改行号。
- 长方法内部的特征行改引方法起止行（`DisplayPolicy.java:1561-1574`）；审计输出重定向到文件再读尾部。
