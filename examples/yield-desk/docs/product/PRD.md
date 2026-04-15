# Yield Desk v2 · 完整产品技术 PRD
## 稳定币收益决策台 — 4 层 Pipeline 全链路规范

> 版本 2.0 · 2026-04-10
> 产品代号 `yield-desk` · Skill 包编号 TBD

---

# 目录

- 〇、架构总览：4 层 Pipeline
- 一、L1 数据层 — 从哪获取、接哪些口
- 二、L2 计算层 — 结构化加工与多维评分
- 三、L3 决策层 — 大模型推理与金字塔输出
- 四、L4 渲染层 — 前端容器与数据灌注
- 五、Pipeline 编排 — Skill 执行流程
- 六、边界情况与异常处理
- 七、Skill 包最终产物清单

---

# 〇、架构总览：4 层 Pipeline

```
┌───────────────────────────────────────────────────────────────────────┐
│                        Yield Desk Skill Pipeline                      │
├───────────┬──────────────┬──────────────┬────────────────────────────┤
│  L1 数据层 │  L2 计算层    │  L3 决策层    │  L4 渲染层                  │
│  (API/MCP) │  (固定脚本)   │  (LLM Skill)  │  (前端容器)                │
├───────────┼──────────────┼──────────────┼────────────────────────────┤
│           │              │              │                            │
│ Antseer → │              │              │                            │
│ DefiLlama │  normalize() │              │  ┌─ Hero 大卡               │
│ Binance   │  ↓            │  LLM 读取    │  ├─ Ranking 列表            │
│ OKX       │  score()     │  结构化数据   │  ├─ Radar 对比              │
│ Bybit     │  ↓            │  ↓            │  ├─ Trust 信任层            │
│ Bitget    │  rank()      │  生成军师叙事 │  └─ Footer                 │
│ KuCoin    │  ↓            │  + 推荐理由   │                            │
│ Gate      │  detect_     │  + 机会成本   │  数据灌注:                  │
│ HTX       │  anomaly()   │  + 风险提醒   │  scored_products → rows    │
│ CryptoQ   │              │              │  decision_output → hero     │
│           │  → scored_   │  → decision_ │  → rendered HTML            │
│           │    products  │    output    │                            │
└───────────┴──────────────┴──────────────┴────────────────────────────┘

执行顺序: L1 → L2 → L3 → L4 (严格串行，每层输入=前层输出)
```

---

# 一、L1 数据层 — 从哪获取、接哪些口

## 1.1 数据源总表

| # | 数据源 | 类型 | 接入方式 | 覆盖范围 | 刷新频率 | 延迟 | 认证 | 状态 |
|---|--------|------|----------|----------|----------|------|------|------|
| D1 | **Antseer MCP / API** | 聚合层 | MCP Server 或 REST | 统一聚合下游 | 依赖配置 | <5s | API Key | **主通道** |
| D2 | **DefiLlama Yields** | DeFi 收益池 | REST `GET /yields/pools` | 12K+ 池, 539 协议, 118 链 | ~10 min | <30s | Pro Key (推荐) | 已验证 |
| D3 | **DefiLlama Yields History** | 历史时序 | REST `GET /yields/chart/{pool}` | 同上单池历史 | 按需 | <2s | Pro Key | 已验证 |
| D4 | **DefiLlama Protocol** | 协议元数据 | REST `GET /protocol/{slug}` | 协议描述/TVL/链 | ~30 min | <1s | 免费 | 已验证 |
| D5 | **Binance Simple Earn** | CEX 理财 | REST `GET /sapi/v1/simple-earn/flexible/list` + `/locked/list` | Flexible + Locked 全产品 | ~5 min | <1s | HMAC Key | 已验证 |
| D6 | **OKX Finance** | CEX 理财 | REST `GET /api/v5/finance/savings/lending-rate-summary` + `/staking-defi/offers` | Savings + Staking | ~5 min | <1s | API Key | 已验证 |
| D7 | **Bybit Earn** | CEX 理财 | REST `GET /v5/earn/product/list` | Savings + Fixed | ~10 min | <1s | API Key | 需确认 |
| D8 | **Bitget Earn** | CEX 理财 | REST `GET /api/v2/earn/savings/product` | 活期+定期 | ~10 min | <1s | API Key | 需确认 |
| D9 | **KuCoin Earn** | CEX 理财 | REST `GET /api/v3/earn/saving/products` | Lending | ~10 min | <1s | API Key | 需确认 |
| D10 | **Gate.io Earn** | CEX 理财 | REST `GET /api/v4/earn/uni/lends` | Uni Lending | ~10 min | <1s | API Key V4 | 需确认 |
| D11 | **HTX (Huobi) Earn** | CEX 理财 | REST `GET /v2/earn/products` | 活期+定期 | ~10 min | <1s | API Key | 需确认 |
| D12 | **CryptoQuant PoR** | CEX 储备金 | REST / 爬虫 | BTC/ETH/USDT 余额 | ~24 h | <1 min | API Key | 辅助 |
| D13 | **CoinGecko** | 现货价格 | REST `GET /api/v3/simple/price` | 全币种 | ~1 min | <2s | 免费/Pro | 辅助 |
| D14 | **DeFiSafety** | 审计评分 | REST / 爬虫 | 头部 DeFi 协议 | ~7 d | N/A | 免费 | 辅助 |

## 1.2 优先级与降级策略

```
Primary Path (最优):
  Antseer MCP → 一次调用拿到所有 CEX + DeFi 聚合后的标准化数据
  如果 Antseer 已封装了上述 D2-D11，Skill 只需调 Antseer 一个入口

Fallback Path (Antseer 不可用或不完整时):
  DeFi 数据: DefiLlama Yields API 直连
  CEX 数据: 各交易所 Earn API 并发直连
  安全数据: CryptoQuant + DeFiSafety 补充

降级规则:
  - 若某 CEX API 超时 (>10s)，跳过该平台，在输出中标注 "⚠ {平台} 数据暂不可用"
  - 若 DefiLlama 返回 429 (限流)，使用本地缓存 (最长 30 min 前数据)
  - 若所有 DeFi 源失败，仅展示 CEX 数据 + 提示 "DeFi 数据暂时无法获取"
  - 若所有 CEX 源失败，仅展示 DeFi 数据 + 提示
```

## 1.3 各接口字段映射

### 1.3.1 DefiLlama `/yields/pools` 响应 → 内部 Schema

| DefiLlama 字段 | 内部字段 | 类型 | 说明 |
|---|---|---|---|
| `pool` | `source_id` | string | UUID, 用于查历史 |
| `chain` | `chain` | string | "Ethereum" / "Arbitrum" |
| `project` | `platform_slug` | string | "aave-v3" / "compound-v3" |
| `symbol` | `asset_symbol` | string | "USDC" / "USDT" |
| `tvlUsd` | `tvl_usd` | float | 池 TVL |
| `apy` | `apy_total` | float | 总 APY = base + reward |
| `apyBase` | `apy_base` | float | 基础 APY (无代币奖励) |
| `apyReward` | `apy_reward` | float | 代币激励部分 |
| `rewardTokens` | `reward_tokens` | list | 奖励代币地址 |
| `exposure` | `exposure` | string | "single" / "multi" |
| `apyBase7d` | `apy_base_7d` | float | 7 日均值 |
| `poolMeta` | `pool_meta` | string | "Lending" / "LP" 等 |
| `stablecoin` | `is_stablecoin` | bool | 是否稳定币池 |

### 1.3.2 Binance Simple Earn → 内部 Schema

| Binance 字段 | 内部字段 | 类型 | 说明 |
|---|---|---|---|
| `asset` | `asset_symbol` | string | |
| `latestAnnualPercentageRate` | `apy_total` | float | 活期用此字段 |
| `tierAnnualPercentageRate` | `apr_tiers` | dict | 阶梯利率 — 关键! |
| `canPurchase` | `available` | bool | 是否可申购 |
| `isSoldOut` | `is_sold_out` | bool | |
| `minPurchaseAmount` | `min_amount` | float | |
| `productId` | `source_id` | string | |
| 定期追加字段: `detail.duration` | `lock_days` | int | |
| 定期追加字段: `detail.apr` | `apy_total` | float | |
| 定期追加字段: `quota.totalPersonalQuota` | `max_per_user` | float | |

### 1.3.3 OKX Finance → 内部 Schema

| OKX 字段 | 内部字段 | 说明 |
|---|---|---|
| `ccy` | `asset_symbol` | |
| `rate` | `apy_total` | 需 ×100 转为百分比 |
| `productType` | `product_type` | 映射: "savings" → "flexible", "staking" → "locked" |
| `term` | `lock_days` | 0=活期 |
| `minAmt` | `min_amount` | |

> 其他交易所 (Bybit / Bitget / KuCoin / Gate / HTX) 的字段映射结构相似，
> 需在 Antseer 聚合层做统一标准化，输出统一 Schema（见 §1.4）。

## 1.4 L1 输出 Schema: `RawProduct[]`

这是 L1 交给 L2 的统一数据结构。每个元素代表一个可投资产品。

```typescript
interface RawProduct {
  // ── 身份 ──
  source_id: string;          // 来源方内部 ID (UUID / productId)
  venue: "CEX" | "DeFi";
  platform_slug: string;      // "binance" / "aave-v3" / ...
  platform_name: string;      // 展示名
  product_name: string;       // "Flexible USDC" / "USDC Supply"
  asset_symbol: string;       // "USDT" / "USDC" / "DAI"
  chain: string | null;       // DeFi 有, CEX 为 null

  // ── 收益 (L1 原始) ──
  apy_total: number;          // 总 APY %
  apy_base: number | null;    // 基础
  apy_reward: number | null;  // 奖励
  reward_tokens: string[];
  apy_base_7d: number | null;
  apr_tiers: Record<string, number> | null;  // Binance 阶梯

  // ── 产品属性 ──
  product_type: "flexible" | "locked" | "structured";
  lock_days: number;          // 0 = 活期
  min_amount: number;
  max_per_user: number | null;
  is_sold_out: boolean;
  available: boolean;

  // ── 规模 ──
  tvl_usd: number;
  remaining_capacity: number | null;  // CEX 定期限额 - 已售

  // ── 安全 (L1 能拿到的) ──
  pool_meta: string | null;   // "Lending" / "LP" / "RWA"
  exposure: string | null;    // "single" / "multi"
  is_stablecoin: boolean;

  // ── 元数据 ──
  source_api: string;         // "defillama" / "binance" / ...
  fetched_at: string;         // ISO timestamp
  raw_json: object;           // 信任层展示用
}
```

## 1.5 给 Antseer 的数据需求清单

如果 Antseer 作为聚合层，需要提供：

### 已有（确认可用）
- [ ] DefiLlama Yields 全量池数据（周期刷新）
- [ ] CoinGecko / CMC 现货价格

### 需要新增
- [ ] **CEX Earn 聚合端点**：`GET /api/v1/earn/products?venue=all&asset=USDT,USDC,DAI,FDUSD`
  - 返回 Binance / OKX / Bybit / Bitget / KuCoin / Gate / HTX 全部活期+定期产品
  - 按上面 RawProduct Schema 统一标准化
  - 包含阶梯利率、剩余容量、是否售罄
  - 刷新频率 ≤ 5 min

- [ ] **CEX 安全元数据**：`GET /api/v1/cex/safety-meta`
  - 返回每家 CEX 的 tier 等级、PoR 最近时间戳、审计机构列表、历史安全事件
  - 刷新频率 ≤ 24 h（人工 + 自动混合维护）

- [ ] **DeFi 协议安全元数据**：`GET /api/v1/defi/safety-meta`
  - 返回每个协议的审计列表（审计公司 + 报告 URL）、保险覆盖、合约可升级性、历史黑客事件
  - 刷新频率 ≤ 24 h

- [ ] **单池历史 APY 时序**：`GET /api/v1/yield/history?pool_id=xxx&days=30`
  - 用于 L2 计算 30 日均值、标准差、趋势
  - 每日一个数据点即可

- [ ] **DefiLlama MCP Server**（如果走 MCP 通道）
  - DefiLlama 官方已有 MCP Server：https://defillama.com/subscription
  - Antseer 可直接接入

---

# 二、L2 计算层 — 结构化加工与多维评分

L2 是 **纯算法层**，输入 `RawProduct[]`，输出 `ScoredProduct[]`。
所有计算都是确定性的（给同样的输入一定给同样的输出），**不调 LLM**。

## 2.1 步骤概览

```
RawProduct[]
  │
  ├── Step 1: 过滤 (Filter)
  ├── Step 2: 补全 (Enrich)
  ├── Step 3: 计算派生字段 (Derive)
  ├── Step 4: 归一化 (Normalize)
  ├── Step 5: 多维评分 (Score)
  ├── Step 6: 排序 (Rank)
  └── Step 7: 异常检测 (AnomalyDetect)
  │
  ▼
ScoredProduct[]
```

## 2.2 Step 1: 过滤 — `filter(raw[], ctx)`

输入：`RawProduct[]` + 用户参数 `UserContext`

```python
def filter(products: list[RawProduct], ctx: UserContext) -> list[RawProduct]:
    out = []
    for p in products:
        # ─ 基础过滤 ─
        if not p.available or p.is_sold_out:
            continue
        if p.apy_total <= 0 or p.apy_total > 200:  # APY 异常值
            continue

        # ─ 资产过滤 ─
        if p.asset_symbol not in ctx.assets:
            continue

        # ─ Venue 过滤 ─
        if p.venue not in ctx.venues:
            continue

        # ─ 便利性过滤 ─
        if ctx.conv_priority == "flex" and p.lock_days > 0:
            continue
        if ctx.conv_priority == "balanced" and p.lock_days > 30:
            continue
        # conv_priority == "any" 不过滤

        # ─ 安全过滤 ─
        # 在 Step 2 补全 tier 后才能执行, 这里先标记
        # (详见 §2.8 边界处理)

        # ─ KYC 过滤 ─
        # CEX 产品 kyc_level 来自安全元数据
        # ctx.kyc == "none" 且 p.kyc_level > 0 → 跳过

        # ─ 曝露类型 ─
        if p.exposure == "multi":  # 仅保留单资产曝露
            continue

        out.append(p)
    return out
```

**边界情况**：
- `apy_total > 200%`：视为异常数据或高风险代币激励池，直接过滤
- `tvl_usd < 100_000`：DeFi 池 TVL 过低，流动性风险大，过滤
- CEX 产品无 `tvl_usd` 字段：不按 TVL 过滤，CEX 以 tier 和 capacity 判断
- 用户未选任何 venue：默认两个都选
- 用户未选任何资产：默认 USDT + USDC

## 2.3 Step 2: 补全 — `enrich(products[])`

从安全元数据库（Antseer `/safety-meta` 或本地 YAML）补全以下字段：

```python
@dataclass
class PlatformMeta:
    tier: int                      # 1 / 2 / 3
    audits: list[dict]             # [{firm, date, url}]
    has_insurance: bool
    has_por: bool
    last_por_at: str | None
    incident_history: list[dict]   # [{date, desc, severity}]
    kyc_level: int                 # 0=免KYC, 1=基础, 2=高级
    restricted_regions: list[str]
    contract_upgradeable: bool | None  # DeFi only
    multisig_signers: int | None       # DeFi only
    site_url: str
    yield_source: str              # "lending" / "lp" / "rwa" / "structured" / "delta-neutral" / "staking"
    redeem_delay_hours: float      # CEX 活期 ~0.1h, DeFi ~0.05h, 定期=到期
    fees: dict                     # {subscribe: "0", redeem: "0", mgmt: "0", gas_est: "$3"}

# 维护方式: 静态 YAML + Antseer 自动更新覆盖
# 新协议/平台默认 tier=3, kyc_level=0, has_insurance=false
```

**平台 Tier 分级标准**：

| Tier | CEX 标准 | DeFi 标准 |
|---|---|---|
| 1 | 日交易量 > $10B + PoR + 成立 > 3 年 + 无重大安全事件 | TVL > $1B + 2+ 顶级审计 + 成立 > 2 年 + 无被黑事件 |
| 2 | 日交易量 > $1B + PoR 或 成立 > 2 年 | TVL > $100M + 1+ 审计 + 成立 > 1 年 |
| 3 | 其他 | 其他 |

**当前 Tier 分配**（初始化）：

```yaml
# CEX
binance:     { tier: 1, kyc: 1, por: true,  insurance: true }
okx:         { tier: 1, kyc: 1, por: true,  insurance: true }
bybit:       { tier: 1, kyc: 1, por: true,  insurance: false }
bitget:      { tier: 2, kyc: 1, por: true,  insurance: false }
kucoin:      { tier: 2, kyc: 0, por: true,  insurance: false }
gate:        { tier: 2, kyc: 1, por: true,  insurance: false }
htx:         { tier: 2, kyc: 1, por: false, insurance: false }

# DeFi
aave-v3:     { tier: 1, audits: [OpenZeppelin, Trail of Bits, Sigma Prime] }
compound-v3: { tier: 1, audits: [OpenZeppelin, ChainSecurity] }
morpho-blue: { tier: 1, audits: [Spearbit, Cantina] }
spark:       { tier: 1, audits: [ChainSecurity, Cantina] }
pendle:      { tier: 1, audits: [Ackee, WatchPug] }
curve:       { tier: 1, audits: [Trail of Bits, MixBytes] }
fluid:       { tier: 2, audits: [StateMind] }
ethena:      { tier: 2, audits: [Spearbit, Quantstamp] }
```

## 2.4 Step 3: 计算派生字段 — `derive(product)`

对每个产品计算以下 **派生字段**，这些字段 L1 原始数据中没有：

```python
def derive(p: EnrichedProduct, history: list[float] | None) -> DerivedProduct:
    # ── 30 日 APY 统计 ──
    # history 来自 DefiLlama /yields/chart/{pool} 或 Antseer 历史端点
    if history and len(history) >= 7:
        p.apy_30d_avg = mean(history[-30:]) if len(history) >= 30 else mean(history)
        p.apy_30d_std = stdev(history[-30:]) if len(history) >= 30 else stdev(history)
        p.apy_7d_trend = history[-1] - history[-7]  # 正=上升
    else:
        # 无历史: 用当前值近似
        p.apy_30d_avg = p.apy_total
        p.apy_30d_std = 0  # 保守假设: 稳定性未知 → 不给稳定性加分
        p.apy_7d_trend = 0

    # ── 收益稀释风险 ──
    # 如果总 APY 中有 reward 部分, 计算 "如果奖励代币归零还剩多少"
    if p.apy_reward and p.apy_reward > 0:
        p.apy_without_reward = p.apy_base or (p.apy_total - p.apy_reward)
        p.reward_dependency = p.apy_reward / p.apy_total
    else:
        p.apy_without_reward = p.apy_total
        p.reward_dependency = 0

    # ── APR 阶梯衰减 (CEX 特有) ──
    if p.apr_tiers:
        # 根据用户本金找到适用的阶梯
        applicable_rate = find_tier_rate(p.apr_tiers, ctx.amount)
        p.effective_apy = applicable_rate  # 覆盖 apy_total
    else:
        p.effective_apy = p.apy_total

    # ── 安全分计算 ──
    p.security_score = calc_security_score(p)

    # ── 便利性分计算 ──
    p.convenience_score = calc_convenience_score(p)

    return p
```

### 安全分计算公式 — `calc_security_score(p) → 0-100`

```python
def calc_security_score(p):
    score = 0

    # ─ 平台基础分 (最高 40 分) ─
    if p.venue == "CEX":
        tier_map = {1: 40, 2: 25, 3: 12}
        score += tier_map.get(p.tier, 12)
    else:  # DeFi
        tier_map = {1: 38, 2: 22, 3: 10}
        score += tier_map.get(p.tier, 10)

    # ─ 审计加分 (最高 25 分) ─
    n_audits = len(p.audits)
    score += min(n_audits * 8, 25)  # 每次审计 +8, 上限 25

    # ─ 储备金/保险 (最高 15 分) ─
    if p.has_por:
        score += 8
    if p.has_insurance:
        score += 7

    # ─ 历史安全记录 (扣分, 最多 -20) ─
    for incident in p.incident_history:
        sev = incident.get("severity", "low")
        penalty = {"critical": -20, "high": -12, "medium": -6, "low": -3}.get(sev, -3)
        score += penalty

    # ─ TVL/规模加分 (最高 10 分) ─
    if p.venue == "DeFi":
        if p.tvl_usd >= 5e9: score += 10
        elif p.tvl_usd >= 1e9: score += 8
        elif p.tvl_usd >= 1e8: score += 5
        elif p.tvl_usd >= 1e7: score += 2

    # ─ 合约可升级扣分 (DeFi, -5) ─
    if p.contract_upgradeable:
        score -= 5

    return max(0, min(100, score))
```

### 便利性分计算公式 — `calc_convenience_score(p) → 0-100`

```python
def calc_convenience_score(p):
    score = 0

    # ─ 产品类型 (最高 40 分) ─
    if p.product_type == "flexible" and p.lock_days == 0:
        score += 40
    elif p.lock_days <= 3:
        score += 32
    elif p.lock_days <= 7:
        score += 25
    elif p.lock_days <= 14:
        score += 18
    elif p.lock_days <= 30:
        score += 12
    elif p.lock_days <= 90:
        score += 6
    else:
        score += 2

    # ─ 赎回速度 (最高 25 分) ─
    if p.redeem_delay_hours <= 0.1:     # 近实时
        score += 25
    elif p.redeem_delay_hours <= 1:
        score += 20
    elif p.redeem_delay_hours <= 24:
        score += 12
    elif p.redeem_delay_hours <= 168:   # 7天
        score += 5
    else:
        score += 0

    # ─ KYC 门槛 (最高 15 分) ─
    kyc_score = {0: 15, 1: 10, 2: 3}
    score += kyc_score.get(p.kyc_level, 0)

    # ─ 最低门槛 (最高 10 分) ─
    if p.min_amount <= 1:
        score += 10
    elif p.min_amount <= 100:
        score += 7
    elif p.min_amount <= 1000:
        score += 3

    # ─ 手续费 (最高 10 分) ─
    total_fee = parse_fee_pct(p.fees)
    if total_fee <= 0:
        score += 10
    elif total_fee <= 0.1:
        score += 7
    elif total_fee <= 0.5:
        score += 3

    return max(0, min(100, score))
```

## 2.5 Step 4: 归一化 — `normalize(products[])`

将各维度映射到 [0, 1] 区间，用于加权求和。

```python
def normalize_dimension(value, dim_type):
    NORMS = {
        "apy":        (0, 15),    # 0-15% 映射到 0-1, >15% = 1
        "security":   (0, 100),
        "convenience": (0, 100),
        "stability":  (0, 100),   # 由 apy_30d_std / apy_30d_avg 计算后反转
        "capacity":   (0, 100),
    }
    lo, hi = NORMS[dim_type]
    return max(0, min(1, (value - lo) / (hi - lo)))
```

**稳定性分计算**：

```python
def stability_score(p):
    if p.apy_30d_avg <= 0:
        return 50  # 无数据, 中性
    cv = p.apy_30d_std / p.apy_30d_avg  # 变异系数
    # cv=0 → 100分, cv=0.5 → 50分, cv≥1 → 0分
    return max(0, min(100, round(100 * (1 - cv))))
```

**容量分计算**：

```python
def capacity_score(p, user_amount):
    if p.remaining_capacity is None or p.remaining_capacity == float('inf'):
        return 100  # 无限容量
    if p.remaining_capacity <= 0:
        return 0    # 已售罄 (应在 filter 阶段拦截)
    ratio = p.remaining_capacity / max(user_amount, 1)
    if ratio >= 10:
        return 100  # 容量充裕
    elif ratio >= 2:
        return 85
    elif ratio >= 1:
        return 65   # 刚好容得下
    else:
        return 30   # 容不下全额, 但可部分投入
```

## 2.6 Step 5: 多维评分 — `compute_score(p, ctx)`

```python
def compute_score(p, ctx):
    # 归一化各维度
    dims = {
        "apy":    normalize(p.effective_apy, "apy"),
        "sec":    normalize(p.security_score, "security"),
        "conv":   normalize(p.convenience_score, "convenience"),
        "cap":    normalize(capacity_score(p, ctx.amount), "capacity"),
        "stab":   normalize(stability_score(p), "stability"),
    }

    # 加权求和
    w = get_weights(ctx.sec_priority, ctx.conv_priority)
    total = sum(dims[k] * w[k] for k in dims)
    return round(total * 100)
```

### 权重矩阵 — 由用户的两个旋钮决定

| 用户设定 | apy | sec | conv | cap | stab |
|---|---|---|---|---|---|
| **默认 (平衡/平衡)** | 0.35 | 0.25 | 0.20 | 0.10 | 0.10 |
| 安全=严格, 便利=平衡 | 0.25 | **0.40** | 0.15 | 0.10 | 0.10 |
| 安全=宽松, 便利=平衡 | **0.45** | 0.15 | 0.20 | 0.10 | 0.10 |
| 安全=平衡, 便利=活期 | 0.30 | 0.25 | **0.25** | 0.10 | 0.10 |
| 安全=平衡, 便利=不限 | **0.40** | 0.25 | 0.15 | 0.10 | 0.10 |
| 安全=严格, 便利=活期 | 0.20 | **0.35** | **0.25** | 0.10 | 0.10 |
| 安全=宽松, 便利=不限 | **0.50** | 0.10 | 0.15 | 0.10 | 0.15 |

> 权重总和恒为 1.0。极端组合时（宽松+不限），APY 权重拉到 0.50，安全降到 0.10。

## 2.7 Step 6+7: 排序 + 异常检测

```python
def rank_and_detect(products):
    # 排序
    products.sort(key=lambda p: p.composite_score, reverse=True)
    for i, p in enumerate(products):
        p.rank = i + 1

    # 异常检测
    apys = [p.effective_apy for p in products]
    median_apy = sorted(apys)[len(apys) // 2]
    for p in products:
        p.anomaly_flags = []
        if p.effective_apy > median_apy * 3:
            p.anomaly_flags.append("APY_OUTLIER")
        if p.apy_7d_trend < -2:
            p.anomaly_flags.append("APY_DECLINING")
        if p.reward_dependency > 0.7:
            p.anomaly_flags.append("HIGH_REWARD_DEPENDENCY")
        if p.remaining_capacity and p.remaining_capacity < 1e6:
            p.anomaly_flags.append("LOW_CAPACITY")

    return products
```

## 2.8 L2 输出 Schema: `ScoredProduct[]`

```typescript
interface ScoredProduct extends RawProduct {
  // ── 补全字段 ──
  tier: number;
  audits: Audit[];
  has_insurance: boolean;
  has_por: boolean;
  kyc_level: number;
  yield_source: string;
  redeem_delay_hours: number;
  fees: FeeInfo;
  site_url: string;

  // ── 派生字段 ──
  apy_30d_avg: number;
  apy_30d_std: number;
  apy_7d_trend: number;
  apy_without_reward: number;
  reward_dependency: number;
  effective_apy: number;

  // ── 评分字段 ──
  security_score: number;       // 0-100
  convenience_score: number;    // 0-100
  stability_score: number;      // 0-100
  capacity_score: number;       // 0-100
  composite_score: number;      // 0-100 加权综合

  // ── 排名 ──
  rank: number;

  // ── 异常标记 ──
  anomaly_flags: string[];

  // ── 各维度归一化值 (给雷达图用) ──
  radar: {
    apy: number;    // 0-1
    sec: number;
    conv: number;
    cap: number;
    stab: number;
  };
}
```

---

# 三、L3 决策层 — 大模型推理与金字塔输出

## 3.1 定位

L3 是 **唯一调用 LLM 的层**。输入是 L2 的 `ScoredProduct[]` + `UserContext`，输出是给人读的结构化叙事。

LLM 在这里扮演 **军师 / 投资顾问**，而不是数据处理器。它的任务是：

1. 看完全部排名后，**用金字塔原理**先给结论（TOP 1 推荐 + 一句话理由）
2. 给出机会成本对比（TOP 1 vs 市场均值）
3. 对 TOP 2-3 说明"为什么不选它而选 TOP 1"
4. 如果存在异常标记，主动预警
5. 风险提醒（对称呈现上行和下行）

## 3.2 Decision Skill Prompt

```markdown
# System Prompt — Yield Desk Decision Layer

你是 Yield Desk 的「收益军师」，一个专业的稳定币理财顾问。
你的任务是根据结构化的评分数据，向用户推荐最优产品并解释原因。

## 你的输入
你将收到以下 JSON:
- `user_context`: 用户设定（资产/金额/安全偏好/便利偏好/KYC）
- `scored_products`: 已按综合分排序的产品列表（前 20 名）
- `market_stats`: 市场均值统计（avg_apy, median_apy, count）
- `weights_used`: 本次使用的权重

## 你的输出（严格 JSON，不含 markdown）
```json
{
  "headline": "一句话结论（<40字）",
  "top1_reason": "为什么 TOP 1 是最佳选择（80-120字，金字塔原理：结论→论据→数据）",
  "opportunity_cost": "机会成本提示：TOP1 比市场均值高多少",
  "top2_reason": "TOP 2 的差异点（50-80字）",
  "top3_reason": "TOP 3 的差异点（50-80字）",
  "risk_warning": "当前市场环境下的主要风险提醒（60-100字）",
  "anomaly_alerts": ["异常预警列表，无则空数组"],
  "brief_for_card": [
    {"product_id": "xxx", "one_liner": "一句话卡片文案（<30字）"}
  ]
}
```

## 写作原则

### 金字塔原理
- 先结论，后论据，再数据
- 不要铺垫，第一句就是答案
- 每段用 "因为... 所以..." 或 "虽然... 但是..." 保持逻辑链

### 风险对称
- 推荐了收益就必须说风险
- CEX 要说对手方风险
- DeFi 要说合约风险
- 高 APY 要说稀释风险

### 机会成本思维
- 不要单独夸 TOP 1 好，要和均值/次优对比
- "选它比选均值每年多赚 $X" 比 "它年化 Y%" 更有冲击力

### 异常检测叙事化
- 如果产品有 APY_OUTLIER 标记：点名说明为什么高到异常
- 如果有 APY_DECLINING：提醒用户趋势在下行
- 如果有 HIGH_REWARD_DEPENDENCY：提醒奖励代币价格风险

### 语言风格
- 专业但不晦涩
- 简体中文为主
- 关键数字用阿拉伯数字
- 不说 "我认为"，说 "数据表明" / "模型显示"
```

## 3.3 LLM 调用参数

| 参数 | 值 | 理由 |
|---|---|---|
| model | `claude-sonnet-4-20250514` | 速度与质量平衡 |
| max_tokens | 1000 | 输出上限约 500 中文字 |
| temperature | 0.3 | 偏确定性输出，避免编造数据 |
| top_p | 0.9 | |
| stop | 无 | |
| system | 上面的 Decision Skill Prompt | |
| messages | user: `{user_context, scored_products[:20], market_stats, weights_used}` | |

## 3.4 L3 输出 Schema: `DecisionOutput`

```typescript
interface DecisionOutput {
  headline: string;
  top1_reason: string;
  opportunity_cost: string;
  top2_reason: string;
  top3_reason: string;
  risk_warning: string;
  anomaly_alerts: string[];
  brief_for_card: Array<{
    product_id: string;
    one_liner: string;
  }>;
}
```

## 3.5 降级：LLM 不可用时

如果 LLM 调用超时或失败：

```python
def fallback_decision(scored_products, market_stats):
    top = scored_products[0]
    return {
        "headline": f"{top.platform_name} {top.product_name} 综合分最高 ({top.composite_score})",
        "top1_reason": f"在{len(scored_products)}个产品中排名第一，"
                       f"APY {top.effective_apy:.1f}%，安全分 {top.security_score}。",
        "opportunity_cost": f"比市场均值 {market_stats['avg_apy']:.1f}% 高出 "
                           f"{top.effective_apy - market_stats['avg_apy']:.1f} 个百分点",
        "top2_reason": "综合分次优选项",
        "top3_reason": "综合分第三选项",
        "risk_warning": "请注意 CEX 存在对手方风险，DeFi 存在合约风险。",
        "anomaly_alerts": [f.anomaly_flags for f in scored_products[:3] if f.anomaly_flags],
        "brief_for_card": [
            {"product_id": p.source_id, "one_liner": f"{p.effective_apy:.1f}% · {p.yield_source}"}
            for p in scored_products[:5]
        ],
    }
```

---

# 四、L4 渲染层 — 前端容器与数据灌注

## 4.1 设计原则

L4 是**纯展示层**，只负责把 L2 和 L3 的输出渲染成前端页面。
前端框架提供一组**通用容器组件**，每个容器接受固定 Props，由上游灌数据。

## 4.2 容器组件清单

| 容器 ID | 组件名 | 数据源 | 用途 |
|---|---|---|---|
| C1 | `<StatusBar />` | Pipeline 执行状态 | 顶部状态条 |
| C2 | `<HeroTopCard />` | `ScoredProduct[0]` + `DecisionOutput` | TOP 1 大卡 + 军师文案 |
| C3 | `<HeroStatsCard />` | `market_stats` + `DecisionOutput.opportunity_cost` | 扫描统计 + 机会成本 |
| C4 | `<SectionHeader />` | 静态 | "The Ranking" 标题 |
| C5 | `<ColumnHeader />` | 静态 | 表头行 |
| C6 | `<ProductRow />` | `ScoredProduct[i]` + `DecisionOutput.brief_for_card[i]` | 每行一个产品 |
| C7 | `<RadarCompare />` | 用户勾选的 2-4 个 `ScoredProduct` | 雷达对比图 |
| C8 | `<AnomalyBanner />` | `DecisionOutput.anomaly_alerts` | 异常预警横幅 |
| C9 | `<TrustPanel />` | `weights_used` + 方法论文案 + `raw_json` | 信任层 |
| C10 | `<Footer />` | 数据源列表 + 时间戳 + 免责 | 页脚 |

## 4.3 各容器 Props 详细定义

### C2 — `<HeroTopCard />`

```typescript
interface HeroTopCardProps {
  product: ScoredProduct;
  score: number;
  headline: string;            // from DecisionOutput
  top1_reason: string;         // from DecisionOutput
  principal: number;           // 用户本金
  annual_yield: number;        // = principal * effective_apy / 100
}
```

**渲染规则**：
- 左上角: venue 圆点 + `CEX`/`DeFi` 标签 + Tier 标签 + Chain (如有)
- 标题: platform_name (Fraunces 32px 700) + product_name (italic subtitle)
- 军师引用框: `top1_reason`，左侧 2px mint 色条
- 底部 4 列: APY / 产品类型 / 安全分 / 综合分，每列底色 `card` + border
- 如果 `anomaly_flags` 非空: 右上角显示 ⚠️ 角标

**边界情况**：
- `headline` 超过 40 字: 截断 + "…"
- `top1_reason` 为空 (LLM 降级): 使用 fallback 文案
- venue="DeFi" 且 chain 很长: 截断显示前 12 字符

### C6 — `<ProductRow />`

```typescript
interface ProductRowProps {
  product: ScoredProduct;
  rank: number;
  selected: boolean;           // 是否被勾选进雷达对比
  onToggle: () => void;
  one_liner: string | null;    // from DecisionOutput.brief_for_card
  principal: number;
}
```

**渲染规则 — 8 列 Grid**：

| 列 | 内容 | 数据字段 | 显示格式 | 颜色规则 |
|---|---|---|---|---|
| 1 | 复选框 | `selected` | mint accent checkbox | |
| 2 | 排名 | `rank` | Fraunces italic 24px | rank=1: mint, 其他: text4 |
| 3 | 产品信息 | platform + product + venue + tier + chain + one_liner | 3 行文本 | venue=CEX: coral dot, DeFi: mint dot |
| 4 | APY | `effective_apy` + `apy_30d_std` | 20px bold + "σ0.4 · 30D" | mint 色 |
| 5 | 便利性 | lock_days + redeem_delay_hours | "活期 T+0" / "锁7天" | 活期=mint, 锁仓=yellow |
| 6 | 安全 | security_score + audit count | "顶级" / "优良" / "中等" | ≥90:mint, ≥80:浅绿, ≥70:黄, <70:coral |
| 7 | 容量 | remaining_capacity + tvl_usd | "$8M" / "充足" | ∞=mint, <5M=yellow |
| 8 | 综合分 | composite_score | 24px bold | ≥85:mint, ≥70:yellow, <70:text2 |

**边界情况**：
- `effective_apy` 不同于 `apy_total`（因阶梯利率）: 显示 effective，tooltip 说明阶梯
- `anomaly_flags` 包含 `APY_OUTLIER`: APY 数字旁加 ⚠️ 图标
- `remaining_capacity` = 0: 整行灰色 + "已售罄" overlay
- `one_liner` 为 null (未匹配到 LLM 输出): 使用 `yield_source + why[:38]` 替代

### C7 — `<RadarCompare />`

**渲染规则**：
- 5 轴: 收益APY / 安全性 / 便利性 / 容量 / 稳定性
- 数据来自 `ScoredProduct.radar` (0-1 归一化值)
- 最多 4 个产品叠加，颜色: `[mint, coral, #9b9eff, yellow]`
- 右侧面板: 所选产品列表（含综合分 + 名称）
- 空状态: "点击左侧产品行的复选框，选 2-4 个加入对比"
- 产品数 < 2: 雷达图可画但意义不大，提示 "建议选 2 个以上对比"

## 4.4 数据灌注流程

```
L2 Output (ScoredProduct[]) ─────┬──────────────────────────────┐
                                 │                              │
L3 Output (DecisionOutput) ──────┤                              │
                                 │                              │
                                 ▼                              ▼
                    ┌──────────────────────┐    ┌──────────────────────┐
                    │  Template Binding     │    │  React State         │
                    │                      │    │                      │
                    │  hero_data = {       │    │  const [products,    │
                    │    product: sp[0],   │    │    setProducts] =    │
                    │    score: sp[0].     │    │    useState([]);     │
                    │      composite_score,│    │                      │
                    │    headline: dec.    │    │  const [decision,    │
                    │      headline,       │    │    setDecision] =    │
                    │    top1_reason: dec. │    │    useState(null);   │
                    │      top1_reason,    │    │                      │
                    │    principal: ctx.   │    │  // L4 只消费,       │
                    │      amount,         │    │  // 不做任何计算     │
                    │    annual_yield:     │    │                      │
                    │      ctx.amount *    │    │                      │
                    │      sp[0].eff_apy   │    │                      │
                    │      / 100           │    │                      │
                    │  }                   │    │                      │
                    └──────────────────────┘    └──────────────────────┘
```

---

# 五、Pipeline 编排 — Skill 执行流程

## 5.1 执行序列

```
用户点击 [▶ 帮我找最划算的]
    │
    ├── Phase 0: 解析 UserContext (从 sidebar 参数)          ~0ms
    │
    ├── Phase 1: L1 数据获取                                 ~1.5-4s
    │   ├── 1a. Antseer MCP: fetch_yield_products()         并发
    │   ├── 1b. Fallback: DefiLlama + CEX APIs              并发
    │   └── 1c. 合并去重 → RawProduct[]
    │
    ├── Phase 2: L2 计算加工                                 ~200ms
    │   ├── 2a. filter(raw, ctx)
    │   ├── 2b. enrich(filtered) — 查安全元数据
    │   ├── 2c. derive(enriched) — 历史统计 + 评分
    │   ├── 2d. normalize + score + rank
    │   └── 2e. anomaly_detect → ScoredProduct[]
    │
    ├── Phase 3: L3 决策推理                                 ~2-4s
    │   ├── 3a. 组装 prompt (ctx + top20 + market_stats)
    │   ├── 3b. 调用 LLM → DecisionOutput JSON
    │   └── 3c. 解析 + 校验 (schema validation)
    │          如果失败 → fallback_decision()
    │
    └── Phase 4: L4 渲染                                     ~100ms
        ├── 4a. 绑定数据到各容器 Props
        ├── 4b. setState 触发 React 渲染
        └── 4c. 动画入场 (fadeUp stagger)

总耗时预期: 3-8 秒 (取决于 LLM 响应)
Loading 动画覆盖 Phase 1-3
```

## 5.2 Loading 步骤映射

| 步骤 | 对应 Phase | 文案 | 进度 |
|---|---|---|---|
| 1 | 1a | "拉取 8 家 CEX 理财产品..." | 0-20% |
| 2 | 1b | "从 DefiLlama 同步 500+ DeFi 池..." | 20-40% |
| 3 | 2a-2c | "计算 30 日真实 APY 与稳定性..." | 40-55% |
| 4 | 2b | "更新平台信用与储备金状态..." | 55-70% |
| 5 | 2d-2e | "按你的安全/便利偏好加权评分..." | 70-85% |
| 6 | 3a-3c + 4 | "生成排行与对比视图..." | 85-100% |

## 5.3 Skill 包文件结构

```
yield-desk/
├── SKILL.md                    # Skill 入口描述 (被 trading-skill-creator 注册)
├── implementation/pipeline/
│   ├── orchestrator.py         # Pipeline 编排器 — 按 L1→L2→L3→L4 执行
│   ├── l1_data/
│   │   ├── fetcher.py          # 统一数据获取 (Antseer → fallback)
│   │   ├── schema.py           # RawProduct dataclass
│   │   ├── normalizer.py       # 各 API 响应 → RawProduct 的映射
│   │   └── sources/
│   │       ├── antseer.py      # Antseer MCP / REST client
│   │       ├── defillama.py    # DefiLlama Yields API client
│   │       ├── binance.py      # Binance Simple Earn client
│   │       ├── okx.py          # OKX Finance client
│   │       └── ...             # 其他 CEX
│   ├── l2_compute/
│   │   ├── filter.py           # Step 1 过滤
│   │   ├── enrich.py           # Step 2 补全
│   │   ├── derive.py           # Step 3 派生字段
│   │   ├── scorer.py           # Step 4-5 归一化 + 评分
│   │   ├── ranker.py           # Step 6 排序
│   │   ├── anomaly.py          # Step 7 异常检测
│   │   └── schema.py           # ScoredProduct dataclass
│   ├── l3_decision/
│   │   ├── prompt.md           # Decision Skill 的 system prompt
│   │   ├── decision.py         # LLM 调用 + 解析 + fallback
│   │   └── schema.py           # DecisionOutput dataclass
│   └── l4_render/
│       └── (渲染逻辑内嵌在 HTML 的 React 中)
├── implementation/data/
│   ├── platform_meta.yaml      # 平台安全元数据 (初始 + 人工维护)
│   └── protocol_meta.yaml      # DeFi 协议安全元数据
├── frontend/
│   └── yield-desk.html         # 单文件 HTML (React + Babel + D3)
│                                # 包含所有 L4 容器组件
│                                # L1-L3 在执行环境中调用, 结果注入前端
└── implementation/tests/
    ├── test_l2_scorer.py       # 评分逻辑单测
    ├── test_l2_edge_cases.py   # 边界情况测试
    └── fixtures/               # mock API 响应
```

---

# 六、边界情况与异常处理

## 6.1 数据层边界

| 场景 | 处理 | 前端表现 |
|---|---|---|
| Antseer 超时 (>10s) | 降级到直连各 API | 状态栏显示 "⚠ 部分数据源延迟" |
| 单个 CEX API 失败 | 跳过该平台, 继续处理 | 该平台产品不出现, footer 标注 |
| DefiLlama 返回空 | 仅展示 CEX | 提示 "DeFi 数据暂不可用" |
| API 返回 APY > 1000% | 视为脏数据, 丢弃 | 不展示 |
| API 返回 TVL = 0 | DeFi 池丢弃, CEX 保留 | |
| 阶梯利率导致 effective_apy 远低于 apy_total | 展示 effective, tooltip 说明 | 文案: "按你的本金 $100K, 适用阶梯利率" |

## 6.2 计算层边界

| 场景 | 处理 |
|---|---|
| 无 30 日历史 (新池) | apy_30d_std = 0, stability = 50 (中性) |
| security_score 计算为负 (多次安全事件) | floor = 0 |
| 用户本金 = 0 或未填 | 默认 $10,000 |
| 所有产品被 filter 清空 | 放宽安全过滤到 Tier 3, 重试; 仍空则提示 "无匹配" |
| 两个产品综合分完全相同 | 按 security_score 降序 → apy 降序 → platform 字母序 |
| Pendle PT 产品: lock_days > 100 但用户选了 "活期" | 被 filter 拦截, 不展示 |

## 6.3 决策层边界

| 场景 | 处理 |
|---|---|
| LLM 超时 (>15s) | 使用 fallback_decision() 模板输出 |
| LLM 返回非法 JSON | try parse → 失败 → fallback |
| LLM 编造了不存在的产品数据 | schema validation 校验 product_id 必须在 scored_products 里 |
| headline 超长 | 客户端截断 40 字 |
| anomaly_alerts 为 null | 转为 [] |

## 6.4 渲染层边界

| 场景 | 处理 |
|---|---|
| 产品数 < 3 | Hero 大卡仍展示 TOP 1, Ranking 正常, Radar 提示 "建议至少选 2 个" |
| 产品数 = 0 | 空状态: "当前条件下无匹配产品, 请放宽安全或便利要求" |
| 用户勾选 > 4 个进雷达 | 阻止勾选, toast "最多 4 个" |
| 极窄屏幕 (< 1200px) | 8 列 grid → 简化为 5 列 (隐藏便利/容量/安全文字, 保留综合分) |
| platform_name 超长 | 截断 16 字 + "…" |

---

# 七、Skill 包最终产物清单

| 文件 | 类型 | 作用 | 维护方 |
|---|---|---|---|
| `SKILL.md` | Skill 注册文件 | 被 trading-skill-creator 索引 | 开发 |
| `implementation/pipeline/orchestrator.py` | Python 脚本 | Pipeline 编排 | 开发 |
| `implementation/pipeline/l1_data/*` | Python 模块 | 数据获取 + Schema | 开发 |
| `implementation/pipeline/l2_compute/*` | Python 模块 | 固定算法 (filter/score/rank) | 开发 |
| `implementation/pipeline/l3_decision/prompt.md` | Markdown | LLM System Prompt | 产品 + 开发 |
| `implementation/pipeline/l3_decision/decision.py` | Python 模块 | LLM 调用 + fallback | 开发 |
| `implementation/data/platform_meta.yaml` | YAML | CEX 安全元数据 | 运营 (月度更新) |
| `implementation/data/protocol_meta.yaml` | YAML | DeFi 协议安全元数据 | 运营 (月度更新) |
| `implementation/frontend/yield-desk.html` | HTML (React) | 单文件前端, 含全部 L4 容器 | 开发 |
| `implementation/tests/*` | Python | L2 评分单测 + 边界测试 | 开发 |

---

*文档版本 v2.0 · 2026-04-10*
*下一步: 确认 Antseer 可提供的数据范围 → 实现 L1 fetcher → L2 scorer 单测 → L3 prompt 调优 → 前端集成*
