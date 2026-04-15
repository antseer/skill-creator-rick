# DualYield v2 — 产品需求文档 (PRD)

> 版本: 2.1.0 | 最后更新: 2026-04-10
> Pipeline: L1(数据获取) → L2(计算评分) → L3(结论生成) → L4(渲染)

---

## 一、产品概述

### 1.1 定位
双币投助手。帮用户在多家交易所中找到「高收益且大概率不会被行权」的档位。核心体验是**降低认知负担**——用户不需要理解波动率和概率模型，只需选择意图和风险偏好，系统给出推荐 + 一句话结论 + 技术面佐证 + 全量档位供自行比较。

底层设计思路是「为用户出谋划策」：不是罗列数据让用户自己看，而是先给结论、再给证据、最后给原始数据。但这个设计理念体现在信息架构和排版逻辑上，**不体现在文案风格上**——前端语言保持工具化、克制、专业。

### 1.2 用户画像
- **主要**: 有闲置 BTC/ETH/USDT，想赚取高于活期的利率，不希望被行权
- **次要**: 有目标入场/出场价的交易者，用双币投锁定价位同时赚利率

### 1.3 核心指标
| 指标 | 目标 |
|---|---|
| 推荐准确率 (TOP 1 未触达) | ≥ 85% (保守档) |
| 端到端响应时间 | ≤ 3s (模板模式) |
| 平台覆盖 | ≥ 5 CEX |

---

## 二、L1 数据层

### 2.1 数据源

| # | 来源 | 端点 | 刷新 | 认证 |
|---|---|---|---|---|
| 1 | **Antseer** 产品 | `GET /api/v1/dci/products` | 5min | API Key |
| 2 | **Antseer** 市场 | `GET /api/v1/market/{underlying}` | 1min | API Key |
| 3 | Binance DCI | `GET /sapi/v1/dci/product/list` | 5min | HMAC |
| 4 | OKX 双币赢 | `POST /api/v5/finance/staking-defi/` | 5min | HMAC |
| 5 | Bybit DCI | `GET /v5/earn/dual-investment/product/list` | 5min | HMAC |
| 6 | Bitget 鲨鱼鳍 | `GET /api/v2/earn/sharkfin/product-list` | 5min | HMAC |
| 7 | KuCoin DCI | `GET /api/v1/earn/dci/products` | 5min | HMAC |
| 8 | Deribit IV | `GET /api/v2/public/get_book_summary_by_currency` | 1min | 公开 |
| 9 | Binance K线 | `GET /api/v3/klines` | 1min | 公开 |

### 2.2 统一 Schema

```python
product = {
    "platform": str,       # "Binance" / "OKX" / ...
    "side": str,           # "buy" (低买) / "sell" (高卖)
    "strike": int,         # 执行价 USD, 取整到百
    "duration": int,       # 天
    "apr": float,          # 百分比数值 e.g. 18.5
    "prob": float,         # 到达概率 0~1
    "distance": float,     # 距现价 % (正数)
    "minAmt": int,         # 最低投入 USDT
    "autoCompound": bool,  # 复投
    "earlyExit": bool,     # 提前赎回
    "settlement": str,     # 结算时间 "T+0" / "T+1"
    "fee": str,            # 手续费 "无" / "0.1%"
}
```

### 2.3 降级: Antseer → 直连 → Redis(TTL 10min) → 报错

---

## 三、L2 计算层

### 3.1 Pipeline 步骤

```
raw_products
  │
  ├─ filter: side (yield→sell, buy→buy, sell→sell)
  ├─ filter: duration in 用户选择
  ├─ enrich: 计算 touch_prob
  ├─ filter: prob ≤ risk_cap
  ├─ score: 评分排序
  ├─ group: 按 strike+duration+side 分组
  ├─ sort_within_group: 组内按 APR 降序
  ├─ select_top3: 去重后取前 3
  └─ sort_groups: 按用户选择的排序模式
```

### 3.2 到达概率

**公式** (无漂移 GBM 首次通过时间):
```
P(touch) = 2 × (1 - Φ(d))
d = |ln(K/S)| / (σ × √(T/365))
```
- S = 现货价, K = 执行价, σ = 年化波动率, T = 天数
- σ 优先取 Deribit IV，fallback 取 180 天历史波动率

**边界**: S=K → 1.0; σ=0 或 T=0 → 0.0

### 3.3 评分函数

```
score = apr × 0.60                    # 收益权重
      + (1 - prob) × 30 × 0.30       # 安全度: prob 越低分越高
      + tier_bonus × 100              # 平台可信度加分
```

**tier_bonus**: Binance 0.10, OKX 0.08, Bybit 0.06, Bitget 0.04, KuCoin 0.03

### 3.4 风险过滤

| 档位 | prob 上限 |
|---|---|
| 保守 | ≤ 5% |
| 平衡 | ≤ 15% |
| 激进 | ≤ 30% |

### 3.5 安全度标签

| 距现价 | 标签 | 颜色 |
|---|---|---|
| > 13% | 安全 | 绿 `#22c55e` |
| 6~13% | 适中 | 黄 `#eab308` |
| < 6% | 激进 | 橙 `#f97316` |

### 3.6 排序模式 (用户可切换)

| 模式 | 规则 |
|---|---|
| APR ↓ | 组最高 APR 降序 |
| 安全度 ↓ | 距现价绝对值降序 |
| 目标价 | buy→strike 升序; sell→strike 降序 |
| 期限 | duration 升序 |

### 3.7 TOP 3 去重
同一 `strike-duration` 只取一个（避免三个推荐都是同档不同平台）。

---

## 四、L3 结论生成

### 4.1 模板模式 (v2 默认)

不需要 LLM。由模板函数直接拼接：

```
在{风险档位}策略下（到达概率 ≤ {上限}），{平台} 的 ${执行价} 档位
表现最优：年化 {APR}%，{期限}天内触达概率仅 {prob}%。
该价位{高于/低于}当前价 {distance}%。
```

字段着色:
- 平台名 → `<strong>`
- 执行价 → 蓝色 (hl-blue)
- APR → 绿色 (hl-green)
- 概率 → 黄色 (hl-yellow)

### 4.2 LLM 增强 (P2 可选)

后续可接入 Claude Sonnet 生成:
- 加入 TA 解读 ("当前 RSI 42 偏中性，MA20 下方...")
- 对比前一期推荐变化
- 但 v2 模板已足够，不阻塞上线

---

## 五、L4 渲染层

### 5.1 视觉规范

| 属性 | 值 |
|---|---|
| 背景 | `#0c0e14` |
| Surface | `#13161f` |
| Surface2 | `#1a1e2a` |
| 边框 | `#2a2f3e` |
| Accent | `#3b82f6` |
| 正文字体 | DM Sans |
| 数字字体 | JetBrains Mono |

### 5.2 组件清单

| 组件 | 数据来源 | 关键字段 |
|---|---|---|
| 左侧参数面板 (272px) | 用户输入 | coin, intent, principal, durations, risk |
| TOP 3 推荐卡 (3列grid) | top3[] | platform, strike, distance, duration, apr, prob |
| Conclusion Bar | top1 + risk | 模板拼接 |
| K 线图 (Canvas) | klines[] + SR + top3 strikes | 日线蜡烛+MA20/60+SR+MACD+推荐价标注 |
| TA Sidebar (260px, 3 卡) | TA 指标 | MA/RSI/MACD/Vol + SR levels + 市场状态 |
| 全部档位列表 | grouped products | 分组行 + 可展开详情 |
| 展开行 — 到达概率 | group[0].prob | 组级别显示一次（概率条+波动率说明） |
| 展开行 — 场景模拟 | group[0] (最佳平台) | 未触达/触达计算 |
| 展开行 — 平台条件对比 | group members | 平台/APR/最低投入/复投/提前赎回/结算/手续费 |
| 风险提示 | 固定文案 | — |

### 5.3 TOP 3 卡详细规格

```
┌──────────────────────────────┐
│ ★ BEST (或 #2/#3)            │  ← 浮动标签
│ Binance            高卖 ▌    │  ← 平台 + 方向标签
│ $87,100   ↑3.0%             │  ← 执行价(mono 20px) + 距现价
│ 1天                          │
│ ─────────────────────        │
│ 年化      到达概率    预期收益│
│ 18.5%    2.3%       $5.07   │
└──────────────────────────────┘
```

**BEST**: border=accent, 标签背景=accent
**概率颜色**: <5% 绿, 5-15% 黄, ≥15% 橙
**预期收益**: `principal × apr/100 × duration/365`

### 5.4 展开行详细规格

展开行自上而下分三个区域:

**① 到达概率 (组级别, 显示一次)**

```
┌─────────────────────────────────────────────────────┐
│ 到达概率  56.7%  ████████████░░░░  基于 58% 年化波动率 · 3天 │
└─────────────────────────────────────────────────────┘
```

- 概率颜色: <5% 绿, 5-15% 黄, ≥15% 橙
- 同一 strike+duration 所有平台概率相同（仅取决于现价/波动率/时间），所以只显示一次
- 右侧标注波动率来源和期限

**② 场景模拟** (2 列 grid, 按最佳平台 APR 计算):

| 未触达 | 触达 |
|---|---|
| ✅ BTC > $strike | ⚠ BTC ≤ $strike |
| 拿回原币种 + 利息 | 本金+利息按目标价转换 |
| **10,050.68** USDT | **0.115432** BTC |
| 本金 10,000 + 利息 50.68（按最佳平台 18.5% 计算） | 以 $strike 买入 BTC |

**③ 各平台条件对比**

| 平台 | APR | 最低投入 | 复投 | 提前赎回 | 结算 | 手续费 |
|---|---|---|---|---|---|---|
| 👑 Binance | **18.5%** | 100 USDT | ✅ | ✅ | T+0 | 无 |
| OKX | 17.2% | 200 USDT | ✅ | ✅ | T+0 | 无 |
| Bybit | 16.8% | 200 USDT | — | 不支持 | T+1 | 无 |

**设计原则**: 只展示平台间真正有差异的信息。到达概率和预估收益（可从 APR 直接推算）不在此表中重复。

**各字段说明**:
| 字段 | 含义 | 数据来源 |
|---|---|---|
| APR | 该平台对此档位的年化收益 | 平台 API |
| 最低投入 | 起投门槛 | 平台 API |
| 复投 | 到期后是否自动续投 | 平台 API / 元数据 |
| 提前赎回 | 锁仓期内能否提前退出 | 平台 API / 元数据 |
| 结算 | 到期后多久到账 (T+0 / T+1) | 平台元数据 |
| 手续费 | 买入或结算时的额外费用 | 平台元数据 |

### 5.5 平台视觉标识

| 平台 | 缩写 | 色 | icon样式 |
|---|---|---|---|
| Binance | Bn | `#F0B90B` | 24px 圆角方块, 色15%底+色字 |
| OKX | OK | `#FFFFFF` | 同上 |
| Bybit | By | `#F7A600` | 同上 |
| Bitget | Bg | `#00D395` | 同上 |
| KuCoin | KC | `#23AF91` | 同上 |

---

## 六、边界条件

| # | 场景 | 处理 |
|---|---|---|
| 1 | 未选期限 | 默认 [1,3] |
| 2 | 筛选后无产品 | empty state + 建议放宽 |
| 3 | TOP 3 不足 | 有几个显示几个 |
| 4 | 档位仅 1 平台 | 对比表 1 行 |
| 5 | K 线不足 | chart 显示提示 |
| 6 | 全部数据源失败 | "数据获取失败" |

---

## 七、数据需求 (给 Antseer)

| 端点 | 说明 | 优先级 |
|---|---|---|
| `GET /dci/products?underlyings=BTC,ETH` | 5 家 CEX 产品聚合 | P0 |
| `GET /market/{underlying}?candles=1d&days=180` | K 线 | P0 |
| `GET /market/{underlying}/price` | 现货价 | P0 |
| `GET /iv/chain?underlying=BTC` | Deribit IV | P1 |

---

## 八、验收标准

| # | 标准 |
|---|---|
| 1 | L2 单测全过 |
| 2 | touch_prob 手算校验通过 |
| 3 | TOP 3 卡 3 秒可读 |
| 4 | 展开行收益计算正确 |
| 5 | 排序切换 < 100ms |
| 6 | 风险提示始终可见 |
