# Antseer Components Standard — 前端组件库 SoT

> 组件库地址：https://github.com/antseer/antseer-components
> 本地缓存：`${XDG_CACHE_HOME:-~/.cache}/skill-creator-rick/antseer-components`
> 同步脚本：`scripts/sync_antseer_components.sh`

## 1. 定位

`antseer-components` 是 Antseer Skill 前端生成 / 改造时的组件级参考来源，地位类似 MCP 能力地图：

- MCP 能力地图回答“真实数据能力从哪里来”。
- `antseer-components` 回答“结构化、模块化、产品规范前端怎么写”。

凡是生成或重构 Skill 前端，尤其是 K 线、附图、marker、event rail、数据 inspector、source footer 这类通用模块，应优先参考本组件库，而不是从旧 HTML 里复制一次性实现。

## 1.1 发布包边界

组件库 checkout 是运行时参考缓存，不是 `skill-creator-rick` 发布内容：

- 不要把 `antseer-components` 的 `.git`、`node_modules` 或完整源码 vendoring 进本 skill。
- 发布包只保留本规范文档和 `scripts/sync_antseer_components.sh`。
- 需要参考组件时，先运行同步脚本，读取外部缓存 commit，并在最终报告中说明。

## 2. 使用前必须检查最新版

每次执行以下任务前，必须先同步或检查组件库：

1. S3 高保真 HTML 生成。
2. V2-style 产品化改造。
3. Stage 2 前端接真实数据。
4. 抽象可复用图表 / 事件 / 数据表组件。
5. 用户明确提到 `antseer-components` 或组件化前端。

执行：

```bash
bash /Users/rick/.claude/skills/skill-creator-rick/scripts/sync_antseer_components.sh
```

如果 GitHub 暂时不可达，必须说明：

- 当前使用的是外部本地缓存版本。
- 缓存 commit 是什么。
- 本次改造只作为临时实现，后续需重新同步确认。

## 3. 组件库使用原则

1. **参考结构，不照搬假数据**：组件库可提供架构、组件接口、样式模式；不得继承 demo / fixture / synthetic 数据。
2. **真实数据优先**：Stage 2 页面必须继续读取真实 MCP/API/数据包。
3. **组件输入必须是 view model**：组件不直接读 raw MCP payload，也不在 renderer 中计算业务口径。
4. **保留 Antseer Design System**：组件样式必须同时符合 `design-system/antseer-design-system.md`。
5. **沉淀通用接口**：K 线、附图、marker、事件列表、数据来源 footer 应定义清晰输入合约，方便后续 Skill 复用。

## 3.0 官网 JSON 响应交付形态

Antseer 官网 / SkillHub 的消费方式是：**最终 HTML 模板会作为 JSON 响应中的字段返回给官网使用**。因此正式交付的 Skill 前端必须是可被 JSON 包装、可单文件渲染的模板。

硬约束：

1. **正式交付模板的数据必须放在模板里**
   - `#antseer-data` 应内联完整的渲染数据或完整的真实数据快照。
   - 不要依赖同级 `../data/*.js`、`../data/*.json`、本地文件路径或另一个静态资源作为用户主路径数据入口。
   - 如需调试态外部数据包，可以保留为开发辅助文件，但不得作为官网正式消费路径。

2. **内联不等于 mock**
   - Stage 2 的 `#antseer-data` 可以内联，但内容必须来自已验证 MCP / API / 数据库 / 真实文件产物。
   - 不允许为了让模板自包含而内联 demo / fixture / synthetic / random 数据。
   - `README` / `MCP-COVERAGE.md` / 验证脚本必须说明内联数据的真实来源、生成时间和复现方式。

3. **模板里保留数据契约**
   - 必须同时保留 `#antseer-data-schema`，说明字段、枚举、单位、时间口径、必填项和可推导项。
   - `#antseer-data` 应尽量接近官网最终 JSON payload；renderer 从该 payload 构建 view model。

4. **可复现生成**
   - 如果真实数据来自 MCP/API，应提供脚本把真实响应固化进模板，例如 `fetch → validate → inject #antseer-data → e2e`。
   - 校验应覆盖：无 mock/random、字段完整、样本量、时间范围、数据来源可见、核心交互可用。

## 3.1 主题色与外层布局硬约束

Skill 前端通常被嵌入到 SkillHub / host page 中，**host 负责页面宽度、居中、外边距和外层 padding**。Skill 自身只负责内部模块排布。

硬约束：

1. **最外层容器不得设置宽度约束**
   - 不要在 root / `.container` / `main` 这类最外层 wrapper 上写 `max-width`。
   - 不要写 `margin: 0 auto` 做居中。
   - 不要在最外层 wrapper 上写水平 / 垂直 `padding` 来制造页面边距。
   - 合法写法示例：`.container { display:flex; flex-direction:column; gap:24px; }`
   - 内部 section、card、grid 可以有 padding / gap；禁止的是页面 root 的外层约束。

2. **主题色必须使用 Antseer Design System 口径**
   - 主色：Antseer Green `#36DD0C`，用于 logo、primary、verified、主图强调。
   - 警示 / 二级图表：Amber `#FFB000`。
   - 信息 / 三级图表：Blue `#1196DD`。
   - 成功 / 失败：`#05DF72` / `#FF4444`。
   - 页面 / 卡片 / muted / accent：`#080807` / `#1D1D1A` / `#121210` / `#2A2926`。
   - 不要随意引入组件库 palette 之外的新主题色（例如临时 teal / cyan）作为模块主色；除非产品规范明确指定。

3. **优先使用 token，不在业务样式里散落硬编码颜色**
   - 推荐变量命名沿用页面现有 Antseer token：`--antseer-bg`、`--antseer-card`、`--antseer-primary`、`--antseer-info` 等。
   - 半透明背景优先用 `color-mix(in oklab, var(--antseer-primary) 10%, transparent)`。
   - 少量 chart point / overlay color 可以传 token 或标准 palette 色值，但不得改变整体主题口径。

## 4. 推荐前端分层

```text
raw data package / API result
  → data adapter
  → domain calculator
  → view model
  → antseer-components / renderers
  → interaction state
```

硬约束：

- renderer 不请求数据。
- renderer 不生成业务口径。
- renderer 不制造 fallback 数据。
- 缺数据必须由 view model 输出 empty/error/warning state。

## 5. 与 V2-style 写法的关系

V2-style 改造时：

- 旧 `index.html` / `*-v2.html` 只作为功能和视觉意图参考。
- `antseer-components` 作为模块化前端结构参考。
- 真实数据合约以当前 Skill 的 `data-prd.md`、`MCP-COVERAGE.md`、真实数据包为准。

一句话：**用组件库重构结构，用真实数据包保住事实。**
