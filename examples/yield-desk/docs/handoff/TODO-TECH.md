# Yield Desk · 技术同事待办清单

> 本文档列出 Skill 包中所有需要技术同事完成或确认的事项。
> 标记: 🔴 阻塞上线 · 🟡 重要但有降级 · 🟢 优化项

---

## 一、L1 数据层 — API 接入

### 🔴 1.1 Antseer 聚合端点 (最高优先)

如果 Antseer 作为主通道，需要新增 3 个端点：

| 端点 | 文件 | 说明 |
|---|---|---|
| `GET /api/v1/earn/products` | `implementation/implementation/pipeline/l1_implementation/data/sources/antseer.py` | 返回全部 CEX+DeFi Earn 产品，统一为 RawProduct Schema |
| `GET /api/v1/yield/history` | 同上 | 单池 30 日 APY 时序 |
| `GET /api/v1/safety/meta` | 同上 | CEX+DeFi 安全元数据 (可选，也可用本地 YAML) |

**需确认**：
- [ ] Antseer base URL 是什么？
- [ ] 认证方式：Bearer token / API Key / HMAC？
- [ ] 返回的 JSON 结构——是否能直接对应 `RawProduct` 字段？
- [ ] 刷新频率保证 ≤ 5 分钟？

### 🔴 1.2 CEX Earn API 直连 (Fallback)

以下 5 家交易所的 Earn API 需要实现，代码在 `implementation/implementation/pipeline/l1_implementation/data/sources/cex_others.py`:

| 交易所 | 函数 | 状态 | 需要 |
|---|---|---|---|
| OKX | `fetch_okx_savings()` + `fetch_okx_staking()` + `normalize_okx()` | ❌ 存根 | API Key + 签名实现 |
| Bybit | `fetch_bybit_products()` + `normalize_bybit()` | ❌ 存根 | 确认 Earn API 是否需要 Key |
| Bitget | `fetch_bitget_products()` + `normalize_bitget()` | ❌ 存根 | API V2 签名 |
| KuCoin | `fetch_kucoin_products()` + `normalize_kucoin()` | ❌ 存根 | API V3 签名 |
| Gate.io | `fetch_gate_products()` + `normalize_gate()` | ❌ 存根 | API V4 签名 |
| HTX | `fetch_htx_products()` + `normalize_htx()` | ❌ 存根 | V2 Earn API |

**已完成**: Binance (`sources/binance.py`) + DefiLlama (`sources/defillama.py`)

**注意事项**：
- 每家 normalize 函数必须输出 `RawProduct` 格式
- 阶梯利率 `apr_tiers` 各家格式不同，需统一为 `{str: float}`
- `remaining_capacity` (剩余容量) 不是每家都有，没有的返回 None
- API Key 统一从环境变量读取，格式: `{EXCHANGE}_API_KEY` / `{EXCHANGE}_SECRET`

### 🟡 1.3 API Key 管理

- [ ] 确定 Key 存储方式: 环境变量 / Vault / Antseer 代理
- [ ] Binance / OKX 需要 HMAC 签名，其他交易所签名方式各异
- [ ] 建议: 如果 Antseer 已代理全部 CEX API，则 fallback 路径优先级降低

---

## 二、L2 计算层 — 需要完善的算法

### 🟡 2.1 阶梯利率解析

文件: `implementation/implementation/pipeline/l2_compute/compute.py` → `_find_tier_rate()`

当前实现是简化版（取第一档），需要完善：
- [ ] 解析 Binance 格式 `"0-5BTC": 0.05` → 根据用户本金找适用档
- [ ] 处理单位转换: BTC 数量 vs USDT 金额
- [ ] OKX/Bybit 可能用 `[{min, max, rate}]` 格式

### 🟡 2.2 手续费解析

文件: `implementation/implementation/pipeline/l2_compute/compute.py` → `_calc_convenience_score()`

当前手续费默认给 10 分（假设无手续费），需要：
- [ ] 解析 `fees` dict 中的 subscribe/redeem/gas_est 为百分比
- [ ] DeFi Gas 费估算需要实时 gas price（可从 Antseer 获取）

### 🟢 2.3 Pendle PT 锁仓天数

`implementation/implementation/data/protocol_meta.yaml` 中 Pendle 标注了需要根据到期日动态计算 `lock_days`：
- [ ] 在 `enrich()` 中，如果 `platform_slug == "pendle"`，从 DefiLlama pool 数据提取到期时间

---

## 三、L3 决策层 — LLM 集成

### 🔴 3.1 Anthropic API Key

文件: `implementation/implementation/pipeline/l3_decision/decision.py`

- [ ] `ANTHROPIC_API_KEY` 需要从环境变量读取
- [ ] 确认使用 Anthropic SDK 还是 httpx 直调（当前是 httpx）
- [ ] 如果在 Antseer 内部有 LLM 代理层，改为调代理

### 🟡 3.2 Prompt 调优

文件: `implementation/implementation/pipeline/l3_decision/prompt.md`

- [ ] 使用 `frontend/l3-decision-prompt-tuner.html` 调优工具跑完 4 个场景
- [ ] 根据 Quality Checklist 结果调整 prompt
- [ ] 关注: headline 长度 / 金字塔首句 / 异常叙事 / 边界场景弹性

---

## 四、数据层 — 元数据维护

### 🟡 4.1 初始数据校验

- [ ] `implementation/implementation/data/platform_meta.yaml` — 校验每家 CEX 的 tier / PoR 时间 / 审计信息
- [ ] `implementation/implementation/data/protocol_meta.yaml` — 校验每个 DeFi 协议的审计列表 / 事件历史
- [ ] 建立月度更新 SOP: 谁负责 / 数据来源 / 审批流程

### 🟢 4.2 自动化

- [ ] CryptoQuant PoR 数据自动更新 `last_por_at`
- [ ] Rekt News / SlowMist 安全事件自动更新 `incident_history`

---

## 五、前端 — 集成

### 🟡 5.1 Pipeline → 前端数据注入

当前 `implementation/implementation/frontend/yield-desk.html` 使用硬编码 mock 数据。需要：
- [ ] 将 `orchestrator.py` 的输出 JSON 注入前端
- [ ] 方式 A: 后端 API 返回 JSON，前端 fetch
- [ ] 方式 B: 在 Skill 执行环境中，Python 输出 JSON → 前端模板替换
- [ ] 方式 C: MCP 工具链中直接传递

### 🟢 5.2 响应式适配

- [ ] 窄屏 (<1200px) 简化列数
- [ ] 移动端适配

---

## 六、测试

### 🟡 6.1 L2 单测

文件: `implementation/implementation/tests/test_l2_scorer.py`

- [ ] 安装依赖: `pip install pyyaml`
- [ ] 运行: `python implementation/tests/test_l2_scorer.py`
- [ ] 当前覆盖: security_score / convenience_score / stability_score / filter / anomaly / rank
- [ ] 需补充: 阶梯利率 / 手续费解析 / 完整 run_l2 集成测试

### 🟢 6.2 L1 集成测试

- [ ] 需要真实 API Key 才能跑
- [ ] 建议: 录制一次真实 API 响应作为 fixture

---

## 七、部署

### 🔴 7.1 环境变量清单

```bash
# 必须
ANTHROPIC_API_KEY=sk-ant-...

# Antseer (主通道)
ANTSEER_API_KEY=...
ANTSEER_BASE_URL=https://api.antseer.ai/v1

# CEX Fallback (如果不走 Antseer)
BINANCE_API_KEY=...
BINANCE_SECRET=...
OKX_API_KEY=...
OKX_SECRET=...
OKX_PASSPHRASE=...
BYBIT_API_KEY=...
BYBIT_SECRET=...
# ... 其余交易所
```

### 🟡 7.2 依赖安装

```bash
pip install httpx pyyaml anthropic
```

---

## 完成状态汇总

| 模块 | 完成度 | 阻塞项 |
|---|---|---|
| L1 Antseer | 20% — 存根 | Antseer 端点确认 |
| L1 DefiLlama | ✅ 90% | 无 |
| L1 Binance | ✅ 80% | API Key |
| L1 其他 CEX | 5% — 存根 | 各家 API 实现 |
| L2 评分算法 | ✅ 95% | 阶梯利率完善 |
| L3 Decision | ✅ 85% | API Key + prompt 调优 |
| 数据 YAML | ✅ 90% | 人工校验 |
| 前端 HTML | ✅ 95% | 数据注入方式 |
| 单测 | ✅ 70% | 补充集成测试 |
