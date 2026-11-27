# 框架级服务篇（ATMS / AMS / PMS…）：新建与挂载

触发：用户说「X 是什么」「我要学习，也给我整个文章」，X 是 system_server 里的服务或管理器。

## 步骤

1. 先查目标文件是否存在：
   `Get-Item "D:\openclaw\Android framework\android-framework-<slug>.html"`
   - 已存在且近期被改过：并行会话在写，只核对与补链，不重写（重写会覆盖别人的改动）。
   - 已存在且未被改：把这当作「已有篇目」，直接给结构、阅读顺序与审计结论，不重写。
2. 定基线并全程同树：新篇所有锚点只用一棵树（`/home/book/aosp13` 或 `/home/book/aosp12`）。同目录已有篇基线不同时，在文末写明「本篇基线 X，与同族篇行号不可混用」。
   - 跨服务边界断言（是否共享锁、共享树、互相持有）先 grep 赋值语句取证再写，不按「同在 system_server」推断：`grep -n 'mGlobalLock' <svc>.java` 会给出三种写法（自持 `= this`、`new WindowManagerGlobalLock()`、`= atm.getGlobalLock()`），三种写法对应三种不同结论。
3. 样式从同族最新篇提取，不手抄 CSS：
   - 正文写进临时文件，`<head>` 里留 `<style>/*__CSS__*/</style>` 占位。
   - Python 读同族篇的 `<style>…</style>` 正则取出，替换占位后写入正式路径，同时打印 `<div>/<table>/<pre>` 开闭计数与 `<h2>` 列表。
4. 锚点审计：`python3 /mnt/d/openclaw/skills/android-framework-tutor/scripts/audit_anchors.py --html '<html>' --root <同一棵树>`，要求 n/n 全过；同名文件多（`Task.java`、`Process.java`）时锚点带目录前缀。
5. 挂载与互链：
   - 卡片加到 `D:\openclaw\Android framework\index.html` 的同族专题区（如「ATMS / AMS 专题」），**不是**窗口系列的 `index.html`。
   - 同族篇页脚加互链；改前确认锚点文本唯一命中，命中数≠1 就跳过（避免与并行编辑冲突）。
6. 末尾固定三段：本篇锚点基线、同族前后篇链接、学习站/路线图入口。

## 章节骨架（实测好用）

它是什么（与相邻服务的边界表）→ 服务结构（六个字段表）→ 锁与共享结构 → 主链路逐跳 → 状态对象 → 资源/回收策略 → 子系统（Service/广播/Provider 类）→ 死亡与收尾 → 观测命令表 → 八个坑 → 源码速查 + 实践题 → 自测 3 题。

## 检查

- `<div>/<table>/<pre>` 开闭相等；`<h2>` 数与 TOC 项一致。
- Edge headless 截图看首屏：标题、系列条、TOC、第一张表不能溢出。
- 正文无 Markdown 残留（`**`、反引号）——写 HTML 时容易把 `**强调**` 直接敲进去，装配后统计应为 0。
