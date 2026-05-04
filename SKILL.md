---
name: skill-creator-rick
description: "Convert local skills through a two-stage lifecycle and the original AntSkill Creator S0-S5 pipeline: Stage 1 Semi-finished Skill with complete product plan, mock/data-gap transparency, methodology, SOP, UI, and handoff docs; then Stage 2 Finished Skill with all mock data replaced by verified real MCP/data sources."
compatibility: filesystem, python3, git
---

# Skill Creator Rick

把一个本地 skill 按 **两阶段生命周期**整理、审计、补包和发布：

1. **Stage 1 — Semi-finished Skill（半成品）**：产品方案完整，前端 / 后端 / 数据源依赖讲清楚，用 mock 数据展示效果，交付研发接手。
2. **Stage 2 — Finished Skill（成品）**：把 Stage 1 的 mock 全部替换为真实数据源，并验证 MCP / API 能覆盖全部数据依赖，可直接安装、运行、分享。

同时恢复并保留 AntSkill Creator 原始的 **S0-S5 流水线编排**：

- S0 需求锚定 + 需求结晶 + 粗 Demo
- S1 数据盘点
- S2 MCP 真源同步 + 路由审计 + 双 PRD
- S3 高保真 HTML
- S4 HTML ↔ PRD Review
- S5 Skill 半成品交付

> 两阶段生命周期回答“这个包当前真实可用到什么程度”；S0-S5 流水线回答“从一个想法如何一步步做出可交付 skill”。两者是正交关系，不互相替代。

## Core promise

这个 skill 不做“表面包装”。每次先回答三个现实问题：

1. 当前包处在 **Stage 1 半成品**，还是 **Stage 2 成品**？
2. 产品方案、前后端方案、数据依赖是否足够研发接手？
3. 所有 mock 是否已经被真实 MCP / API / 数据库替换，并有验证证据？

> `split` 是拆包动作，不是第三阶段。边界不清时，先 split，再分别进入 Stage 1 或 Stage 2。

## Pipeline model（S0-S5）

当用户是“从 0 创建 / 梳理一个新 Antseer 可视化 skill”时，优先走流水线；当用户是“review / validate / package 现有 skill”时，优先走 Stage gate。

| Step | Goal | SOP | Gate | Output |
|---|---|---|---|---|
| S0 | 需求锚定 + 需求结晶 + 粗 Demo | `sop/s0_requirement.md` | `quality/G0_requirement.md` | intent-card.md + 需求画布 + demo-v0 |
| S1 | 数据盘点，只列不判 | `sop/s1_data_inventory.md` | `quality/G1_data_inventory.md` | data-inventory.md |
| S2 | MCP 真源同步 + 路由审计 + 双 PRD | `sop/s2_routing_and_prd.md` | `quality/G2_routing_and_prd.md` | mcp-audit.md + data-prd.md + skill-prd.md |
| S3 | 高保真 HTML | `sop/s3_html_design.md` | `quality/G3_html_design.md` | demo-v1.html |
| S4 | HTML ↔ PRD 双向对齐 | `sop/s4_review.md` | `quality/G4_review.md` | review-report.md |
| S5 | Skill 半成品交付 | `sop/s5_skill_delivery.md` | `quality/G5_skill_delivery.md` | 完整 skill 目录 + handoff docs |

完整说明见 `PIPELINE.md`。阶段门禁总表见 `STAGE-GATES.md`。方法论见 `methodology/`，其中 S0 需求锚定见 `methodology/intent-anchoring.md`；质量门禁见 `quality/`，MCP 路由决策树见 `mcp-capability-map/routing-decision-tree.md`。

### Layer ownership model

每个可见数据点必须归属到：

| Layer | Owner | Meaning |
|---|---|---|
| L1-A | Existing MCP | MCP 已能直接提供 |
| L1-B | Backend | 需要新建原始 MCP tool |
| L2 | Backend | 需要新建聚合 MCP/API |
| L3 | Skill | skill-local deterministic computation |
| L4 | Skill | LLM structured interpretation + fallback |
| L5 | Skill | frontend presentation |

Stage 1 可以包含 L1-B / L2 缺口，但必须在 `TECH-INTERFACE-REQUEST.md` / `data-prd.md` 中写清接口契约；Stage 2 必须验证这些缺口已经被真实来源覆盖。

### Frontend Source of Truth model

`antseer-components` 对前端的权威等级，等同于 MCP capability map 对数据源的权威等级：

| Authority | Governs | Stage 1 | Stage 2 |
|---|---|---|---|
| MCP capability map | real data source / routing / ownership | gaps allowed if explicit | full real coverage required |
| `antseer-components` | code style / UI style / design style / component contracts | best-effort compliance + disclosed deviations | hard compliance required |

因此：
- 做 S3 HTML、V2-style 改造、Stage 2 真实数据 UI、K 线 / 指标附图 / event marker / source footer 时，必须先同步或检查 `antseer-components` 外部缓存并记录 commit。
- Stage 1 前端要尽量符合组件库规范；不符合项必须写入 `review-report.md`、`TODO-TECH.md` 或 `TECH-INTERFACE-REQUEST.md`，作为 Stage 2 blocker。
- Stage 2 前端必须符合 `references/antseer-components-standard.md` 的代码风格、UI 风格、设计样式、数据契约、官网 JSON 模板和 host 嵌入规则；任一 critical 不符合，不得称为 Finished Skill。

### Stage 1 shapes

Stage 1 有两个合法形态，不能混淆：

| Shape | 用途 | 额外要求 |
|---|---|---|
| Lite Semi-finished Package | 轻量产品/工程提需包 | `REQUIREMENT-REVIEW.md`、`TODO-TECH.md`、`TECH-INTERFACE-REQUEST.md`、产品 spec/prototype |
| Antseer S5 Semi-finished Package | 完整 Antseer 可视化 skill 半成品 | Lite 全部要求 + `data-inventory.md`、`mcp-audit.md`、`data-prd.md`、`skill-prd.md`、`review-report.md`、`frontend/index.html`、`layers/L1-L5` |

如果包里出现任一 S5 产物，就按 S5 严格结构校验。脚手架刚生成时允许带 `{{FILL_BEFORE_VALIDATE}}` 占位，但占位未填完不得通过 Stage 1 validation，也不得上传为 share-ready。

## Stage model

### Stage 1 — Semi-finished Skill（半成品）

适用于：
- 已有完整产品方案 / PRD / 用户流程
- 已有前端方案或高保真 UI / HTML 原型 / 输出样式
- 已定义后端能力、接口、数据源依赖、字段口径
- 真实数据源尚未完全接入，当前用 mock / fixture / stub 展示效果
- 目标是交付研发继续开发

核心特征：
- 可以使用 mock 数据，但必须逐项标注
- 必须说明每个 mock 数据项未来由哪个 MCP / API / 数据库提供
- 必须有前端、后端、数据源依赖的工程实现信息
- 不能声称“可直接使用 / direct-use ready / 已完整可用”

必备交付：
- `SKILL.md`
- `README.md`：必须有 `Data Reality` 章节
- `README.zh.md`：必须有 `数据真实性` 章节
- `skill.meta.json`：如果有用户参数，必须包含标准 `input_schema`
- `REQUIREMENT-REVIEW.md`
- `TODO-TECH.md`
- `TECH-INTERFACE-REQUEST.md`：列出所有真实接口 / MCP / 数据源需求
- 产品方案：PRD / spec / 用户流 / 原型 / 前后端说明，至少一种明确文档或目录
- 不得保留未解决占位符：`TODO`、`Replace this`、`{{FILL_BEFORE_VALIDATE}}` 等

`Data Reality` 必须回答：

```markdown
## Data Reality / 数据真实性

| 数据项 | 当前状态 | 当前用途 | 需要的真实数据源 / MCP | 是否阻塞 Stage 2 |
|---|---|---|---|---|
| 资金费率历史数据 | Mock（硬编码 fixture） | 图表展示与回测示例 | mcp://market/funding-rate 或 GET /api/funding-rate/history | 是 |
| BTC 价格 | Mock（随机生成） | 实时价格卡片 | mcp://market/ticker 或 WebSocket /ws/ticker | 是 |

**重要**：当前 skill 是 Stage 1 Semi-finished Skill，mock 数据仅用于展示产品效果和交互逻辑，不能作为真实分析或交易依据。真实数据源需求见 `TECH-INTERFACE-REQUEST.md`。
```

### Stage 2 — Finished Skill（成品）

适用于：
- Stage 1 的 mock / fixture / stub 已全部替换为真实数据源
- MCP / API / 数据库已经能提供全部数据依赖
- skill 可以直接运行、调用或复用
- 有最小运行记录、数据源验证记录、MCP 覆盖矩阵或测试证据
- 目标是直接安装、分享、发布或真实使用

核心特征：
- 用户主路径不能依赖 mock / random / hardcoded 示例数据
- 所有数据项都有真实来源、调用方式、验证时间、失败处理
- MCP 覆盖全部必需数据依赖；若某项不用 MCP，必须说明替代真实来源
- 可以立即安装使用，并给出运行 / 验证证据

必备交付：
- `SKILL.md`
- `README.md`：必须有 `Data Sources` 和 `Validation Evidence` 章节
- `README.zh.md`：必须有 `数据来源` 和 `验证证据` 章节
- `skill.meta.json`：如果有用户参数，必须包含标准 `input_schema`
- `agents/openai.yaml`
- `VERSION`
- `.env.example`：如需要环境变量 / 鉴权
- `MCP-COVERAGE.md`：验证 MCP / API 是否覆盖全部数据依赖
- 可运行逻辑 / scripts / pipeline
- 测试或最小验证记录
- `validation.checks.json`：如需要可执行 Stage 2 检查

`Data Sources` 必须回答：

```markdown
## Data Sources / 数据来源

| 数据项 | 真实来源 | MCP / API / 方法 | 最后验证时间 | 失败处理 |
|---|---|---|---|---|
| 资金费率历史数据 | Binance / 内部市场数据服务 | mcp://market/funding-rate | 2026-04-27 | 返回空态并提示数据不可用 |
| BTC 实时价格 | 行情 MCP | mcp://market/ticker | 2026-04-27 | 使用最近有效值并标注延迟 |

**验证状态**：用户主路径不再依赖 mock 数据；全部必需数据项已通过 `MCP-COVERAGE.md` 验证。
```




## Repository ownership

两个仓库边界必须分清：

| Repository | Purpose | URL |
|---|---|---|
| Creator repo | 发布和维护 `skill-creator-rick` 这个 creator skill 自身 | `https://github.com/antseer/skill-creator-rick` |
| Generated skill publish repo | 发布由 creator 产出的 Stage 1 / Stage 2 成品 skill | `https://github.com/antseer/test_skills` |

## Generated skill publishing repository

后续 Antseer/Rick Stage 1 / Stage 2 成品 skill 的默认发布目录是：

- Local: `/Users/rick/code/job/external/test_skills`
- Remote: `https://github.com/antseer/test_skills.git`
- Branch: `main`

把 `test_skills` 视为成品 skill 的 shared publish repo，而不是本机安装目录；它也不是 `skill-creator-rick` 自身源码仓库。发布前可以参考同仓库已有 skill 的写法、目录、README、`skill.meta.json` 和 release 口径，但只能作为风格参考，不能继承过期 mock 数据、未验证来源或 secrets。完整规则见 `references/skill-publishing-standard.md`。

发布原则：
- 一个 skill 一个顶层目录，目录名用稳定 kebab-case slug。
- 只同步已通过 Stage gate 的 skill package；不要把 `.skill`、pycache、`.DS_Store`、本地缓存、组件库 checkout、`node_modules` 或 secrets 发进去。
- 发布前先看 `git status --short`，不得清理或覆盖发布仓库里的无关改动。
- 如果 README/index 维护 skill 列表，发布时同步更新。

## Antseer components frontend SoT

Before generating or refactoring any Skill frontend, especially S3 HTML, V2-style productization, Stage 2 real-data UI, K-line charts, indicator subplots, event markers, event rails, data inspectors, or source footers, sync and inspect the maintained component library:

```bash
bash /Users/rick/.claude/skills/skill-creator-rick/scripts/sync_antseer_components.sh
```

Use `references/antseer-components-standard.md` as the rule. Treat `https://github.com/antseer/antseer-components` as the frontend component source of truth, similar to the MCP capability map for data. Reference its modular structure and component contracts, but never inherit demo/fixture/synthetic data into Stage 2 user paths.

Stage rule:
- **Stage 1**: best-effort compliance; disclose every code/UI/design deviation as an implementation gap.
- **Stage 2**: hard compliance; code style, UI style, design style, data contract, source footer, no-demo-data, and host embedding constraints are release blockers.

## V2-style productization writing

When a user provides a `*-v2.html` page, says the page was generated from a publication/template/old version, or asks to keep functionality unchanged while aligning internal logic and visual style with product standards, follow `references/v2-writing-standard.md`.

V2-style writing must preserve functional invariants while specifying product-system aligned internal logic, data contracts, visual behavior, reusable component boundaries, and acceptance gates.

## Standard workflow

### Step 1. Reality review

优先看：
- `SKILL.md`
- README / PRD / Stage 1 implementation docs
- `PIPELINE.md`
- `STAGE-GATES.md`
- `methodology/`
- `sop/`
- `quality/`
- frontend prototype / output UI
- backend/data interface request
- scripts / pipeline / tests
- agent config / metadata
- MCP / API 调用和验证记录

先输出一句判断：
- 这是 **Stage 1 Semi-finished Skill**
- 这是 **Stage 2 Finished Skill**
- 这是 **混合包，需要先 split**
- 这是 **not packageable yet**（目标或输入输出不清）

### Step 2. Classify by stage gate

按四问判断：

1. **边界**：这个包是否只解决一个清晰问题？多职责混杂 → 先 split。
2. **产品方案**：用户流程、前端展示、后端能力、数据依赖是否讲清楚？不清楚 → not packageable yet。
3. **mock 状态**：用户主路径是否仍依赖 mock / random / hardcoded 示例数据？是 → Stage 1。
4. **真实数据覆盖**：所有数据依赖是否由 MCP / API / 数据库真实提供，并有验证证据？是 → Stage 2；否则 Stage 1。

判断细化：
- 生产用户路径存在 mock / fixture / stub → Stage 1
- 测试、fixture、文档样例中存在 mock → 不自动降级，但必须标注不是用户主路径
- 部分真实、部分 mock → Stage 1，并在 `Data Reality` 逐项标注
- 不需要外部数据源的 skill → Stage 2 也可以成立，但 `Data Sources` 必须说明“仅使用用户输入 / 本地文件 / 仓库内容”，并给验证证据
- MCP 不能覆盖全部必需数据项 → 不能进入 Stage 2

### Step 3. Fill the right artifacts

如果是 Stage 1，优先补：
- `Data Reality / 数据真实性`
- `REQUIREMENT-REVIEW.md`
- `TODO-TECH.md`
- `TECH-INTERFACE-REQUEST.md`
- PRD / 前端方案 / 后端方案 / 数据依赖说明
- mock / stub 边界和替换计划

如果是 Stage 2，优先补：
- `Data Sources / 数据来源`
- `Validation Evidence / 验证证据`
- `MCP-COVERAGE.md`
- `README.md` / `README.zh.md`
- `skill.meta.json`
- `agents/openai.yaml`
- `VERSION`
- `.env.example`
- 最小运行说明和测试记录

### Step 4. Validate

至少执行：

```bash
python /Users/rick/.claude/skills/skill-creator-rick/scripts/quick_validate.py <skill_dir>
python /Users/rick/.claude/skills/skill-creator-rick/scripts/validate_shareable_skill.py <skill_dir> --stage requirement
# 或
python /Users/rick/.claude/skills/skill-creator-rick/scripts/validate_shareable_skill.py <skill_dir> --stage complete
# Stage 2 如果提供 validation.checks.json，执行真实检查：
python /Users/rick/.claude/skills/skill-creator-rick/scripts/validate_shareable_skill.py <skill_dir> --stage complete --run-checks
python /Users/rick/.claude/skills/skill-creator-rick/scripts/audit_skill.py <skill_dir> --stage complete --run-checks --format markdown
```

如果是 Stage 2 且有测试 / MCP 连通性检查，应写入 `validation.checks.json` 并用 `--run-checks` 执行。

### Step 4.5. Mandatory sub-agent review gate

任何 Antseer frontend / Stage 2 / 发布前验收，主 agent 自测通过不算完成，必须再做 **子 agent 独立规范复核**，且复核通过后才能声明完成、上传或 push。

最低要求：
- 至少 2 个子 agent：
  1. **规范/API reviewer**：检查 `antseer-components`、数据契约、Stage gate、mock/fixture、模板数据放置规则、组件 API 用法。
  2. **UI/UX/browser reviewer**：检查 V2 风格继承、视觉规范、交互行为、浏览器可用性、console error。
- 子 agent 必须只读 review，避免和主流程互相覆盖。
- 如果任一子 agent 给出 P0/P1，禁止说“完成”，必须先修复再复审。
- P2 可由主 agent 判断是否阻塞，但必须在最终报告中说明取舍。
- 最终报告必须写明：子 agent 数量、结论、剩余问题、是否通过。

完成定义：
> 本地自测通过 + 子 agent 规范复核无 P0/P1 + 必要文件同步一致，才算完成。

### Step 5. Publish when asked

如果用户要求上传 / 发布 skill：
- 默认发布到 `/Users/rick/code/job/external/test_skills`（remote: `https://github.com/antseer/test_skills.git`），除非用户明确指定其他目标
- 发布前读取 `references/skill-publishing-standard.md`，确认本地 checkout 的 remote 正是 `https://github.com/antseer/test_skills.git` 且当前分支是 `main`，并参考发布仓库里相关 skill 的写法
- 先检查 publish repo 的 `git status --short`，只改目标 skill 目录和必要 index/README，不覆盖无关改动
- 同步已验证 package 到 `<publish-repo>/<skill-slug>/`，必要时更新 publish repo README/index
- 从发布后的目录重新运行对应 Stage gate；发布前验收 / Stage 2 / Antseer frontend 仍必须通过子 agent review gate 且无 P0/P1
- validation 和 review gate 都通过后，commit / push 到 publish repo
- 返回发布路径、commit、branch、remote 链接
- 明确说明发布的是 Stage 1 Semi-finished Skill 还是 Stage 2 Finished Skill
- Stage 1 发布时必须醒目标注：mock 数据仅用于展示，不可直接用于真实分析或生产

## Split rule

满足任意两条，建议先 split：
- 面向两个以上明显不同用户
- 有两个以上独立触发场景
- 输出物完全不同
- 依赖完全不同的数据源 / MCP / API
- README 里出现多个互不依赖的核心 promise
- 一个包同时包含 Stage 1 半成品文档和 Stage 2 可运行产品，但两者边界不清
- 用户可以只安装其中一半而不影响另一半

split 输出必须包含：

```markdown
## Split Plan

| 子 skill | 目标用户 | 输入 | 输出 | 数据依赖 | 阶段 |
|---|---|---|---|---|---|
```

## Non-negotiables

1. 先判断阶段，再包装
2. Stage 1 必须有完整产品方案：前端、后端、数据源依赖都要讲清楚
3. Stage 1 必须有 `Data Reality`，标清楚哪些是 mock、未来由哪个 MCP / API / 数据源替换
4. Stage 1 不能写成“可直接使用 / direct-use ready”
5. Stage 2 必须把用户主路径里的 mock 全部替换为真实数据源
6. Stage 2 必须有 `Data Sources`、`Validation Evidence`、`MCP-COVERAGE.md`
7. Stage 2 必须验证 MCP 是否覆盖全部必需数据依赖；不能覆盖的必须说明真实替代来源
8. 中英 README 要结构对等
9. 不能隐瞒接口 / 数据 / MCP 覆盖缺口
10. 如果 skill 有用户参数，`skill.meta.json > input_schema` 必须存在，且 zh/en key 完全一致
11. split 不是阶段
12. 不得删除或省略方法论、流水线编排和阶段门禁；轻量分享包也必须至少保留 `PIPELINE.md` + `STAGE-GATES.md`，完整 creator 包必须保留 `methodology/`、`sop/`、`quality/`
13. Antseer frontend / Stage 2 / 发布前验收必须通过子 agent 独立规范复核；无 P0/P1 后才允许声明完成或 push
14. `antseer-components` 是前端权威参考和硬门禁：Stage 1 尽量符合并披露偏差；Stage 2 必须符合代码风格、UI 风格、设计样式和数据契约
15. 后续 skill 默认发布到 `/Users/rick/code/job/external/test_skills` / `https://github.com/antseer/test_skills.git`；发布前参考同仓库已有 skill 写法，但不得覆盖无关改动或继承未验证内容

## input_schema standard

凡是带参数的 shareable skill，参数配置一律写在 `skill.meta.json > input_schema`。

格式要求见：

- `/Users/rick/.claude/skills/skill-creator-rick/references/input-schema-standard.md`

最低要求：
- 顶层必须有 `zh` / `en`
- 每个参数必须包含 `type` / `label` / `default` / `options` / `description` / `required`
- `input` 的 `options` 必须是 `[]`
- `select.default` 必须存在于 `options[].value`
- `multiple.default` 必须是数组，且每个值存在于 `options[].value`
- `required` 必须是 boolean

## Required output contract

最终汇报至少包含：
1. 阶段判断：Stage 1 Semi-finished / Stage 2 Finished / 需先拆分 / not packageable yet
2. 完成度判断
3. 补了哪些文件
4. 已具备哪些能力
5. 还缺什么，尤其是 mock → MCP / 真实数据源的缺口
6. MCP / API / 数据源覆盖是否已验证
7. 如执行 audit，附结构化分数、缺失项和 Stage 2 blockers
7. 是否已上传 / 发布
