# S3 — 高保真 HTML + 视觉差异化登记

> **v5 新增步骤**:S0 的 demo-v0 是粗版,S3 要基于 PRD 产出**生产级高保真 HTML**,同时在 `design-system/visual-registry.md` 做差异化登记。

## 阶段目标

1. 产出 **高保真 HTML**(`demo-v1.html`),对齐 PRD 所有 L5 组件、覆盖所有状态、响应式
2. 在 `visual-registry.md` 登记本 Skill 的视觉指纹(主色/字体/Hero 类型),确保与现有 Skill 不撞脸

## 入口条件

- S2 产出的 skill-prd.md + data-prd.md + mcp-audit.md 已通过 G2
- 用户说"出高保真 / 画 HTML / 出前端"

## 方法论

1. **规范先于创作**。先读 design-system 和 visual-registry,再动手。
2. **开工前登记**。选主色、字体、Hero 类型,先在 visual-registry 登记本 Skill,再开写。不允许边画边改再登记。
3. **对齐 PRD**。PRD 每个 L5 组件都必须有实现,缺的标明 v2 延期。
4. **状态完整**。不只画 happy path,loading / empty / error / hover / click 全要有。
5. **数据契约优先**。HTML 里每个动态字段对应到某个 Dxx(S1/S2 的 ID),前端不自造数据。

---

## §1 开工前的视觉登记(必做)

### Step 0:同步 Antseer 组件源

生成或重构 Skill 前端前，先同步组件库并记录 commit：

```bash
bash /Users/rick/.claude/skills/skill-creator-rick/scripts/sync_antseer_components.sh
```

要求：
- 参考 `${XDG_CACHE_HOME:-~/.cache}/skill-creator-rick/antseer-components` 的模块结构、组件 API、K 线 / marker / event rail / source footer 示例。
- 不把组件库 checkout、`.git`、`node_modules` 或 demo/fixture 数据复制进本 Skill 发布包。
- 如果 GitHub 不可达，只能使用已有外部缓存，并在 S3 记录缓存 commit。

### Step 1:查 visual-registry

```
1. 执行 scripts/sync_antseer_components.sh,记录外部缓存 commit
2. 读 design-system/visual-registry.md
3. 看已登记 Skill 的主色/Display 字体/Hero 类型
4. 在 design-system/color-pool.md 里选未被占用的主色
5. 在 design-system/display-font-pool.md 里选未被占用的字体
6. 选一个与已有 Skill 不同的 Hero 类型(军师/编辑部/实验室/控制台/仪表盘/...)
```

### Step 2:登记本 Skill 条目

在 `design-system/visual-registry.md` 追加一行:

```markdown
| Skill 名称 | 主色 | 次色 | Display 字体 | Hero 类型 | 气质关键词 |
|---|---|---|---|---|---|
| {skill-name} | #XXXXXX | #YYYYYY | Space Grotesk | 控制台 | 冷静 · 精准 · 数据驱动 |
```

**登记完才能开工。** 画完再登记 = 门禁不过。

---

## §2 HTML 实现要求

### 2.1 技术约束

- 单个 HTML 文件(CSS + JS 内联)
- React 可通过 CDN 引入(可选)
- 图表用 D3 / Recharts / Plotly 任选
- **禁止** localStorage / sessionStorage,用内存状态
- 底部标注 `demo-v1 · Powered by Antseer.ai`

### 2.2 规范达标

**全部颜色/间距/字号/圆角必须引用 design-system 的 tokens,禁止硬编码**:
- 颜色:从 `antseer-design-system.md` 的色彩体系 + 本 Skill 登记的主色
- 字号/行高/间距:从设计规范的 scale
- 圆角:从设计规范的 radius scale
- 阴影:从设计规范的 elevation scale

### 2.3 状态完整

每个组件至少画三态(happy / loading / empty),并展示:
- **Hover 态**:按钮、卡片、图表数据点
- **Active 态**:选中、展开
- **Error 态**:数据源失败、超时
- **加载态**:骨架屏或 spinner

### 2.4 响应式

至少两个断点:
- 桌面(≥ 1280px)
- 移动(≤ 480px)

### 2.5 数据契约对齐

HTML 里每个动态字段必须对应 PRD 附录 A 中的某个 D 编号:
```html
<!-- 数据点 D30:概率时序 -->
<div id="prob-chart" data-binding="D30"></div>
```
(不强制加 `data-binding` 属性,但心里要有这个映射,S4 会 review)

### 2.6 金字塔信息架构

Hero 必须有结论(3 秒内可理解),不允许只放输入表单。
中间可视化每个都要支撑 Hero 的结论。
信任层放方法 + 风险 + 原始数据(可折叠)。

---

## §3 执行步骤总览

```
1. 执行 scripts/sync_antseer_components.sh,记录 antseer-components 外部缓存 commit
2. 读 references/antseer-components-standard.md
3. 读 design-system/antseer-design-system.md
4. 读 design-system/visual-registry.md,选未占主色 + 字体 + Hero 类型
5. 在 visual-registry.md 登记本 Skill(先登记后画)
6. 读 skill-prd.md,列出所有 L5 组件清单
7. 按金字塔搭骨架:Hero → 中间可视化 → 信任层
8. 按 PRD 附录 A 的字段 schema 做 mock 数据(用真实感的假数据)
9. 每个组件实现 3+ 状态(happy/loading/empty/error/hover)
10. 实现响应式(桌面 + 移动)
11. 至少实现一个完整交互链路(输入 → 切换 → 重渲染)
12. 检查 token 引用,全部颜色/字号/间距无硬编码
13. 执行 G3 门禁
```

## §4 产出物

| 文件 | 内容 |
|------|------|
| `demo-v1.html` | 高保真 HTML,对齐 PRD,状态完整,响应式 |
| `design-system/visual-registry.md` | 新增本 Skill 条目 |

## §5 质量门 → `quality/G3_html_design.md`

## §6 常见错误

| 错误 | 纠正 |
|------|------|
| 画完再登记 visual-registry | 必须开工前登记,门禁会查顺序 |
| 主色与某已登记 Skill 过近 | 看色池选距离更远的色,或调整饱和度/明度 |
| 颜色/字号硬编码 | 全部改用 CSS 变量,引 tokens |
| 只画 happy path | 每个组件补 loading / empty,至少 Hero + 主图表补 error 态 |
| 没有响应式 | 至少补一个 ≤ 480px 的断点样式 |
| 前端自造数据(PRD 里没有的字段) | 删掉或回 S2 补 PRD |
| 少了 PRD 某个 L5 组件 | 要么补上,要么在 PRD 明确标"v2 延期" |
| lorem ipsum 或占位图 | 替换为基于 PRD 附录 A 的真实感 mock |
