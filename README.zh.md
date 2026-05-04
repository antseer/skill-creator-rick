<div align="center">

# Skill Creator Rick

把 skill 按两阶段生命周期推进，同时保留原 AntSkill Creator 的方法论与 S0-S5 流水线编排。

[English](README.md) | 简体中文

</div>

## 两个阶段

### Stage 1 — 半成品 Skill

适用于产品方案已经完整，但真实数据集成尚未完成的情况。

必须交付：
- 完整产品方案 / PRD / 用户流程
- 前端或输出体验
- 后端能力需求
- 数据源依赖清单
- mock 数据边界和替换计划
- 工程实现文档

可以使用 mock 数据，但每个 mock 数据项都必须说明未来由哪个真实 MCP / API / 数据库替换。

### Stage 2 — 成品 Skill

适用于 Stage 1 的 mock 数据已经被替换之后。

必须交付：
- 用户主路径不再依赖 mock / stub / random 演示数据
- 全部必需数据依赖由 MCP / API / 数据库覆盖，或者明确说明不需要外部数据
- `MCP-COVERAGE.md` 证明覆盖情况
- README 包含数据来源和验证证据
- package 可以安装、运行、分享或发布

> `split` 是拆包动作，不是第三阶段。

## 这个 skill 做什么

- 判断本地 skill 是 Stage 1 半成品还是 Stage 2 成品
- 按原 S0-S5 流水线从原始想法推进到可交付 skill 包
- 保留方法论、SOP、质量门禁、设计规范和 MCP 路由判定
- 识别混合包是否需要先 split
- 基于可维护模板生成阶段专属文件
- 补双语 README、元数据、图标和 agent 门面
- 生成给工程同学看的 MCP / API / 数据源提需文档
- 按阶段校验 package 是否达标
- 生成带分数、缺失项和 Stage 2 blockers 的结构化审计报告
- 用户要求时发布到 GitHub

## 流水线与方法论

生命周期阶段与构建流水线是两条不同轴线：

| 轴线 | 作用 |
|---|---|
| Stage 1 / Stage 2 | 判断 package 的真实完成度、mock 边界、数据源覆盖 |
| S0-S5 pipeline | 编排如何从想法 → 数据盘点 → MCP 路由 → PRD → UI → Review → 打包 |

已恢复的核心资产：

| 资产 | 作用 |
|---|---|
| `PIPELINE.md` | S0-S5 编排总览，以及它和 Stage 1 / Stage 2 的关系 |
| `STAGE-GATES.md` | 生命周期与 S0-S5 workflow 的 pass / stop / split / publish 门禁 |
| `methodology/` | 核心原则、需求锚定、范式、责任边界、半成品边界、事实源优先级 |
| `sop/` | S0-S5 每一步执行 SOP |
| `quality/` | G0-G5 质量门禁 |
| `mcp-capability-map/` | L1-A / L1-B / L2 / L3 / L4 / L5 路由决策树 |
| `design-system/` | Antseer 视觉规范与视觉登记表 |

## 数据来源

这个元 skill 不需要外部行情数据。它处理的是用户本地提供的 skill 文件。

| 数据项 | 真实来源 | 方法 | 最后验证时间 | 失败处理 |
|---|---|---|---|---|
| Skill 包文件 | 用户本地文件系统 | 直接读写文件 | 2026-04-27 | 报告缺失文件和修复项 |
| 打包标准 | 本 skill 内置引用文档 | `references/*.md` | 2026-04-27 | 回退到 `SKILL.md` 契约 |
| 阶段门禁 | 本地门禁文档 | `STAGE-GATES.md`, `quality/*.md` | 2026-05-04 | 缺失时停止包装 |
| 流水线 SOP | 本地流水线文档 | `PIPELINE.md`, `sop/*.md`, `quality/*.md` | 2026-05-04 | 回退到 `SKILL.md` 流水线表 |
| 方法论 | 本地方法论文档 | `methodology/*.md` | 2026-05-04 | 报告方法论缺失并停止 creator workflow |
| 校验规则 | 本地 Python 脚本 | `scripts/quick_validate.py`, `scripts/validate_shareable_skill.py`, `scripts/audit_skill.py` | 2026-05-04 | 输出校验错误和审计报告 |
| 脚手架模板 | 本地模板文件 | `templates/requirement`, `templates/complete`, `templates/common` | 2026-05-04 | 模板缺失时快速失败 |
| 可执行检查 | 本地检查配置 | `validation.checks.json` | 2026-05-04 | 使 Stage 2 `--run-checks` 闸门失败 |
| Antseer 前端组件标准 | 外部 GitHub repo + 外部本地缓存 | `scripts/sync_antseer_components.sh` → `${XDG_CACHE_HOME:-~/.cache}/skill-creator-rick/antseer-components` | 2026-05-04 | 使用已有缓存并披露 commit；如果没有缓存则停止 |

## 验证证据

| 检查项 | 命令 / 方法 | 结果 | 日期 |
|---|---|---|---|
| Frontmatter 校验 | `PYTHONDONTWRITEBYTECODE=1 python scripts/quick_validate.py .` | pass | 2026-05-04 |
| 阶段校验脚本语法 | `PYTHONDONTWRITEBYTECODE=1 python -m py_compile scripts/*.py` | pass | 2026-05-04 |
| Raw Stage 1 scaffold guard | 生成临时半成品包，并确认占位符未填完时 validation 必须失败 | pass | 2026-05-04 |
| Stage 2 脚手架冒烟测试 | 原始 complete scaffold 必须在占位符填完前失败；填充示例值后 pass | pass | 2026-05-04 |
| 可执行校验闸门 | `PYTHONDONTWRITEBYTECODE=1 python scripts/validate_shareable_skill.py . --stage complete --run-checks` | pass | 2026-05-04 |
| 结构化审计报告 | `PYTHONDONTWRITEBYTECODE=1 python scripts/audit_skill.py . --stage complete --run-checks --format json` | pass | 2026-05-04 |
| 发布边界检查 | 确认组件库 checkout、`.git`、`node_modules`、pycache、生成缓存未进入 package source | pass | 2026-05-04 |

## 示例请求

```text
/skill-creator-rick review 这个 skill，判断它处在哪个阶段
/skill-creator-rick 根据这个 PRD + 原型生成 Stage 1 半成品 Skill
/skill-creator-rick MCP ready 后，把这个 Stage 1 包升级到 Stage 2
/skill-creator-rick 按 Stage 2 Finished 校验这个包
/skill-creator-rick 把这个大 skill 拆成多个独立包
```
