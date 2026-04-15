# DualYield — 技术入门指南

> 10 分钟读完，知道代码在哪、怎么跑、怎么改。

---

## 1. 这是什么

双币投产品推荐助手。用户选意图+风险 → 系统从 5+ 家交易所抓产品 → 算出哪些档位「高收益+低风险」→ 推荐 TOP 3 + 一句话结论 + K 线佐证 + 全量列表。

## 2. 架构

```
用户点击「开始分析」
  → L1: 获取 5 家 CEX 产品 + K 线
  → L2: 计算 touch_prob → 评分 → 分组 → 排序 → TOP 3
  → L3: 模板生成一句话结论
  → L4: 渲染 (HTML/Canvas)
```

## 3. 目录

```
dualyield/
├── SKILL.md                          # 入口
├── implementation/pipeline/
│   ├── orchestrator.py               # 编排 L1→L2→L3
│   ├── l1_data/sources/              # ⬜ 数据源 (需要填)
│   ├── l2_compute/compute.py         # ✅ 核心算法
│   └── l3_decision/decision.py       # ✅ 模板结论
├── implementation/data/platform_meta.yaml           # ✅ 平台元数据
├── implementation/frontend/dualyield.html           # ✅ 完整前端 (mock 数据)
├── tests/test_l2.py                  # ✅ 32 测试全过
└── docs/
    ├── PRD.md                        # ✅ 完整 PRD
    ├── docs/handoff/TODO-TECH.md                  # ✅ 待办清单
    └── TECH-ONBOARDING.md            # ← 这个文件
```

## 4. 跑测试

```bash
cd dualyield
python -m unittest implementation.tests.test_l2 -v
# Ran 32 tests ... OK
```

## 5. 核心算法

**到达概率**: `P = 2×(1-Φ(|ln(K/S)|/(σ√(T/365))))`
- 远 → 低概率 → 安全但 APR 低; 近 → 高概率 → APR 高但可能被行权

**评分**: `score = apr×0.6 + 安全度×0.3 + 平台加分×0.1`

**风险过滤**: 保守≤5%, 平衡≤15%, 激进≤30%

## 6. 快速上手

1. **确认 Antseer 端点** → 填 `sources/antseer.py`
2. **Binance API Key** → 填 `sources/binance.py`
3. **前端集成** → 把 mock 替换为 orchestrator 输出

## 7. 怎么加交易所

1. `sources/` 下新建文件
2. 实现 `fetch_xxx_dci()` → 返回统一 schema 列表
3. `fetcher.py` fallback 列表加一行
4. `platform_meta.yaml` 加元数据
5. 前端 `PM` 对象加平台颜色和缩写

## 8. 前端技术栈

- 纯 HTML/CSS/JS，无框架依赖
- 字体: DM Sans + JetBrains Mono (Google Fonts CDN)
- K 线图: Canvas 2D (无 D3)
- 交互: 原生 DOM 操作
