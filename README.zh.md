# AntSkill Creator

一套将 skill 从需求推进到可交付包的结构化生产系统。

[![X](https://img.shields.io/badge/%E5%85%B3%E6%B3%A8-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

[English](README.md) | 简体中文

---

## 核心机制

| 机制 | 作用 | 对应文件 |
|------|------|----------|
| 范式分类 | 区分实现型(A)、规范型(B)、双模(C)，按类型走不同流程 | `methodology/paradigms.md` |
| S1–S6 阶段门控 | 需求→原型→精修→PRD→交付→Review，每阶段有准入/准出标准 | `sop/`、`quality/gates.md` |
| 4 层 Pipeline | 数据、计算、决策、渲染分离，防止逻辑耦合 | `prompts/layer_design_guides.md` |
| Source of Truth 裁决 | PRD、API spec、prompt、Demo 冲突时的优先级规则 | `methodology/source-of-truth.md` |
| Production / Prototype 边界 | 区分视觉参考与生产契约 | `methodology/responsibility-split.md` |

## 数据概览

| 指标 | 数值 |
|------|------|
| Skill 范式 | 3 |
| SOP 阶段 | 6 |
| 方法论模块 | 4 |
| 文档模板 | 10 |
| 内置示例包 | 4 |
| Yield Desk PRD | 1060 行 |
| DualYield 测试 | 32/32 通过 |
| Yield Desk 测试 | 16/16 通过 |

## 这版标准新增了什么

这次标准明确补了两件事：

1. **严肃的 skill 必须有完整 PRD**，把产品逻辑讲清楚，而不是只靠零散 spec。
2. **需求型文档和实现型产物必须物理分层**，评审时一眼就能看出这是规范型、实现型还是双模包。

## 标准包结构

```
skill-name/
├── docs/                     # 面向需求/规范
│   ├── product/PRD.md        # 完整产品逻辑（B/C 必须有）
│   ├── requirements/         # 业务/API/计算/Prompt/可视化/测试规范
│   ├── review/               # review 和 gap 报告
│   └── handoff/              # 可选的工程交接文档
├── implementation/           # 面向实现/运行
│   ├── pipeline/
│   ├── frontend/
│   ├── tests/
│   └── scripts/
├── delivery/                 # 面向发布/分发
│   ├── SKILL.md
│   ├── README.md
│   ├── README.zh.md
│   ├── VERSION
│   ├── agents/openai.yaml
│   └── assets/
└── examples/                 # 可选参考包
```

## 仓库结构

```
antskill-creator/
├── SKILL.md                  # 主控逻辑与决策树
├── docs/                     # 索引 + 产品 PRD + 包规范 + 指南
├── methodology/              # 范式、SoT、职责边界
├── sop/                      # S1–S6 阶段操作手册
├── prompts/                  # L1–L4 层设计指导
├── quality/                  # 质量门与评估标准
├── templates/                # 模板、骨架、校验脚本
└── examples/                 # 完整案例包
```

## 从这里开始

- 文档索引：`docs/INDEX.md`
- 快速上手：`docs/guides/quickstart.md`
- 包结构标准：`docs/standards/package-standard.md`
- 迁移指南：`docs/guides/migration-guide.md`
- 示例编写指南：`docs/guides/example-authoring-guide.md`
- 示例包索引：`examples/README.md`

## 案例

### DualYield — C 范式（双模）

包含产品规范、Pipeline 代码、前端原型、单测、技术 onboarding 文档。L2 测试 32/32 通过。

路径：`examples/dualyield/`

### Yield Desk — C 范式（偏 handoff）

包含 1060 行分层 PRD、高保真前端原型、工程交接文档。L2 测试 16/16 通过。

路径：`examples/yield-desk/`

### SeerClaw Ref — B 范式（规范型）

纯规范包，适合 scanner/analyzer 类产品参考。

路径：`examples/seerclaw-ref/`

## 产出类型

| 范式 | 产出 |
|------|------|
| A — 实现型 | pipeline 代码、测试、前端 demo |
| B — 规范型 | 规范文档、SKILL.md、前端 demo、元数据 |
| C — 双模 | A + B |

## 使用方式

```
/antskill-creator 做一个链上国库监控 skill
/antskill-creator 把这个大 skill 拆成 scanner 和 analyzer
/antskill-creator 把这个 PRD + 原型打包成 GitHub 可分享的 skill
/antskill-creator review 一下这个 skill，先出 gap report 再交付
```

内部流程：判断范式 → 采集需求 → 快速原型 → 精修 → PRD/规范包 → 打包 Review。

## 适用场景

**适合：** 需要产品清晰度与工程可实现性兼顾的 skill 生产；需要 demo/PRD/打包/review 全链路管理；需要可复用方法论的团队协作。

**不适合：** 一次性 throwaway skill；不需要 review 和规范的个人实验。

---

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents
