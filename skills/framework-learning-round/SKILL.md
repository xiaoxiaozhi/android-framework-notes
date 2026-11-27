---
name: framework-learning-round
description: "学 Android Framework 或任何大型代码库时用：一轮只产『骨架 + 骨架解说 + 决策点 + 3 个反问 + 阅读法』，再用带判据的 L0 题验证并回填落卡。触发词：学 X、过一遍流程、出实践题、回填、落卡。不用于写正式文章、要完整调用链、要学习路线规划。"
---

# Framework 学习轮次

一轮 = 一条链 + 三块 + 两段配套 + 一道能跑出输出的题。**先写骨架，再解释，再反问，最后用命令结账。一轮一结，不兜圈。**

## 输出形状（唯一允许，顺序固定）

1. **骨架**：12–18 行，每行带 `文件:行号`，每行含 `→` 或 `←`，至少一条 `├─` / `└─` 分支。
2. **骨架解说**：5–8 行，**一行一个标号**（①②③…），说清“谁把什么交给了谁”，不写新锚点。
3. **决策点**：3–5 条，每条一句“这里在决定什么” + 锚点。
4. **3 个问题**：正好 3 条，每条能被一条命令或一个断点回答。
5. **骨架阅读法**：固定 5 行——一句话定位 / 三个接力边界 / 最小验证命令 / 本链最贵的一行 / 可追问的三个名字。

> 只允许 ①②③ 三个编号块；解说、阅读法、基线附注都不编号。
> 形状门槛：`python scripts/check_round.py <round.md>` 退出码 0 才许发给用户；不过就改，不许解释。

## 步骤

1. **定模式**：A（一页骨架 + 3 问，默认）/ B（直接给判据题，边做边学）。
   判据：回复第一行写明模式；用户没选就按 A，只问一次。
2. **选链 + 核锚点**：在基线树现地 `grep`，不引用记忆里的行号；12/13 混用时分别标注。
   判据：`python scripts/check_anchors.py <round.md> --root /home/book/aosp13` 无 error；warning 逐条看。
3. **写形状**：按上面 5 项从骨架写到阅读法。
   判据：`check_round.py` PASS，且解说真的是一行一个标号、骨架不是方法名清单。
4. **出 L0 题**：触发 / 判据 / 锚点 / 产出 四件套，≤25 分钟，零编译。
   判据：判据能 `grep` 出确定字符串；锚点能解释这条判据。
5. **回填**：只答第 4 项那 3 个问题，每问 ≤5 句 + 锚点；先判对错再补细节。
   判据：3 问全答，且没有重讲骨架。
6. **落盘 + 验证**：材料、文章、学习卡三处一起落，最后跑无头验证。
   判据：`references/html-production.md` 的清单全部勾上；卡片查重命中为空。

## 目录与产物

- 文章：`D:\openclaw\Android framework\学习XXX\<主题>学习轮次-AOSP13.html`
- 材料：`...\学习XXX\<主题>\`（`README.md` / `round-01.md` / `walkthrough-01.md` / `evidence-01.md`）
- 卡片：追加到 `D:\workspace\FramworkContent\LAB.md` 记录区（四列，写法见 `references/card-format.md`）
- 视觉：一律用 `android-source-html-analyzer` 的设计系统；CSS/模板在 `assets/`，构建与验证用 `scripts/`

## 资源

- `assets/round-template.md`、`assets/article.css`、`assets/article-template.html`
- `references/practice-design.md` —— 四件套、L0–L2、已有题库（别重复造题）
- `references/skeleton-reading.md` —— 阅读法五行怎么写
- `references/html-production.md` —— 分块构建、无头断言、截图
- `references/example-round.md` —— 完整一轮范例（含解说与阅读法）
- `references/anti-patterns.md` —— 六条失守信号，命中即打断
- `scripts/check_round.py` / `check_anchors.py` / `build_article.py` / `verify_html.py`

## 失守就停

命中 `references/anti-patterns.md` 任意一条：停止输出，按右列动作处理。
**没有一条真实命令输出 = 这一轮没完成**；“我理解了”不算。
